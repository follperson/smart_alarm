import pandas as pd
from .db import get_db
from threading import Thread
import time
import datetime as dt
from math import ceil
from .code.wakeup import read_aloud as read_weather_quote
from .code.play import Song
from .utils import get_repeat_dates
from flask import g, app, current_app, Blueprint, render_template, request

bp = Blueprint('wakeup', __name__,url_prefix='/')


def close_watchers(e=None):
    watcher = g.pop('watcher', None)
    if watcher is not None:
        watcher.close()


def init_app(app):
    app.teardown_appcontext(close_watchers())

def get_watcher():
    try:
        current_app.watcher
    except AttributeError as ok:
        watcher = AlarmWatcher()
        print('Begin Run Watcher for the first time')
        current_app.watcher = watcher
    current_app.watcher.check()
    return current_app.watcher


def get_days_from_now(today, next_day):
    days_from_now = 7 - today + next_day
    if days_from_now >= 7:
        return days_from_now - 7
    return days_from_now


@bp.route('/', methods=('GET', 'POST'))
def view():
    db = get_db()
    watcher = get_watcher()
    if request.method == 'POST':
        print(request.form)
        for alarm in watcher.alarms:
            aid = str(alarm.id)
            if aid in request.form:
                break
        assert aid in request.form
        if request.form[aid] == 'Snooze':
            alarm.snooze()
        elif request.form[aid] == 'TurnOff':
            if alarm.on:
                alarm.turnoff()
            else:
                alarm.turnon()
    return render_template('active/index.html', alarms=watcher.alarms)


class Alarm(Thread):
    def __init__(self, id, beg_vol=-60, end_vol=0,*args, **kwargs):
        self.id = id
        self.alarm_time = None
        self.sound_profile = None
        self.color_profile = None
        self.wake_window = None
        self.repeat_days = []
        self.on = False
        self.snoozed = False
        self.current_song = None
        self.snooze_time = 10 # give this to the alarm table
        self.next_alarm_datetime = None
        self.time_til_wake = None
        self.initialized_time = dt.datetime.now()
        self.running = False
        self.vol = beg_vol
        self.vol_change_total = abs(end_vol - beg_vol)
        Thread.__init__(self, *args, **kwargs)
        self.get_alarm()
        self.start()

    def play_song(self, index, time_left):
        fp, start, end, max_duration = self.sound_profile.df.loc[
            index, ['filepath', 'audio_start', 'audio_end', 'duration']]
        duration = max(end, max_duration)
        if start == -1:
            start = 0
        if duration > time_left: # shouldnt happen
            duration = time_left
        if ceil(duration) <= 0: # also shouldnt happen
            return
        print(fp)
        # print(start, ceil(duration))
        vol_increase = self.vol_change_total * duration / self.wake_window
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
                time.sleep(self.snooze_time * 60)
                self.current_song.play()
                # todo add more snooze options
            if not self.running:
                self.current_song.stop()
                break
            i += 1
            time_left = self.wake_window - snooze_check_window
            self.vol += vol_increase / check_periods
        self.current_song.pause()
        self.current_song.join(0)
        if self.vol != local_max:
            print('Current Volume is %s, supposed to be %s' % (self.vol, local_max))
        return time_left

    def check(self):
        if self.next_alarm_datetime - dt.timedelta(seconds=self.wake_window) <= dt.datetime.now():
            return True
        return False

    def run(self):
        # print("Checking %s" % self.name)
        if not self.check():
            return
        print('Beginning Alarm Sequence for %s' % self.name)
        self.running = True
        time_left = min(self.wake_window, self.get_time_til_wake().seconds)
        if time_left != self.wake_window: print('under wake window amount of time')
        for i in self.sound_profile.df.index:
            time_left = self.play_song(i, time_left)
        read_weather_quote()
        self.running = False

    def _get_alarm_db(self):
        alarm_info = g.db.execute('SELECT * FROM alarms WHERE id=?', (self.id,)).fetchone()
        self.alarm_time = alarm_info['alarm_time'] # string
        self.name = alarm_info['name']
        self.repeat_days = get_repeat_dates(alarm_info, string=False)
        playlist_id = alarm_info['sound_profile']
        self.sound_profile = Playlist(playlist_id=playlist_id)
        self.wake_window = self.sound_profile.wake_window
        self.color_profile = alarm_info['color_profile'] # todo
        self.on = alarm_info['active']

    def _get_alarm_countdown(self):
        self.get_next_alarm_time()
        self.get_time_til_wake()

    def get_alarm(self):
        self._get_alarm_db()
        self._get_alarm_countdown()


    # todo put generic snooze in

    def turnoff(self):
        self.on = False
        self.running = False
        g.db.execute('UPDATE alarms SET active = 0 WHERE id=?', (self.id,))
        g.db.commit()

    def snooze(self):
        self.snoozed = True

    def turnon(self):
        self.on = True
        g.db.execute('UPDATE alarms SET active = 1 WHERE id=?', (self.id,))
        g.db.commit()

    def get_next_alarm_time(self):
        now = dt.datetime.now()
        today = now.weekday()
        alarm_hour = int(self.alarm_time.split(':')[0])
        alarm_min = int(self.alarm_time.split(':')[-1])
        if not any([today <= day for day in self.repeat_days]):
            next_day = self.repeat_days[0]
            days_from_now = get_days_from_now(today, next_day)
        else:
            if today in self.repeat_days:
                if (now.hour == alarm_hour and now.minute < alarm_min) or (now.hour < alarm_hour):
                    days_from_now = 0
                else:
                    days_from_now = 7
            else:
                for day in self.repeat_days:
                    if today < day:
                        next_day = day
                        days_from_now = get_days_from_now(today, next_day)
                        break
        self.next_alarm_datetime = dt.datetime.combine(now.date() + dt.timedelta(days=days_from_now), dt.time(alarm_hour,alarm_min))
        return self.next_alarm_datetime

    def get_time_til_wake(self):
        self.time_til_wake = self.next_alarm_datetime - dt.datetime.now()
        return self.time_til_wake


class Playlist(object):
    def __init__(self, playlist_id=None, name=None):
        if playlist_id is not None and name is None:
            self.playlist_id = playlist_id
            self.name = self.get_name()
        elif playlist_id is None and name is not None:
            self.name = name
            self.playlist_id = self.get_playlist_id()
        else:
            raise NotImplementedError('You must pass either a playlist id or a name')
        self.df = self.get_playlist()
        self.wake_window = self.get_wake_window()

    def get_name(self):
        return g.db.execute('SELECT name FROM playlists WHERE id=?', (self.playlist_id,)).fetchone()['name']

    def get_playlist_id(self):
        return g.db.execute('SELECT id FROM playlists WHERE name=?', (self.name,)).fetchone()['id']

    def get_playlist(self):
        df_playlist = pd.read_sql('SELECT * FROM playlist WHERE playlist_id=%s' % self.playlist_id, con=g.db)
        df_sounds = pd.read_sql('SELECT * FROM audio', con=g.db).rename(columns={'id': 'audio_id'})
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
        self.wake_window = wake_window
        return self.wake_window


class AlarmWatcher(Thread):
    def __init__(self):
        self.alarms = []
        self.closed = False
        get_db()
        Thread.__init__(self)
        self.start()

    def check(self):
        df_alarms = pd.read_sql('SELECT id, name, modified FROM alarms', con=g.db).set_index('id')
        for i in range(len(self.alarms)):
            alarm = self.alarms[i]
            if alarm.initialized_time < df_alarms.loc[alarm.id, 'modified']:
                alarm.turnoff()
                print(alarm.initialized_time, 'is less than', df_alarms.loc[alarm.id, 'modified'])
                alarm = Alarm(alarm.id)
            else:
                alarm._get_alarm_countdown()
            alarm.check()
            self.alarms[i] = alarm
        df_alarms = df_alarms[~df_alarms['name'].isin([alarm.name for alarm in self.alarms])]
        if not df_alarms.empty:
            for alarm_id in df_alarms.index:
                alarm = Alarm(alarm_id)
                self.alarms.append(alarm)

    def run(self):
        while not self.closed:
            print("Inside Washer, checking")
            self.check()
            time.sleep(20)

    def close(self):
        self.closed = True

    def get_alarm(self):
        for alarm in self.alarms:
            if alarm.on:
                return alarm
