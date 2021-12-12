from smart_alarm.src.color import white_ColorProfile, Colors, ColorProfile, time


def test_colors(profile: ColorProfile = white_ColorProfile, seconds=25):
    leds = Colors(profile, seconds=seconds)
    leds.play()
    time.sleep(seconds)


