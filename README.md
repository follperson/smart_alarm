# smart_alarm

code repository for an alarm, run on raspberry pi. 

flask app interface to set / update / snooze alarms. 

You set alarm start time, wake up time interval. Sounds and lights slowly rise over interval, ending in google voice generated wake up voice.

audio raise and alarm basics function. Light non-functioning. Audio recording functioning, but intelligent alarm time does not and will not be functioning in 1.0.0
 
current version is 0.1.0

needs light functionality added fully
needs music functionality
needs website structure fleshed out
- view -> CRUD on profiles
- view -> CRUD on alarms
- view current alarm

must install and make available to path:
https://avbin.github.io/AVbin/Download.html
https://www.ffmpeg.org/



make systemd file, name it smartalarm.service

copy to /etc/systemd/system/smartalarm.service

reset the daemons with sudo systemctl daemon-reload
start it with sudo systemctl

sudo systemctl enable smartalarm

review logs with systemctl status smartalarm.service -n 200
or like journalctl smartalarm.service