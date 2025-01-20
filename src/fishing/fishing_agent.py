
import cv2 as cv
import numpy as np
import pyautogui
import time
from threading import Thread
import os
import random
class FishingAgent:
    def __init__(self, main_agent):
        self.main_agent = main_agent
        
        # interpolate here_path to get the path to the fishing target image
        here_path = os.path.dirname(os.path.realpath(__file__))
        self.fishing_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "fishing_target.png"
            )
        )
        
        self.fishing_thread = None

    def cast_lure(self):
        print("Casting!...")
        self.fishing = True
        self.cast_time = time.time()
        pyautogui.press('1')
        time.sleep(2)
        self.find_lure()

    def find_lure(self):
        start_time = time.time()
        lure_location = cv.matchTemplate(self.main_agent.cur_img, self.fishing_target, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(lure_location)
        self.lure_location = max_loc
        self.move_to_lure()

    def move_to_lure(self):
        if self.lure_location:
            pyautogui.moveTo(self.lure_location[0] + 25, self.lure_location[1], .45, pyautogui.easeOutQuad)
            self.watch_lure()
        else:
            print("Warning: Attempted to move to lure_location, but lure_location is None (fishing_agent.py line 32)")
            return False

    def watch_lure(self):
        time.sleep(0.5)
        pixel_set = self.main_agent.cur_imgHSV[self.lure_location[1] + 25][self.lure_location[0]]
        print(f"Final pixel set: {pixel_set[0]}")
        time_start = time.time()
        while True:
            pixel = self.main_agent.cur_imgHSV[self.lure_location[1] + 25][self.lure_location[0]]            
            if self.main_agent.zone == "Feralas" and self.main_agent.time == "night":
                if (pixel_set[0] + 10) < pixel[0] or (pixel_set[0] - 6) > pixel[0]:
                    print(f"Bite detected! Pixel: {pixel[0]} | Pixel_Set: {pixel_set[0]}")
                    break
                if time.time() - time_start >= 28:
                    print("Didn't see a bite, I'm stupid!")
                    break
        self.pull_line()

    def pull_line(self):
        pyautogui.rightClick()
        # os.system("sh -c 'xdotool keydown Shift_L; sleep 0.1; xdotool mousedown 3; sleep 0.1; xdotool mouseup 3; sleep 0.1; xdotool keyup Shift_L; sleep 0.1'")
        time.sleep(1)
        self.run()

    def run(self):
        if self.main_agent.cur_img is None:
            print("Image capture not found!  Did you start the screen capture thread?")
            return
        randtime = random.randint(1,3)
        print(f"Starting fishing thread in {randtime} seconds...")
        time.sleep(randtime)
        
        # print("Switching to fishing hotbar (hotbar 2)")
        # pyautogui.keyDown('shift')
        # pyautogui.press('2')
        # pyautogui.keyUp('shift')
        # time.sleep(1)
        
        self.fishing_thread = Thread(
            target=self.cast_lure, 
            args=(),
            name="fishing thread",
            daemon=True)    
        self.fishing_thread.start()
