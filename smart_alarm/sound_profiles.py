from flask import (Blueprint, flash, redirect, render_template, request, url_for)
from numpy import ceil
import pandas as pd
from .db import get_db
from .utils import *

bp = Blueprint('sound', __name__, url_prefix='/sound')


@bp.route('/view', methods=('GET',))
def view():
    db = get_db()
    df = pd.read_sql('SELECT * FROM playlists', con=db)
    df_alarms = pd.read_sql('SELECT * FROM alarms', con=db)
    df = pd.merge(df, df_alarms[['name', 'sound_profile']], how='left', right_on='sound_profile',
                  left_on='id', suffixes=['_playlist', '_alarm'])
    df = df.rename(columns={'name_alarm':'Alarm Name','name_playlist':'Playlist Name','time_span':'Time Span','playlist_id':'id'})
    print(df)
    print(df.empty)
    return render_template('sound_color/view_playlists.html', df=df[['id', 'Playlist Name', 'Alarm Name']])


@bp.route('/create', methods=('GET','POST'))
def create():
    if request.method == 'POST':
        error = []
        db = get_db()
        name = request.form['name']
        try:
            get_profile_from_name(db, name, 'playlists')
            error.append('Please choose another name, %s is already defined' % name)
        except AssertionError:
            pass
        if not error:
            db.execute('INSERT INTO playlists (name) VALUES (?)',(name,))
            db.commit()
            db = get_db()
            playlist_id = get_profile_from_name(db, name, 'playlists')['id']
            return redirect(url_for('.update',id=playlist_id))
        flash(error)
    return render_template('sound_color/create_playlist.html')


@bp.route('/<int:id>/view', methods=('GET',))
def view_playlist(id):
    db = get_db()
    name = get_profile_from_id(db,id, 'playlists')
    df = pd.read_sql('SELECT * FROM playlist WHERE playlist_id=%s' % id, con=db)
    df_audio = pd.read_sql('SELECT * FROM audio', con=db).rename(columns={'id':'audio_id','name':'Audio Name'})
    df = pd.merge(df, df_audio, how='left', on='audio_id').sort_values('playlist_order').rename(columns={'playlist_order':'Order','audio_start':'Start Time','audio_end':'End Time'})
    return render_template('sound_color/view_playlist.html', name=name, df=df[['playlist_id', 'Order', 'Audio Name','Start Time', 'End Time']], id=id)


@bp.route('/<int:id>/update',methods=('GET','POST'))
def update(id):
    db = get_db()
    name = get_profile_from_id(db, id, 'playlists')
    df = pd.read_sql('SELECT * FROM playlist WHERE playlist_id=%s' % id, con=db)
    df_audio = pd.read_sql('SELECT * FROM audio', con=db).rename(columns={'id':"audio_id"})
    df = pd.merge(df, df_audio, how='outer', on='audio_id',suffixes=['_playlist','_audio'])
    df = df.fillna('').sort_values(['playlist_order','name','filename'])
    df['duration'] = ceil(df['duration'])
    int_cols = ['playlist_order','audio_start','audio_end']
    cols_to_show = ['filename','album','artist','duration','audio_start','audio_end','playlist_order']
    if request.method == 'POST':
        print(request.form)
        if 'cancel' in request.form:
            flash('Update Cancelled')
            return redirect(url_for('.view_playlist', id=id))
        elif 'submit' in request.form:
            mod_songs = [tag.split('_')[-1] for tag in request.form if 'update' in tag]
            print(mod_songs)
            fields = ['audio_start','audio_end','playlist_order']
            updates = {song_id: {field: request.form[song_id + '_' + field] for field in fields} for song_id in mod_songs}
            print(updates)
            updates = verify_updates(updates)

            db.execute('DELETE FROM playlist WHERE playlist_id = ?', (id,))
            for song in updates:
                update_input = tuple([updates[song][field] for field in fields] + [song, id])
                # print(update_input)
                text = 'INSERT INTO playlist (%s) VALUES (%s ?, ?)' % (', '.join(fields + ['audio_id','playlist_id']), '?, ' * (len(fields)))
                db.execute(text, update_input)
            db.commit()
            flash('Success!')
            return redirect(url_for('.view_playlist', id=id))
    return render_template('sound_color/modify_playlist.html',name=name, df=df, int_cols=int_cols,
                           cols_to_show=cols_to_show)


# todo fix audio_end (shows up null)
def verify_updates(updates): # generalize / abstract
    for song in updates:
        fields = ['audio_start', 'audio_end', 'playlist_order']
        for field in fields:
            try:
                updates[song][field] = int(updates[song][field])
            except ValueError as null:
                updates[song][field] = -1
        if updates[song]['audio_end'] <= updates[song]['audio_start']:
            updates[song]['audio_end'] = -1
    order = [(song, updates[song]['playlist_order']) for song in updates]
    order.sort(key=lambda x: x[1])
    order = [x[0] for x in order]
    for i, id in enumerate(order):
        updates[id]['playlist_order'] = i
    return updates
