from .utils import get_logger
import time
import numpy as np
from dataclasses import dataclass
from threading import Thread, Event
from typing import Tuple
import adafruit_dotstar as dotstar

logger = get_logger('play-color')

n_dotstar = 90

try:
    import board
    dots = dotstar.DotStar(board.SCLK, board.MOSI, n_dotstar, brightness=1)
except NotImplementedError:
    class dumbdots:
        def __init__(self):
            pass

        def fill(self, x):
            pass

    dots = dumbdots()


@dataclass
class ColorProfile:
    cycle: Tuple[Tuple] # ((1,0,0),(2,0,0), (0,1,2))
    end: Tuple
    start: Tuple

    def get_steps(self) -> int:
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
    def __init__(self, profile: ColorProfile, seconds: int, *args, **kwargs):
        logger.debug(f'Initializing color profile {profile}')
        self.profile = profile
        
        # print('audiosegment set')

        self.is_paused = True
        self.dots = dots
        self.cur_colors = self.profile.start
        self.seconds = seconds
        self.dummy = not isinstance(dots, dotstar.DotStar)
        Thread.__init__(self, *args, **kwargs)
        
        # Thread functions
        self._stop_event = Event()
        self.start()

    def pause(self):
        """ pause the updates """
        logger.info('Pausing Dots')
        self.is_paused = True

    def play(self):
        logger.info('Unpausing Dots')
        self.is_paused = False

    def stop(self):
        """ turn off the puppies """
        logger.info('Stopping Dots')
        self.turn_off_dots()
        self._stop_event.set()

    def stopped(self):
        """ check if the thread is stopped """
        return self._stop_event.is_set()

    def turn_off_dots(self):
        logger.info('Turning Off Dots')
        self.dots.fill((0, 0, 0))
        
    def reset_dots(self, start):
        logger.info('Resetting Dots')
        self.dots.fill(start)
    
    def run(self):
        logger.info('Running Dotstar')
        self.run_fill()

    def run_fill(self):
        """ run this puppy! """
        logger.info("Running Color Profile")
        self.play()
        
        steps = self.profile.get_steps()
        cycle_length = len(self.profile.cycle)
        self.dots.fill(self.profile.start)
        wait_seconds = self.seconds / steps
        
        for i in range(steps):  # is_paused maybe interferes?
            time.sleep(wait_seconds)
            
            ix = i % cycle_length
            
            increment = self.profile.cycle[ix]
            next_step = tuple(self.cur_colors[i] + increment[i] for i in [0, 1, 2])
            self.cur_colors = next_step

            while self.is_paused:
                self.turn_off_dots()
                if self.stopped():
                    break
                time.sleep(5)

            if self.stopped():
                break
            
            self.dots.fill(next_step)
        
        self.turn_off_dots()
        self.stop()
