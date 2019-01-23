from voice import WakeupSpeaker
from quotes import get_weather_nws, get_weather_owm, get_quote
from record_audio import SoundRecorderAnalyzer
from play import Song, get_playlist
from threading import Thread
from math import ceil
import datetime as dt
import time


def get_wake_time(wakeup_hour=7.):
    tomorrow = dt.datetime(dt.datetime.now().year, dt.datetime.now().month, dt.datetime.now().day) + dt.timedelta(1,60 * 60 * wakeup_hour)
    return (tomorrow - dt.datetime.now()).seconds / 60 / 60


def record_ready(num_hours=1., to_record=False, name=SoundRecorderAnalyzer.Names.WORK, record_period=10):
    sleep_period = 0
    sound_recorder = SoundRecorderAnalyzer(name, record_secs=record_period, sleep_period=sleep_period, to_record=to_record)
    sound_recorder.record_hours(num_hours=num_hours)


def record_ready_slowroll(num_hours=1, to_record=False, name=SoundRecorderAnalyzer.Names.WORK, record_period=10, wake_window=30):
    start = dt.datetime.now()
    print('Begin',start)
    sleep_period = 0
    sound_recorder = SoundRecorderAnalyzer(name, record_secs=record_period, sleep_period=sleep_period, to_record=to_record)
    sound_recorder.record_hours(num_hours=num_hours - wake_window / 60)

    example_song = r"C:\Users\follm\Downloads\torrents\audio\Brian Eno - Ambient 1 Music for Airports Electronic\Brian Eno - Ambient 1 Music for Airports [FLAC-Lossless]\01 Brian Eno - 1-1.flac"
    try:
        song = Song(example_song)
        song.play()
    except Exception as ok:
        print('Failure with the ol soundy', ok)
        pass
    time.sleep(wake_window * 60)
    time_taken = (dt.datetime.now() - start)
    print('Finish', dt.datetime.now())
    print('Took', time_taken)
    read_aloud()


def slow_alarm(playlist_name, num_hours, min_vol=-60, max_vol=0, max_time=10**10):
    time_left = max_time # in seconds
    vol = min_vol
    vol_change_total = abs(max_vol - vol)
    playlist = get_playlist(playlist_name)
    total_secs = playlist['length'].sum()
    if total_secs > max_time:
        total_secs = max_time
    # todo turn this sleep into a loop which checks for input, so i can say stop calm sounds and start wakeup now
    wakeup_buffer = num_hours * 60 * 60 - total_secs
    if wakeup_buffer < 0:
        wakeup_buffer = 0
    time.sleep(wakeup_buffer)

    for fp, duration in playlist[['filepath', 'length']].values:  # add start and end times to the playlist feature (soundprofile= plalist??)
        print(fp)
        if duration > time_left:
            duration = time_left
        if ceil(duration) == 0:
            break
        local_max = vol + vol_change_total * duration / total_secs
        song = Song(fp, min_vol=vol, max_vol=local_max, start_sec=0, end_sec=ceil(duration))
        song.play()
        time.sleep(duration)  # song plays on separate thread
        time_left = total_secs - ceil(duration)
        vol = local_max
    read_aloud()


# button to stop alarm and start good morning
# button to stop alarm and good morning  (press first one twice)


def alarm(waketime=7., playlist_name='Huerco S', wake_window=15):
    num_hours = get_wake_time(waketime)
    print(num_hours)
    name = SoundRecorderAnalyzer.Names.SLEEPING
    record_time = num_hours - wake_window / 60
    if record_time > 0:
        recorder = Thread(target=record_ready, kwargs={'name':name, 'num_hours':record_time})
        recorder.start()
    slow_alarm(playlist_name, num_hours=num_hours, max_time=wake_window * 60)


def read_aloud():
    ws = WakeupSpeaker()
    ws.initialize()
    weather_nws = get_weather_nws()
    weather_owm = get_weather_owm()
    quote = get_quote()
    for text in [weather_nws, weather_owm, quote]:
        ws.read_aloud(text)


def main():
    playlist_name = 'Eno 1'
    # playlist_name = 'Elliot Smith Either Or'
    # playlist_name = 'Bird Songs'
    alarm(waketime=6, playlist_name=playlist_name)

if __name__ == '__main__':
    main()