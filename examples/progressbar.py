#! /usr/bin/env python3
from tkinter import *

class Progressbar:

    def __init__(self, master, cnf={}, **kw):
        self.__handle = None
        self.orient = kw.pop('orient', HORIZONTAL)
        self.mode = kw.pop('mode', 'indeterminate')
        self.maximum = kw.pop('maximum', 100)
        kw.update({'background': 'white', 'highlightthickness': 0})
        self.__canvas = Canvas(master, cnf, **kw)

    def __getitem__(self, key):
        if key == 'orient':
            return self.orient
        if key == 'mode':
            return self.mode
        if key == 'maximum':
            return self.maximum
        return self.__canvas[key]

    def __setitem__(self, key, value):
        if key == 'orient':
            self.orient = value
        elif key == 'mode':
            self.mode = value
        elif key == 'maximum':
            self.maximum = value
        else:
            self.__canvas[key] = value

    def grid(self, cnf={}, **kw):
        self.__canvas.grid(cnf, **kw)

    def configure(self, **kw):
        if kw:
            self.orient = kw.pop('orient', self.orient)
            self.mode = kw.pop('mode', self.mode)
            self.maximum = kw.pop('maximum', self.maximum)
            if kw:
                self.__canvas.configure(self, **kw)
        return self.__canvas.configure(self)

    def start(self, interval=None):
        if self.__handle is not None:
            raise RuntimeError('Cannot start while running!')
        if self.mode != 'indeterminate':
            raise ValueError(self.mode)
        if interval is None:
            interval = 50
        elif not isinstance(interval, int):
            raise TypeError(type(interval))
        elif interval <= 0:
            raise ValueError(value)
        self.__progress = 0
        self.__direction = 1
        self.__handle = self.__canvas.after_idle(self.__animate, interval)

    def step(self, amount=None):
        if self.__handle is not None:
            raise RuntimeError('Cannot step while running!')
        if self.mode != 'determinate':
            raise ValueError(self.mode)
        if amount is None:
            amount = 1.0
        raise NotImplementedError()

    def stop(self):
        if self.__handle is None:
            raise RuntimeError('Cannot stop while not running!')
        if self.mode != 'indeterminate':
            raise ValueError(self.mode)
        self.__canvas.after_cancel(self.__handle)

    def __animate(self, interval):
        self.__canvas.delete(ALL)
        if self.maximum == 1:
            self.__progress ^= 1
            if self.__progress:
                self.__draw(int(self['width']), int(self['height']))
        else:
            if self.orient == HORIZONTAL:
                width = self.__canvas.winfo_width() / self.maximum
                self.__draw(round(self.__progress * width), 0,
                            round((self.__progress + 1) * width),
                            self.__canvas.winfo_height())
            else:
                height = self.__canvas.winfo_height() / self.maximum
                self.__draw(0, round(self.__progress * height),
                            self.__canvas.winfo_width(),
                            round((self.__progress + 1) * height))
            if self.__progress <= 0 and self.__direction == -1 or \
               self.__progress + 1 >= self.maximum and self.__direction == +1:
                self.__direction *= -1
            self.__progress += self.__direction
        self.__canvas.after(interval, self.__animate, interval)

    def __draw(self, x1, y1, x2=None, y2=None):
        if x2 is None:
            if y2 is not None:
                raise ValueError(y2)
            x1, y1, x2, y2 = 0, 0, x1, y1
        self.__canvas.create_rectangle(
            x1, y1, x2, y2, fill='green', outline='green')

    def __get_orient(self):
        return self.__orient

    def __set_orient(self, value):
        if value not in (HORIZONTAL, VERTICAL):
            raise ValueError(value)
        self.__orient = value

    orient = property(__get_orient, __set_orient)

    def __get_mode(self):
        return self.__mode

    def __set_mode(self, value):
        if self.__handle is not None:
            raise RuntimeError('Cannot set mode while running!')
        if value not in ('indeterminate', 'determinate'):
            raise ValueError(value)
        self.__mode = value

    mode = property(__get_mode, __set_mode)

    def __get_maximum(self):
        return int(self.__maximum)

    def __set_maximum(self, value):
        if not isinstance(value, int):
            raise TypeError(type(value))
        if value <= 0:
            raise ValueError(value)
        self.__maximum = float(value)

    maximum = property(__get_maximum, __set_maximum)

def main():
    root = Tk()
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    pb = Progressbar(root, height=10, width=200, maximum=20)
    pb.grid(sticky=NSEW)
    pb.start()
    root.mainloop()

if __name__ == '__main__':
    main()
