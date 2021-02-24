import pyaudio
import wave
import audioop
import pandas as pd
import time
import datetime as dt

import threading
import os
import numpy as np


class SoundRecorderAnalyzer(threading.Thread):
    """
      Record sleeping audio using Thread object. 
       This currently specifies the amount of time we seek to record and sleep 
       Might be better served if it is not prespecified and just waits for an external event
      (like a executive thread telling it to stop) 
    """

    class Names:
        HOME = 'Home'
        SLEEPING = 'Sleeping'
        WORK = 'Work'

    def __init__(self, name='', record_secs=5, sleep_period=10, to_record=False, record_hours=8, *args, **kwargs):
        """
          Setup object for recording audio.
        inputs:
          name: str name for saving files
          record_secs: int number of seconds in each audio record window to get idea of audio intensity
          sleep_period: int number of seconds between each audio recording period
          to_record: bool if we want to save the audio itself or just the images
          record_hours:  number of hours we are going to record
        """
        self.record_secs = record_secs
        self.sleep_period = sleep_period
        self.to_record = to_record
        self.name = name
        self.form_1 = pyaudio.paInt16  # 16-bit resolution
        self.chans = 1  # 1 channel
        self.samp_rate = 44100  # 44.1kHz sampling rate
        self.chunk = 4096  # 2^12 samples for buffer
        self.dev_index = 1  # device index found by p.get_device_info_by_index(ii)
        self.audio = pyaudio.PyAudio()  # create pyaudio instantiation
        self.frames_to_record = int((self.samp_rate / self.chunk) * self.record_secs)
        self.hours_to_record = record_hours
        self.stream = None
        self.image_paths = dict()
        self.__quit = False

        threading.Thread.__init__(*args, **kwargs)
        self.start()


    def initialize(self):
        """
          Open up the input audio stream functionality with PyAudio
        """
        stream = self.audio.open(format=self.form_1, rate=self.samp_rate, channels=self.chans,
                                 input_device_index=self.dev_index, input=True,
                                 frames_per_buffer=self.chunk)
        self.stream = stream

        # need to specify microphone neame. Can be finicky
        mic_name = self.audio.get_device_info_by_index(self.dev_index).get('name')
        print('Using microphone %s' % mic_name)
        buffer = mic_name + '_' + str(dt.datetime.now()).split('.')[0].replace(':', '.')
        self.name = self.name + '_' + buffer
        if self.to_record:
            os.makedirs('audio_records\\%s' % self.name)

    def check_name(self):
        """ helper function to get the microphone name """
        for ii in range(self.audio.get_device_count()):
            print(self.audio.get_device_info_by_index(ii).get('name'))

    def record(self):
        """
          Record audio snippet, single datapoint in hourly record
        """
        frames = []
        audio_power = []
        self.stream.start_stream()
        # for each audio frame, record a chunk
        for ii in range(0, self.frames_to_record):
            try:
                data = self.stream.read(self.chunk)
            except OSError as disconn:
                self.initialize()
                print('Lost connection, reinitializing')
                data = self.stream.read(self.chunk)
            
            # get power of the audio signal (loudness, kind of)
            audio_power.append(audioop.rms(data, self.audio.get_sample_size(self.form_1)))
            
            if self.to_record:
                frames.append(data)
            if self.__quit:
                break

        # done recording audio, close the audio input object
        self.stream.stop_stream()

        if self.to_record:
            wavefile = wave.open('audio_records\\%s\\audio at %s.wav' % (self.name, str(time.time()).split('.')[0]), 'wb')
            wavefile.setnchannels(self.chans)
            wavefile.setsampwidth(self.audio.get_sample_size(self.form_1))
            wavefile.setframerate(self.samp_rate)
            wavefile.writeframes(b''.join(frames))
            wavefile.close()
        return audio_power

    def quit(self):
        self.__quit = True

    def collect_n_soundamps(self,n=10):
        """
          Primary recorder main function. This iterates over a specified set of recording periods,
           and executes the self.record() function over each window. 
           Between each recording instance we pause for 'self.sleep_period' seconds
        inputs:
          n: number of recording periods
        """
        data = []
        for i in range(n):
            print(round((i+1) / n, 4))
            start = time.time()
            amplitude = self.record()
            avg_amp = sum(amplitude) / len(amplitude)
            print(avg_amp)
            data.append([i,start, avg_amp, amplitude])
            if self.__quit:
                break
            time.sleep(self.sleep_period)

        # finished with the audio recording period, close out
        self.stream.close()
        self.audio.terminate()

        # compile data into dataframe, and save it
        df = pd.DataFrame(data, columns=['index', 'start_time', 'average_amplitude', 'full_amplitude'])
        if not os.path.exists('data_collection\\%s' % self.name):
            os.makedirs('data_collection\\%s'  % self.name)
        df.to_csv('data_collection\\%s\\data_collection_raw.csv' % self.name)
        return df

    def record_hours(self):
        """
          Main Driver. Computes window to record, calls amplitude recorder,  
        """
        print(self.hours_to_record)
        seconds_total = self.hours_to_record * 60 * 60
        rolling_window = 5 * 60 // (
                    self.record_secs + self.sleep_period)  # x min window (x min / time record period to approximate the right time)
        if self.Names.SLEEPING in self.name:
            rolling_window *= 4

        # calculate number of periods to be recorded
        num_periods = seconds_total / (self.sleep_period + self.record_secs)
        print(num_periods)

        # Collect the audio
        df = self.collect_n_soundamps(n=int(num_periods))

        # draw graphs 
        self.smooth_transform_write(df, 'average_amplitude', 2)
        self.construct_rolling_volume(df, 'average_amplitude', rolling_window)
        data = []
        frame_length = self.record_secs / self.frames_to_record
        for start_time, full_amplitude in df[['start_time', 'full_amplitude']].values.tolist():
            for i, v in enumerate(full_amplitude):
                data.append([start_time + i * frame_length, v])
        df_full = pd.DataFrame(data, columns=['start_time', 'actual amplitude'])
        self.smooth_transform_write(df_full, 'actual amplitude', 4 * self.record_secs)
        self.construct_rolling_volume(df_full, 'actual amplitude', rolling_window * self.frames_to_record)

    def run(self):
        self.initialize()
        self.record_hours()
        return self.image_paths

    def smooth_transform_write(self, df, col, smoothing_multiplier=1, datetime_index=True):
        """
          Save graphs of amplitude over time
        inputs:
          df: dataframe with series of observations, each row is a record
          col: column of amplitude to be calculated
          multiplier: 
          datetime_index: boolean if we wish to coerce the x axis to a datetime
        """
        import matplotlib.pyplot as plt

        if not os.path.exists('audio_graphs\\' + self.name):
            os.makedirs('audio_graphs\\' + self.name)
        if datetime_index:
            df.index = pd.DatetimeIndex((df['start_time'] - 3600 * 5) * 10 ** 9)  # utc offset, convert from sec to nano
        
        # Construct smoothing calculations for graphing
        df_aa = self.smoothing_calcs(df, col, smoothing_multiplier=smoothing_multiplier)
        df_aa.plot(figsize=(50, 30))
        fp = 'audio_graphs\\%s\\%s_(%s).png' % (self.name, col, str(time.time()).split('.')[0])
        self.image_paths[col] = fp
        plt.savefig(fp)

        # log transformations of amplitudes, then smooth, then graph
        df.loc[df[col] == 0, col] = 1
        df['log_%s' % col] = np.log(df[col])
        df_laa = self.smoothing_calcs(df, 'log_%s' % col, smoothing_multiplier=smoothing_multiplier)
        df_laa.plot(figsize=(50, 30))
        fp_log = 'audio_graphs\\%s\\log_%s_(%s).png' % (self.name, col, str(time.time()).split('.')[0])
        self.image_paths['Log(%s)' % col] = fp_log
        plt.savefig(fp_log)

    def construct_rolling_volume(self, df, col, window_base):
        """
          Construct the rolling amplitude, for an alternate amplitude calc
        inputs:
          df: dataframe of amplitudes recorded
          col: amplitude of columns 
        """
        df[col + '_rolling_' + str(window_base)] = df[col].rolling(window=window_base).sum() / window_base
        df[col + '_rolling_' + str(window_base * 2)] = df[col].rolling(window=window_base * 2).sum() / (2*window_base)
        df[col + '_rolling_' + str(window_base * 4)] = df[col].rolling(window=window_base * 4).sum() / (4*window_base)
        df[[col + '_rolling_' + str(window_base), 
            col + '_rolling_' + str(window_base * 2),
            col + '_rolling_' + str(window_base * 4)]].plot(
                figsize=(50, 30))
        fp = 'audio_graphs\\%s\\%s_rolling_(%s).png' % (self.name, col, str(time.time()).split('.')[0])
        self.image_paths['Rolling ' + col] = fp
        plt.savefig(fp)

    @staticmethod
    def smoothing_calcs(df, col, smoothing_multiplier):
        """ gaussian filter of the data to reduce outliers (low pass filter), makes data smoother"""
        from scipy.ndimage.filters import gaussian_filter1d
        df['%s_smoothed_gaussian_%s' % (col, 1 * smoothing_multiplier)] = gaussian_filter1d(df[col], 1 * smoothing_multiplier)
        df['%s_smoothed_gaussian_%s' % (col, 2 * smoothing_multiplier)] = gaussian_filter1d(df[col], 2*smoothing_multiplier)
        df['%s_smoothed_gaussian_%s' % (col, 4*smoothing_multiplier)] = gaussian_filter1d(df[col], 4*smoothing_multiplier)
        return df[['%s_smoothed_gaussian_%s' % (col, 1 * smoothing_multiplier), '%s_smoothed_gaussian_%s' % (col, 2 * smoothing_multiplier), '%s_smoothed_gaussian_%s' % (col, 4 * multiplier)]]
