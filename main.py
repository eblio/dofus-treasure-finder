import tkinter as tk
import tkinter.ttk as ttk
import api
import sys
from PIL import ImageTk

APP_NAME = 'Dofus treasure finder'
START_BUTTON_TEXT = 'Démarrer'
RESULT_FRAME_TEST = 'Résultat'
NOTHING_HERE = 'Rien par là'

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.wm_attributes("-topmost", 1)
        self.arrow_images = {
            'top': ImageTk.PhotoImage(file=r'.\assets\arrow_top.png'),
            'bottom': ImageTk.PhotoImage(file=r'.\assets\arrow_bottom.png'),
            'left': ImageTk.PhotoImage(file=r'.\assets\arrow_left.png'),
            'right': ImageTk.PhotoImage(file=r'.\assets\arrow_right.png')
        }
        self.create_widgets()


    def create_widgets(self):
        self.start_button = ttk.Button(self, text=START_BUTTON_TEXT, command=self.start)
        self.result_frame = ttk.LabelFrame(self, text=RESULT_FRAME_TEST)
        self.from_label = ttk.Label(self.result_frame, text=api.FROM_FORMAT.format('x', 'y'))
        self.directions_labels = {
            'top': (ttk.Label(self.result_frame, image=self.arrow_images['top']), ttk.Label(self.result_frame, text=NOTHING_HERE)),
            'bottom': (ttk.Label(self.result_frame, image=self.arrow_images['bottom']), ttk.Label(self.result_frame, text=NOTHING_HERE)),
            'left': (ttk.Label(self.result_frame, image=self.arrow_images['left']), ttk.Label(self.result_frame, text=NOTHING_HERE)),
            'right': (ttk.Label(self.result_frame, image=self.arrow_images['right']), ttk.Label(self.result_frame, text=NOTHING_HERE))
        }

        self.start_button.pack()
        self.result_frame.pack(fill='both', expand='yes')
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


    def fetch_result(self, window_handler):      
        try:
            image = api.screenshot_window(window_handler)
            position_image, hint_image = api.process_screenshot(image)
            x, y, hints = api.find_relevant_data(position_image, hint_image)

            self.change_from(api.FROM_FORMAT.format(x, y))

            for direction in hints:
                hint = hints[direction]

                if hint is not None:
                    self.change_result(direction, api.TO_FORMAT.format(hint['n'], hint['d'], hint['x'], hint['y']))
                else:
                    self.change_result(direction, NOTHING_HERE)

        except:
            e = sys.exc_info()
            self.change_from('Aucune solution : ' + str(e))


    def start(self):
        api.find_dofus_window_exec(self.fetch_result)


if __name__ == '__main__':
    app = App()
    app.title(APP_NAME)
    app.mainloop()

