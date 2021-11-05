from flask import Blueprint, flash, render_template
import os
from .src.utils import get_logger

bp = Blueprint('logs', __name__, url_prefix='/logs')
logger = get_logger(__name__)


@bp.route('/<string:logname>/<int:n>', methods=('GET',))
def return_log_n(logname, n):
    return return_log(logname, n)

@bp.route('/', methods=('GET',))
def view_logs():
    lognames = [f.split('.log')[0] for f in os.listdir('logs') if f.endswith('.log')]
    return render_template('viewlog/index.html',lognames=lognames)




@bp.route('/<string:logname>', methods=('GET',))
def return_log_all(logname):
    return return_log(logname, n=0)


def return_log(logname, n=0):
    """
    Create a nm new alarm using already established playlists and color profiles
    """
    logger.debug(f'Reading Log {logname}')
    if not os.path.exists(f'logs/{logname}.log'):
        flash(f'No Log Named {logname}')
        log_info = ''
    else:
        with open(f'logs/{logname}.log','r') as fo:
            log_info = fo.readlines()
        if n != 0:
            log_info = log_info[-n:]
    cleaned_log_info = []
    for line in log_info:
        if not line.startswith('['):
            line = '&nbsp;&nbsp;&nbsp;&nbsp;' + line
        cleaned_log_info.append(line + '<br>')
    return render_template('viewlog/view-log.html', log=''.join(cleaned_log_info))
