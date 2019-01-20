import pyaudio
import wave
import audioop
import pandas as pd
import time
import matplotlib.pyplot as plt
import datetime as dt
from scipy.ndimage.filters import gaussian_filter1d
import os
import numpy as np


class SoundRecorderAnalyzer(object):
    class Names:
        HOME = 'Home'
        SLEEPING = 'Sleeping'
        WORK = 'Work'

    def __init__(self, name='', record_secs=5, sleep_period=10, to_record=False):
        self.record_secs = record_secs
        self.sleep_period = sleep_period
        self.to_record = to_record

        self.form_1 = pyaudio.paInt16  # 16-bit resolution
        self.chans = 1  # 1 channel
        self.samp_rate = 44100  # 44.1kHz sampling rate
        self.chunk = 4096  # 2^12 samples for buffer
        self.dev_index = 1  # device index found by p.get_device_info_by_index(ii)
        self.audio = pyaudio.PyAudio()  # create pyaudio instantiation
        stream = self.audio.open(format=self.form_1, rate=self.samp_rate, channels=self.chans,
                                 input_device_index=self.dev_index, input=True,
                                 frames_per_buffer=self.chunk)
        self.stream = stream
        self.frames_to_record = int((self.samp_rate / self.chunk) * self.record_secs)
        mic_name = self.audio.get_device_info_by_index(self.dev_index).get('name')
        print('Using microphone %s' % mic_name)
        buffer = mic_name + '_' + str(dt.datetime.now()).split('.')[0].replace(':', '.')
        self.name = name + '_' + buffer
        if self.to_record:
            os.makedirs('audio_records\\%s' % self.name)

    def check_name(self):
        for ii in range(self.audio.get_device_count()):
            print(self.audio.get_device_info_by_index(ii).get('name'))

    def record(self):
        frames = []
        audio_power = []
        self.stream.start_stream()
        for ii in range(0, self.frames_to_record):
            data = self.stream.read(self.chunk)
            audio_power.append(audioop.rms(data, self.audio.get_sample_size(self.form_1)))
            if self.to_record:
                frames.append(data)
        self.stream.stop_stream()

        if self.to_record:
            wavefile = wave.open('audio_records\\%s\\audio at %s.wav' % (self.name, str(time.time()).split('.')[0]), 'wb')
            wavefile.setnchannels(self.chans)
            wavefile.setsampwidth(self.audio.get_sample_size(self.form_1))
            wavefile.setframerate(self.samp_rate)
            wavefile.writeframes(b''.join(frames))
            wavefile.close()
        return audio_power

    def collect_n_soundamps(self,n=10):
        data = []
        for i in range(n):
            print(round((i+1) / n, 4))
            start = time.time()
            amplitude = self.record()
            avg_amp = sum(amplitude) / len(amplitude)
            print(avg_amp)
            data.append([i,start, avg_amp, amplitude])
            time.sleep(self.sleep_period)
        self.stream.close()
        self.audio.terminate()
        df = pd.DataFrame(data, columns=['index', 'start_time', 'average_amplitude', 'full_amplitude'])
        if not os.path.exists('data_collection\\%s' % self.name):
            os.makedirs('data_collection\\%s'  % self.name)
        df.to_csv('data_collection\\%s\\data_collection_raw.csv' % self.name)
        return df

    def record_hours(self, num_hours):
        seconds_total = num_hours * 60 * 60
        rolling_window = 5*60 // (self.record_secs + self.sleep_period) # x min window (x min / time record period)
        num_periods = seconds_total / (self.sleep_period + self.record_secs)
        print(num_periods)
        df = self.collect_n_soundamps(n=int(num_periods))
        self.smooth_transform_write(df, 'average_amplitude')
        # self.construct_rolling_volume(df, 'average_amplitude', rolling_window)
        data = []
        frame_length = self.record_secs / self.frames_to_record
        for start_time, full_amplitude in df[['start_time', 'full_amplitude']].values.tolist():
            for i, v in enumerate(full_amplitude):
                data.append([start_time + i * frame_length, v])
        df_full = pd.DataFrame(data, columns=['start_time', 'actual amplitude'])
        self.smooth_transform_write(df_full, 'actual amplitude', 2 * self.record_secs)
        # self.construct_rolling_volume(df_full, 'actual amplitude', rolling_window * self.frames_to_record)


    def smooth_transform_write(self, df, col, multiplier=1, datetime_index=True):
        if not os.path.exists('audio_graphs\\' + self.name):
            os.makedirs('audio_graphs\\' + self.name)
        if datetime_index:
            df.index = pd.DatetimeIndex((df['start_time'] - 3600 * 5) * 10 ** 9)  # utc offset, convert from sec to nano
        df_aa = self.smooth_graph(df, col, multiplier=multiplier)
        df_aa.plot(figsize=(50, 30))
        plt.savefig('audio_graphs\\%s\\%s_(%s).png' % (self.name, col, str(time.time()).split('.')[0]))

        df.loc[df[col] == 0, col] = 1
        df['log_%s' % col] = np.log(df[col])
        df_laa = self.smooth_graph(df, 'log_%s' % col, multiplier=multiplier)
        df_laa.plot(figsize=(50, 30))
        plt.savefig('audio_graphs\\%s\\log_%s_(%s).png' % (self.name, col, str(time.time()).split('.')[0]))

    def construct_rolling_volume(self,df, col, window_base):
        df[col + '_rolling_' + str(window_base)] = df[col].rolling(window=window_base).sum() / window_base
        df[col + '_rolling_' + str(window_base * 2)] = df[col].rolling(window=window_base * 2).sum() / (2*window_base )
        df[col + '_rolling_' + str(window_base * 4)] = df[col].rolling(window=window_base * 4).sum() / (4*window_base)
        df[[col + '_rolling_' + str(window_base), col + '_rolling_' + str(window_base * 2),
            col + '_rolling_' + str(window_base * 4)]].plot(figsize=(50, 30))
        plt.savefig('audio_graphs\\%s\\%s_rolling_(%s).png' % (self.name, col, str(time.time()).split('.')[0]))

    @staticmethod
    def smooth_graph(df, col, multiplier):
        df['%s_smoothed_gaussian_%s' % (col, 1 * multiplier)] = gaussian_filter1d(df[col], 1 * multiplier)
        df['%s_smoothed_gaussian_%s' % (col, 2 * multiplier)] = gaussian_filter1d(df[col], 2*multiplier)
        df['%s_smoothed_gaussian_%s' % (col, 4*multiplier)] = gaussian_filter1d(df[col], 4*multiplier)
        return df[['%s_smoothed_gaussian_%s' % (col, 1 * multiplier), '%s_smoothed_gaussian_%s' % (col, 2 * multiplier), '%s_smoothed_gaussian_%s' % (col, 4 * multiplier)]]
