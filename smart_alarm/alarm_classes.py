import pandas as pd
from threading import Thread, Event
import time
import datetime as dt
import json
from math import ceil
from .src.wakeup import WakeupSpeaker, get_weather_nws, get_weather_owm, get_quote
from .src.play import Song
from .src.color import ColorProfile, Colors
from .src.utils import get_repeat_dates_list, get_db_generic
from typing import List
from flask import current_app
from flask.logging import default_handler
import logging
logger = logging.getLogger(__name__)
logger.addHandler(default_handler)
logger.setLevel(logging.INFO)
# todo make wake_window consistent just pulled

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
                 beg_vol=-40, end_vol=-12, snooze_time=2,  *args, **kwargs):
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

        self.muted = False
        self.blinded = False
        self.skip_songs = False

        self.current_song = None
        self.colors = None
        
        self.initialized_time = dt.datetime.now()

        Thread.__init__(self, *args, name=name, **kwargs)
        self._stop_event = Event()

    def play_audio(self, index, time_left):
        fp, start, end, max_duration = self.playlist.loc[index, ['filepath', 'audio_start', 'audio_end', 'duration']]
        duration = max(end, max_duration)
        if duration > time_left:  # shouldnt happen
            duration = time_left  # but if it does we go with the 'time left' indicator
        if ceil(duration) <= 0:  # also shouldnt happen
            return  # need to be positive duration
        print(fp, time_left, duration)
        vol_increase = self.vol_change_total * (duration / time_left) # something messed up here with snooze
        local_max = min(self.vol + vol_increase, self.end_vol)
        logger.info(f'Starting Song: {fp}')
        self.current_song = Song(fp, min_vol=self.vol, max_vol=local_max, start_sec=start, end_sec=ceil(duration))
        logger.info(f'using outpud ID: {self.current_song.output_device_index}')
        if not self.muted:
            self.current_song.play()
        else:
            logger.info(f'Song is Muted so we are chilling')
        snooze_check_window = .25
        check_periods = ceil(duration / snooze_check_window)
        i = 0
        while (i < check_periods) and not self.stopped():
            time.sleep(snooze_check_window)
            if self.snoozed:
                self._snooze()
            if self.skip_songs:
                break
            i += 1
            time_left = time_left - snooze_check_window
            self.vol += vol_increase / check_periods

        self.current_song.stop()
        self.current_song = None

        self.vol = min(self.end_vol, local_max)
        return time_left

    def play_colors(self):
        logger.info('loading colors', self.color_profile)
        color_info = ColorProfile(**self.color_profile)
        logger.info('setting color')
        self.colors = Colors(color_info, seconds=self.wake_window)
        logger.info('set, now playing')
        self.colors.play()
        
    def _snooze(self):
        logger.info('Snoozing')
        self.colors.pause()
        self.current_song.pause()
        while self.snooze_time_left > 0:
            time.sleep(.99)
            self.snooze_time_left -= 1
            if self.stopped():
                return
        logger.info('le snooze is over')
        self.current_song.play()
        self.colors.play()
        self.snoozed = False

    def run(self):
        self.run_alarm()

    def run_playlist(self):
        time_left = self.wake_window
        for i in self.playlist.index:
            if self.stopped() or self.skip_songs:
                logger.info('Ended Alarm Sequence %s Early' % self.alarm_name)
                break
            time_left = self.play_audio(i, time_left)

    def run_text_to_voice(self):
        ws = WakeupSpeaker(volume_gain=self.end_vol)
        ws.initialize()
        try:
            weather_nws = get_weather_nws()
            weather_owm = get_weather_owm()
            quote = get_quote()
        except Exception as e:
            logger.info('Error getting info')
            logger.info(str(e))
        else:
            for text in [weather_nws, weather_owm, quote]:
                if not self.stopped() and not self.muted:
                    ws.read_aloud(text)

    def run_alarm(self):
        logger.info('Beginning Alarm Sequence for %s' % self.alarm_name)
        self.play_colors()
        self.run_playlist()
        self.run_text_to_voice()
        self.stop()
        logger.info('Completed Alarm Sequence for %s' % self.alarm_name)

    def stop(self):
        if self.current_song is not None:
            self.current_song.stop()
        if self.colors is not None:
            self.colors.stop()
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def snooze(self):
        self.snoozed = True
        self.snooze_time_left = self.snooze_min * 60

    def mute(self):
        print('muting')
        if isinstance(self.current_song, Song):
            self.current_song.pause()
            self.muted = True

    def unmute(self):
        print('unmuting')
        if isinstance(self.current_song, Song):
            if self.current_song.is_paused:
                self.current_song.play()
            self.muted = False

    def blind(self):
        print('blinding')
        if isinstance(self.colors, Colors):
            self.colors.pause()
            self.blinded = True

    def unblind(self):
        print('blinding')
        if isinstance(self.colors, Colors):
            if self.colors.is_paused:
                self.colors.play()
            self.blinded = False

    def skip(self):
        print('skipping songs')
        self.skip_songs = True

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
        self.alarms = dict()  # {id: object}
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
        df_alarms = pd.read_sql("""SELECT * FROM alarms inner join
                                         (select id cid, profile cprofile from color_profiles) colors
                                        on alarms.color_profile=colors.cid
                                        inner join
                                         (select id pid, wake_window from playlists) playlists
                                   on alarms.sound_profile=playlists.pid""", con=db).set_index('id')

        df_alarms['color_profile'] = df_alarms['cprofile'].apply(json.loads)
        if df_alarms.empty:
            return
        df_alarms.loc[:, 'dow'] = df_alarms.apply(lambda x: get_repeat_dates_list(x), axis=1)
        alarm_ids = list(self.alarms.keys())
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
                try:
                    alarm.start()
                except RuntimeError as e:
                    logger.info('error:', str(e))
                    # raise MultipleAlarmStartAttempts('Alarm:' + str(alarm.name))
                    continue

    def close(self):
        self.closed = True

    def get_alarm(self):
        for alarm in self.alarms:
            if not alarm.stopped():
                return alarm


def get_alarm(df_alarms, alarm_id, db):
    print(df_alarms.loc[alarm_id,['dow', 'alarm_time', 'wake_window', 'active', 'sound_profile', 'name', 'color_profile']])
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

class MultipleAlarmStartAttempts(Exception):
    pass

