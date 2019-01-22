from flask import (
Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import functools
import pandas as pd
import calendar
import os

from .db import get_db


bp = Blueprint('alarm', __name__, url_prefix='/alarm')



@bp.route('/')
def index():
    return render_template('alarm_setup/index.html')

@bp.route('/create', methods=('GET', 'POST'))
def create_alarm():
    db = get_db()
    sound_profiles = db.execute('SELECT name FROM sound_profiles').fetchall()
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

        sound_profile_id = db.execute('SELECT id FROM sound_profiles WHERE name = ?', (sound_profile,)).fetchone()
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
        if len(error) == 0:
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
            return render_template('alarm_setup/success.html', params={'name':name, 'action':'create alarm', 'return':url_for('alarm.create_alarm')})
        flash('. '.join(error))
    return render_template('alarm_setup/create_alarm.html', use=use, name=name, time=time, days=days,
                           sound_profile=sound_profile, color_profile=color_profile, active=active,
                           sound_profiles=sound_profiles, color_profiles=color_profiles)


#TODO: view = create/read/update/delete home
@bp.route('/<int:id>/update/', methods=('GET', 'POST'))
def update_alarm(id):
    db = get_db()
    sound_profiles = db.execute('SELECT name FROM sound_profiles').fetchall()
    color_profiles = db.execute('SELECT name FROM color_profiles').fetchall()
    # print(type(id), id)
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
    sound_profile = db.execute('SELECT name FROM sound_profiles WHERE id = ?', (alarm['sound_profile'],))
    color_profile = db.execute('SELECT name FROM color_profiles WHERE id = ?', (alarm['color_profile'],))
    use = 'update'

    if request.method == 'POST':
        print(request.form)
        time = request.form['time']
        name = request.form['name']
        sound_profile = request.form['sound_profile']
        color_profile = request.form['color_profile']
        active = 'active' in request.form
        days = [day for day in range(7) if calendar.day_name[day] in request.form]
        sound_profile_id = db.execute('SELECT id FROM sound_profiles WHERE name = ?', (sound_profile,)).fetchone()
        color_profile_id = db.execute('SELECT id FROM color_profiles WHERE name = ?', (color_profile,)).fetchone()
        error = []
        if len(days) == 0:
            error.append("Please select a day for this alarm")
        if sound_profile_id is None:
            error.append('Sound profile {} is not defined'.format(sound_profile))
        if sound_profile_id is None:
            error.append('Color profile {} is not defined'.format(color_profile))
        if len(error) == 0:
            print('Commit update')
            db.execute(
                'UPDATE alarms SET name = ?, alarm_time = ?, active = ?, sound_profile = ?, color_profile = ?, repeat_monday = ?, repeat_tuesday = ?, repeat_wednesday = ?, repeat_thursday = ?, repeat_friday = ?, repeat_saturday = ?, repeat_sunday = ? WHERE id = ?',
                (name, time, active, sound_profile_id['id'], color_profile_id['id'], 1 in days, 2 in days, 3 in days, 4 in days,
                 5 in days, 6 in days, 7 in days, id,))
            db.commit()
        flash('. '.join(error))
        return render_template('alarm_setup/success.html',
                           params={'name': name, 'action': 'update alarm', 'return': url_for('alarm.update_alarm', id=id)})
    return render_template('alarm_setup/create_alarm.html', use=use, name=name, time=time, days=days,
                           sound_profile=sound_profile, color_profile=color_profile, active=active,
                           sound_profiles=sound_profiles, color_profiles=color_profiles)



@bp.route('/sound_profile', methods=('GET', 'POST'))
def create_sound_profile():
    if request.method == 'POST':
        profile_name = request.form['name']
        time_span = request.form['time_span']
        db = get_db()

        error = ''
        if not os.path.exists('profiles/sound/%s.py' % profile_name):
            error = 'Sound profile %s does not exists on the server' % profile_name
        if db.execute('SELECT id FROM sound_profiles WHERE name = ?',(profile_name,)).fetchone() is not None:
            error = 'Sound profile %s already exists in the database' % profile_name
        if error != '':
            db.execute('INSERT INTO sound_profiles (name, time_span) VALUES (?,?)', (profile_name, time_span))
            db.commit()
            return render_template('alarm_setup/success.html', params={'name': profile_name, 'action': 'create sound profile', 'return':url_for('alarm.create_sound_profile')})
        flash(error)
    return render_template('alarm_setup/create_profile.html', name='Sound ')


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
                                                                 'return': url_for('alarm.create_color_profile')})
        flash(error)
    return render_template('alarm_setup/create_profile.html', name='Color ')


@bp.route('/view', methods=('GET', 'POST'))
def view_alarms():
    db = get_db()
    df = pd.read_sql('SELECT * FROM alarms',con=db)
    df['repeat_dates'] = df.apply(lambda x: ', '.join([calendar.day_name[i] for i in range(7) if
                                                       x['repeat_' + calendar.day_name[i].lower()]]), axis=1)
    df['active'] = df['active'].astype(bool)
    # df['sound_profile']= df['sound_profile'].apply(lambda x: )
    df_sound = pd.read_sql('select * from sound_profiles', con=db).rename(
        columns={'id': 'sound_profile', 'name': 'sound_profile_name'})
    df_color = pd.read_sql('select * from color_profiles', con=db).rename(
        columns={'id': 'color_profile', 'name': 'color_profile_name'})
    df = pd.merge(df, df_sound[['sound_profile','sound_profile_name']], on='sound_profile', how='left')
    df = pd.merge(df, df_color[['color_profile','color_profile_name']], on='color_profile', how='left')
    return render_template('alarm_setup/view_alarms.html', df_alarms=df[
        ['id','name', 'alarm_time', 'repeat_dates', 'active', 'sound_profile_name', 'color_profile_name', 'created']])