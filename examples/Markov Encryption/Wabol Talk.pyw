#! /usr/bin/env python3
from tkinter import NoDefaultRoot, Tk
from tkinter.ttk import Frame, LabelFrame
from tkinter.constants import NSEW, WORD, SEL, END, DISABLED
from tkinter.scrolledtext import ScrolledText

################################################################################

class WabolTalk(Frame):

    TEXT = dict(height=2, width=46, wrap=WORD)
    GRID = dict(sticky=NSEW, padx=5, pady=5)

    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self.build_widgets()
        self.place_widgets()
        self.setup_widgets()
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def build_widgets(self):
        # Needs a way to decrypt !!!
        self.public_frame = LabelFrame(self, text='Public Message:')
        self.public_text = ScrolledText(self.public_frame, **self.TEXT)
        self.private_frame = LabelFrame(self, text='Private Message:')
        self.private_text = ScrolledText(self.private_frame, **self.TEXT)
        self.output_frame = LabelFrame(self, text='Output Area:')
        self.output_text = ScrolledText(self.output_frame, **self.TEXT)

    def place_widgets(self):
        self.public_frame.grid(**self.GRID)
        self.public_text.grid(**self.GRID)
        self.public_frame.grid_rowconfigure(0, weight=1)
        self.public_frame.grid_columnconfigure(0, weight=1)
        self.private_frame.grid(**self.GRID)
        self.private_text.grid(**self.GRID)
        self.private_frame.grid_rowconfigure(0, weight=1)
        self.private_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid(**self.GRID)
        self.output_text.grid(**self.GRID)
        self.output_frame.grid_rowconfigure(0, weight=1)
        self.output_frame.grid_columnconfigure(0, weight=1)

    def setup_widgets(self):
        self.public_text.bind('<Key>', self.handle_key_events)
        self.public_text.bind('<Control-Key-a>', self.handle_control_a)
        self.public_text.bind('<Control-Key-/>', lambda event: 'break')
        self.private_text.bind('<Key>', self.handle_key_events)
        self.private_text.bind('<Control-Key-a>', self.handle_control_a)
        self.private_text.bind('<Control-Key-/>', lambda event: 'break')
        self.output_text['state'] = DISABLED
        self.output_text.bind('<Control-Key-a>', self.handle_control_a)
        self.output_text.bind('<Control-Key-/>', lambda event: 'break')

    def handle_key_events(self, event):
        if event.char and event.state | 0o11 == 0o11:
            self.after_idle(self.refresh)

    @staticmethod
    def handle_control_a(event):
        event.widget.tag_add(SEL, 1.0, END + '-1c')
        return 'break'

##    def refresh(self):
##        pass
##
##    def output(self, value):
##        self.output_text['state'] = NORMAL
##        self.output_text.delete(1.0, END)
##        self.output_text.insert(END, value)
##        # CONTINUE HERE

    @classmethod
    def main(cls):
        NoDefaultRoot()
        root = Tk()
        root.minsize(420, 330)
        root.title('Wabol Talk')
        talk = cls(root)
        talk.grid(sticky=NSEW)
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.mainloop()

################################################################################

if __name__ == '__main__':
    WabolTalk.main()
