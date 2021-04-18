import board
import adafruit_dotstar as dotstar
import time
import numpy as np
from dataclasses import dataclass
from threading import Thread, Event
from typing import Tuple
import json
dots = dotstar.DotStar(board.SCLK, board.MOSI, 120, brightness=0.9)

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

    def save(self, filepath):
        with open(filepath,'w') as fo:
            json.dump({'cycle': self.cycle,
                        'end':self.end,
                        'start':self.start}, fo)
        
    @classmethod
    def load(cls, filepath):
        with open(filepath, 'r') as fo:
            config = json.load(fo)
        return cls(**config)


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
            print('index', ix)
            print('cycle length',len(self.profile.cycle))
            increment = self.profile.cycle[ix]
            next_step = tuple(self.cur_colors[i] + increment[i] for i in [0,1,2])
            self.cur_colors = next_step
            
            print(f'Step {i} out of {steps} ', self.cur_colors)
            
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

def ctest():
    #p=ColorProfile(cycle=((1,0,0),(0,2,0),(0,0,1),(1,0,0),(0,0,1)),
    #            end=(255,255,255),start=(0,0,0))
    p = ColorProfile.load('/home/pi/red_orange_only.json')
    t = 120
    c = Colors(p, t)
    time.sleep(t)
    #time.sleep(15)
    #c.pause()
    #time.sleep(10)
    #c.play()
    #time.sleep(10)
    #c.pause()
    #time.sleep(1)
    #c.stop()

if __name__ is "__main__":
    ctest()