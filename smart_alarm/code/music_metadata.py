import subprocess
import os
import pandas as pd
import hashlib


def md5(fname):
    """
      collect a unique file signature(to protect against identical files with different names, 
      and against file name collision)
    """
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def scan_directory(root=r'C:\Users\follm\Documents\coding\smart_alarm_clock\assets'):
    """
      Iteratue through directory, gather metadata about all audio file types, and return the data as a pandas 
      dataframe.
      This is to be used in initalizing the 'available audio' data table for our alarm audio playlists 
    inputs:
      root: directory root which we will iterate through and collect audio data  
    outputs:
      pd.DataFrame, with filepath, filename, md5hash, audio name, album name, artist, audio duration
    """
    # acceptable music extensions
    music_exts = ['mp3', 'flac', 'ogg', 'mp4']
    data = []
    
    # walk through the directory
    for _root, dirs, files in os.walk(root):
        for f in files:
            # if the extension is recognized as an audio file
            if f.split('.')[-1].lower() in music_exts:
                fp = _root + '\\' + f
                
                # gather metadata about the audio using the ffprobe cmdlet
                proc = subprocess.Popen(['ffprobe','-show_format',fp],stdout=subprocess.PIPE)
                output = proc.stdout.read().decode().split('\n')
                tag = dict()

                # parse the stdoutput according to our expected audio media types 
                for i in output:
                    if '=' in i:
                        tag[i.split('=')[0]] = i.split('=')[1]
                track_info = []
                for key in ['TAG:TITLE','TAG:ALBUM','TAG:ARTIST','duration']:
                    try:
                        val = tag[key]
                    except KeyError as ok:
                        val = ''
                    track_info.append(val.strip())
                data.append([fp, f, md5(fp)] + track_info)
    return pd.DataFrame(data, columns=['filepath','filename','hash','name','album','artist','duration'])

def update_songs():
    df = scan_directory()
    df.to_csv('assets\\playlists\\songs.csv')

if __name__ == '__main__':
    # print(scan_directory().iloc[:,2:])
    # update_songs()
    print(scan_directory())