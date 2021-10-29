source ~/miniconda3/bin/activate SmartAlarm
export FLASK_APP=smart_alarm
export FLASK_ENV=development
export FLASK_RUN_RELOAD=False

flask run --host=0.0.0.0 --port=8080