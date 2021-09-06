# coding: utf-8

import tkinter as tk
import tkinter.ttk as ttk
import api
import sys
import uuid
import time

APP_NAME = str(uuid.uuid4()) # Whatever ...
START_BUTTON_TEXT = 'Démarrer'
RESULT_FRAME_TEST = 'Résultat'
NOTHING_HERE = 'Rien par là'
TIME_FORMAT = 'En {:.2f} s'

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.wm_attributes("-topmost", 1)
        self.iconphoto(False, tk.PhotoImage(file=r'.\assets\icon.png'))
        self.geometry('330x270')
        self.arrow_images = {
            'top': tk.PhotoImage(file=r'.\assets\arrow_top.png'),
            'bottom': tk.PhotoImage(file=r'.\assets\arrow_bottom.png'),
            'left': tk.PhotoImage(file=r'.\assets\arrow_left.png'),
            'right': tk.PhotoImage(file=r'.\assets\arrow_right.png')
        }
        self.create_widgets()


    def create_widgets(self):
        self.world_select = ttk.Combobox(self)
        self.world_select['values'] = tuple(api.WORLD_TO_ID.keys())
        self.world_select.current(0)
        self.start_button = ttk.Button(self, text=START_BUTTON_TEXT, command=self.start)
        self.result_frame = ttk.LabelFrame(self, text=RESULT_FRAME_TEST)
        self.info_label = ttk.Label(self, text='')
        self.from_label = ttk.Label(self.result_frame, text=api.FROM_FORMAT.format('x', 'y'))
        self.directions_labels = {
            'top': (ttk.Label(self.result_frame, image=self.arrow_images['top']), ttk.Label(self.result_frame, text=NOTHING_HERE)),
            'bottom': (ttk.Label(self.result_frame, image=self.arrow_images['bottom']), ttk.Label(self.result_frame, text=NOTHING_HERE)),
            'left': (ttk.Label(self.result_frame, image=self.arrow_images['left']), ttk.Label(self.result_frame, text=NOTHING_HERE)),
            'right': (ttk.Label(self.result_frame, image=self.arrow_images['right']), ttk.Label(self.result_frame, text=NOTHING_HERE))
        }

        self.world_select.pack(pady=5)
        self.start_button.pack()
        self.result_frame.pack(expand='yes', pady=5)
        self.info_label.pack(expand='yes')
        self.from_label.grid(row=0, column=0, columnspan=2)
        self.directions_labels['top'][0].grid(row=1, column=0)
        self.directions_labels['top'][1].grid(row=1, column=1)
        self.directions_labels['bottom'][0].grid(row=2, column=0)
        self.directions_labels['bottom'][1].grid(row=2, column=1)
        self.directions_labels['left'][0].grid(row=3, column=0)
        self.directions_labels['left'][1].grid(row=3, column=1)
        self.directions_labels['right'][0].grid(row=4, column=0)
        self.directions_labels['right'][1].grid(row=4, column=1)


    def change_from(self, text):
        self.from_label['text'] = text


    def change_result(self, direction, text):
        self.directions_labels[direction][1]['text'] = text
        

    def change_info(self, text):
        self.info_label['text'] = text


    def fetch_result(self, window_handler):      
        try:
            ta = time.perf_counter()

            image = api.screenshot_window(window_handler)
            x, y, hints = api.find_relevant_data(image, api.WORLD_TO_ID[self.world_select.get()])

            tb = time.perf_counter()

            self.change_from(api.FROM_FORMAT.format(x, y))

            for direction in hints:
                hint = hints[direction]

                if hint is not None:
                    self.change_result(direction, api.TO_FORMAT.format(hint['n'], hint['d'], hint['x'], hint['y']))
                else:
                    self.change_result(direction, NOTHING_HERE)

            self.change_info(TIME_FORMAT.format(tb - ta))
        except IndexError:
            self.change_from('Impossible de lire la position.')
        except:
            self.change_from('Aucune solution.')


    def start(self):
        api.find_dofus_window_exec(self.fetch_result)


if __name__ == '__main__':
    app = App()
    app.title(APP_NAME)
    app.mainloop()

