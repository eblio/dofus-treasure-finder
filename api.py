
"""
Various processing functions.
"""

import pytesseract
import win32gui
import win32ui
import re
import json
from PIL import ImageOps
from ctypes import windll
from fuzzywuzzy import fuzz
from enum import Enum

try:
    from PIL import Image
except ImportError:
    import Image

DOFUS_WINDOW_NAME = '- Dofus '
POSITION_TRESHOLDS = [130, 140, 150, 160, 170, 180, 190]
HINT_TRESHOLD = 130
MIN_TEXT_SIZE = 2

class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

re_coords = re.compile('(-?[0-9]+,-?[0-9]+)')

def black_n_white(treshold):
    """
    Returns a function that determines whether a pixel should be white or black.
    """
    return lambda i : 255 if i > treshold else 0


def sufficient_length(t):
    """
    Determines whether the length of the text is sufficient to be considered valid.
    """
    return len(t) > MIN_TEXT_SIZE


def identity(item):
    """
    Identity function.
    """
    return item


def first(iterable, predicate=identity):
    """
    Find the first element of an iterable.
    """
    for item in iterable:
        if predicate(item):
            return item

    return None


def match_to_hints(text, hints):
    """
    Match each piece of text to the best hint.
    """
    max_ratio = 0
    valid_hints = []

    for t in text:
        max_ratio = 0
        hint = None

        for h in hints:
            ratio = fuzz.ratio(t, h['n'])

            if ratio > 60 and ratio > max_ratio:
                max_ratio = ratio
                hint = h

        if hint is not None:
            valid_hints.append(hint)

    return valid_hints


def image_to_text(image):
    """
    Find all the text in an image using OCR.
    """
    return pytesseract.image_to_string(image, config='--psm 11')


def is_dofus_window(window_handler):
    """
    Returns whether the window is Dofus one.
    """
    return (DOFUS_WINDOW_NAME in win32gui.GetWindowText(window_handler))


def is_dofus_window_exec(window_handler, callback):
    """
    Executes the callback function if the handled window is Dofus one.
    """
    if is_dofus_window(window_handler):
        callback(window_handler)


def find_dofus_window_exec(callback):
    """
    Executes a specific function on the Dofus window.
    """
    win32gui.EnumWindows(is_dofus_window_exec, callback)


def screenshot_window(window_handler):
    """
    Processes the window to screenshot the interesting parts of the window.
    """
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


def find_position(image):
    """
    Processes the window screenshot to extract the coordinates.
    """
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
    

def find_hints(image):
    """
    Processes the window screenshot to extract the hints.
    """
    h = image.height
    w = image.width

    hint_image = image.crop((3 * w / 4, 0, w, h / 2.8)).convert('L').point(black_n_white(HINT_TRESHOLD), mode='1').convert('RGB')
    hint_texts = image_to_text(hint_image).split('\n')

    # Filter to remove garbage data
    hint_texts = list(filter(sufficient_length, hint_texts))

    return hint_texts


def find_relevant_data(image):
    """
    Finds the relevant data (position and hint).
    """
    x, y = find_position(image)
    hints = find_hints(image)

    return x, y, hints

