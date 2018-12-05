#!/usr/bin/env python3

import time
from numpy.random import randint
import os
import pyaudio
from google.cloud import texttospeech
from config import api_key_google_path

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = api_key_google_path


class WakeupSpeaker():
    class Voices:
        IraGlass = ['en-US-Wavenet-D', 24000]
        BritishSnob = ['en-GB-Wavenet-D', 24000]
        NiceBritishLady = ['en-GB-Wavenet-C', 24000]

    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()
        self.voice = None
        self.samp_rate = None
        self.audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)
        self.play_audio = pyaudio.PyAudio()
        self.play_stream = None


    def set_stream(self):
        channels = 1
        audio_format = pyaudio.paInt16
        self.play_stream = self.play_audio.open(format=audio_format, channels=channels, rate=self.samp_rate,
                                                output=True)

    def initialize(self):
        self.choose_voice()
        self.set_stream()

    def choose_voice(self, voice_info=None):
        if voice_info is None:
            voices = self.client.list_voices('en')
            voice_info_list = [[voice.name, voice.natural_sample_rate_hertz] for voice in voices.voices]
            voice_info = randomly_select_from_list(voice_info_list)
        choice, samp_rate = voice_info
        lang = '-'.join(choice.split('-')[:2])
        print(lang, choice, samp_rate)
        self.voice = texttospeech.types.VoiceSelectionParams(language_code=lang, name=choice)
        if samp_rate != self.samp_rate:
            self.samp_rate = samp_rate
            self.set_stream()

    def read_aloud(self, text, filename=None, write=False):
        synthesis_input = texttospeech.types.SynthesisInput(text=text)
        response = self.client.synthesize_speech(synthesis_input, self.voice, self.audio_config)
        if write:
            if filename is None:
                filename = 'Testing'
            with open('%s.wav' % filename, 'wb') as out:
                out.write(response.audio_content)
            os.system("start %s.wav" % filename)
            sleep_time = int(text.count(' ') / 1.5)
            time.sleep(sleep_time)
        else:
            self.play_stream.start_stream()
            self.play_stream.write(response.audio_content)
            self.play_stream.stop_stream()


    def close():
        self.play_stream.close()
        self.play_audio.terminate()


def randomly_select_from_list(choices, neg_filter='ignore', pos_filter='-'):
    choices = [i for i in choices if neg_filter not in i[0] and pos_filter in i[0]]
    return choices[randint(len(choices))]

# todo: https://cloud.google.com/speech-to-text/ (interpret us saying shutup)

if __name__ == '__main__':
    main()
