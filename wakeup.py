from voice import WakeupSpeaker
from quotes import get_weather_nws, get_weather_owm, get_quote
from record_audio import SoundRecorderAnalyzer
import datetime as dt


def get_wake_time(wakeup_hour=7):
    tomorrow = dt.datetime(dt.datetime.now().year, dt.datetime.now().month, dt.datetime.now().day) + dt.timedelta(1,60 * 60 * wakeup_hour)
    return (tomorrow - dt.datetime.now()).seconds / 60 / 60


def record_ready(num_hours=1, to_record=False, name=SoundRecorderAnalyzer.Names.WORK, record_period=10):
    start = dt.datetime.now()
    print('Begin',start)
    sleep_period = 0
    sound_recorder = SoundRecorderAnalyzer(name, record_secs=record_period, sleep_period=sleep_period, to_record=to_record)
    sound_recorder.record_hours(num_hours=num_hours)
    time_taken = (dt.datetime.now() - start)
    print('Finish', dt.datetime.now())
    print('Took', time_taken)
    read_aloud()


def alarm(weekend=False):
    if weekend:
        waketime = 9
    else:
        waketime =7.06
    time_til_wake = get_wake_time(wakeup_hour=waketime)
    print(time_til_wake)
    record_ready(time_til_wake, False, name=SoundRecorderAnalyzer.Names.SLEEPING,record_period=90)

def read_aloud():
    ws = WakeupSpeaker()
    ws.initialize()
    weather_nws = get_weather_nws()
    weather_owm = get_weather_owm()
    quote = get_quote()
    for text in [weather_nws, weather_owm, quote]:
        ws.read_aloud(text)


if __name__ == '__main__':
    # record_ready(name='Work 30', record_period/=30, num_hours=1)
    # record_ready(name='Period Test 5',record_period = 5)
    alarm(True)
