from flask import current_app, Blueprint, render_template, request, flash
from flask.logging import default_handler
from .alarm_classes import AlarmWatcher #, PyAudio, USBAUDIOID
from .db import get_db
import pandas as pd
import datetime as dt
import logging
bp = Blueprint('wakeup', __name__, url_prefix='/')
logger = logging.getLogger(__name__)
logger.addHandler(default_handler)
logger.setLevel(logging.INFO)


def get_watcher() -> AlarmWatcher:
    try:
        current_app.watcher
    except AttributeError as ok:
        logger.info('new watcher')
        watcher = AlarmWatcher()
        current_app.watcher = watcher
    current_app.watcher.check()
    return current_app.watcher

# todo give wake_window to the 'playlist' class?
#  and then calculate it on the fly for the alarm with a join

# todo prefill the current values when doing 'update'

# todo alarm volume min and max
# todo change volume on the fly???
# todo snoozetime variability

@bp.route('/', methods=('GET', 'POST'))
def view():
    """
        This is the base landing page which shows all the alarms and allows you to snooze, or turn them on/off
    :return:
    """
    db = get_db()
    df_alarms = pd.read_sql('select *, 2 snooze_time from ALARMS inner join '
                            '(select id sound_profile, name playlist_name from playlists) p '
                            'on p.sound_profile=ALARMS.sound_profile;', con=db)
    watcher = get_watcher()
    alarm_dict = df_alarms.set_index('id').to_dict('index')

    if request.method == 'POST':
        print(request.form)
        if 'snooze_generic' in request.form:
            for alarm_id in watcher.alarms:
                if watcher.alarms[alarm_id].isAlive():
                    watcher.alarms[alarm_id].snooze()
                    flash('Snoozed %s' % watcher.alarms[alarm_id].name)
            else:
                flash('No Alarms To Snooze')
        else:
            for alarm_id in alarm_dict:
                alarm = watcher.alarms[alarm_id]
                if f'snooze_{alarm_id}' in request.form:
                    alarm.snooze()
                    alarm_dict[alarm_id]['snoozed'] = True
                if f'io_{alarm_id}' in request.form:
                    alarm.active = not alarm.active  # switch it!
                    if alarm.isAlive():
                        alarm.join(0)
                        alarm.stop()
                    db.execute('UPDATE alarms SET active = ?, modified = ? WHERE id=?',
                               (alarm.active, dt.datetime.now(), alarm_id,))
                    db.commit()
                if f'mute_{alarm_id}' in request.form:
                    if not alarm.muted:
                        alarm.mute()
                    else:
                        alarm.unmute()
                if f'blind_{alarm_id}' in request.form:
                    if not alarm.blinded:
                        alarm.blind()
                    else:
                        alarm.unblind()
                if f'skip_{alarm_id}' in request.form:
                    alarm.skip()

    for alarm_id in alarm_dict:
        assert alarm_id in watcher.alarms, 'Alarm ID not in sql'
        alarm = watcher.alarms[alarm_id]
        alarm_dict[alarm_id]['snoozed'] = alarm.snoozed
        alarm_dict[alarm_id]['active'] = alarm.active
        alarm_dict[alarm_id]['running'] = alarm.isAlive()
        alarm_dict[alarm_id]['snooze_time_left'] = alarm.snooze_time_left
        alarm_dict[alarm_id]['next_alarm_time'] = alarm.next_alarm_time
    any_running = any(alarm_dict[alarm_id]['running'] for alarm_id in alarm_dict)

    return render_template('active/index.html', alarms=alarm_dict, any_active=any_running)
