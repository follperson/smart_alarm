import os
from smart_alarm.src.play import Song, time


def test_song(example_song='assets/sounds/music/Brian Eno/Ambient 1 Music For Airports/03 Brian Eno - 2-1.flac'):
    song = Song(f=example_song, min_vol=-20, max_vol=-15)
    song.play()
    time.sleep(10)
    song.stop()
