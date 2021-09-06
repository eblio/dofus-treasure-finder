# coding: utf-8

import pytesseract
import sys
import win32gui
import win32ui
import re
import data
import requests
import json
import traceback
from PIL import ImageOps
from ctypes import windll
from fuzzywuzzy import fuzz

try:
    from PIL import Image
except ImportError:
    import Image

DOFUS_TEXT = '- Dofus'
REQUEST_FORMAT = 'https://dofus-map.com/huntTool/getData.php?x={}&y={}&direction={}&world={}&language=fr'
DIRECTIONS = ['top', 'bottom', 'left', 'right']
DIRECTIONS_SIGLE = {'top': '^', 'bottom': 'v', 'left': '<', 'right': '>'}
FROM_FORMAT = 'Depuis [{},{}]'
TO_FORMAT = '{} à {} case en [{},{}]'
RATIO_TRESHOLD = 65
POSITION_TRESHOLDS = [130, 140, 150, 160, 170, 180, 190]
HINT_TRESHOLD = 130
MIN_TEXT_SIZE = 2
WORLD_TO_ID = {'Monde des Douze': 0, 'Village de la canopée': 2}

re_coords = re.compile('(-?[0-9]+,-?[0-9]+)')

###
# Filter functions
###

def black_n_white(treshold):
    '''
    Returns a function that determines whether a pixel should be white or black.
    '''
    return lambda i : 255 if i > treshold else 0


def sufficient_length(t):
    '''
    Determines whether the length of the text is sufficient to be considered valid.
    '''
    return len(t) > MIN_TEXT_SIZE

###
# dofus-map.com functions
###

def is_a_hint(text):
    '''
    Returns whether a string is a hint.
    '''
    for hint in data.hint_list:
        if fuzz.ratio(text, hint) > 60:
            return hint
            

def is_hint_in(hint, data):
    '''
    Returns whether a hint is contained into a dofus map data object.
    '''
    for d in data:
        if data.dofus_map_text[str(d['n'])] == hint:
            return True, d['d'], d['x'], d['y']

    return False, 0, 0, 0


def format_hints(hints):
    '''
    Formats hints with a more understandable name.
    '''
    for hint in hints:
        hint['n'] = data.dofus_map_text[str(hint['n'])]

    return hints


###
# OCR functions
###

def image_to_text(image):
    '''
    Find all the text in an image using OCR.
    '''
    return pytesseract.image_to_string(image, config='--psm 11')


###
# Windows GUI management functions
###

def is_dofus_window(window_handler):
    '''
    Returns whether the window is Dofus one.
    '''
    return (DOFUS_TEXT in win32gui.GetWindowText(window_handler))


def is_dofus_window_exec(window_handler, callback):
    '''
    Executes the callback function if the handled window is Dofus one.
    '''
    if is_dofus_window(window_handler):
        callback(window_handler)


def find_dofus_window_exec(callback):
    '''
    Executes a specific function on the Dofus window.
    '''
    win32gui.EnumWindows(is_dofus_window_exec, callback)


def screenshot_window(window_handler):
    '''
    Processes the window to screenshot the interesting parts of the window.
    '''
    left, top, right, bot = win32gui.GetWindowRect(window_handler)
    w = right - left
    h = bot - top

    # Create and get the proper device contexts
    window_dc = win32gui.GetWindowDC(window_handler)
    new_dc = win32ui.CreateDCFromHandle(window_dc)
    screenshot_dc = new_dc.CreateCompatibleDC()

    # Create the screenshot holding bitmap and bind it to its DC
    bit_map = win32ui.CreateBitmap()
    bit_map.CreateCompatibleBitmap(new_dc, w, h)

    screenshot_dc.SelectObject(bit_map)

    # Screenshot the window into its DC
    retval = windll.user32.PrintWindow(
        window_handler, 
        screenshot_dc.GetSafeHdc(), 
        0)

    # Create the image from the bitmap
    bm_info = bit_map.GetInfo()
    bm_str = bit_map.GetBitmapBits(True)

    image = Image.frombuffer(
        'RGB',
        (bm_info['bmWidth'], bm_info['bmHeight']),
        bm_str, 'raw', 'BGRX', 0, 1)

    # Free the resources
    win32gui.DeleteObject(bit_map.GetHandle())
    screenshot_dc.DeleteDC()
    new_dc.DeleteDC()
    win32gui.ReleaseDC(window_handler, window_dc)

    return image


###
# Use case specific functions
###

def request_hints(x, y, direction, world):
    '''
    Requests the hints through dofus-map and format them.
    '''
    url = REQUEST_FORMAT.format(x, y, direction, world)
    response = requests.get(url, auth=('user', 'pass'))

    hints = list(json.loads(response.text)['hints'])
    hints = format_hints(hints)

    return hints


def find_best_hint(hint, hints):
    '''
    Finds the best corresponding hint.
    '''
    max_ratio = 0
    best_hint_data = None

    for hint_data in hints:
        ratio = fuzz.ratio(hint, hint_data['n'])

        if ratio > RATIO_TRESHOLD and ratio > max_ratio:
            max_ratio = ratio
            best_hint_data = hint_data

    return best_hint_data


def find_position(image):
    '''
    Processes the window screenshot to extract the coordinates.
    '''
    h = image.height
    w = image.width

    # Crop the image
    position_image = image.crop((0, 0, w / 4, h / 3)).convert('L')

    # Iterate through the possible tresholds to find the text
    pos_texts = []

    for treshold in POSITION_TRESHOLDS:
        temp_image = ImageOps.invert(position_image.point(black_n_white(treshold), mode='1').convert('RGB'))

        pos_texts = image_to_text(temp_image).split('\n')
        pos_texts = list(filter(sufficient_length, pos_texts))
        pos_texts = list(filter(re_coords.match, pos_texts))

        if len(pos_texts) >= 1:
            break
    
    # Extract the information
    pos_texts = pos_texts[0].split(',')
    x, y = int(pos_texts[0]), int(pos_texts[1])

    return x, y
    

def find_hints(image, x, y, world):
    '''
    Processes the window screenshot to extract the hints.
    '''
    h = image.height
    w = image.width

    hint_image = image.crop((3 * w / 4, 0, w, h / 2.8)).convert('L').point(black_n_white(HINT_TRESHOLD), mode='1').convert('RGB')
    hint_texts = image_to_text(hint_image).split('\n')

    # Filter to remove garbage data
    hint_texts = list(filter(sufficient_length, hint_texts))

    # Find the best hint in each direction
    best_hints = {}

    for direction in DIRECTIONS:
        hints = request_hints(x, y, direction, world)
        best_hint = None

        for hint_text in hint_texts:
            temp_best_hint = find_best_hint(hint_text, hints)

            if temp_best_hint is not None:
                best_hint = temp_best_hint

        best_hints[direction] = best_hint

    return best_hints


def find_relevant_data(image, world):
    '''
    Finds the relevant data (position and hint).
    '''
    x, y = find_position(image)
    best_hints = find_hints(image, x, y, world)

    return x, y, best_hints


def process_window(window_handler):
    '''
    Process the window to extract its information and display the solution.
    '''
    try:
        image = screenshot_window(window_handler)
        x, y, hints = find_relevant_data(image, 0)

        print(FROM_FORMAT.format(x, y))

        for direction in hints:
            hint = hints[direction]
            
            if hint is not None:
                print(DIRECTIONS_SIGLE[direction] + ' ' + TO_FORMAT.format(hint['n'], hint['d'], hint['x'], hint['y']))
    except:
        print("No results found : ")
        traceback.print_exc()


###
# Main
###

def main():
    find_dofus_window_exec(process_window)


if __name__ == '__main__':
    main()
