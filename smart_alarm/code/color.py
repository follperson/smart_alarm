import board
import adafruit_dotstar as dotstar
import time
import numpy as np
from dataclasses import dataclass
from threading import Thread, Event
from typing import Tuple
import json
dots = dotstar.DotStar(board.SCLK, board.MOSI, 30, brightness=0.9)

@dataclass
class ColorProfile:
    cycle : Tuple[Tuple] # ((1,0,0),(2,0,0), (0,1,2))
    end : Tuple
    start : Tuple

    def get_steps(self):
        assert self.end > self.start, 'end cannot be less than start'
        cycle_length = len(self.cycle)
        diff = np.array(self.end) - np.array(self.start)
        if cycle_length == 1:
            cycle_total = np.array(self.cycle)
        else:
            cycle_total = np.array(self.cycle).sum(axis=0)

        n = np.nanmin(diff / cycle_total)

        return int(n) * cycle_length


class Colors(Thread):
    """
      dotstart player object. building on Thread object and dotsstart
      Used to play audio files
    """
    def __init__(self, profile, seconds, *args, **kwargs):
        print('initialized color',profile)
        self.profile = profile
        
        # print('audiosegment set')
        self.__is_paused = True
        self.dots = dots
        self.cur_colors = self.profile.start
        self.seconds = seconds
        Thread.__init__(self, *args, **kwargs)
        
        # Thread functions
        self._stop_event = Event()
        self.start()

    def pause(self):
        """ pause the updates """ 
        self.__is_paused = True

    def play(self):
        self.__is_paused = False

    def stop(self):
        """ turn off the puppies """
        self._stop_event.set()

    def stopped(self):
        """ check if the thread is stopped """
        return self._stop_event.is_set()

    def turn_off_dots(self):
        self.dots.fill((0,0,0))
        
    def reset_dots(self, start):
        self.dots.fill(start)
    
    def run(self):
        self.run_fill()

    def run_fill(self):
        """ run this puppy! """
        print("Running")
        self.play()
        
        steps = self.profile.get_steps()
        cycle_length = len(self.profile.cycle)
        self.dots.fill(self.profile.start)
        wait_seconds = self.seconds / steps
        
        for i in range(steps):
            time.sleep(wait_seconds)
            
            ix = i % cycle_length
            
            increment = self.profile.cycle[ix]
            next_step = tuple(self.cur_colors[i] + increment[i] for i in [0,1,2])
            self.cur_colors = next_step
            
            
            while self.__is_paused:
                print('paused')
                if self.stopped():
                    print('pause stopped')
                    break
                time.sleep(5)

            if self.stopped():
                print('stopped')
                break
            
            self.dots.fill(next_step)
        
        self.turn_off_dots()
        self.stop()
