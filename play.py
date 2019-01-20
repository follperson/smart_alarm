from pydub import AudioSegment
from pydub.utils import make_chunks
from pyaudio import PyAudio
from threading import Thread
from math import ceil
SECOND = 1000

#
#
# def make_chunks(audio_segment, chunk_length):
#     """
#     Breaks an AudioSegment into chunks that are <chunk_length> milliseconds
#     long.
#     if chunk_length is 50 then you'll get a list of 50 millisecond long audio
#     segments back (except the last one, which can be shorter)
#     """
#     number_of_chunks = ceil(len(audio_segment) / float(chunk_length))
#     return [audio_segment[i * chunk_length:(i + 1) * chunk_length]
#             for i in range(int(number_of_chunks))]

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
        maxvol = 0
        minvol = -60
        incr = abs(maxvol - minvol) / len(chunks)
        vol = minvol
        while chunk_count <= len(chunks):
            if not self.__is_paused:
                cur_chunk = chunks[chunk_count] + vol
                data = cur_chunk._data
                chunk_count += 1
                vol -= incr
            else:
                free = stream.get_write_available()
                data = chr(0) * free
            # try:
            stream.write(data)
            # except OSError as soundfucked:
            #     print(soundfucked)
                # vol += incr
                # chunk_count -= 1

        stream.stop_stream()
        self.p.terminate()


def main():
    example_song = r"C:\Users\follm\Downloads\torrents\audio\Brian Eno - Ambient 1 Music for Airports Electronic\Brian Eno - Ambient 1 Music for Airports [FLAC-Lossless]\01 Brian Eno - 1-1.flac"
    song = Song(example_song)
    song.play()


if __name__ == '__main__':
    main()
