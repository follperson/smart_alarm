from pydub import AudioSegment
from pydub.utils import make_chunks
from pyaudio import PyAudio
from threading import Thread
#from smart_alarm.db import get_db
import pandas as pd
SECOND = 1000


def get_playlist(name):
    df = pd.read_csv('assets\\playlists\\playlists.csv')
    df_songs = pd.read_csv('assets\\playlists\\songs.csv')
    playlist = pd.merge(df.loc[df['name'] == name][['filepath']], df_songs, how='left',on='filepath')
    # playlist = playlist.sort_values('order')
    return playlist

# todo change the way that the sound rises over time - more at end less at beginning


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
        Thread.__init__(self, *args, **kwargs)
        self.start()

    def pause(self):
        self.__is_paused = True

    def quit(self):
        self.p.terminate()

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
        print('cur vol:', self.cur_vol)
        while chunk_count <= len(chunks) - 1:
            if not self.__is_paused:
                cur_chunk = chunks[chunk_count] + self.cur_vol
                data = cur_chunk._data
                chunk_count += 1
                self.cur_vol += increment
            else:
                free = stream.get_write_available()
                data = chr(0) * free
            stream.write(data)

        stream.stop_stream()
        self.p.terminate()


def main():
    example_song = ''
    song = Song(example_song)
    song.play()


if __name__ == '__main__':
    main()
