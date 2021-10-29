from os.path import basename
from pydub import AudioSegment
from pydub.utils import make_chunks
from pyaudio import PyAudio
from threading import Thread, Event
import time
from .utils import get_logger
from math import ceil
import pandas as pd
SECOND = 1000
time.sleep(5)
p = PyAudio()
try:
    USBAUDIOID = [i for i in range(p.get_device_count()) if 'USB' in p.get_device_info_by_index(i)['name']][0]
except IndexError:
    USBAUDIOID = None

logger = get_logger('play-audio')


def get_playlist(name):
    df = pd.read_csv('assets\\playlists\\playlists.csv')
    df_songs = pd.read_csv('assets\\playlists\\songs.csv')
    playlist = pd.merge(df.loc[df['name'] == name][['filepath']], df_songs, how='left',on='filepath')
    return playlist

# todo change the way that the sound rises over time - more at end less at beginning


class Song(Thread):
    """
      Audio player object building on Thread object and PyAudio
      Used to play audio files
    """
    def __init__(self, f, min_vol=-60, max_vol=0, start_sec=0, end_sec=6000,
                 output_device_index=USBAUDIOID, *args, **kwargs):
        """
        inputs:
            f: filepath of audiofile
            min_vol: minimum volume
            max_vol: maximum volume
            start_sec: second of the song which we will start playing from
            end_sec: ending second of the song 
        """
        logger.debug(f'initialize song file {f}')
        # initalize audio object
        self.seg = AudioSegment.from_file(f)
        self.filename = f
        # print('audiosegment set')
        # limit audio to be accessed to just the window between start and end seconds
        self.seg = self.seg[start_sec * SECOND:end_sec * SECOND]
        self.is_paused = True
        self.p = PyAudio()
        self.cur_vol = min_vol
        self.max_vol = max_vol
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.output_device_index = output_device_index
        Thread.__init__(self, name=basename(f), *args, **kwargs)
        # print('Thread goes')

        # Thread functions
        self._stop_event = Event()
        self.start()

    def pause(self):
        """ pause the audio """ 
        self.is_paused = True

    def is_paused(self):
        return self.is_paused

    def stop(self):
        """ end the audio to kill the song """
        # self.p.terminate()
        self._stop_event.set()

    def stopped(self):
        """ check if the thread is stopped """
        return self._stop_event.is_set()

    def play(self):
        self.is_paused = False

    def __get_stream(self):
        """ access the audio handler for playing audio"""
        # print('open stream')
        
        if self.output_device_index is not None:
            info = self.p.get_device_info_by_index(self.output_device_index)
        else:
            info = self.p.get_default_output_device_info()
        device_sample_rate = info['defaultSampleRate']
        logger.debug(f'Using Audio Device: {info["name"]}')
        device_sample_rate = int(device_sample_rate)        
        sample_rate = max(device_sample_rate, self.seg.frame_rate)
        return self.p.open(format=self.p.get_format_from_width(self.seg.sample_width),
                           channels=self.seg.channels,
                           rate=sample_rate,
                           output=True,
                           output_device_index=self.output_device_index)

    def run(self):
        """ Kick off playing the audio """
        stream = self.__get_stream()
        chunk_count = 0
        chunks = make_chunks(self.seg, 100)[:-1]
        increment = abs(self.max_vol - self.cur_vol) / len(chunks)
        # print('cur vol:', self.cur_vol, 'chunks ', len(chunks))
        logger.info(f'Begin Streaming {self.filename}. Current Volume is {self.cur_vol}. {len(chunks)} chunks')
        while (chunk_count <= len(chunks) - 1) and not self.stopped():
            if not self.is_paused:  # write the audio content
                cur_chunk = chunks[chunk_count] + self.cur_vol
                data = cur_chunk._data
                chunk_count += 1
                self.cur_vol += increment
            else:  # write nullity to the data, play nothing.
                free = stream.get_write_available()
                data = chr(0) * free
            stream.write(data)  # play the audio data just written
        logger.info(f'Close {self.filename}. Current Volume is {self.cur_vol}.')
        stream.stop_stream()  # end the audio stream
        stream.close()


# demoing
def slow_roll(playlist, time_left):
    """
      slowly increase volume of audio in playlist
    inputs:
      playlist: pandas dataframe with length, filepath of each audio file in order.
      time_left: time until alarm is supposed to end
    """
    total_secs = playlist['length'].sum()
    vol = -60
    vol_change_total = 60

    # go through the playlist and play the audio
    for fp, duration in playlist[
        ['filepath', 'length']].values:  # add start and end times to the playlist feature (soundprofile= plalist??)
        print(fp)

        # if the playlist song time is more than the amount of time that we care to wake up,
        #   then only play the first time_left seconds of playlists
        if duration > time_left:
            duration = time_left

        # if no time left, then do not play anything
        if ceil(duration) <= 0:
            break

        # set the intermediate max volume (of current audio file)
        local_max = vol + (vol_change_total * (duration / total_secs))

        # initalize the audio object
        song = Song(fp, min_vol=vol, max_vol=local_max, start_sec=0, end_sec=ceil(duration))

        # play the audio
        song.play()
        time.sleep(duration)  # song plays on separate thread
        time_left = total_secs - ceil(duration)
        vol = local_max


def main():
    example_song = ''
    song = Song(example_song)
    song.play()


if __name__ == '__main__':
    main()
