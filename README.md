# YARPAC: (Yet Another) Raspberry Pi Alarm Clock 

## Abstract

Instructions for a hardware lite / software heavy Rasbperry Pi alarm clock, using Dotstar LEDs and an external speaker
to wake you up. 

## Introduction

Do you want a physical alarm clock (beyond just your phone) that you can interface with using your phone? 
Are you tired of waking up only to the blaring sound of an alarm, instead of a more organic gradual rise? 
Would you like an alarm clock which uses both light and audio to gently raise you from dream land to wakefulness, 
where the first thing you think is not 'I hate my alarm'?

Well if you also dabble in software and hardware (an educated guess, considering you are reading this), perhaps
you will like this Raspberry Pi Alarm clock project! If you are familiar with flask and raspberry pis this should not
be too much of a lift. 

[This repository](https://github.com/follperson/smart-alarm-clock) will set you up with the primary software drivers 
to implement this. 

### Agenda 

This article will loosely document the primary steps in this project. 

1. Explore at the hardware reuirements and softwares used.
2. High level code and software setup
3. Usage and high level configurations
4. Improvements
5. References

## Getting Started

### Hardware and Software Overview

This project runs off of a Raspberry Pi, I used a Raspberry Pi 3B+(link), but certainly more recent versions will work, and
older ones will probably too, if you have Wifi card. 
The Raspberry Pi Zero (link) will not because there are not enough usb ports. The software is
here in this repository, but the functionality is enabled by: the Flask(link) microframework for Python for remote interfacing, the
PyAudio (link) python bindings for LibAudio, PyDub (link) for manipulating raw audio, Adafruit Dotstar bindings, and google voice to speech (link). 

#### Hardware Requirements

1. Raspberry Pi (3b+) or newer, preferably
1. adafruit dotstars (1 yard) (link) 
    - you can use more but will require an external power source, which may further require logic gate shifting, which is not covered here, but see: (link)
    - could also use other thing
2. USB Speaker (link)
2. breadboard (optional but recommended) (link)
2. rpi gpio to breadboard connector (optional but recommended) (link)
2. rpi gpio bus (link)
2. rpi solder board (link)
2. rpi socket for solder board (link)

4. peripherals: 
    4. HDMI based monitor
    5. USB keyboard
    6. USB Mouse
    7. Wifi + Router
    8. phone or other device connected to wifi to drive it
    
#### Software Version Requirements

1. python 3.6
2. miniconda
3. pyaudio
4. pydub


### Pre-RPI Alarm clock Setup

Need a rasbian burned raspberry pi. There are many tutorials (links).

Need google voice stuff, save to a file called `google-key.txt`

miniconda

must install and make available to path:

- https://avbin.github.io/AVbin/Download.html
- https://www.ffmpeg.org/

## repoistory setup and config setup

clone the repo

get some audio bro

test the dotstars


### internal setup

start it up

add color

add playlist

add alrm

start it

should work!

## next steps

celery or rabbitmq?

give dns to router somehow??


previous readme work:

An alarm clock, run off of a raspberry pi via python and flask.

create, edit, and snooze alarms via a web interface. 

Alarm has two components - color and sound. 

color is driven by adafruit dotstars.

sound is driven by a USB speaker pyaudio interface. 



code repository for an alarm, run on raspberry pi. 

flask app interface to set / update / snooze alarms. 

You set alarm start time, wake up time interval. Sounds and lights slowly rise over interval, ending in google voice generated wake up voice.

audio raise and alarm basics function. 
 
current version is 0.1.0




make systemd file, name it smartalarm.service

copy to /etc/systemd/system/smartalarm.service

reset the daemons with sudo systemctl daemon-reload
start it with sudo systemctl

sudo systemctl enable smartalarm

review logs with systemctl status smartalarm.service -n 200
or like journalctl smartalarm.service


to get portaudio 
- (error: portaudio.h: No such file or directory
- solve: `sudo apt-get install portaudio19-dev`

to get hardware spi working:
- https://www.raspberrypi-spy.co.uk/2014/08/enabling-the-spi-interface-on-the-raspberry-pi/

wiring
- https://cdn-learn.adafruit.com/assets/assets/000/063/404/medium640/led_strips_raspi_DotStar_SPI_bb.jpg?1539274090
- https://learn.adafruit.com/adafruit-dotstar-leds/python-circuitpython


todo:  set it up as static IP

https://pimylifeup.com/raspberry-pi-static-ip-address/

dockered

docker build .
docker run -it (to get into the container)

step 1
`ip r | grep default`
`default via 192.168.1.1 dev wlan0 proto dhcp src 192.168.1.16 metric 303`

step 2
nameserver: 192.168.1.1
????


