from os.path import basename, dirname
from pydub import AudioSegment
from pydub.utils import make_chunks
from pyaudio import PyAudio
from threading import Thread, Event
#from smart_alarm.db import get_db
import time
from math import ceil
import pandas as pd
SECOND = 1000


def get_playlist(name):
    df = pd.read_csv('assets\\playlists\\playlists.csv')
    df_songs = pd.read_csv('assets\\playlists\\songs.csv')
    playlist = pd.merge(df.loc[df['name'] == name][['filepath']], df_songs, how='left',on='filepath')
    # playlist = playlist.sort_values('order')
    return playlist

# todo change the way that the sound rises over time - more at end less at beginning
# todo make sound fade out into the word time


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
    for fp, duration in playlist[['filepath', 'length']].values:  # add start and end times to the playlist feature (soundprofile= plalist??)
        print(fp)

        # if the playlist song time is more than the amount of time that we care to wake up,
        #   then only play the first time_left seconds of playlists 
        if duration > time_left:
            duration = time_left

        # if no time left, then do not play anything
        if ceil(duration) <= 0:
            break

        # set the intermediate max volume (of current audio file)
        local_max = vol + (vol_change_total * (duration / total_secs) )
        
        # initalize the audio object 
        song = Song(fp, min_vol=vol, max_vol=local_max, start_sec=0, end_sec=ceil(duration))
        
        # play the audio
        song.play()
        time.sleep(duration)  # song plays on separate thread
        time_left = total_secs - ceil(duration)
        vol = local_max


class Song(Thread):
    """
      Audio player object building on Thread object and PyAudio
      Used to play audio files
    """
    def __init__(self, f, min_vol=-60, max_vol=0, start_sec=0, end_sec=6000, *args, **kwargs):
        """
        inputs:
            f: filepath of audiofile
            min_vol: minimum volume
            max_vol: maximum volume
            start_sec: second of the song which we will start playing from
            end_sec: ending second of the song 
        """

        # initalize audio object
        self.seg = AudioSegment.from_file(f)
        # limit audio to be accessed to just the window between start and end seconds
        self.seg = self.seg[start_sec*1000:end_sec*1000]
        self.__is_paused = True
        self.p = PyAudio()
        self.cur_vol = min_vol
        self.max_vol = max_vol
        self.start_sec = start_sec
        self.end_sec = end_sec
        Thread.__init__(self, name=basename(f), *args, **kwargs)
        
        # Thread functions
        self._stop_event = Event()
        self.start()

    def pause(self):
        """ pause the audio """ 
        self.__is_paused = True

    def stop(self):
        """ end the audio to kill the song """
        self._stop_event.set()

    def stopped(self):
        """ check if the thread is stopped """
        return self._stop_event.is_set()

    def quit(self):
        """ close the thread and the audio object """
        self.__is_paused = True
        self.p.terminate()
        self.stop()

    def play(self):
        self.__is_paused = False

    def __get_stream(self):
        """ access the audio handler for playing audio"""
        return self.p.open(format=self.p.get_format_from_width(self.seg.sample_width),
                           channels=self.seg.channels,
                           rate=self.seg.frame_rate,
                           output=True)

    def run(self):
        """ Kick off playing the audio """
        stream = self.__get_stream()
        chunk_count = 0
        chunks = make_chunks(self.seg, 100)
        increment = abs(self.max_vol - self.cur_vol) / len(chunks)
        print('cur vol:', self.cur_vol, 'chunks ', len(chunks))
        while chunk_count <= len(chunks) - 1:
            if not self.__is_paused: # write the audio content
                cur_chunk = chunks[chunk_count] + self.cur_vol
                data = cur_chunk._data
                chunk_count += 1
                self.cur_vol += increment
            else: # write nullity to the data, play nothing.
                free = stream.get_write_available()
                data = chr(0) * free
            if self.stopped(): # thread can be stopped externally, so keep checking
                break
            stream.write(data) # play the audio data just written
        
        stream.stop_stream() # end the audio stream
        self.stop() # end the audio device


def main():
    example_song = ''
    song = Song(example_song)
    song.play()


if __name__ == '__main__':
    main()
