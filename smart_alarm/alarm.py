import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import calendar
import os

from .db import get_db


bp = Blueprint('alarm', __name__, url_prefix='/alarm')

def format_time(time):
    return time

@bp.route('/')
def index():
    return render_template('setup/index.html')

@bp.route('/create', methods=('GET', 'POST'))
def create_alarm():
    db = get_db()
    sound_profiles = db.execute('SELECT name FROM sound_profiles').fetchall()
    color_profiles = db.execute('SELECT name FROM color_profiles').fetchall()
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

        if not len(error) == 0:
            time = format_time(time)
            db.execute(
                'INSERT INTO alarms (name, alarm_time, active, sound_profile, color_profile repeat_monday, repeat_tuesday, repeat_wednesday, repeat_thursday, repeat_friday, repeat_saturday, repeat_sunday) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (name, time, active, sound_profile_id, color_profile_id, 0 in days, 1 in days, 2 in days, 3 in days, 4 in days, 5 in days, 6 in days)
            )
            db.commit()

            print(url_for(create_alarm))
            return render_template('setup/success.html', params={'name':name, 'action':'create alarm', 'return':url_for('alarm.create_alarm')})
        flash('. '.join(error))


    return render_template('setup/create_alarm.html', sound_profiles=sound_profiles, color_profiles=color_profiles)

#TODO: view = create/read/update/delete home
@bp.route('/update', methods=('GET', 'POST'))
def update_alarm():
    if request.method == 'POST':
        time = request.form['time']
        # name = request.form['name']
        # sound_profile = request.form['sound_profile']
        # color_profile = request.form['color_profile']
        # active = 'active' in request.form
        # days = [day for day in range(1, 8) if calendar.day_name[day] in request.form]
        # db = get_db()
        #
        # sound_profile_id = db.execute('SELECT id FROM sound_profiles WHERE name = ?', sound_profile).fetchone()
        # color_profile_id = db.execute('SELECT id FROM color_profiles WHERE name = ?', color_profile).fetchone()
        #
        # error = []
        # if len(days) == 0:
        #     error.append("Please select a day for this alarm")
        # if db.execute('SELECT id FROM alarms WHERE name = ?', name).fetchone() is not None:
        #     error.append('Alarm name {} is already registered, please select another.'.format(name))
        # if sound_profile_id is None:
        #     error.append('Sound profile {} is not defined'.format(sound_profile))
        # if sound_profile_id is None:
        #     error.append('Color profile {} is not defined'.format(color_profile))
        #
        # if not len(error) == 0:
        #     time = format_time(time)
        #     db.execute(
        #         'INSERT INTO alarms (name, alarm_time, active, sound_profile, color_profile repeat_monday, repeat_tuesday, repeat_wednesday, repeat_thursday, repeat_friday, repeat_saturday, repeat_sunday) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        #         (name, time, active, sound_profile_id, color_profile_id, 1 in days, 2 in days, 3 in days, 4 in days,
        #          5 in days, 6 in days, 7 in days)
        #     )
        #     db.commit()
        # flash('. '.join(error))

    return render_template('setup/update_alarm.html')



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
            return render_template('setup/success.html', params={'name': profile_name, 'action': 'create sound profile', 'return':url_for('alarm.create_sound_profile')})
        flash(error)
    return render_template('setup/create_profile.html', name='Sound ')


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
            return render_template('setup/success.html', params={'name': profile_name, 'action': 'create sound profile',
                                                                 'return': url_for(create_sound_profile)})
        flash(error)
    return render_template('setup/create_profile.html', name='Color ')



@bp.route('/view', methods=('GET', 'POST'))
def view_alarms():
    pass