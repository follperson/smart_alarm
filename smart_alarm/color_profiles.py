from flask import (Blueprint, flash, render_template, request, url_for)
import os
import json
from .db import get_db
import pandas as pd


bp = Blueprint('color', __name__, url_prefix='/color')

def process_profile_creation(form):
    
    start = form['R_start'], form['G_start'], form['B_start']
    end = form['R_end'], form['G_end'], form['B_end']
    cycle = []
    for i in map(str, range(10)):
        cycle.append((form['R_' + i], form['G_'+ i], form['B_'+ i]))
    start = tuple(map(int, start))
    end = tuple(map(int, end))
    cycle = tuple(tuple(map(int, inc)) for inc in cycle)
    for i, color  in enumerate(cycle[::-1]):
        if color != (0,0,0):
            break
    print(i)
    print(cycle[:-i])
    return {'start':start, 'end':end, 'cycle':tuple(cycle[:-i])}


@bp.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        profile_name = request.form['name']
        profile = process_profile_creation(request.form)
        db = get_db()

        error = ''
        if db.execute('SELECT id FROM color_profiles WHERE name = ?',(profile_name,)).fetchone() is not None:
            error += 'Color profile %s already exists in the database.\t' % profile_name
        elif len(profile['cycle']) ==0:
            error += "No nonzero cycle elements!"
        else:
            db.execute('INSERT INTO color_profiles (name, profile) VALUES (?,?)', (profile_name, json.dumps(profile)))
            db.commit()
            return render_template('alarms/success.html', params={'name': profile_name,
                                                                  'action': 'create color profile',
                                                                  'return': url_for('color.create')})
        flash(error)
    return render_template('sound_color/create_profile.html', name='Color ')

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
def update(id):
    if request.method == 'POST':
        profile_name = request.form['name']
        profile = process_profile_creation(request.form)

        db = get_db()

        error = ''

        if db.execute('SELECT id, name, profile FROM color_profiles WHERE id = ?',(id,)).fetchone() is not None:
            error = 'Color profile %s does not exist, cannot update' % profile_name
        elif len(profile['cycle']) ==0:
            error += "No nonzero cycle elements!"
        else:
            db.execute('INSERT INTO color_profiles (name, profile) VALUES (?,?)', (profile_name, json.dumps(profile)))
            db.commit()
            return render_template('alarms/success.html', params={'name': profile_name, 'action': 'update color profile',
                                                                 'return': url_for('color.create')})
        flash(error)
    return render_template('sound_color/create_profile.html', name='Update Color ')


@bp.route('/view', methods=('GET',))
def view():
    db = get_db()
    df = pd.read_sql('SELECT * FROM color_profiles', con=db)
    df_alarms = pd.read_sql('SELECT * FROM alarms', con=db)
    df = pd.merge(df, df_alarms[['name', 'color_profile']], how='left', right_on='color_profile',
                  left_on='id', suffixes=['_profile', '_alarm'])
    df = df.rename(columns={'name_alarm': 'Alarm', 'name_profile': 'Profile', 'profile': 'profile_json', 'id_profile': 'id'})
    df['profile'] = df['profile_json'].apply(json.loads)
    df['color cycle'] = df['profile'].str['cycle']
    df['start color'] = df['profile'].str['start']
    df['end color'] = df['profile'].str['end']
    print(df)
    return render_template('sound_color/view_color_profiles.html', df=df[['id','Profile', 'Alarm', 'color cycle','start color','end color']])
