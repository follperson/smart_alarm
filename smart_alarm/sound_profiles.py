from flask import (Blueprint, flash, redirect, render_template, request, url_for)
from numpy import floor
import pandas as pd
from .db import get_db
from .src.utils import *
from .src.exceptions import InvalidInputError

bp = Blueprint('sound', __name__, url_prefix='/sound')

# TODO THERE IS A Bug in computing the wake window

@bp.route('/view', methods=('GET',))
def view():
    """
       Look at sound profiles and their associated alarms (if any)
    """
    db = get_db()
    df = pd.read_sql('SELECT * FROM playlists', con=db)  # do this in sql...?
    df_alarms = pd.read_sql('SELECT * FROM alarms', con=db)
    # combine playlist and alarm tables, rename
    df = pd.merge(df, df_alarms[['name', 'sound_profile']], how='left', right_on='sound_profile',
                  left_on='id', suffixes=['_playlist', '_alarm'])
    df = df.rename(columns={'name_alarm': 'Alarm Name', 'name_playlist': 'Playlist Name',
                            'time_span': 'Time Span', 'playlist_id': 'id', 'wake_window': 'Playlist Length'})
    # render more info (like total length, names of songs?)
    return render_template('sound_color/view_playlists.html',
                           df=df[['id', 'Playlist Name', 'Playlist Length', 'Alarm Name']])


@bp.route('/create', methods=('GET', 'POST'))
def create():
    """
    allow user to create playlist
    """
    if request.method == 'POST':
        error = []
        db = get_db()
        name = request.form['name']
        try:
            # check if the playlist name is already taken
            get_profile_from_name(db, name, 'playlists')
        except PlaylistNotFound:
            pass
        else:
            error.append('Please choose another name, %s is already defined' % name)
        if not error:
            # insert playlist name, then redirect the user to the playlist update page to choose audio
            db.execute('INSERT INTO playlists (name) VALUES (?)', (name,))
            db.commit()
            db = get_db()
            playlist_id = get_profile_from_name(db, name, 'playlists')
            return redirect(url_for('.update', id=playlist_id))
        flash(error)
    return render_template('sound_color/create_playlist.html')


@bp.route('/<int:id>/view', methods=('GET',))
def view_playlist(id):
    """ Look at all the audio specifications for a single playlist"""
    db = get_db()

    # I could do all this in one sql query... is that better or worse? Faster, cleaner.  harder to debug
    name = get_profile_from_id(db, id, 'playlists')
    df = pd.read_sql('SELECT * FROM playlist WHERE playlist_id=%s' % id, con=db)

    # get the audio information for those tracks which are in the current playlist
    df_audio = pd.read_sql('SELECT * FROM audio', con=db).rename(columns={'id': 'audio_id', 'name': 'Audio Name'})
    df = pd.merge(df, df_audio, how='left', on='audio_id').sort_values('playlist_order').rename(
        columns={'playlist_order': 'Order', 'audio_start': 'Start Time', 'audio_end': 'End Time'})

    return render_template('sound_color/view_playlist.html', name=name, id=id,
                           df=df[['playlist_id', 'Order', 'Audio Name', 'Start Time', 'End Time']])


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
def update(id):
    """ select songs and set song lengths for given audio profile (overwrites previously set information)"""

    # todo - fill in the template with the audio playlist info
    db = get_db()
    name = get_profile_from_id(db, id, 'playlists')

    # get playlist and song info
    df = pd.read_sql('SELECT * FROM playlist WHERE playlist_id=%s' % id, con=db)
    df_audio = pd.read_sql('SELECT * FROM audio', con=db).rename(columns={'id': "audio_id"})
    df = pd.merge(df, df_audio, how='outer', on='audio_id', suffixes=['_playlist', '_audio'])
    df = df.fillna('').sort_values(['playlist_order', 'name', 'filename'])
    df['duration'] = floor(df['duration']).astype(int)
    df['audio_id'] = df['audio_id'].astype(str)

    int_cols = ['playlist_order', 'audio_start', 'audio_end']
    cols_to_show = ['filename', 'album', 'artist', 'duration', 'audio_start', 'audio_end', 'playlist_order']
    if request.method == 'POST':  # putting update
        print(request.form)  # reference

        if 'cancel' in request.form:  # dont update
            flash('Update Cancelled')
            return redirect(url_for('.view_playlist', id=id))

        elif 'submit' in request.form:
            mod_songs = [tag.split('_')[-1] for tag in request.form if 'update' in tag]

            fields = ['audio_start', 'audio_end', 'playlist_order']
            updates = {song_id:
                           {field: request.form[song_id + '_' + field] for field in fields}
                       for song_id in mod_songs}
            dfinfo = df.loc[df['audio_id'].isin(mod_songs), ['audio_id', 'duration']
                            ].set_index('audio_id').to_dict()['duration']
            print(dfinfo)
            try:
                updates = verify_updates(updates, dfinfo)
            except InvalidInputError as err:
                flash(str(err))
                return render_template('sound_color/modify_playlist.html', name=name, df=df, int_cols=int_cols,
                                       cols_to_show=cols_to_show)

            # todo use sql UPDATE not DELETE/INSERT
            db.execute('DELETE FROM playlist WHERE playlist_id = ?',
                       (id,))  # drop old playlist, insert updated playlist

            # update playlist with each audio item and it's specification
            wake_window = 0
            for song in updates:
                wake_window += updates[song]['audio_end'] - updates[song]['audio_start']
                update_input = tuple([updates[song][field] for field in fields] + [song, id])
                text = 'INSERT INTO playlist (%s) VALUES (%s ?, ?)' % (
                        ', '.join(fields + ['audio_id', 'playlist_id']), '?, ' * (len(fields)))
                db.execute(text, update_input)
            print('total', wake_window)

            db.execute('UPDATE playlists set wake_window = ? where id = ?;', (wake_window, id))
            db.commit()

            flash('Success!')
            return redirect(url_for('.view_playlist', id=id))

    return render_template('sound_color/modify_playlist.html', name=name, df=df, int_cols=int_cols,
                           cols_to_show=cols_to_show)


def verify_updates(updates, durations):  # generalize / abstract
    if len(updates) == 0:
        raise InvalidInputError("No audio selected!!")
    for song in updates:
        if updates[song]['audio_start'] == '':
            updates[song]['audio_start'] = 0
        else:
            updates[song]['audio_start'] = int(updates[song]['audio_start'])

        if updates[song]['audio_end'] == '':
            updates[song]['audio_end'] = durations[song]
        else:
            updates[song]['audio_end'] = int(updates[song]['audio_end'])

        if updates[song]['audio_end'] <= updates[song]['audio_start']:
            raise InvalidInputError('Audio End was set before Audio Start')

        if updates[song]['playlist_order'] == '':
            raise InvalidInputError('You Must Specify the playlist order!')

    order = [(song, updates[song]['playlist_order']) for song in updates]
    order.sort(key=lambda x: x[1])
    order = [x[0] for x in order]
    for i, id in enumerate(order):
        updates[id]['playlist_order'] = i
    return updates
