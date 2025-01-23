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
        self.root.title("PPFB v1.1")

        self.text_area = scrolledtext.ScrolledText(self.root, width=75, height=15)
        self.text_area.pack()
        self.text_area.tag_config('center', justify='center')
        self.text_area.tag_config('bold_underline', font=('Shentox', '12', 'bold underline'))
        self.text_area.insert(tk.INSERT, """
*************************************************************************
""")
        self.text_area.insert(tk.INSERT, "Primary Pixel Fishing Bot v1.1\n", ('bold_underline', 'center'))
        self.text_area.insert(tk.INSERT, """
Deleting unwanted fish is supported through the bait checkbox.

1. Start Screen Capture

2. Start Fishing (5 second delay)

3. Maximize WoW window.                 
*************************************************************************
""")


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
        self.clam_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "clam_target.png"
            )
        )
        self.yellowtail_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "yellowtail_target.png"
            )
        )
        self.yes_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "yes_target.png"
            )
        )
        self.mightfish_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "mightfish_target.png"
            )
        )
        self.cod_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "cod_target.png"
            )
        )
        self.fishing_thread = None

    def bait_hook(self):
        # Initialize a set to store the clicked locations
        clicked_locations = set()
        # Find the clam_target image on the screen
        print("Opening Bags...")
        pyautogui.press('b')
        time.sleep(1)
        print("Clearing bags...")
        # Finding Images for bag cleanup
        clams = cv.matchTemplate(self.main_agent.cur_img, self.clam_target, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(clams)
        yellowtails = cv.matchTemplate(self.main_agent.cur_img, self.yellowtail_target, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(yellowtails)
        yes_button = cv.matchTemplate(self.main_agent.cur_img, self.yes_target, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(yes_button)
        mightfish = cv.matchTemplate(self.main_agent.cur_img, self.mightfish_target, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(mightfish)
        cod = cv.matchTemplate(self.main_agent.cur_img, self.cod_target, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(cod)
        # Get the width and height of the clam_target image
        clam_w, clam_h = self.clam_target.shape[1], self.clam_target.shape[0]
        yellowtail_w, yellowtail_h = self.yellowtail_target.shape[1], self.yellowtail_target.shape[0]
        yes_w, yes_h = self.yes_target.shape[1], self.yes_target.shape[0]
        mightfish_w, mightfish_h = self.mightfish_target.shape[1], self.mightfish_target.shape[0]
        cod_w, cod_h = self.cod_target.shape[1], self.cod_target.shape[0]
        
        clam_count = 0
        yellowtail_count = 0
        mightfish_count = 0
        cod_count = 0
        
        # Iterate over the locations where the image was found
        if np.any(clams >= 0.9):
            for loc in zip(*np.where(clams >= 0.9)[::-1]):
                # Calculate the center of the image
                clam_x = loc[0] + clam_w // 2
                clam_y = loc[1] + clam_h // 2
            # Check if the location has already been clicked
                if (clam_x, clam_y) not in clicked_locations:
                    # Click in the center of the image
                    pyautogui.moveTo(clam_x, clam_y)
                    pyautogui.rightClick()
                    # Add the location to the set of clicked locations
                    clicked_locations.add((clam_x, clam_y))
                    time.sleep(1)
        else:
            print("No clams found.")
        print("Clams operation complete.")
        print("Checking for Yellowtails...")
        if np.any(yellowtails >= 0.9):
            for loc in zip(*np.where(yellowtails >= 0.9)[::-1]):
                # Get the screen width and height
                screen_width, screen_height = pyautogui.size()
                
                # Calculate the center of the screen
                screen_x = screen_width // 2
                screen_y = screen_height // 2
                
                # Calculate the center of the image
                yellowtail_x = loc[0] + yellowtail_w // 2
                yellowtail_y = loc[1] + yellowtail_h // 2
                
                # Check if the location has already been clicked
                if (yellowtail_x, yellowtail_y) not in clicked_locations:
                    
                    # Click in the center of the image
                    pyautogui.moveTo(yellowtail_x, yellowtail_y)
                    pyautogui.leftClick()
                    time.sleep(1)
                    
                    # Add the location to the set of clicked locations
                    clicked_locations.add((yellowtail_x, yellowtail_y))
                    
                    # Move to center screen.
                    pyautogui.moveTo(screen_x, screen_y)
                    pyautogui.leftClick()
                    time.sleep(1)
                    yes_button = cv.matchTemplate(self.main_agent.cur_img, self.yes_target, cv.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(yes_button)
                    yes_w, yes_h = self.yes_target.shape[1], self.yes_target.shape[0]
                    # Move to yes button
                    yes_x = max_loc[0] + yes_w // 2
                    yes_y = max_loc[1] + yes_h // 2
                    pyautogui.moveTo(yes_x, yes_y)
                    pyautogui.leftClick()
                    time.sleep(1)
        else:
            print("No yellowtails found.")
        print("Yellowtails operation complete...")
        if np.any(mightfish >= 0.9):
            for loc in zip(*np.where(mightfish >= 0.9)[::-1]):
                # Get the screen width and height
                screen_width, screen_height = pyautogui.size()
                
                # Calculate the center of the screen
                screen_x = screen_width // 2
                screen_y = screen_height // 2
                
                # Calculate the center of the image
                mightfish_x = loc[0] + mightfish_w // 2
                mightfish_y = loc[1] + mightfish_h // 2
                
                # Check if the location has already been clicked
                if (mightfish_x, mightfish_y) not in clicked_locations:
                    
                    # Click in the center of the image
                    pyautogui.moveTo(mightfish_x, mightfish_y)
                    pyautogui.leftClick()
                    time.sleep(1)
                    
                    # Add the location to the set of clicked locations
                    clicked_locations.add((mightfish_x, mightfish_y))
                    
                    # Move to center screen.
                    pyautogui.moveTo(screen_x, screen_y)
                    pyautogui.leftClick()
                    time.sleep(1)
                    yes_button = cv.matchTemplate(self.main_agent.cur_img, self.yes_target, cv.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(yes_button)
                    yes_w, yes_h = self.yes_target.shape[1], self.yes_target.shape[0]
                    
                    # Move to yes button
                    yes_x = max_loc[0] + yes_w // 2
                    yes_y = max_loc[1] + yes_h // 2
                    pyautogui.moveTo(yes_x, yes_y)
                    pyautogui.leftClick()
                    time.sleep(1)
        else:
            print("No mightfish found.")       
        print(f"{clam_count} clams opened.")
        print(f"{yellowtail_count} yellowtails deleted.")
        print(f"{mightfish_count} mightfish deleted.")
        print(f"Closing Bags...")
        pyautogui.press('b')
        bait_location = cv.matchTemplate(self.main_agent.cur_img, self.bait_target, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(bait_location)
        bait_w, bait_h = self.bait_target.shape[1], self.bait_target.shape[0]
        bait_mid_x, bait_mid_y = bait_w // 2, bait_h // 2
        self.bait_location = (max_loc[0] + bait_mid_x, max_loc[1] + bait_mid_y)
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
            print("Baiting hook...")
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
        time.sleep(0.5)
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
            if time.time() - time_start >= 26:
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