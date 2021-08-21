import tkinter as tk
import tkinter.ttk as ttk
import api
import sys

APP_NAME = 'Dofus treasure finder'

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.wm_attributes("-topmost", 1)
        self.create_widgets()

    def create_widgets(self):
        self.start_button = ttk.Button(self, text='Démarrer', command=self.start)
        self.result_frame = ttk.LabelFrame(self, text='Résultat')
        self.result_labels = []

        self.start_button.pack()
        self.result_frame.pack(fill="both", expand="yes")

    def add_result(self, label_text):
        label = ttk.Label(self, text=label_text)
        self.result_labels.append(label)
        label.pack()

    def clean_result(self):
        for label in self.result_labels:
            label.destroy()

        self.result_labels = []

    def fetch_result(self, window_handler):
        self.clean_result()
        
        try:
            image = api.screenshot_window(window_handler)
            position_image, hint_image = api.process_screenshot(image)
            x, y, hints = api.find_relevant_data(position_image, hint_image)

            self.add_result(api.FROM_FORMAT.format(x, y))

            for direction in hints:
                hint = hints[direction]

                if hint is not None:
                    self.add_result(api.TO_FORMAT.format(
                        api.DIRECTIONS_SIGLE[direction], hint['n'], hint['d'], hint['x'], hint['y']))

        except:
            e = sys.exc_info()
            self.add_result('Aucune solution : ' + str(e))

    def start(self):
        api.find_dofus_window_exec(self.fetch_result)

if __name__ == '__main__':
    app = App()
    app.title(APP_NAME)
    app.mainloop()

