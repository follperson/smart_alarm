#!/usr/bin/env python3

import time
from numpy.random import randint
import os
import pyaudio
from google.cloud import texttospeech as tts
from .config import api_key_google_path
from .play import USBAUDIOID
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = api_key_google_path

p = pyaudio.PyAudio()
if USBAUDIOID is not None:
    SAMPLE_RATE = int(p.get_device_info_by_index(USBAUDIOID)['defaultSampleRate'])
else:
    SAMPLE_RATE = int(p.get_default_output_device_info()['defaultSampleRate'])


class WakeupSpeaker:
    class Voices:
        IraGlass = ['en-US-Wavenet-D', SAMPLE_RATE]
        BritishSnob = ['en-GB-Wavenet-D', SAMPLE_RATE]
        NiceBritishLady = ['en-GB-Wavenet-C', SAMPLE_RATE]

    def __init__(self, output_id=USBAUDIOID, volume_gain=0):
        self.client = tts.TextToSpeechClient()
        self.voice = None
        self.audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16,
                                            sample_rate_hertz=SAMPLE_RATE,
                                            volume_gain_db=volume_gain)

        self.pa = pyaudio.PyAudio()
        self.output_device_index = self.pa.get_default_output_device_info()['index'] if output_id is None else output_id
        self.play_stream = None

    def set_stream(self):
        channels = 1
        audio_format = pyaudio.paInt16
        info = self.pa.get_device_info_by_index(self.output_device_index)
        # device_sample_rate = info['defaultSampleRate']
        print('Audio Device Name:', info['name'])
        # device_sample_rate = int(device_sample_rate)
        # sample_rate = max(device_sample_rate, sample_rate)
        # print(f'device sample rate: {device_sample_rate}, audioo sample rate: {sample_rate}, using bigger one')
        self.play_stream = self.pa.open(format=audio_format, channels=channels, rate=SAMPLE_RATE, output=True,
                                        output_device_index=self.output_device_index)

    def initialize(self):
        self.choose_voice()
        self.set_stream()

    def choose_voice(self, voice_info=None):
        if voice_info is None:
            voices = self.client.list_voices(language_code='en')
            voice_info_list = [[voice.name, voice.natural_sample_rate_hertz] for voice in voices.voices]
            voice_info = randomly_select_from_list(voice_info_list)
        choice, sample_rate = voice_info
        lang = '-'.join(choice.split('-')[:2])
        self.voice = tts.VoiceSelectionParams(language_code=lang, name=choice)
        return voice_info

    def get_audio_bits_from_text(self, text):
        synthesis_input = tts.SynthesisInput(text=text)
        response = self.client.synthesize_speech(input=synthesis_input, voice=self.voice,
                                                 audio_config=self.audio_config)
        return response.audio_content

    def read_aloud(self, text, filename=None, write=False):
        audio_content = self.get_audio_bits_from_text(text)
        if write:
            if filename is None:
                filename = 'Testing'
            with open('%s.wav' % filename, 'wb') as out:
                out.write(audio_content )

            os.system("start %s.wav" % filename)
            sleep_time = int(text.count(' ') / 1.5)
            time.sleep(sleep_time) # todo: wait here in a better way
        else:
            self.play_stream.start_stream()
            self.play_stream.write(audio_content)
            self.play_stream.stop_stream()

    def close(self):
        self.play_stream.close()
        self.pa.terminate()


def randomly_select_from_list(choices, neg_filter='ignore', pos_filter='-'):
    choices = [i for i in choices if neg_filter not in i[0] and pos_filter in i[0]]
    return choices[randint(len(choices))]


if __name__ == '__main__':
    speaker = WakeupSpeaker()
    speaker.initialize()
    speaker.read_aloud('The Dog is very small')