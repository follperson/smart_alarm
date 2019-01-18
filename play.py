from pydub import AudioSegment
from pydub.utils import make_chunks
from pyaudio import PyAudio
from threading import Thread

SECOND = 1000


class Song(Thread):
    def __init__(self, f, *args, **kwargs):
        self.seg = AudioSegment.from_file(f)
        self.__is_paused = True
        self.p = PyAudio()
        Thread.__init__(self, *args, **kwargs)
        self.start()

    def pause(self):
        self.__is_paused = True

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
        maxvol = -10
        minvol = -60
        incr = abs(maxvol - minvol) / len(chunks)
        vol = minvol
        while chunk_count <= len(chunks):
            if not self.__is_paused:
                cur_chunk = chunks[chunk_count] - vol
                data = cur_chunk._data
                chunk_count += 1
                vol -= incr
                print(vol)
            else:
                free = stream.get_write_available()
                data = chr(0) * free

            stream.write(data)

        stream.stop_stream()
        self.p.terminate()

def main():
    example_song = r"C:\Users\follm\Downloads\torrents\audio\Brian Eno - Ambient 1 Music for Airports Electronic\Brian Eno - Ambient 1 Music for Airports [FLAC-Lossless]\01 Brian Eno - 1-1.flac"
    example_format = 'flac'
    song = Song(example_song)
    song.play()

if __name__ == '__main__':
    main()