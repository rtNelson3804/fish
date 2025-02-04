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
import threading
import enum
import random

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

# Define an enumeration for the different states
class FishingState(enum.Enum):
    BAIT = 1
    IDLE = 2
    CASTING = 3
    MOVE_TO_LURE = 4
    WATCH_LURE = 5
    PULL_LINE = 6
    TRASH = 7

class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PPFB v1.4")

        self.text_area = scrolledtext.ScrolledText(self.root, width=75, height=15)
        self.text_area.pack()
        self.text_area.tag_config('center', justify='center')
        self.text_area.tag_config('bold_underline', font=('Shentox', '12', 'bold underline'))
        self.text_area.insert(tk.INSERT, """
*************************************************************************
""")
        self.text_area.insert(tk.INSERT, "Primary's Pixel Fishing Bot v1.4\n", ('bold_underline', 'center'))
        self.text_area.insert(tk.INSERT, """
Added a Max Fishing Time control, and a second check for another template.

Make sure you have enough bait in your bags and your fishing pole equipped.

1. Start Screen Capture

2. Start Fishing (5 second delay)

3. Maximize WoW window.                 
*************************************************************************
""")

        self.timer_label = tk.Label(self.root, text="Time Remaining: 00:00:00")
        self.timer_label.pack(side=tk.TOP, anchor=tk.W)

        self.timer_running = False
        self.start_time = None

        self.fps_label = tk.Label(self.root, text="FPS: 0")
        self.fps_label.pack(side=tk.TOP, anchor=tk.W)

        checkbox_frame = tk.Frame(self.root)
        checkbox_frame.pack(side=tk.RIGHT)

        self.human_mouse_checkbox_var = tk.IntVar(value=1)
        self.human_mouse_checkbox = tk.Checkbutton(checkbox_frame, text="Human Mouse", variable=self.human_mouse_checkbox_var)
        self.human_mouse_checkbox.pack(side=tk.TOP)

        self.trash_fish_checkbox_var = tk.IntVar(value=1)
        self.trash_fish_checkbox = tk.Checkbutton(checkbox_frame, text="Trash Fish", variable=self.trash_fish_checkbox_var)
        self.trash_fish_checkbox.pack(side=tk.TOP)

        self.bait_checkbox_var = tk.IntVar(value=1)
        self.bait_checkbox = tk.Checkbutton(checkbox_frame, text="Bait", variable=self.bait_checkbox_var)
        self.bait_checkbox.pack(side=tk.TOP)

        self.pick_open_boxes_checkbox_var = tk.IntVar(value=0)
        self.pick_open_boxes_checkbox = tk.Checkbutton(checkbox_frame, text="Pick/Open Boxes", variable=self.pick_open_boxes_checkbox_var)
        self.pick_open_boxes_checkbox.pack(side=tk.TOP)

        input_frame = tk.Frame(self.root)
        input_frame.pack(side=tk.LEFT, fill=tk.Y)

        pick_lock_key_frame = tk.Frame(input_frame)
        pick_lock_key_frame.pack(side=tk.BOTTOM, anchor=tk.W)

        tk.Label(pick_lock_key_frame, text="Pick Lock Key:").pack(side=tk.LEFT, anchor=tk.W)
        self.pick_lock_key_entry = tk.Entry(pick_lock_key_frame, width=2)
        self.pick_lock_key_entry.insert(0, "]")  # default value
        self.pick_lock_key_entry.pack(side=tk.LEFT)

        fishing_key_frame = tk.Frame(input_frame)
        fishing_key_frame.pack(side=tk.BOTTOM, anchor=tk.W)

        tk.Label(fishing_key_frame, text="Fishing Key:").pack(side=tk.LEFT)
        self.fishing_key_entry = tk.Entry(fishing_key_frame, width=2)
        self.fishing_key_entry.insert(0, "[")  # default value
        self.fishing_key_entry.pack(side=tk.LEFT)

        trash_delay_frame = tk.Frame(input_frame)
        trash_delay_frame.pack(side=tk.BOTTOM, anchor=tk.W)

        tk.Label(trash_delay_frame, text="Trash Fish (Minutes):").pack(side=tk.LEFT)
        self.trash_delay_frame_entry = tk.Entry(trash_delay_frame, width=3)
        self.trash_delay_frame_entry.insert(0, "30")  # default value
        self.trash_delay_frame_entry.pack(side=tk.LEFT)

        fishing_time_frame = tk.Frame(input_frame)
        fishing_time_frame.pack(side=tk.BOTTOM, anchor=tk.W)

        tk.Label(fishing_time_frame, text="Fishing Time (Hours):").pack(side=tk.LEFT)
        tk.Label(fishing_time_frame, text=" 0 = Unlimited").pack(side=tk.RIGHT)
        self.fishing_time_frame_entry = tk.Entry(fishing_time_frame, width=3)
        self.fishing_time_frame_entry.insert(0, "6")  # default value
        self.fishing_time_frame_entry.pack(side=tk.LEFT)

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

    def send_camp_command(self):
        pyautogui.press("enter")  # Press Enter
        time.sleep(0.2)  # Short delay to ensure input field is ready
        pyautogui.write("/camp", interval=0.05)  # Type the command
        pyautogui.press("enter")  # Press Enter again to send the command
        time.sleep(23)
        pyautogui.hotkey('alt', 'f4')  # Simulates pressing Alt + F4
        print()
        print("Exited WoW.")

    def update_timer(self):
        if self.end_time is None and self.fishing_time_frame_entry != 0:  # Set end_time only once
            ending_time = self.fishing_time_frame_entry.get()
            self.end_time = time.time() + (float(ending_time) * 3600)
        if self.timer_running:
            self.remaining_time = int(self.end_time - time.time())  # Calculate remaining time

            if self.remaining_time <= 0:
                self.timer_label.config(text="Remaining Time: 00:00:00")
                self.stop_all_operations()  # Stop operations when the timer reaches zero
                self.timer_running = False  # Ensure it doesn't keep running
            hours, remainder = divmod(self.remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.timer_label.config(text=f"Remaining Time: {hours:02}:{minutes:02}:{seconds:02}")

            # Schedule the method to run again after 1 second
            self.root.after(1000, self.update_timer)


    def start_fishing(self):
        self.end_time = None
        print("\nStarting fishing... 15 seconds...")
        self.root.after(5000, self.five_seconds_left)
        
    def five_seconds_left(self):
        print("\n10 seconds...")
        self.root.after(5000, self.two_seconds_left)

    def two_seconds_left(self):
        print("\n5 seconds...")
        self.root.after(3000, self.one_second_left)

    def one_second_left(self):
        print("\nReady, Steady, GO!")
        self.initialize_fishing_agent()
        
    def initialize_fishing_agent(self):
        self.fishing_agent = FishingAgent(self.main_agent, self.bait_checkbox_var, self.root, self.fishing_key_entry, 
                                          self.trash_fish_checkbox_var, self.pick_lock_key_entry, self.pick_open_boxes_checkbox_var,
                                          self.trash_delay_frame_entry, self.human_mouse_checkbox_var, self.fishing_time_frame_entry
                                          )
        self.fishing_agent_thread = Thread(target=self.fishing_agent.run)
        self.fishing_agent_thread.start()

        # Start the timer
        self.timer_running = True
        self.start_time = time.time()
        self.update_timer()

    def stop_all_operations(self):
        def stop_threads():
            if self.screen_capture_thread:
                self.main_agent.stop_event = True
                self.screen_capture_thread.join()
                self.screen_capture_thread = None
                print()
                print("Screen capture stopped...")

            if self.fishing_agent_thread:
                self.fishing_agent.stop_event.set()
                self.fishing_agent_thread.join()
                self.fishing_agent_thread = None
                print()
                print("Fishing stopped...")

                self.main_agent.stop_event = False
                if self.fishing_agent:
                    self.fishing_agent.stop_event.clear()
                time.sleep(1)
            if float(self.fishing_time_frame_entry.get()) > 0 and self.remaining_time <=0:
                print()
                print("Camping...")
                self.send_camp_command() # Camp
                # self.fishing_agent.reset()  # Call the reset method

            # Stop the timer
            self.timer_running = False

        stop_thread = Thread(target=stop_threads)
        stop_thread.start()

class FishingAgent:
    def __init__(self, main_agent, bait_checkbox_var, root, fishing_key_entry, trash_fish_checkbox_var, pick_lock_key_entry, pick_open_boxes_checkbox_var, trash_delay_frame_entry, human_mouse_checkbox_var, fishing_time_frame_entry):
        self.main_agent = main_agent
        self.state = FishingState.BAIT
        self.bait_checkbox_var = bait_checkbox_var
        self.root = root
        self.fishing_key_entry = fishing_key_entry
        self.pick_lock_key_entry = pick_lock_key_entry
        self.trash_delay_frame_entry = trash_delay_frame_entry
        self.fishing_time_frame_entry = fishing_time_frame_entry
        self.trash_fish_checkbox_var = trash_fish_checkbox_var
        self.pick_open_boxes_checkbox_var = pick_open_boxes_checkbox_var
        self.human_mouse_checkbox_var = human_mouse_checkbox_var
        self.human_mouse = self.human_mouse_checkbox_var.get()
        self.stop_event = threading.Event()
        self.casts = 0
        self.fails = 0
        
        # interpolate here_path to get the path to the fishing target image
        here_path = os.path.dirname(os.path.realpath(__file__))
        self.fishing_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "fishing_target.png"
            )
        )
        self.small_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "small_target.png"
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
        self.zesty_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "zesty_target.png"
            )
        )
        self.firefin_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "firefin_target.png"
            )
        )
        self.grouper_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "grouper_target.png"
            )
        )
        self.crate_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "crate_target.png"
            )
        )
        self.chest_target = cv.imread(
            os.path.join(
                here_path,
                "assets", "chest_target.png"
            )
        )
        self.fishing_thread = None

    def mouse_operation(self, start=None, end=None, click=None, steps=7, max_jitter=3, base_duration=0.4):

        if self.human_mouse == 0:
            if end is None:
                # If end is None, get the current mouse position as the destination
                end = pyautogui.position()
            pyautogui.moveTo(end[0], end[1], duration=0.1, tween=pyautogui.easeInOutQuad)  # Move directly to the target
            if click:
                pyautogui.click(button=click)
            return
        if start is None and end is None:
            start = pyautogui.position()
            end = pyautogui.position()
        elif start is None:
            start = pyautogui.position()
        elif end is None:
            end = start

        # If start and end are the same, no need to move, just click if specified
        if start == end:
            if click:
                delay = random.uniform(0.1, 0.05)  # Random delay
                time.sleep(delay)
                if click == "left":
                    pyautogui.click()
                elif click == "right":
                    pyautogui.click(button="right")
            return

        # Calculate a random control point for a Bézier curve
        control_x = (start[0] + end[0]) / 2 + random.randint(-100, 100)
        control_y = (start[1] + end[1]) / 2 + random.randint(-100, 100)

        # Generate the Bézier curve
        t = np.linspace(0, 1, steps)
        x_vals = (1 - t)**2 * start[0] + 2 * (1 - t) * t * control_x + t**2 * end[0]
        y_vals = (1 - t)**2 * start[1] + 2 * (1 - t) * t * control_y + t**2 * end[1]

        # Move along the path
        for i in range(steps):
            # Add jitter to simulate hand movement
            jitter_x = random.uniform(-max_jitter, max_jitter)
            jitter_y = random.uniform(-max_jitter, max_jitter)

            # Apply easing function to control movement smoothness
            duration = base_duration / steps + random.uniform(-0.05, 0.05)  # Vary speed slightly
            pyautogui.moveTo(x_vals[i] + jitter_x, y_vals[i] + jitter_y, duration=duration, tween=pyautogui.easeInOutQuad)

        # Simulate a slight adjustment at the target
        adjustment_x = random.randint(-3, 3)
        adjustment_y = random.randint(-3, 3)
        pyautogui.moveRel(adjustment_x, adjustment_y, duration=random.uniform(0.01, 0.03))

        # Final move to the exact target position
        pyautogui.moveTo(end[0], end[1], duration=random.uniform(0.1, 0.3))

        # Perform a click if the `click` parameter is specified
        if click:
            delay = random.uniform(0.09, 0.16)  # Random delay between 250ms and 1000ms
            time.sleep(delay)  # Simulate natural delay before clicking
            if click == "left":
                pyautogui.click()
            elif click == "right":
                pyautogui.click(button="right")
    
    def trashing_fish(self):
        # Initialize a set to store the clicked locations
        clicked_locations = set()
        clam_count = 0
        # Find the clam_target image on the screen
        print()
        print("Opening Bags to clear inventory...")
        time.sleep(1)
        pyautogui.press('b')
        time.sleep(1)
        print()
        time.sleep(1)

        click_templates = {
            'clam': self.clam_target,
            'crate': self.crate_target,
        }
        click_counts = {name: 0 for name in click_templates.keys()}        
        # Iterate over the locations where the image was found
        for name, template in click_templates.items():
            click_result = cv.matchTemplate(self.main_agent.cur_img, template, cv.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv.minMaxLoc(click_result)
            if np.any(click_result >= 0.9):
                for loc in zip(*np.where(click_result >= 0.9)[::-1]):
                    # Calculate the center of the image
                    clam_x = loc[0] + self.clam_target.shape[1] // 2
                    clam_y = loc[1] + self.clam_target.shape[0] // 2
                # Check if the location has already been clicked
                    if (clam_x, clam_y) not in clicked_locations:
                        click_counts[name] += 1
                        # Click in the center of the image
                        self.mouse_operation(end=(clam_x, clam_y), click="right")
                        # Add the location to the set of clicked locations
                        time.sleep(1)
                        clicked_locations.add((clam_x, clam_y))

        # Define a dictionary with templates and their names
        templates = {
            'zesty': self.zesty_target,
            'yellowtail': self.yellowtail_target,
            'mightfish': self.mightfish_target,
            'cod': self.cod_target,
            'firefin': self.firefin_target,
            'grouper': self.grouper_target,
            'chest': self.chest_target
        }

        def is_nearby(loc, clicked_locations, radius=10):
            for clicked_x, clicked_y in clicked_locations:
                if abs(clicked_x - loc[0]) <= radius and abs(clicked_y - loc[1]) <= radius:
                    return True
            return False

        # Initialize counters for each type of fish
        counts = {name: 0 for name in templates.keys()}

        # Iterate over the templates
        for name, template in templates.items():
            pick_open_boxes = self.pick_open_boxes_checkbox_var.get()
            # Find the template on the screen
            result = cv.matchTemplate(self.main_agent.cur_img, template, cv.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
            lock_key = self.pick_lock_key_entry.get()
            # If the template is found, perform the actions
            if np.any(result >= 0.9):
                if name == 'chest' and pick_open_boxes == 1:
                    for loc in zip(*np.where(result >= 0.9)[::-1]):
                        # Calculate the center of the image
                        x = loc[0] + template.shape[1] // 2
                        y = loc[1] + template.shape[0] // 2
                        
                        # Check if the location has already been clicked
                        if (x, y) not in clicked_locations:
                            # counts[name] += 1
                            
                            # Click in the center of the image
                            pyautogui.press(lock_key)
                            self.mouse_operation(end=(x, y), click="left")
                            time.sleep(5)
                            self.mouse_operation(end=(x, y), click="right")
                            
                            # Add the location to the set of clicked locations
                            clicked_locations.add((x, y))

                for loc in zip(*np.where(result >= 0.9)[::-1]):
                    # Calculate the center of the image
                    x = loc[0] + template.shape[1] // 2
                    y = loc[1] + template.shape[0] // 2
                    
                    # Check if the location has already been clicked
                    if not is_nearby((x, y), clicked_locations) and name != 'chest':
                        counts[name] += 1
                        
                        # Click in the center of the image
                        self.mouse_operation(end=(x, y), click="left")
                        time.sleep(0.3)
                        
                        # Add the location to the set of clicked locations
                        clicked_locations.add((x, y))
                        
                        # Move to center screen and click
                        screen_width, screen_height = pyautogui.size()
                        screen_x = screen_width // 2
                        screen_y = screen_height // 2
                        self.mouse_operation(end=(screen_x, screen_y), click="left")
                        time.sleep(0.3)
                        
                        # Click the yes button
                        yes_button = cv.matchTemplate(self.main_agent.cur_img, self.yes_target, cv.TM_CCOEFF_NORMED)
                        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(yes_button)
                        yes_w, yes_h = self.yes_target.shape[1], self.yes_target.shape[0]
                        yes_x = max_loc[0] + yes_w // 2
                        yes_y = max_loc[1] + yes_h // 2
                        self.mouse_operation(end=(yes_x, yes_y), click="left")
                        time.sleep(0.3)

        # Now, reset the clicked_locations after all templates have been processed
        clicked_locations = set()

        time.sleep(0.5)

        print()
        print(f"Closing Bags...")
        pyautogui.press('b')
        self.state = FishingState.BAIT
        pass
    
    def bait_hook(self):
        while not self.stop_event.is_set():
            # Check if the state is still BAIT, otherwise exit the loop
            if self.state != FishingState.BAIT:
                break
            print()
            print("State: BAIT")
            # Find bait location
            bait_location = cv.matchTemplate(self.main_agent.cur_img, self.bait_target, cv.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv.minMaxLoc(bait_location)
            bait_w, bait_h = self.bait_target.shape[1], self.bait_target.shape[0]
            bait_mid_x, bait_mid_y = bait_w // 2, bait_h // 2
            self.bait_location = (max_loc[0] + bait_mid_x, max_loc[1] + bait_mid_y)

            # Move to bait location
            if self.bait_location:
                self.mouse_operation(end=(self.bait_location[0], self.bait_location[1]), click="left")
                time.sleep(1)

                # Find pole location
                pole_location = cv.matchTemplate(self.main_agent.cur_img, self.pole_target, cv.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv.minMaxLoc(pole_location)
                pole_w, pole_h = self.pole_target.shape[1], self.pole_target.shape[0]
                pole_mid_x, pole_mid_y = pole_w // 2, pole_h // 2
                self.pole_location = (max_loc[0] + pole_mid_x, max_loc[1] + pole_mid_y)

                # Move to pole location
                if self.pole_location:
                    self.mouse_operation(end=(self.pole_location[0], self.pole_location[1]), click="left")
                    time.sleep(1)

                    # Click yes button
                    yes_button = cv.matchTemplate(self.main_agent.cur_img, self.yes_target, cv.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(yes_button)
                    if np.any(yes_button >= 0.9):
                        yes_w, yes_h = self.yes_target.shape[1], self.yes_target.shape[0]
                        yes_x = max_loc[0] + yes_w // 2
                        yes_y = max_loc[1] + yes_h // 2
                        self.mouse_operation(end=(yes_x, yes_y), click="left")
                        time.sleep(1)
                    self.state = FishingState.IDLE
                    time.sleep(5)  # schedule cast_lure to run after 6 seconds
                else:
                    print("Warning: could not find fishing pole...")
            else:
                print("Warning: Attempted to move to bait_location, but bait_location is None")

            # If stop_event is set, break the loop
            if self.stop_event.is_set():
                break



    def cast_lure(self):
        # print("Casting!...")
        # end_time = time.time() + (float(self.fishing_time_frame_entry * 3600)) # Converting hours to seconds.
        # if time.time() > end_time and end_time != 0:
        #     return self.stop_all_operations()
        self.casts += 1
        self.fishing = True
        self.cast_time = time.time()
        fishing_key = self.fishing_key_entry.get()
        pyautogui.press(fishing_key)
        self.state = FishingState.CASTING
        time.sleep(1.5)
        pass

    def find_lure(self):
        self.lure_location = None  # Initialize to None
        self.small_location = None  # Initialize to None
        lure_location = cv.matchTemplate(self.main_agent.cur_img, self.fishing_target, cv.TM_CCOEFF_NORMED)
        small_location = cv.matchTemplate(self.main_agent.cur_img, self.small_target, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, small_loc = cv.minMaxLoc(small_location)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(lure_location)
        if np.any(lure_location >= 0.55):
            # Save the lure's top-left location
            self.lure_location = max_loc
            self.state = FishingState.MOVE_TO_LURE
            pass
        elif np.any(small_location >= 0.55):
            # Save the lure's top-left location
            self.small_location = small_loc
            self.state = FishingState.MOVE_TO_LURE
            pass
        else:
            delay = random.uniform(2, 4)
            time.sleep(delay)
            self.state = FishingState.BAIT
            pass

    def move_to_lure(self):
        while not self.stop_event.is_set():    
            if self.lure_location:
                # Move to the bottom-middle of the template
                lure_x = self.lure_location[0] + self.fishing_target.shape[1] // 2
                lure_y = (self.lure_location[1] + 10) + self.fishing_target.shape[0]
                self.mouse_operation(start=None, end=(lure_x, lure_y))

                self.state = FishingState.WATCH_LURE
                break
            elif self.small_location:
                # Move to the bottom-middle of the template
                lure_x = self.small_location[0] + self.small_target.shape[1] // 2
                lure_y = (self.small_location[1] + 10) + self.small_target.shape[0]
                self.mouse_operation(start=None, end=(lure_x, lure_y))

                self.state = FishingState.WATCH_LURE
                break
            time.sleep(0.01)  # Add a 10ms delay
        else:
            pass

    def watch_lure(self):
        # Initialize variables
        time.sleep(0.5)  # Wait briefly before monitoring
        if self.lure_location:
            template_width, template_height = self.fishing_target.shape[1], self.fishing_target.shape[0]
        elif self.small_location:
            template_width, template_height = self.small_target.shape[1], self.small_target.shape[0]
            self.lure_location = self.small_location
        matched_region_previous = None
        bite_detected = False
        sensitivity_threshold = 20  # Percentage of changed pixels to detect motion
        gaussian_blur_size = (3, 3)  # Small blur to reduce noise
        time_start = time.time()

        while not self.stop_event.is_set():
            # Extract the matched region (template area) from the current image
            matched_region = self.main_agent.cur_img[
                self.lure_location[1]:self.lure_location[1] + template_height,
                self.lure_location[0]:self.lure_location[0] + template_width,
            ]

            # Skip processing if the matched region is invalid or empty
            if matched_region.size == 0:
                print("Warning: Extracted matched region is empty. Skipping iteration.")
                time.sleep(0.005)
                continue

            # Apply Gaussian blur to reduce noise
            matched_region = cv.GaussianBlur(matched_region, gaussian_blur_size, 0)

            # Convert to HSV for color-based comparison
            matched_region_hsv = cv.cvtColor(matched_region, cv.COLOR_BGR2HSV)

            # If this is the first iteration, save the HSV region for comparison
            if matched_region_previous is None:
                matched_region_previous = matched_region_hsv
                continue

            # Calculate the absolute difference between current and previous HSV regions
            difference = cv.absdiff(matched_region_hsv, matched_region_previous)

            # Split the HSV channels and focus on V (brightness) for motion detection
            _, _, diff_v = cv.split(difference)

            # Threshold the difference (very low to detect minimal changes)
            _, threshold = cv.threshold(diff_v, 10, 255, cv.THRESH_BINARY)

            # Calculate the percentage of changed pixels
            change_percentage = (cv.countNonZero(threshold) / threshold.size) * 100

            # Detect motion if change percentage exceeds the sensitivity threshold
            if change_percentage > sensitivity_threshold:
                print(f"State: PULL_LINE - Motion detected: {change_percentage:.2f}% of the template area has changed.")
                delay = random.uniform(0.25, 0.9)
                time.sleep(delay)
                bite_detected = True
                break

            # Save the current HSV region for the next comparison
            matched_region_previous = matched_region_hsv

            # Timeout after 26 seconds
            if time.time() - time_start >= 26:
                print("State: PULL_LINE - Failed to see a bite...")
                self.fails += 1
                bite_detected = True
                break

            time.sleep(0.005)  # Increased monitoring frequency to 5ms for sensitivity

        # Update the state to pull the line
        if bite_detected:
            self.state = FishingState.PULL_LINE



    def pull_line(self):
        self.mouse_operation(click="right")
        time.sleep(1.5)
        # screen_width, screen_height = pyautogui.size()
        # screen_x = screen_width // 2
        # screen_y = screen_height // 2
        # self.mouse_operation(end=(screen_x, screen_y))
        self.state = FishingState.TRASH
        pass

    def run(self):
        while not self.stop_event.is_set():
            current_time = time.time()
            fish_bait = self.bait_checkbox_var.get()
            trash_fish = self.trash_fish_checkbox_var.get()
            trash_delay = int(self.trash_delay_frame_entry.get())
            if self.state == FishingState.BAIT and fish_bait == 1:
                current_time = time.time()
                if not hasattr(self, 'last_bait_hook_time') or current_time - self.last_bait_hook_time >= 610:
                    self.last_bait_hook_time = current_time
                    self.bait_hook()
                else:
                    self.state = FishingState.IDLE
            elif self.state == FishingState.BAIT and fish_bait == 0:
                self.state = FishingState.IDLE    
            elif self.state == FishingState.IDLE:
                self.cast_lure()
            elif self.state == FishingState.CASTING:
                print()
                print(f"State: CASTING #{self.casts}")
                self.find_lure()                
            elif self.state == FishingState.MOVE_TO_LURE:
                self.move_to_lure()
            elif self.state == FishingState.WATCH_LURE:
                print("State: WATCH_LURE")
                self.watch_lure()                
            elif self.state == FishingState.PULL_LINE:
                self.pull_line()
            elif self.state == FishingState.TRASH and trash_fish == 1:
                if not hasattr(self, 'last_trash_fish_time') or current_time - self.last_trash_fish_time >= (trash_delay * 60):
                    print("State: TRASH")
                    self.last_trash_fish_time = current_time
                    self.trashing_fish()
                    print()
                    print("-----------------------------------")
                    print(f"Total Casts: {self.casts}")
                    print(f"Total Fails: {self.fails}")
                    print(f"Percent Fails: {round((self.fails / self.casts) * 100, 2)}%")
                    print("-----------------------------------")
                    print()
                else:
                    print()
                    print("-----------------------------------")
                    print(f"Total Casts: {self.casts}")
                    print(f"Total Fails: {self.fails}")
                    print(f"Percent Fails: {round((self.fails / self.casts) * 100, 2)}%")
                    print("-----------------------------------")
                    print()
                    self.state = FishingState.BAIT
            elif self.state == FishingState.TRASH and trash_fish == 0:
                self.state = FishingState.BAIT
        time.sleep(0.1)  # Add a delay to avoid overwhelming the system

if __name__ == "__main__":
    gui = GUI()
    gui.run()