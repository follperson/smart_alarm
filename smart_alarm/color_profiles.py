from flask import (Blueprint, flash, render_template, request, url_for)
import os
from .db import get_db
import pandas as pd

# todo

bp = Blueprint('color', __name__, url_prefix='/color')

@bp.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        profile_name = request.form['name']
        time_span = request.form['time_span']
        db = get_db()

        error = ''
        if not os.path.exists('smart_alarm/profiles/color/%s.py' % profile_name): # make flexible
            error = 'Color profile %s does not exists on the server' % profile_name

        if db.execute('SELECT id FROM color_profiles WHERE name = ?',(profile_name,)).fetchone() is not None:
            error = 'Color profile %s already exists in the database' % profile_name
        if error == '':
            db.execute('INSERT INTO color_profiles (name, time_span) VALUES (?,?)', (profile_name, time_span))
            db.commit()
            return render_template('alarms/success.html', params={'name': profile_name, 'action': 'create color profile',
                                                                 'return': url_for('color.create')})
        flash(error)
    return render_template('sound_color/create_profile.html', name='Color ')

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
def update():
    flash('NOT IMPLEMENTED _ HOLDER PAGE')
    if request.method == 'POST':
        profile_name = request.form['name']
        time_span = request.form['time_span']
        db = get_db()

        error = ''
        if not os.path.exists('smart_alarm/profiles/color/%s.py' % profile_name): # make flexible
            error = 'Color profile %s does not exists on the server' % profile_name

        if db.execute('SELECT id FROM color_profiles WHERE name = ?',(profile_name,)).fetchone() is not None:
            error = 'Color profile %s already exists in the database' % profile_name
        if error == '':
            db.execute('INSERT INTO color_profiles (name, time_span) VALUES (?,?)', (profile_name, time_span))
            db.commit()
            return render_template('alarms/success.html', params={'name': profile_name, 'action': 'create color profile',
                                                                 'return': url_for('color.create')})
        flash(error)
    return render_template('sound_color/create_profile.html', name='Color ')


@bp.route('/view', methods=('GET',))
def view():
    db = get_db()
    df = pd.read_sql('SELECT * FROM color_profiles', con=db)
    df_alarms = pd.read_sql('SELECT * FROM alarms', con=db)
    df = pd.merge(df, df_alarms[['name', 'color_profile']], how='left', right_on='color_profile',
                  left_on='id', suffixes=['_profile', '_alarm'])
    df = df.rename(columns={'name_alarm': 'Alarm Name', 'name_profile': 'profile Name', 'time_span': 'Time Span',
                            'id_profile': 'id'})
    print(df)

    print(df.empty)
    return render_template('sound_color/view_color_profiles.html', df=df[['id', 'profile Name', 'Alarm Name']])
