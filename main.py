# coding: utf-8

import pytesseract
import sys
import win32gui
import win32ui
import re
import dofus_data
import requests
import json
from PIL import ImageOps
from ctypes import windll
from fuzzywuzzy import fuzz

try:
    from PIL import Image
except ImportError:
    import Image

DOFUS_TEXT = 'Dofus'
REQUEST_FORMAT = 'https://dofus-map.com/huntTool/getData.php?x={}&y={}&direction={}&world=0&language=fr'
DIRECTIONS = ['top', 'bottom', 'left', 'right']
DIRECTIONS_SIGLE = {'top': '^', 'bottom': 'v', 'left': '<', 'right': '>'}
CLUE_FORMAT = 'depuis {},{} vers {}'
SOL_FORMAT = '{} : à {} case en {},{}'

black_n_white = lambda x : 255 if x > 120 else 0
re_coords = re.compile('(-?[0-9]+,-?[0-9]+)')

def is_a_clue(text):
    '''
    Returns whether a string is a clue.
    '''
    for clue in dofus_data.clue_list:
        if fuzz.ratio(text, clue) > 60:
            return clue


def is_clue_in(clue, data):
    '''
    Returns whether a clue is contained into a dofus map data object.
    '''
    for d in data:
        if dofus_data.dofus_map_text[str(d['n'])] == clue:
            return True, d['d'], d['x'], d['y']

    return False, 0, 0, 0

def image_to_text(image):
    '''
    Find all the text in an image using OCR.
    '''
    return pytesseract.image_to_string(image, config='--psm 11')

def image_path_to_text(path):
    '''
    Find all the text in an image using OCR.
    '''
    text = ''

    with Image.open(path) as image:
        text = image_to_text(image)
        image.close()

    return text

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

def process_screenshot(image):
    '''
    Processes the screenshot to keep the interesting parts.
    '''
    h = image.height
    w = image.width

    # Crop and filter
    position_image = ImageOps.invert(image.crop((0, 0, w / 3, h / 3)).convert('L').point(black_n_white, mode='1').convert('RGB'))
    clue_image = image.crop((2 * w / 3, 0, w, h / 3)).convert('L').point(black_n_white, mode='1').convert('RGB')

    # position_image.save('./test-images/pos.png')
    # clue_image.save('./test-images/clue.png')

    return position_image, clue_image

def find_relevant_data(position_image, clue_image):
    '''
    Finds the relevant data (position and clue).
    '''

    # Find the text using OCR
    pos_texts = image_to_text(position_image).split('\n')
    clue_texts = image_to_text(clue_image).split('\n')
    print(clue_texts)
    
    # Filter to get the position
    pos_texts = list(filter(re_coords.match, pos_texts))[0].split(',')
    x, y = int(pos_texts[0]), int(pos_texts[1])

    # Filter to get the clue
    clue_texts = [c for c in map(is_a_clue, clue_texts) if c is not None]
    print(clue_texts)
    clue = clue_texts[len(clue_texts) - 1]

    return x, y, clue

def request_dofus_map(x, y, clue, direction):
    url = REQUEST_FORMAT.format(x, y, direction)
    response = requests.get(url, auth=('user', 'pass'))
    json_data = json.loads(response.text)
    data = list(json_data['hints'])

    return is_clue_in(clue, data)

def process_window(window_handler):
    '''
    Process the window to extract its information and display the solution.
    '''
    try:
        image = screenshot_window(window_handler)
        position_image, clue_image = process_screenshot(image)
        x, y, clue = find_relevant_data(position_image, clue_image)

        print(CLUE_FORMAT.format(x, y, clue))

        for direction in DIRECTIONS:
            v, d, xx, yy = request_dofus_map(x, y, clue, direction)

            if v:
                print(SOL_FORMAT.format(DIRECTIONS_SIGLE[direction], d, xx, yy))
        
    except:
        e = sys.exc_info()
        print("No results founded : " + str(e))

def main():
    find_dofus_window_exec(process_window)

if __name__ == '__main__':
    main()
