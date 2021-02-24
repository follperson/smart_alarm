from flask import current_app, Blueprint, render_template, request, flash
from .alarm_classes import AlarmWatcher
bp = Blueprint('wakeup', __name__, url_prefix='/')


def get_watcher() -> AlarmWatcher:
    try:
        current_app.watcher
    except AttributeError as ok:
        print('new watcher')
        watcher = AlarmWatcher()
        current_app.watcher = watcher
    current_app.watcher.check()
    return current_app.watcher


@bp.route('/', methods=('GET', 'POST'))
def view():
    """
        This is the base landing page which shows all the alarms and allows you to snooze, or turn them on/off
    :return:
    """
    watcher = get_watcher()
    if request.method == 'POST':
        print(request.form)
        if 'snooze_generic' in request.form:
            if any([alarm.running for alarm in watcher.alarms]):
                for alarm in watcher.alarms:
                    if alarm.running:
                        alarm.snooze()
                        flash('Snoozed %s' % alarm.name)
            else:
                flash('No Alarms To Snooze')
        else:
            for alarm in watcher.alarms:
                aid = str(alarm.id)
                if aid in request.form:
                    break
            assert aid in request.form, 'You must select an AlarmID which matches the current running AlarmIDs'
            if request.form[aid] == 'Snooze':
                if alarm.running:
                    alarm.snooze()
            elif request.form[aid] == 'Turn On/Off':
                print('TurnOnOff %s %s' % (aid, alarm.on))
                if alarm.on:
                    alarm.turnoff()
                else:
                    alarm.turnon()
    return render_template('active/index.html', alarms=watcher.alarms)
