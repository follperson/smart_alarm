import pandas as pd
from threading import Thread, Event
import time
import datetime as dt
from math import ceil
from .code.wakeup import read_aloud as read_weather_quote
from .code.play import Song
from .code.utils import get_repeat_dates, get_db_generic
from typing import List
from flask import current_app


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


class Alarm(Thread):
    def __init__(self, id, next_alarm_time, alarm_time, playlist, color_profile, wake_window, name, active,
                 beg_vol=-30, end_vol=-10, snooze_time=2,  *args, **kwargs):
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
        self.end_vol = end_vol
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
        vol_increase = self.vol_change_total * duration / time_left # something messed up here with snooze
        local_max = min(self.vol + vol_increase, self.end_vol)
        self.current_song = Song(fp, min_vol=self.vol, max_vol=local_max,
                                 start_sec=start, end_sec=ceil(duration))
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
        self.current_song = None
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
        self.stop()
        
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