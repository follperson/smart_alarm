from flask import (
Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import functools
import pandas as pd
import calendar
import os

from .db import get_db


bp = Blueprint('alarm_live', __name__, url_prefix='/alarm')
pass




@bp.route('/')
def index():
    return render_template('alarm_setup/index.html')

@bp.route('/change',methods=['GET','POST'])
def cancel():
    if request.method == 'POST':
        # cancel alarm
        # flash(canceled)
        pass
    render_template('active/modify.html')
