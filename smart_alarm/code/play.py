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
    total_secs = playlist['length'].sum()
    vol = -60
    vol_change_total = 60
    for fp, duration in playlist[['filepath', 'length']].values:  # add start and end times to the playlist feature (soundprofile= plalist??)
        print(fp)
        if duration > time_left:
            duration = time_left
        if ceil(duration) <= 0:
            break
        local_max = vol + vol_change_total * duration / total_secs
        song = Song(fp, min_vol=vol, max_vol=local_max, start_sec=0, end_sec=ceil(duration))
        song.play()
        time.sleep(duration)  # song plays on separate thread
        time_left = total_secs - ceil(duration)
        vol = local_max


class Song(Thread):
    def __init__(self, f, min_vol=-60, max_vol=0, start_sec=0, end_sec=6000, *args, **kwargs):
        self.seg = AudioSegment.from_file(f)
        self.seg = self.seg[start_sec*1000:end_sec*1000]
        self.__is_paused = True
        self.p = PyAudio()
        self.cur_vol = min_vol
        self.max_vol = max_vol
        self.start_sec = start_sec
        self.end_sec = end_sec
        Thread.__init__(self, name=basename(f), *args, **kwargs)
        self._stop_event = Event()
        self.start()

    def pause(self):
        self.__is_paused = True

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def quit(self):
        self.__is_paused = True
        self.p.terminate()
        self.stop()

    def play(self):
        self.__is_paused = False

    def __get_stream(self):
        return self.p.open(format=self.p.get_format_from_width(self.seg.sample_width),
                           channels=self.seg.channels,
                           rate=self.seg.frame_rate,
                           output=True)

    def run(self):
        stream = self.__get_stream()
        chunk_count = 0
        chunks = make_chunks(self.seg, 100)
        increment = abs(self.max_vol - self.cur_vol) / len(chunks)
        print('cur vol:', self.cur_vol, 'chunks ', len(chunks))
        while chunk_count <= len(chunks) - 1:
            if not self.__is_paused:
                cur_chunk = chunks[chunk_count] + self.cur_vol
                data = cur_chunk._data
                chunk_count += 1
                self.cur_vol += increment
            else:
                free = stream.get_write_available()
                data = chr(0) * free
            if self.stopped():
                break
            stream.write(data)

        stream.stop_stream()
        self.p.terminate()


def main():
    example_song = ''
    song = Song(example_song)
    song.play()


if __name__ == '__main__':
    main()
