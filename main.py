
"""
Window management.
"""

import tkinter as tk
import tkinter.ttk as ttk
import api
import uuid
from dofusdb import DofusDB

APP_NAME = str(uuid.uuid4()) # Whatever ...
DETECT_BUTTON_TEXT = 'Détecter'
RESULT_FRAME_TEST = 'Direction'
ERROR_TEXT = 'Aucune solution trouvée'
RESULT_TEXT = '{} à {} cases en [{}, {}]'

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.wm_attributes('-topmost', 1)
        self.iconphoto(False, tk.PhotoImage(file=r'.\assets\icon.png'))
        self.geometry('250x170')
        self.arrow_images = {
            api.Direction.UP: tk.PhotoImage(file=r'.\assets\arrow_up.png'),
            api.Direction.DOWN: tk.PhotoImage(file=r'.\assets\arrow_down.png'),
            api.Direction.LEFT: tk.PhotoImage(file=r'.\assets\arrow_left.png'),
            api.Direction.RIGHT: tk.PhotoImage(file=r'.\assets\arrow_right.png')
        }
        self.create_widgets()
        self.dofusdb = DofusDB()


    def create_widgets(self):
        self.coords_frame = ttk.Frame(self)
        self.dir_frame = ttk.Frame(self)
        self.result_frame = ttk.Frame(self)

        self.x_value = tk.IntVar()
        self.y_value = tk.IntVar()
        self.x_entry = ttk.Entry(self.coords_frame, textvariable=self.x_value, width=5)
        self.y_entry = ttk.Entry(self.coords_frame, textvariable=self.y_value, width=5)
        self.coords_button = ttk.Button(
            self.coords_frame, text=DETECT_BUTTON_TEXT, command=self.try_find_coords)

        self.up_button = ttk.Button(
            self.dir_frame, image=self.arrow_images[api.Direction.UP], command=lambda: self.try_find_hint(api.Direction.UP))
        self.down_button = ttk.Button(
            self.dir_frame, image=self.arrow_images[api.Direction.DOWN], command=lambda: self.try_find_hint(api.Direction.DOWN))
        self.left_button = ttk.Button(
            self.dir_frame, image=self.arrow_images[api.Direction.LEFT], command=lambda: self.try_find_hint(api.Direction.LEFT))
        self.right_button = ttk.Button(
            self.dir_frame, image=self.arrow_images[api.Direction.RIGHT], command=lambda: self.try_find_hint(api.Direction.RIGHT))

        self.result_text = ttk.Label(self.result_frame, wraplength=250)

        self.coords_frame.pack(padx=2, pady=2)
        self.dir_frame.pack(padx=2, pady=2)
        self.result_frame.pack(padx=2, pady=2)

        self.x_entry.grid(row=0, column=0, columnspan=1, padx=1)
        self.y_entry.grid(row=0, column=1, columnspan=1, padx=1)
        self.coords_button.grid(row=0, column=2, columnspan=2, padx=1)

        self.up_button.grid(row=0, column=1)
        self.down_button.grid(row=2, column=1)
        self.left_button.grid(row=1, column=0)
        self.right_button.grid(row=1, column=2)

        self.result_text.pack()


    def update_result(self, text):
        self.result_text['text'] = text


    def find_hint(self, window_handler):
        x = self.x_value.get()
        y = self.y_value.get()
        hints = self.dofusdb.get_hints(x, y, self.current_direction)

        image = api.screenshot_window(window_handler)
        text = api.find_hints(image)

        valid_hints = api.match_to_hints(text, hints)

        if len(valid_hints) > 1:
            h = valid_hints[len(valid_hints) - 1]
            
            if h['x'] != x:
                d = abs(x - h['x'])
            else:
                d = abs(y - h['y'])
            
            self.update_result(RESULT_TEXT.format(h['n'], d, h['x'], h['y']))
            self.x_value.set(h['x'])
            self.y_value.set(h['y'])
        else:
            self.update_result(ERROR_TEXT)


    def try_find_hint(self, direction):
        self.current_direction = direction
        api.find_dofus_window_exec(self.find_hint)


    def find_coords(self, window_handler):
        image = api.screenshot_window(window_handler)
        x, y = api.find_position(image)

        self.x_value.set(x)
        self.y_value.set(y)


    def try_find_coords(self):
        api.find_dofus_window_exec(self.find_coords)


if __name__ == '__main__':
    app = App()
    app.title(APP_NAME)
    app.mainloop()
