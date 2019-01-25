from flask import (
Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import functools
import pandas as pd
import calendar
import os
import re
from .db import get_db


bp = Blueprint('alarm_setup', __name__, url_prefix='/alarm_setup')



@bp.route('/')
def index():
    return render_template('alarm_setup/index.html')

@bp.route('/create', methods=('GET', 'POST'))
def create_alarm():
    db = get_db()
    sound_profiles = db.execute('SELECT name FROM playlists').fetchall()
    color_profiles = db.execute('SELECT name FROM color_profiles').fetchall()
    name = ''
    time = ''
    days = []
    active = True
    sound_profile = None
    color_profile = None
    use = 'create'
    if request.method == 'POST':
        print(request.form)
        time = request.form['time']
        name = request.form['name']
        sound_profile = request.form['sound_profile']
        color_profile = request.form['color_profile']
        active = 'active' in request.form
        days = [day for day in range(7) if calendar.day_name[day] in request.form]

        sound_profile_id = db.execute('SELECT id FROM playlists WHERE name = ?', (sound_profile,)).fetchone()
        color_profile_id = db.execute('SELECT id FROM color_profiles WHERE name = ?', (color_profile,)).fetchone()

        error = []
        if len(days) == 0:
            error.append("Please select a day for this alarm")
        if db.execute('SELECT id FROM alarms WHERE name = ?', (name,)).fetchone() is not None:
            error.append('Alarm name {} is already registered, please select another.'.format(name))
        if sound_profile_id is None:
            error.append('Sound profile {} is not defined'.format(sound_profile))
        if sound_profile_id is None:
            error.append('Color profile {} is not defined'.format(color_profile))
        if not error:
            print('Commit Create')
            db.execute(
                'INSERT INTO alarms (name, alarm_time, active, sound_profile, color_profile, repeat_monday, '
                'repeat_tuesday, repeat_wednesday, repeat_thursday, repeat_friday, repeat_saturday, repeat_sunday) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (name, time, active, sound_profile_id['id'], color_profile_id['id'], 0 in days, 1 in days, 2 in days, 3 in days,
                 4 in days, 5 in days, 6 in days,)
            )
            db.commit()

            # print(url_for(create_alarm))
            return render_template('alarm_setup/success.html', params={'name':name, 'action':'create alarm', 'return':url_for('alarm_setup.create_alarm')})
        flash('. '.join(error))
    return render_template('alarm_setup/create_alarm.html', use=use, name=name, time=time, days=days,
                           sound_profile=sound_profile, color_profile=color_profile, active=active,
                           sound_profiles=sound_profiles, color_profiles=color_profiles)

def _get_profile(field_want, field_have, value, table, db):
    val = db.execute('SELECT %s FROM %s WHERE %s=?' % (field_want, table, field_have) , (value,)).fetchone()
    assert val is not None, '{} {} is not defined in {}'.format(field_want, value, table)
    return val


def get_profile_from_id(db, val, table):
    return _get_profile('name','id', val, table, db)

def get_profile_from_name(db, val, table):
    return _get_profile('id','name', val, table, db)

def _get_profiles(fields_want, table, db):
    if type(fields_want) == str:
        fields_want = [fields_want]
    val = db.execute('SELECT %s FROM %s' % (', '.join(fields_want), table)).fetchall()
    assert val is not None, 'Empty table %s' % table
    return val


#TODO: view = create/read/update/delete home
@bp.route('/<int:id>/update/', methods=('GET', 'POST'))
def update_alarm(id):
    db = get_db()
    sound_profiles = _get_profiles('name', 'sound_profiles', db)
    color_profiles = _get_profiles('name', 'color_profiles', db)
    alarm = db.execute(
        'SELECT name, alarm_time, active, sound_profile, color_profile, repeat_monday, repeat_tuesday, repeat_wednesday, repeat_thursday, repeat_friday, repeat_saturday, repeat_sunday FROM alarms WHERE id = ?',
        (id,)).fetchone()
    print(alarm.keys())
    name = alarm['name']
    time = alarm['alarm_time']
    days = [[i, alarm['repeat_' + calendar.day_name[i].lower()]] for i in range(7)]
    print('Days Raw',days)
    days = [i[0] for i in days if i[1]]
    print('Days Filter',days)
    active = alarm['active']
    error = []
    try:
        sound_profile = get_profile_from_id(db, alarm['sound_profile'], 'sound_profiles')
    except AssertionError as known:
        error.append(str(known))
    try:
        color_profile = get_profile_from_id(db, alarm['color_profile'],'color_profiles')
    except AssertionError as known:
        error.append(str(known))
    use = 'update'

    if request.method == 'POST':
        print(request.form)
        time = request.form['time']
        name = request.form['name']
        sound_profile = request.form['sound_profile']
        color_profile = request.form['color_profile']
        active = 'active' in request.form
        days = [day for day in range(7) if calendar.day_name[day] in request.form]
        if len(days) == 0:
            error.append("Please select a day for this alarm")
        try:
            sound_profile_id = get_profile_from_name(db, sound_profile, 'sound_profiles')
        except AssertionError as known:
            error.append(str(known))
        try:
            color_profile_id = get_profile_from_name(db, color_profile, 'color_profiles')
        except AssertionError as known:
            error.append(str(known))
        if not error:
            print('Commit update')
            db.execute(
                'UPDATE alarms SET name = ?, alarm_time = ?, active = ?, sound_profile = ?, color_profile = ?, repeat_monday = ?, repeat_tuesday = ?, repeat_wednesday = ?, repeat_thursday = ?, repeat_friday = ?, repeat_saturday = ?, repeat_sunday = ? WHERE id = ?',
                (name, time, active, sound_profile_id['id'], color_profile_id['id'], 1 in days, 2 in days, 3 in days, 4 in days,
                 5 in days, 6 in days, 7 in days, id,))
            db.commit()
        flash('. '.join(error))
        return render_template('alarm_setup/success.html', params={'name': name, 'action': 'update alarm',
                                                                   'return': url_for('alarm_setup.update_alarm', id=id)})
    flash('\n'.join(error))
    return render_template('alarm_setup/create_alarm.html', use=use, name=name, time=time, days=days,
                           sound_profile=sound_profile, color_profile=color_profile, active=active,
                           sound_profiles=sound_profiles, color_profiles=color_profiles)


@bp.route('/<int:id>/update_sound_profile', methods=('GET','POST'))
def update_sound_profile(id):
    pass


@bp.route('/sound_profile', methods=('GET', 'POST')) # deprecated
def modify_sound_profile():
    db = get_db()
    # table = 'sound_profiles'
    try:
        profiles = _get_profiles('name', 'playlists', db)
    except AssertionError as ok:
        pass
    if request.method == 'POST':
        profile_name = request.form['name']
        time_span = request.form['time_span']
        playlist_name = request.form['profile_name']
        error = []
        try:
            profile_id = get_profile_from_name(db, profile_name, 'sound_profiles')
            error.append('Sound profile %s already exists in the database. <a href={{ url_for("alarm_setup.update_sound_profile, %s)}} Do you want to update?</a>' % (profile_name, profile_id))
        except AssertionError:
            pass
        try:
            playlist_id = _get_profile('id','name', playlist_name,'playlists', db)
        except AssertionError as ok:
            error.append(str(ok))
        if not error:
            db.execute('INSERT INTO sound_profiles (name, time_span, playlist_id) VALUES (?,?,?)', (profile_name, time_span, playlist_id))
            db.commit()
            return render_template('alarm_setup/success.html', params={'name': profile_name, 'action': 'create sound profile', 'return':url_for('alarm_setup.create_sound_profile')})
        flash('\n'.join(error))
    return render_template('alarm_setup/create_profile.html', name='Sound ', profiles=profiles)


@bp.route('/playlists', methods=('GET','POST'))
def view_playlists():
    db = get_db()
    df = pd.read_sql('SELECT * FROM playlists', con=db)
    # df_sound_profiles = pd.read_sql('SELECT * FROM sound_profiles', con=db)
    df_alarms = pd.read_sql('SELECT * FROM alarms', con=db)
    # df = pd.merge(df, df_sound_profiles[['id','playlist_id']], how='left', right_on='playlist_id', left_on='id', suffixes=['_playlist','_sound_profile'])
    df = pd.merge(df, df_alarms[['name', 'sound_profile']], how='left', right_on='sound_profile',
                  left_on='id', suffixes=['_playlist', '_alarm'])
    df = df.rename(columns={'name_alarm':'Alarm Name','name_playlist':'Playlist Name','time_span':'Time Span','playlist_id':'id'})
    print(df)
    print(df.empty)
    return render_template('alarm_setup/view_playlists.html', df=df[['id', 'Playlist Name', 'Alarm Name']])


@bp.route('/playlist/create', methods=('GET','POST'))
def create_playlist():
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
            return redirect(url_for('.modify_playlist',id=playlist_id))
        flash(error)
    return render_template('alarm_setup/create_playlist.html')


@bp.route('/playlist/<int:id>', methods=('GET','POST'))
def view_playlist(id):
    db = get_db()
    name = get_profile_from_id(db,id, 'playlists')
    df = pd.read_sql('SELECT * FROM playlist WHERE playlist_id=%s' % id, con=db)
    df_audio = pd.read_sql('SELECT * FROM audio', con=db).rename(columns={'id':'audio_id','name':'Audio Name'})
    df = pd.merge(df, df_audio, how='left', on='audio_id').sort_values('playlist_order').rename(columns={'playlist_order':'Order','audio_start':'Start Time','audio_end':'End Time'})

    if request.method=='POST':
        print(request.form)
        audio_id = None
        for item in request.form:
            if 'Remove_' in item:
                audio_id = int(item.split('_')[-1])
                break
        if not audio_id:
            flash('Cannot find audio_id field')
            return render_template('alarm_setup/view_playlist.html', name=name,
                                   df=df[['playlist_id', 'Order', 'Audio Name', 'Start Time', 'End Time']])
        # assert that it is here in this playlist
        db.execute('DELETE FROM playlist WHERE playlist_id=? AND audio_id=?'.format(id, audio_id))
        flash('Successfully deleted song from playlist.')
    return render_template('alarm_setup/view_playlist.html', name=name, df=df[['playlist_id', 'Order', 'Audio Name','Start Time', 'End Time']], id=id)


@bp.route('playlist/<int:id>/modify',methods=('GET','POST'))
def modify_playlist(id):
    from numpy import ceil
    db = get_db()
    name = get_profile_from_id(db, id, 'playlists')
    df = pd.read_sql('SELECT * FROM playlist WHERE playlist_id=%s' % id, con=db)
    df_audio = pd.read_sql('SELECT * FROM audio', con=db).rename(columns={'id':"audio_id"})
    df = pd.merge(df, df_audio, how='outer', on='audio_id',suffixes=['_playlist','_audio'])
    print(df)
    df = df.fillna('').sort_values(['playlist_order','name','filename'])
    df['duration'] = ceil(df['duration'])
    int_cols = ['playlist_order','audio_start','audio_end']
    cols_to_show = ['filename','album','artist','duration','audio_start','audio_end','playlist_order']
    if request.method == 'POST':
        print(request.form)
        if 'cancel' in request.form:
            flash('Update Cancelled')
            return url_for('.view_playlist',id=id)
        elif 'submit' in request.form:
            mod_songs = [tag.split('_')[-1] for tag in request.form.getlist('update_id')]
            for song in mod_songs:
                # vals = {col:val for }
                pass


            pass
            # updates = request.form[]
            # 'UPDATE playlist SET name = ?, alarm_time = ?, active = ?, sound_profile = ?, color_profile = ?, repeat_monday = ?, repeat_tuesday = ?, repeat_wednesday = ?, repeat_thursday = ?, repeat_friday = ?, repeat_saturday = ?, repeat_sunday = ? WHERE playlist_id = ?',
            # db.execute('UPDATE playlist WHERE play')
    return render_template('alarm_setup/modify_playlist.html',name=name, df=df, int_cols=int_cols, cols_to_show=cols_to_show)


@bp.route('/color_profile', methods=('GET', 'POST'))
def create_color_profile():
    if request.method == 'POST':
        profile_name = request.form['name']
        time_span = request.form['time_span']
        db = get_db()

        error = ''
        if not os.path.exists('profiles/sound/%s.py' % profile_name):
            error = 'Color profile %s does not exists on the server' % profile_name
        if db.execute('SELECT id FROM color_profiles WHERE name = ?',(profile_name,)).fetchone() is not None:
            error = 'Color profile %s already exists in the database' % profile_name
        if error != '':
            db.execute('INSERT INTO color_profiles (name, time_span) VALUES (?,?)', (profile_name, time_span))
            db.commit()
            return render_template('alarm_setup/success.html', params={'name': profile_name, 'action': 'create color profile',
                                                                 'return': url_for('alarm_setup.create_color_profile')})
        flash(error)
    return render_template('alarm_setup/create_profile.html', name='Color ')


@bp.route('/view', methods=('GET', 'POST'))
def view_alarms():
    db = get_db()
    df = pd.read_sql('SELECT * FROM alarms',con=db)
    df['repeat_dates'] = df.apply(lambda x: ', '.join([calendar.day_name[i] for i in range(7) if
                                                       x['repeat_' + calendar.day_name[i].lower()]]), axis=1)
    df['active'] = df['active'].astype(bool)
    df_sound = pd.read_sql('select * from sound_profiles', con=db).rename(
        columns={'id': 'sound_profile', 'name': 'sound_profile_name'})
    df_color = pd.read_sql('select * from color_profiles', con=db).rename(
        columns={'id': 'color_profile', 'name': 'color_profile_name'})
    df = pd.merge(df, df_sound[['sound_profile','sound_profile_name']], on='sound_profile', how='left')
    df = pd.merge(df, df_color[['color_profile','color_profile_name']], on='color_profile', how='left')
    return render_template('alarm_setup/view_alarms.html', df=df[
        ['id','name', 'alarm_time', 'repeat_dates', 'active', 'sound_profile_name', 'color_profile_name', 'created']])
