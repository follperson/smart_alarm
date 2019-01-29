import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    import pandas as pd
    import sys
    import os
    if os.path.exists(r'C:\Users\follm\Documents\coding\smart_alarm_clock'):
        root = r'C:\Users\follm\Documents\coding\smart_alarm_clock'
    elif os.path.exists(r'C:\Users\Andrew Follmann\Documents\projects\alarm_clock'):
        root = r'C:\Users\Andrew Follmann\Documents\projects\alarm_clock'
    sys.path.append(root)
    import music_metadata

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    db = get_db()
    df = music_metadata.scan_directory(root)
    df.to_sql('audio',con=db,if_exists='append',index=False)
    # with current_app.open_resource('initial_insert.sql') as f:
    #     db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
