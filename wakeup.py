from voice import WakeupSpeaker
from quotes import get_weather_nws, get_weather_owm, get_quote
from record_audio import SoundRecorderAnalyzer
from play import Song, get_playlist
from threading import Thread
import datetime as dt
import time


def get_wake_time(wakeup_hour=7):
    tomorrow = dt.datetime(dt.datetime.now().year, dt.datetime.now().month, dt.datetime.now().day) + dt.timedelta(1,60 * 60 * wakeup_hour)
    return (tomorrow - dt.datetime.now()).seconds / 60 / 60


def record_ready(num_hours=1, to_record=False, name=SoundRecorderAnalyzer.Names.WORK, record_period=10):
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


def slow_alarm(playlist_name, num_hours, min_vol=-60, max_vol=0):
    vol = min_vol
    vol_change_total = abs(max_vol - vol)
    playlist = get_playlist(playlist_name)
    total_secs = playlist['length'].sum()
    # todo turn this sleep into somtn else so i can say stopp and start wakeup now
    wakeup_buffer = num_hours * 60 * 60 - total_secs
    if wakeup_buffer < 0:
        wakeup_buffer = 0
    time.sleep(wakeup_buffer)
    for fp, duration in playlist[['filepath', 'length']].values:
        print(fp, duration)
        local_max = vol + vol_change_total * duration / total_secs
        song = Song(fp, min_vol=vol, max_vol=local_max)
        song.play()
        time.sleep(duration)  # song plays on separate thread
        vol = local_max
    read_aloud()


# button to stop alarm and start good morning
# button to stop alarm and good morning  (press first one twice)


def alarm(waketime=7, playlist_name='Huerco S'):
    num_hours = get_wake_time(waketime)
    name = SoundRecorderAnalyzer.Names.SLEEPING
    recorder = Thread(target=record_ready, kwargs={'name':name, 'num_hours':num_hours})
    recorder.start()
    slow_alarm(playlist_name, num_hours=num_hours)


def read_aloud():
    ws = WakeupSpeaker()
    ws.initialize()
    weather_nws = get_weather_nws()
    weather_owm = get_weather_owm()
    quote = get_quote()
    for text in [weather_nws, weather_owm, quote]:
        ws.read_aloud(text)


def main():
    # playlist_name = 'Eno 1'
    # playlist_name = 'Elliot Smith Either Or'
    # playlist_name = 'Bird Songs'
    alarm(waketime=9)


if __name__ == '__main__':
    main()