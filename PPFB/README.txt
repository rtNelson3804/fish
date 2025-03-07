            ***** This is required reading if you wish to use this bot and don't know what you're doing. *****

v1.4
    - Added Max Fishing Time Input to /camp and quit WoW after elapsed time.
    - Added a second template image check if it doesn't find the lure.

v1.41 
    - Fixed bug attempting to open clams/crates in the same location twice.
    - Added Total Casts: and Total Fails: to the gui and removed the spam.  Fails have been low enough, did not believe it was required to keep the % fails.
    - Fixed bug where it wasn't opening crates at all.
    - Changed Total Fails from counting not seeing the bite, to not finding the lure and recasting.

v1.5
    - Moved checkboxes to an Options Menu
    - Added Trash Menu to select which Fish and Items you would like to Trash or Keep

CONTENTS:

1) SETUP

2) LURE TARGET

3) FISHING

4) BAIT / DELETING FISH

--------------------------------------------------------------------------------------------------------------------------------------------------
SETUP:

1.1) Open PPFB_(version).py in 'VS Studio Code' - https://code.visualstudio.com/download

1.2) If prompted to install Python, click 'Yes' and follow the instructions.

1.3) Install the following packages using the terminal in VS Studio Code:

    A) File > Open Folder
    B) Select the folder containing 'PPFB.py' > Open
    C) Right click 'PPFB_(version).py' in the Explorer on the right side of the screen > Open in Integrated Terminal.  https://snipboard.io/animlM.jpg
    D) In the terminal use command: 'pip install <package_name> for each package.' i.e. pip install tkinter https://snipboard.io/mhurtf.jpg

Packages:
    
tkinter
Pillow
pyautogui
opencv-python
numpy

1.4) With PPFB open in 'VS Studio Code', click on the 'Run Python File' play button at the stop right. https://snipboard.io/pzQ2hI.jpg

1.5) If an error occurs, read the terminal at the bottom to diagnose the problem.  Good luck!

--------------------------------------------------------------------------------------------------------------------------------------------------

--------------------------------------------------------------------------------------------------------------------------------------------------

LURE TARGET:

2.1) The code reads the files from the assets folder. '../PPFB/assets'

2.2) If while fishing it is having a problem finding your lure, you likely need a new screenshot due to changes in lighting/reflections.
    This can be a semi-common occurance during extended fishing due lighting changes in game.

2.3) Press WindowsKey + Shift + S with a fishing lure out in the water and click and drag over your lure.
    Usually about the midpoint of the top feather, stretching to just before the bottom right of the lure.
    Your results may vary, play around with it to find your sweet spot.

2.4) In MSPaint make the panel as small as possible. (We don't want any white in our image)

2.5) Ctrl + V to fill in the panel with your image.

2.6) File > Save As > PNG Picture

2.7) Path to your '../PPFB/assets' folder and name the file 'fishing_target.png'.  (Without the 's dummy.)  Save and replace.

2.8) Yes you want to replace it.

2.9) CLOSE PPFB Program and run it again (1.4) to load in your new image in the program.

2.10) In v1.4 you have the option to add a second image for the program to look for before it gives up and recasts.
    Your initial screenshot you should try and capture the lure about half way out of a "max" cast. This is your 'fishing_target.png'.
    The second screenshot attempt to get a max range cast where the lure is noticably smaller.  This is your 'small_target.png'.
    Alternatively you could take one during "day" and one during "night" to have it find the lure more consistently during lighting changes.

--------------------------------------------------------------------------------------------------------------------------------------------------

FISHING:

3.1) Go to your fishing location, go in to first person mode. Run PPFB (Line 1.4)  First person mode isn't required, but I've found it helps.

3.2) Select Options from checkboxes (Bait, Trash Fish etc.). Set the hotkeys for Fishing and Pick Lock. (Defaults '[' and ']' respectively)
    Set the desired times for Bag Cleaning and Max Fishing. (Defaults '30 minutes' and '6 hours')

3.3) Press Button 'Start Screen Capture', when FPS tracker is updating continue on.

3.4) Press Button 'Start Fishing' A 15 delay will happen before the fishing thread starts, maximize WoW now.

3.5) Press the stop button and the program will update you with 'Screen Capture Stopped' and 'Fishing Stopped...'

3.6) This is a pixel bot written by a first time coder.  It will not always find your lure, and it will not always click for a bite.
    The success rate is high, but not perfect.  This has been much improved.

3.7) For hardcore there is currently no updates on health, enemies or anything.  If you start to get attacked, you will die.
    In softcore if you die, it will not res, and will continue attempting to cast until Max Time, or you come back.
    Don't die, because sitting there hitting hotkeys for hours when you're dead is likely a flag that could get you banned.

3.8) Hotkey to open bags is set to B, if you changed it and use B for something else feel free to CTRL + F in the code and
    enter 'pyautogui.press('b')' into the field and change the two instances to whatever hotkey you use.  Weirdo.

--------------------------------------------------------------------------------------------------------------------------------------------------

BAIT / DELETING FISH:

            ***** WARNING: USE THE CURRENT IMAGES AS A GUIDE TO UPDATE YOUR OWN, GRAPHICS SETTINGS MAY VARY *****

4.1) Using our assets folder (2.1) '../PPFB/assets' we need to set up our Bait, Fish Deleting, and Clam/Crate/Lockbox images.  Remember to put
    the bait AND fishing pole on your hotbar so the program can find it.  It won't open up your character screen to bait the pole.

4.2) Whatever bait you are using take an image of the TOP HALF of the bait (we try to exclude the numbers as they change) and using
    the same method we used before (2.3), change 'bait_target.png' to that new image.

4.3) We must do the same with our fishing pole.  Take an image of the entire fishing pole on your hotbar and save that image as 'pole_target.png'.

4.4) Currently (v1.4) the trashing is set up for Felaras/Tanaris but you can set up for trashing fish anywhere you just need to add images
    using the current file names.  There is a decent chance one or more of these images will not work due to colors or graphics differences.
    I recommend taking the time to update each image if you have the fish, or letting the bot run for an hour or two with trash off to collect
    the fish to take images of.
    
    The current file names are:
    
    'chest_target.png' - Take an image of your chests if you're a rogue and want to unlock and open them.  If Unlock is off, nothing happens.
    'clam_target.png' - This must stay as clams as they are right clicked, not trashed.
    'crate_target.png' - This must stay as crates as they are right clicked, not trashed.

    The remaining fish can all be substituted for any fish images, or you can add more images and checks in the code:
    
    'cod_target.png'
    'firefin_target.png'
    'grouper_target.png'
    'mightfish_target.png'
    'yellowtail_target.png'
    'zesty_target.png'

4.5) You may need to update 'yes_target.png' if your colors or graphics make it unable to find it.  This is so the mouse can find where to click
    when it asks you if you're sure you want to delete the item.

