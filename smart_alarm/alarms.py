from flask import (
    Blueprint, flash, render_template, request, url_for
)
import pandas as pd
import calendar
import datetime as dt
from .code.exceptions import PlaylistNotFound
from .code.utils import _get_profiles, get_profile_from_id, get_profile_from_name, get_repeat_dates
from .db import get_db


bp = Blueprint('alarm', __name__, url_prefix='/alarm')
# todo - add a 'skip this part' to the activate screen so we can skip a song or the google audio stuff

@bp.route('/create', methods=('GET', 'POST'))
def create():
    """
    Create a new alarm using already established playlists and color profiles
    """
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
    # if we are updating the site (i.e POST command)
    if request.method == 'POST':

        # grab the information present in the input boxes
        time = request.form['time']
        name = request.form['name']
        sound_profile = request.form['sound_profile']
        color_profile = request.form['color_profile']
        active = 'active' in request.form # is 'active' checkbox checked?
        days = [day for day in range(7) if calendar.day_name[day] in request.form] # all days that are checked

        # get the id that corresponds to the named playlist / profiles
        sound_profile_id = db.execute('SELECT id FROM playlists WHERE name = ?', (sound_profile,)).fetchone()
        color_profile_id = db.execute('SELECT id FROM color_profiles WHERE name = ?', (color_profile,)).fetchone()

        # check for any errors in the text boxes
        error = []
        if len(days) == 0:
            error.append("Please select a day for this alarm")
        if db.execute('SELECT id FROM alarms WHERE name = ?', (name,)).fetchone() is not None:
            error.append('Alarm name {} is already registered, please select another.'.format(name))
        if sound_profile_id is None:
            error.append('Sound profile {} is not defined'.format(sound_profile))
        if sound_profile_id is None:
            error.append('Color profile {} is not defined'.format(color_profile))
        
        # update the database with the new alarm information
        if not error:
            wake_window = db.execute("SELECT wake_window FROM playlists WHERE id = ?;", (sound_profile_id['id'],)
                                         ).fetchone()['wake_window']
            print(wake_window)
            db.execute(
                'INSERT INTO alarms (name, modified, alarm_time, active, wake_window, '
                'sound_profile, color_profile, repeat_monday, '
                'repeat_tuesday, repeat_wednesday, repeat_thursday, repeat_friday, repeat_saturday, repeat_sunday) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (name, dt.datetime.now(), time, active, wake_window, sound_profile_id['id'], color_profile_id['id'],
                 0 in days, 1 in days, 2 in days, 3 in days, 4 in days, 5 in days, 6 in days,)
            )
            db.commit()
            
            # return the success page
            return render_template('alarms/success.html',
                                   params={'name': name, 'action':'create alarm', 'return': url_for('alarm.create')})
        
        # there was an error, so flash the errors
        flash('. '.join(error))
    
    # render the base page for creating the alarm
    return render_template('alarms/create_alarm.html', use=use, name=name, time=time, days=days,
                           sound_profile=sound_profile, color_profile=color_profile, active=active,
                           sound_profiles=sound_profiles, color_profiles=color_profiles)


#TODO: view = create/read/update/delete home (consolidate create and update, link them to view)
@bp.route('/<int:id>/update/', methods=('GET', 'POST'))
def update(id):
    """ 
    update a single alarm
    """
    db = get_db()

    # get the availble audio and color profiles
    sound_profiles = _get_profiles('name', 'playlists', db)
    color_profiles = _get_profiles('name', 'color_profiles', db)

    # get alarm's current information, and place them in python variables
    alarm = db.execute(
        'SELECT name, alarm_time, active, sound_profile, color_profile, repeat_monday, repeat_tuesday, repeat_wednesday, repeat_thursday, repeat_friday, repeat_saturday, repeat_sunday FROM alarms WHERE id = ?',
        (id,)).fetchone()
    
    name = alarm['name']
    time = alarm['alarm_time']
    days = [[i, alarm['repeat_' + calendar.day_name[i].lower()]] for i in range(7)]
    days = [i[0] for i in days if i[1]]
    active = alarm['active']
    
    error = []
    try:
        sound_profile = get_profile_from_id(db, alarm['sound_profile'], 'playlists')
    except AssertionError as known:
        error.append(str(known))
    try:
        color_profile = get_profile_from_id(db, alarm['color_profile'],'color_profiles')
    except AssertionError as known:
        error.append(str(known))
    use = 'update'

    if request.method == 'POST':

        # grab information from form
        time = request.form['time']
        name = request.form['name']
        sound_profile = request.form['sound_profile']
        color_profile = request.form['color_profile']
        active = 'active' in request.form
        days = [day for day in range(7) if calendar.day_name[day] in request.form]
        
        # check for errors
        if len(days) == 0:
            error.append("Please select a day for this alarm")
        try:
            sound_profile_id = get_profile_from_name(db, sound_profile, 'playlists')
        except PlaylistNotFound as known:
            error.append(str(known))
        try:
            color_profile_id = get_profile_from_name(db, color_profile, 'color_profiles')
        except PlaylistNotFound as known:
            error.append(str(known))
        
        # update database with the information in the form
        if not error:
            db.execute(
                'UPDATE alarms SET name = ?, alarm_time = ?, active = ?, sound_profile = ?, color_profile = ?, repeat_monday = ?, repeat_tuesday = ?, repeat_wednesday = ?, repeat_thursday = ?, repeat_friday = ?, repeat_saturday = ?, repeat_sunday = ?, modified = ? WHERE id = ?',
                (name, time, active, sound_profile_id['id'], color_profile_id['id'], 0 in days, 1 in days, 2 in days, 3 in days, 4 in days,
                 5 in days, 6 in days, dt.datetime.now(), id,))
            db.commit()

            # return the success page
            return render_template('alarms/success.html', params={'name': name, 'action': 'update alarm',
                                                                   'return': url_for('alarm.update', id=id)})

    flash('\n'.join(error))
    return render_template('alarms/create_alarm.html', use=use, name=name, time=time, days=days,
                           sound_profile=sound_profile, color_profile=color_profile, active=active,
                           sound_profiles=sound_profiles, color_profiles=color_profiles)


@bp.route('/view', methods=('GET', 'POST'))
def view():
    """ 
        Look at the alarms available and update, create, or delete them as desired
    """
    db = get_db()
    df = pd.read_sql('SELECT * FROM alarms',con=db)
    cols = ['name']

    # if we have alarms in database, display them
    if not df.empty:
        df['repeat_dates'] = df.apply(get_repeat_dates, axis=1) # change int day to str days
        df['active'] = df['active'].astype(bool) 
        
        # Get names from color/sound profiles, not just id numbers
        df_sound = pd.read_sql('select * from playlists', con=db).rename(
            columns={'id': 'sound_profile', 'name': 'sound_profile_name'})
        df_color = pd.read_sql('select * from color_profiles', con=db).rename(
            columns={'id': 'color_profile', 'name': 'color_profile_name'})
        df = pd.merge(df, df_sound[['sound_profile','sound_profile_name']], on='sound_profile', how='left')
        df = pd.merge(df, df_color[['color_profile','color_profile_name']], on='color_profile', how='left')
        cols = ['id','name', 'alarm_time', 'repeat_dates', 'active', 'sound_profile_name', 'color_profile_name', 'created']
    
    # return available alarms
    return render_template('alarms/view_alarms.html', df=df[cols])
