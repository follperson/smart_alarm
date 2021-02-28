import pandas as pd
from threading import Thread, Event
import time
import sqlite3
import datetime as dt
from math import ceil
from .code.wakeup import read_aloud as read_weather_quote
from .code.play import Song
from .code.utils import get_repeat_dates, get_db_generic
from typing import List
from flask import current_app

# todo update self.time_left to 0 when alarm is going? 

def get_days_from_now(today: int, day_list: List[int]):
    try:
        next_day = [day for day in day_list if day > today][0]
    except IndexError:
        next_day = day_list[0]
    if today < next_day:
        return next_day - today
    elif today == next_day:
        return 7
    else:
        return 7 - today + next_day

class _Alarm(Thread):
    def __init__(self, id, db_params, beg_vol=-30, end_vol=0, *args, **kwargs):
        # todo only turn on alarm when we are starting it??
        self.id = id
        self.alarm_time = None
        self.sound_profile = None
        self.color_profile = None
        self.wake_window = None
        self.repeat_days = []
        self.on = False
        self.snoozed = False
        self.current_song = None
        self.snooze_time = 2 # give this to the alarm table
        self.snooze_time_left = 0
        self.next_alarm_datetime = None
        self.time_til_wake = None
        self.initialized_time = dt.datetime.now()
        self.running = False
        self.db_params = db_params
        self.vol = beg_vol
        self.vol_change_total = abs(end_vol - beg_vol)
        Thread.__init__(self, *args, **kwargs)
        self.get_alarm()
        self.start()

    def play_song(self, index, time_left):
        fp, start, end, max_duration = self.sound_profile.df.loc[
            index, ['filepath', 'audio_start', 'audio_end', 'duration']]
        duration = max(end, max_duration)
        if duration is None:
            print('dura none')
            duration = time_left
        if time_left is None:
            print('tl none')
            time_left = duration 
        if start == -1:
            start = 0
        if duration > time_left:  # shouldnt happen
            duration = time_left  # but if it does we go with the 'time left' indicator
        if ceil(duration) <= 0:  # also shouldnt happen
            return  # need to be positive duration
        print(time_left, duration)
        vol_increase = self.vol_change_total * duration / time_left
        local_max = self.vol + vol_increase
        self.current_song = Song(fp, min_vol=self.vol, max_vol=local_max, start_sec=start, end_sec=ceil(duration))
        self.current_song.play()

        snooze_check_window = .25
        check_periods = ceil(duration / snooze_check_window)
        i = 0
        while i < check_periods:
            time.sleep(snooze_check_window)
            if self.snoozed:
                print("le snooze")
                self.current_song.pause()
                for i in range(self.snooze_time * 60):
                    time.sleep(.99)
                    self.snooze_time_left = self.snooze_time * 60 - i
                    self.next_alarm_datetime = dt.datetime.now() + dt.timedelta(seconds=time_left + self.snooze_time_left) # dev??
                self.current_song.play()
                print("le snooze is over")
                self.snoozed = False
                # todo add more snooze options
            if not self.running:
                self.current_song.stop()
                break
            i += 1
            time_left = time_left - snooze_check_window
            self.vol += vol_increase / check_periods
        # time_left = time_left - duration
        self.current_song.pause()
        self.current_song.join(0)
        if self.vol != local_max:
            print('Current Volume is %s, supposed to be %s' % (self.vol, local_max))

        return time_left

    def check(self):
        self._get_alarm_countdown()
        if self.on:
            if self.next_alarm_datetime - dt.timedelta(seconds=self.wake_window) <= dt.datetime.now():
                return True
        return False

    def start_alarm(self):
        print('Beginning Alarm Sequence for %s' % self.name)
        self.running = True
        time_left = min(self.wake_window, self.get_time_til_wake().seconds)
        if time_left != self.wake_window: print('under wake window amount of time')
        for i in self.sound_profile.df.index:
            time_left = self.play_song(i, time_left)
            if not self.running:
                return
        read_weather_quote()
        self.running = False
        print('Completed Alarm Sequence for %s' % self.name)

    def run(self):
        while self.on:
            if self.check():
                self.start_alarm()
            time.sleep(1)

    def _get_alarm_db(self):
        db = get_db_generic(self.db_params)
        alarm_info = db.execute('SELECT * FROM alarms WHERE id=?', (self.id,)).fetchone()
        self.alarm_time = alarm_info['alarm_time'] # string
        self.name = alarm_info['name']
        self.repeat_days = get_repeat_dates(alarm_info, string=False)
        playlist_id = alarm_info['sound_profile']
        self.sound_profile = Playlist(self.db_params, playlist_id=playlist_id)
        self.wake_window = self.sound_profile.wake_window
        self.color_profile = alarm_info['color_profile'] # todo
        self.on = alarm_info['active']

    def _get_alarm_countdown(self):
        self.get_next_alarm_time()
        self.get_time_til_wake()

    def get_alarm(self):
        self._get_alarm_db()
        self._get_alarm_countdown()

    def turnoff(self, change_db=True):
        self.on = False
        self.running = False
        if change_db:
            self.db_turn_on_off(0)

    def snooze(self):
        self.snoozed = True
        self.snooze_time_left = self.snooze_time * 60

    def db_turn_on_off(self, on):
        db = get_db_generic(self.db_params)
        db.execute('UPDATE alarms SET active = ?, modified = ? WHERE id=?', (int(on), dt.datetime.now(), self.id,))
        db.commit()

    def turnon(self, change_db=True):
        self.on = True
        if change_db:
            self.db_turn_on_off(1)

    def get_next_alarm_time(self):
        now = dt.datetime.now()
        today = now.weekday()
        alarm_hour = int(self.alarm_time.split(':')[0])
        alarm_min = int(self.alarm_time.split(':')[-1])
        if today in self.repeat_days and (
                (now.hour == alarm_hour and now.minute < alarm_min) or now.hour < alarm_hour):
            days_from_now = 0
        else:
            days_from_now = get_days_from_now(today, self.repeat_days)
        self.next_alarm_datetime = dt.datetime.combine(now.date() +
                                                       dt.timedelta(days=days_from_now),
                                                       dt.time(alarm_hour, alarm_min))
        return self.next_alarm_datetime

    def get_time_til_wake(self):
        time_til_wake = self.next_alarm_datetime - dt.datetime.now()
        self.time_til_wake = time_til_wake - dt.timedelta(microseconds=time_til_wake.microseconds)
        return self.time_til_wake


class Alarm(Thread):
    def __init__(self, id, next_alarm_time, alarm_time, playlist, color_profile, wake_window, name, active,
                 beg_vol=-30, end_vol=0, snooze_time=2,  *args, **kwargs):
        self.alarm_id = id
        self.alarm_time = alarm_time
        self.next_alarm_time = next_alarm_time
        self.alarm_name = name
        self.playlist = playlist
        self.color_profile = color_profile
        self.wake_window = wake_window
        self.snooze_min = snooze_time
        self.vol = beg_vol
        self.active = active
        self.vol_change_total = abs(end_vol - beg_vol)

        self.snoozed = False
        self.snooze_time_left = 0
        self.current_song = None
        self.initialized_time = dt.datetime.now()

        Thread.__init__(self, *args, **kwargs)
        self._stop_event = Event()

    def play_audio(self, index, time_left):
        fp, start, end, max_duration = self.playlist.loc[
            index, ['filepath', 'audio_start', 'audio_end', 'duration']]
        duration = max(end, max_duration)
        if duration > time_left:  # shouldnt happen
            duration = time_left  # but if it does we go with the 'time left' indicator
        if ceil(duration) <= 0:  # also shouldnt happen
            return  # need to be positive duration
        print(fp, time_left, duration)
        vol_increase = self.vol_change_total * duration / time_left
        local_max = self.vol + vol_increase
        self.current_song = Song(fp, min_vol=self.vol, max_vol=local_max, start_sec=start, end_sec=ceil(duration))
        self.current_song.play()

        snooze_check_window = .25
        check_periods = ceil(duration / snooze_check_window)
        i = 0
        while (i < check_periods) and not self.stopped():
            time.sleep(snooze_check_window)
            if self.snoozed:
                self._snooze()
            i += 1
            time_left = time_left - snooze_check_window
            self.vol += vol_increase / check_periods

        self.current_song.stop()
        if self.vol != local_max:
            print('Current Volume is %s, supposed to be %s' % (self.vol, local_max))

        return time_left

    def _snooze(self):
        print('le snooze')
        self.current_song.pause()
        while self.snooze_time_left > 0:
            time.sleep(.99)
            self.snooze_time_left -= 1
            if self.stopped():
                return
        print('le snooze is over')
        self.current_song.play()
        self.snoozed = False

    def run(self):
        self.run_alarm()

    def run_alarm(self):
        print('Beginning Alarm Sequence for %s' % self.alarm_name)
        time_left = self.wake_window
        for i in self.playlist.index:
            time_left = self.play_audio(i, time_left)
            if self.stopped():
                print('Ended Alarm Sequence %s Early' % self.alarm_name)
                break
        if not self.stopped():
            read_weather_quote()
        print('Completed Alarm Sequence for %s' % self.alarm_name)

    def stop(self):
        if self.current_song is not None:
            self.current_song.stop()
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def snooze(self):
        self.snoozed = True
        self.snooze_time_left = self.snooze_min * 60


def get_time_til_wake(next_alarm_datetime):
    time_til_wake = next_alarm_datetime - dt.datetime.now()
    time_til_wake = time_til_wake - dt.timedelta(microseconds=time_til_wake.microseconds)
    return time_til_wake


def get_next_alarm_time(alarm_time, repeat_days):
    now = dt.datetime.now()
    today = now.weekday()
    alarm_hour, alarm_min = alarm_time.split(':')
    alarm_hour, alarm_min = int(alarm_hour), int(alarm_min)
    if today in repeat_days and (
            (now.hour == alarm_hour and now.minute < alarm_min) or now.hour < alarm_hour):
        days_from_now = 0
    else:
        days_from_now = get_days_from_now(today, repeat_days)
    next_alarm_datetime = dt.datetime.combine(now.date() +
                                                   dt.timedelta(days=days_from_now),
                                                   dt.time(alarm_hour, alarm_min))
    return next_alarm_datetime


class Playlist(object):
    """
        Class to manage the audio playlist being used
    """
    def __init__(self, db_params, playlist_id=None, name=None):
        self.db_params = db_params
        if playlist_id is not None and name is None:
            self.playlist_id = playlist_id
            self.name = self.get_name()
        elif playlist_id is None and name is not None:
            self.name = name
            self.playlist_id = self.get_playlist_id()
        else:
            raise NotImplementedError('You must pass either a playlist id or a name')
        self.df = self.get_playlist()
        self.wake_window = 0
        self.get_wake_window()

    def get_name(self):
        db = get_db_generic(self.db_params)
        return db.execute('SELECT name FROM playlists WHERE id=?', (self.playlist_id,)).fetchone()['name']

    def get_playlist_id(self):
        db = get_db_generic(self.db_params)
        return db.execute('SELECT id FROM playlists WHERE name=?', (self.name,)).fetchone()['id']

    def get_playlist(self):
        db = get_db_generic(self.db_params)
        df_playlist = pd.read_sql('SELECT * FROM playlist WHERE playlist_id=%s' % self.playlist_id, con=db)
        df_sounds = pd.read_sql('SELECT * FROM audio', con=db).rename(columns={'id': 'audio_id'})
        df_playlist = pd.merge(df_playlist, df_sounds, how='inner', on='audio_id')
        self.df = df_playlist
        return df_playlist

    def get_wake_window(self):
        wake_window = 0
        for i in self.df.index:
            start, end, max_length = self.df.loc[i, ['audio_start', 'audio_end', 'duration']]
            if (end > max_length) or (end <= 0):
                end = max_length
            wake_window += end - start
        self.wake_window = int(wake_window)
        return self.wake_window

class _AlarmWatcher(Thread):
    def __init__(self):
        self.alarms = []
        self.closed = False
        self.db_params = None
        self.get_db()
        Thread.__init__(self)
        self.start()

    def get_db(self):
        if self.db_params is None:
            self.db_params = current_app.config['DATABASE']
        db = sqlite3.connect(self.db_params,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        db.row_factory = sqlite3.Row
        return db

    def check(self):
        """
            Check the database for any new alarms we should be aware of
        :return:
        """
        print('checking')
        db = self.get_db()

        # Look at the to find what we expect from the web app
        df_alarms = pd.read_sql('SELECT id, name, modified FROM alarms', con=db).set_index('id')

        for i in range(len(self.alarms)):
            # working on each alarm one by one
            alarm = self.alarms[i]

            if alarm.initialized_time < df_alarms.loc[alarm.id, 'modified']:
                # if we have modified the alarm in the database since we initialized the alarm thread
                #  turn it off and start a new one
                alarm.turnoff(False)
                alarm = Alarm(alarm.id, self.db_params)
                self.alarms[i] = alarm

        # Looking at only the alarms that we do not currenlty have active
        df_alarms = df_alarms[~df_alarms['name'].isin([alarm.name for alarm in self.alarms])]

        # start it up
        for alarm_id in df_alarms.index:
            alarm = Alarm(alarm_id, self.db_params)
            self.alarms.append(alarm)
        
    def run(self):
        while not self.closed:
            time.sleep(20)
            self.check()


    def close(self):
        self.closed = True

    def get_alarm(self):
        for alarm in self.alarms: # ugly
            if alarm.on:
                return alarm


class AlarmWatcher(Thread):
    def __init__(self):
        self.alarms = dict()
        self.closed = False
        self.db_params = current_app.config['DATABASE']
        Thread.__init__(self)
        self.start()

    def run(self):
        while not self.closed:
            time.sleep(20)
            self.check()

    def check(self):
        print('checking')

        db = get_db_generic(self.db_params)
        # Look at the to find what we expect from the web app
        df_alarms = pd.read_sql('SELECT * FROM alarms', con=db).set_index('id')
        if df_alarms.empty:
            return
        df_alarms.loc[:, 'dow'] = df_alarms.apply(lambda x: get_repeat_dates(x, False), axis=1)
        alarm_ids =list(self.alarms.keys())
        for alarm_id in alarm_ids:
            if self.alarms[alarm_id].stopped():
                print('pop', alarm_id)
                self.alarms.pop(alarm_id)

        for alarm_id in df_alarms.index:
            if alarm_id in self.alarms:
                if df_alarms.loc[alarm_id, 'modified'] > self.alarms[alarm_id].initialized_time:
                    old_alarm = self.alarms.pop(alarm_id)
                    old_alarm.stop()
                    self.alarms[alarm_id] = get_alarm(df_alarms=df_alarms, alarm_id=alarm_id, db=db)
            else:
                self.alarms[alarm_id] = get_alarm(df_alarms=df_alarms, alarm_id=alarm_id, db=db)
            alarm = self.alarms[alarm_id]
            if alarm.active and \
                    not alarm.isAlive() and \
                    (alarm.next_alarm_time - dt.timedelta(seconds=int(alarm.wake_window)) < dt.datetime.now()):
                alarm.start()

    def close(self):
        self.closed = True

    def get_alarm(self):
        for alarm in self.alarms:
            if not alarm.stopped():
                return alarm


def get_alarm(df_alarms, alarm_id, db):
    dow, alarm_time, wake_window, active, playlist_id, name, color_profile = df_alarms.loc[
        alarm_id, ['dow', 'alarm_time', 'wake_window', 'active', 'sound_profile', 'name', 'color_profile']]

    next_alarm_time = get_next_alarm_time(alarm_time, dow)

    df_playlist = pd.read_sql('SELECT * FROM playlist INNER JOIN '
                              '(select * from audio) a '
                              'ON a.id = playlist.audio_id '
                              'WHERE playlist_id=%s' % playlist_id, con=db)

    return Alarm(id=alarm_id, name=name, alarm_time=alarm_time, next_alarm_time=next_alarm_time,
                 wake_window=wake_window, snooze_time=2,
                 playlist=df_playlist, color_profile=color_profile, active=active)