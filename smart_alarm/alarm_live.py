from flask import (
    Blueprint, flash, render_template, request
)
import pandas as pd

from .db import get_db


bp = Blueprint('live', __name__, url_prefix='/live')


@bp.route('/')
def view():
    db = get_db()
    alarms = pd.read_sql('SELECT * FROM alarms', con=db)
    return render_template('active/index.html', alarms=alarms.to_dict('records'), cols_to_display=['name','alarm_time'])


@bp.route('/<int:id>/modify',methods=['GET','POST'])
def modify(id):
    from smart_alarm.code.alarm_functions import snooze_alarm, cancel_alarm

    if request.method == 'POST':
        if 'snooze1' in request.form:
            snooze_alarm(10)
            message = 'Snoozed for 10 minutes, '
        elif 'snooze2' in request.form:
            snooze_alarm(10, True)
            message = 'Snoozed for 10 and reset awake cycle'
        elif 'cancel' in request.form:
            cancel_alarm()
            message = 'Cancelled alarm. Good morning'
        else:
            message = 'missing you'
        flash(message)
    render_template('active/modify.html')

