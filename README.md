# Readme

## Project - RPi Alarm

An alarm clock, run off of a raspberry pi via python and flask. 

create, edit, and snooze alarms via a web interface. 

Alarm has two components - color and sound. 

color is driven by adafruit dotstars.

sound is driven by a USB speaker pyaudio interface. 



code repository for an alarm, run on raspberry pi. 

flask app interface to set / update / snooze alarms. 

You set alarm start time, wake up time interval. Sounds and lights slowly rise over interval, ending in google voice generated wake up voice.

audio raise and alarm basics function. Light non-functioning. Audio recording functioning, but intelligent alarm time does not and will not be functioning in 1.0.0
 
current version is 0.1.0


must install and make available to path:

- https://avbin.github.io/AVbin/Download.html
- https://www.ffmpeg.org/



make systemd file, name it smartalarm.service

copy to /etc/systemd/system/smartalarm.service

reset the daemons with sudo systemctl daemon-reload
start it with sudo systemctl

sudo systemctl enable smartalarm

review logs with systemctl status smartalarm.service -n 200
or like journalctl smartalarm.service



todo:  set it up as static IP

https://pimylifeup.com/raspberry-pi-static-ip-address/

step 1
`ip r | grep default`
`default via 192.168.1.1 dev wlan0 proto dhcp src 192.168.1.16 metric 303`

step 2
nameserver: 192.168.1.1
????


