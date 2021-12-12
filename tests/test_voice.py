from smart_alarm.src.voice import WakeupSpeaker
initial_text = 'Testing Google text to speech. If you can hear this, then your Google voice credentials and your speakers work'

def test_voice(text=initial_text):
    speaker = WakeupSpeaker(volume_gain=-2)
    speaker.initialize()
    speaker.read_aloud(text)

if __name__ == '__main__':
    test_voice()