import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
import sys
from PIL import Image, ImageGrab
import time
import cv2 as cv 
import numpy as np
import pyautogui
import os
import random
import threading

FPS_REPORT_DELAY = 0.25

def get_asset_path(asset_name):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        executable_path = sys.executable
    else:
        # The application is not frozen
        executable_path = os.path.dirname(__file__)

    assets_path = os.path.join(os.path.dirname(executable_path), 'assets')
    asset_path = os.path.join(assets_path, asset_name)
    return asset_path

# Usage:
fishing_target_path = get_asset_path('fishing_target.png')
bait_target_path = get_asset_path('bait_target.png')
pole_target_path = get_asset_path('pole_target.png')

class TextRedirector:
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.insert(tk.END, str, self.tag)
        self.widget.see(tk.END)  # scroll to the end

    def flush(self):
        pass

class MainAgent:
    def __init__(self):
        self.cur_img = None
        self.cur_imgHSV = None
        self.stop_event = False
        self.zone = None
        self.time = None

class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Fishing")

        self.text_area = scrolledtext.ScrolledText(self.root, width=50, height=10)
        self.text_area.pack()

        self.fps_label = tk.Label(self.root, text="FPS: 0")
        self.fps_label.pack(side=tk.LEFT)

        self.bait_checkbox_var = tk.IntVar()
        self.bait_checkbox = tk.Checkbutton(self.root, text="Bait", variable=self.bait_checkbox_var)
        self.bait_checkbox.pack(side=tk.RIGHT)

        # Redirect print statements to the text area
        sys.stdout = TextRedirector(self.text_area, tag="stdout")

        self.start_screen_button = tk.Button(self.root, text="Start Screen Capture", command=self.start_screen_capture)
        self.start_screen_button.pack()

        self.start_fishing_button = tk.Button(self.root, text="Start Fishing", command=self.start_fishing)
        self.start_fishing_button.pack()

        self.stop_button = tk.Button(self.root, text="Stop All", command=self.stop_all_operations)
        self.stop_button.pack()

        self.main_agent = MainAgent()

        self.screen_capture_thread = None
        self.fishing_agent_thread = None

    def run(self):
        self.root.mainloop()

    def start_screen_capture(self):
        self.screen_capture_thread = Thread(
            target=self.update_screen, 
            args=(self.main_agent,), 
            name="update screen thread",
            daemon=False)
        self.screen_capture_thread.start()

    def update_screen(self, agent):
        print("Screen capture starting...")
        max_fps = 30
        loop_time = time.time()
        fps_print_time = time.time()
        fps = 0
        while not agent.stop_event:
            screenshot = ImageGrab.grab()
            screenshot = np.array(screenshot)
            screenshot = cv.cvtColor(screenshot, cv.COLOR_RGB2BGR)
            screenshotHSV = cv.cvtColor(screenshot, cv.COLOR_BGR2HSV)
            agent.cur_img = screenshot
            agent.cur_imgHSV = screenshotHSV

            cur_time = time.time()
            if cur_time - fps_print_time >= FPS_REPORT_DELAY:
                fps = 1 / (cur_time - loop_time)
                self.fps_label.config(text=f"FPS: {int(fps)}")
                fps_print_time = cur_time
            loop_time = cur_time

            delay = max(0, 1 / max_fps - (cur_time - loop_time))
            time.sleep(delay)
            cv.waitKey(1)

    def start_fishing(self):
        print("Starting fishing... 5 seconds...")
        time.sleep(5)
        self.fishing_agent = FishingAgent(self.main_agent, self.bait_checkbox_var, self.root)
        self.fishing_agent_thread = Thread(target=self.fishing_agent.run)
        self.fishing_agent_thread.start()

    def stop_all_operations(self):
        def stop_threads():
            if self.screen_capture_thread:
                self.main_agent.stop_event = True
                self.screen_capture_thread.join()
                self.screen_capture_thread = None
                print("Screen capture stopped...")

            if self.fishing_agent_thread:
                self.fishing_agent.stop_event.set()
                self.fishing_agent_thread.join()
                self.fishing_agent_thread = None
                print("Fishing stopped...")

        stop_thread = Thread(target=stop_threads)
        stop_thread.start()

class FishingAgent:
    def __init__(self, main_agent, bait_checkbox_var, root):
        self.main_agent = main_agent
        self.bait_checkbox_var = bait_checkbox_var
        self.root = root
        self.stop_event = threading.Event()
        
        # interpolate here_path to get the path to the fishing target image
        here_path = os.path.dirname(os.path.realpath(__file__))
        self.fishing_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "fishing_target.png"
            )
        )
        self.bait_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "bait_target.png"
            )
        )
        self.pole_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "pole_target.png"
            )
        )
        self.fishing_thread = None

    def bait_hook(self):
        bait_location = cv.matchTemplate(self.main_agent.cur_img, self.bait_target, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(bait_location)
        self.bait_location = max_loc
        self.move_to_bait()

    def move_to_bait(self):
        if self.bait_location:
            pyautogui.moveTo(self.bait_location[0], self.bait_location[1], .45, pyautogui.easeOutQuad)
            pyautogui.leftClick()
            time.sleep(1)
            self.find_pole()
        else:
            print("Warning: Attempted to move to bait_location, but bait_location is None (fishing_agent.py line 32)")
            return False
        
    def find_pole(self):
        pole_location = cv.matchTemplate(self.main_agent.cur_img, self.pole_target, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(pole_location)
        
        # Calculate the middle point of the pole_target image
        pole_w, pole_h = self.pole_target.shape[1], self.pole_target.shape[0]
        pole_mid_x, pole_mid_y = pole_w // 2, pole_h // 2
        
        # Add the middle point to the max_loc coordinates
        self.pole_location = (max_loc[0] + pole_mid_x, max_loc[1] + pole_mid_y)
        self.move_to_pole()

    def move_to_pole(self):
        if self.pole_location:
            pyautogui.moveTo(self.pole_location[0], self.pole_location[1], .45, pyautogui.easeOutQuad)
            pyautogui.leftClick()
            print("Left click performed. Waiting for 6 seconds...")
            time.sleep(6)  # schedule cast_lure to run after 6 seconds
        else:
            print("Warning: Attempted to move to pole_location, but pole_location is None (fishing_agent.py line 32)")
            return False


    def cast_lure(self):
        fish_bait = self.bait_checkbox_var.get()
        current_time = time.time()
        if fish_bait == 1:
            if not hasattr(self, 'last_bait_hook_time') or current_time - self.last_bait_hook_time >= 610:
                self.last_bait_hook_time = current_time
                print("Applying bait...")
                self.bait_hook()
            elif current_time - self.last_bait_hook_time >= 610 and fish_bait == 1:  # 600 seconds = 10 minutes
                self.last_bait_hook_time = current_time
                print("Reapplying bait...")
                self.bait_hook()
            else:
                print("Casting!...")
                self.fishing = True
                self.cast_time = time.time()
                pyautogui.press('1')
                time.sleep(2)
                self.find_lure()
        else:
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
            if pixel_set[0] < 11:
                if pixel[0] > 15:
                    print(f"Bite detected! Pixel: {pixel[0]} | Pixel_Set: {pixel_set[0]}")
                    break            
            if (pixel_set[0] + 11) < pixel[0] or (pixel_set[0] - 11) > pixel[0]:
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
        time.sleep(randtime)
        
        while not self.stop_event.is_set():
            self.cast_lure()
            if self.stop_event.is_set():
                break

if __name__ == "__main__":
    gui = GUI()
    gui.run()