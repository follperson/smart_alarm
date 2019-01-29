def get_profile_from_id(db, val, table):
    return _get_profile('name','id', val, table, db)


def get_profile_from_name(db, val, table):
    return _get_profile('id','name', val, table, db)


def _get_profile(field_want, field_have, value, table, db):
    val = db.execute('SELECT %s FROM %s WHERE %s=?' % (field_want, table, field_have) , (value,)).fetchone()
    assert val is not None, '{} {} is not defined in {}'.format(field_want, value, table)
    return val


def _get_profiles(fields_want, table, db):
    if type(fields_want) == str:
        fields_want = [fields_want]
    val = db.execute('SELECT %s FROM %s' % (', '.join(fields_want), table)).fetchall()
    assert val is not None, 'Empty table %s' % table
    return val
