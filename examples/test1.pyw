from tkinter import *

x = Tk()
x.resizable(False, False)
x.title('GUI Test')
def demo():
    x.withdraw()
    import time
    time.sleep(5)
    x.deiconify()
z = Entry()
z.pack()
y = Button(x, command=demo)
y.pack()
y.configure(text='Test Button')
x.mainloop()

