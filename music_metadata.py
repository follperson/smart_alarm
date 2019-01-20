from tinytag import TinyTag
import os
import pandas as pd

def scan_directory(root='assets'):
    music_exts = ['mp3', 'flac', 'ogg']
    data = []
    for _root, dirs, files in os.walk(root):
        for f in files:
            if f.split('.')[-1] in music_exts:
                fp = _root + '\\' + f
                tag = TinyTag.get(fp)
                track_info = [tag.title, tag.album, tag.artist, tag.duration]
                data.append([fp, f] + track_info)
    return pd.DataFrame(data, columns=['filepath','filename','song','album','artist','length'])

if __name__ == '__main__':
    print(scan_directory().iloc[:,2:])