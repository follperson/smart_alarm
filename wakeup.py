from voice import WakeupSpeaker
from quotes import get_weather_nws, get_weather_owm, get_quote
from record_audio import SoundRecorderAnalyzer
import datetime as dt
from pydub import AudioSegment

def get_wake_time(wakeup_hour=7):
    tomorrow = dt.datetime(dt.datetime.now().year, dt.datetime.now().month, dt.datetime.now().day) + dt.timedelta(1,60 * 60 * wakeup_hour)
    return (tomorrow - dt.datetime.now()).seconds / 60 / 60


def record_ready(num_hours=1, to_record=False, name=SoundRecorderAnalyzer.Names.WORK, record_period=10, wake_window=30):
    start = dt.datetime.now()
    print('Begin',start)
    sleep_period = 0
    sound_recorder = SoundRecorderAnalyzer(name, record_secs=record_period, sleep_period=sleep_period, to_record=to_record)
    sound_recorder.record_hours(num_hours=num_hours)
    time_taken = (dt.datetime.now() - start)
    print('Finish', dt.datetime.now())
    print('Took', time_taken)
    read_aloud()


def record_ready_slowroll(num_hours=1, to_record=False, name=SoundRecorderAnalyzer.Names.WORK, record_period=10, wake_window=30):
    start = dt.datetime.now()
    print('Begin',start)
    sleep_period = 0
    sound_recorder = SoundRecorderAnalyzer(name, record_secs=record_period, sleep_period=sleep_period, to_record=to_record)
    sound_recorder.record_hours(num_hours=num_hours - wake_window / 60)
    from play import Song
    import time
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


def record_ready_slowroll_mp(num_hours=1, to_record=False, name=SoundRecorderAnalyzer.Names.WORK, record_period=10, wake_window=30):
    start = dt.datetime.now()
    print('Begin',start)
    sleep_period = 0
    start_wakeup = (num_hours - (wake_window / 60)) * 60
    if start_wakeup < 0:
        start_wakeup = 0
    from threading import Thread
    recorder = SoundRecorderAnalyzer(name, record_secs=record_period, sleep_period=sleep_period, to_record=to_record)
    recorder_thread = Thread(target=recorder.record_hours, kwargs={'num_hours': num_hours})
    recorder_thread.start()
    import time
    time.sleep(start_wakeup * 60)
    # sound_recorder.record_hours(num_hours=num_hours - wake_window / 60)
    from play import Song

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

# button to stop alarm and start good morning
# button to stop alarm and good morning  (press first one twice)

def alarm(waketime=7):
    time_til_wake = get_wake_time(waketime)
    # record_ready(time_til_wake, False, name=SoundRecorderAnalyzer.Names.SLEEPING)
    record_ready_slowroll(time_til_wake, False, name=SoundRecorderAnalyzer.Names.SLEEPING, wake_window=17)

# def alarm_with_buffer():
#     wake=7
#     buffer=30



def read_aloud():
    ws = WakeupSpeaker()
    ws.initialize()
    weather_nws = get_weather_nws()
    weather_owm = get_weather_owm()
    quote = get_quote()
    for text in [weather_nws, weather_owm, quote]:
        ws.read_aloud(text)


if __name__ == '__main__':
    # record_ready(.02)
    # alarm(9.25)
    # read_aloud()
    # record_ready_slowroll(.5, wake_window=17)
    record_ready_slowroll_mp(.1, wake_window=17)