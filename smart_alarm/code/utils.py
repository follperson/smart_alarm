from calendar import day_name
from .exceptions import PlaylistNotFound, EmptyTable
from flask import g
import pandas as pd
import sqlite3


def get_db_generic(db_params):
    db = sqlite3.connect(db_params,
                         detect_types=sqlite3.PARSE_DECLTYPES
                         )
    db.row_factory = sqlite3.Row
    return db


def init_app(app):
    app.teardown_appcontext(close_watchers())


def close_watchers(e=None):
    watcher = g.pop('watcher', None)
    if watcher is not None:
        watcher.close()



def get_profile_from_id(db, val, table):
    """ 
      Get name using id from arbitrary table
    inputs:
      db: database to be queried
      val: id
      table: table to be queried
    """
    return _get_profile('name', 'id', val, table, db)


def get_profile_from_name(db, val, table):
    """ 
      Get id using name from arbitrary table
    inputs:
      db: database to be queried
      val: name
      table: table to be queried
    """
    return _get_profile('id', 'name', val, table, db)


def _get_profile(field_want, field_have, value, table, db):
    val = db.execute('SELECT %s FROM %s WHERE %s=?' % (field_want, table, field_have) , (value,)).fetchone()
    if val is None:
        raise PlaylistNotFound('{} {} is not defined in {}'.format(field_want, value, table))
    return val


def _get_profiles(fields_want, table, db):
    if type(fields_want) == str:
        fields_want = [fields_want]
    val = db.execute('SELECT %s FROM %s' % (', '.join(fields_want), table)).fetchall()
    if val is None:
        raise EmptyTable('Empty table %s' % table)
    return val


def get_repeat_dates(x, string=True):
    if string:
        return ', '.join([day_name[i] for i in range(7) if x['repeat_' + day_name[i].lower()]])
    else:
        return [i for i in range(7) if x['repeat_' + day_name[i].lower()]]
