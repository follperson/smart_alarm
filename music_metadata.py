from tinytag import TinyTag
import os
import pandas as pd
import hashlib


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def scan_directory(root=r'C:\Users\follm\Documents\coding\smart_alarm_clock\assets'):
    music_exts = ['mp3', 'flac', 'ogg', 'mp4']
    data = []
    for _root, dirs, files in os.walk(root):
        for f in files:
            if f.split('.')[-1] in music_exts:
                fp = _root + '\\' + f
                tag = TinyTag.get(fp)
                track_info = [tag.title, tag.album, tag.artist, tag.duration]
                data.append([fp, f, md5(fp)] + track_info)
    return pd.DataFrame(data, columns=['filepath','filename','hash','name','album','artist','duration'])

def update_songs():
    df = scan_directory()
    df.to_csv('assets\\playlists\\songs.csv')

if __name__ == '__main__':
    # print(scan_directory().iloc[:,2:])
    update_songs()