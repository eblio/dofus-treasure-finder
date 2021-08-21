# coding: utf-8

import pytesseract
import sys
import win32gui
import win32ui
import re
import data
import requests
import json
from PIL import ImageOps
from ctypes import windll
from fuzzywuzzy import fuzz

try:
    from PIL import Image
except ImportError:
    import Image

DOFUS_TEXT = '- Dofus'
REQUEST_FORMAT = 'https://dofus-map.com/huntTool/getData.php?x={}&y={}&direction={}&world=0&language=fr'
DIRECTIONS = ['top', 'bottom', 'left', 'right']
DIRECTIONS_SIGLE = {'top': '^', 'bottom': 'v', 'left': '<', 'right': '>'}
FROM_FORMAT = 'depuis {},{}'
TO_FORMAT = '{} = {} à {} case en {},{}'
RATIO_TRESHOLD = 60
INTENSITY_TRESHOLD = 120

black_n_white = lambda x : 255 if x > INTENSITY_TRESHOLD else 0
re_coords = re.compile('(-?[0-9]+,-?[0-9]+)')

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

def process_screenshot(image):
    '''
    Processes the screenshot to keep the interesting parts.
    '''
    h = image.height
    w = image.width

    # Crop and filter
    position_image = ImageOps.invert(image.crop((0, 0, w / 3, h / 3)).convert('L').point(black_n_white, mode='1').convert('RGB'))
    hint_image = image.crop((2 * w / 3, 0, w, h / 3)).convert('L').point(black_n_white, mode='1').convert('RGB')

    # position_image.save('./test-images/pos.png')
    # hint_image.save('./test-images/hint.png')

    return position_image, hint_image


def request_hints(x, y, direction):
    '''
    Requests the hints through dofus-map and format them.
    '''
    url = REQUEST_FORMAT.format(x, y, direction)
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


def find_relevant_data(position_image, hint_image):
    '''
    Finds the relevant data (position and hint).
    '''

    # Find the text using OCR
    pos_texts = image_to_text(position_image).split('\n')
    hint_texts = image_to_text(hint_image).split('\n')

    # Filter to get the position
    pos_texts = list(filter(re_coords.match, pos_texts))[0].split(',')
    x, y = int(pos_texts[0]), int(pos_texts[1])

    # Find the best hint in each direction
    best_hints = {}

    for direction in DIRECTIONS:
        hints = request_hints(x, y, direction)
        best_hint = None

        for hint_text in hint_texts:
            temp_best_hint = find_best_hint(hint_text, hints)

            if temp_best_hint is not None:
                best_hint = temp_best_hint

        best_hints[direction] = best_hint
        
    return x, y, best_hints


def process_window(window_handler):
    '''
    Process the window to extract its information and display the solution.
    '''
    try:
        image = screenshot_window(window_handler)
        position_image, hint_image = process_screenshot(image)
        x, y, hints = find_relevant_data(position_image, hint_image)

        print(FROM_FORMAT.format(x, y))

        for direction in hints:
            hint = hints[direction]
            
            if hint is not None:
                print(TO_FORMAT.format(
                    DIRECTIONS_SIGLE[direction], hint['n'], hint['d'], hint['x'], hint['y']))
        
    except:
        e = sys.exc_info()
        print("No results founded : " + str(e))


###
# Main
###

def main():
    find_dofus_window_exec(process_window)


if __name__ == '__main__':
    main()
