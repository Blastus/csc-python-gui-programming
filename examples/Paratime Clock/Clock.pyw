#! /usr/bin/env python3
import tkinter
import paratime

def main():
    root = tkinter.Tk()
    root.resizable(False, False)
    root.title('Time in Tessaressunago')
    time = tkinter.StringVar()
    text = tkinter.Label(textvariable=time, font=('helvetica', 16, 'bold'))
    text.grid(padx=5, pady=5)
    thread = paratime.Quantum_Timer(update, time)
    thread.start()
    root.mainloop()

def update(time):
    s = paratime.seconds()
    t = paratime.text(s)
    p = 1000000000 * 1.01 ** (s / paratime.SECOND_IN_YEAR)
    time.set('Time = {0}\nNational = {1}'.format(t, fix(p)))

# Without dragons, normal growth is 1.00770786779743 (not 1.01)

def fix(number, sep=','):
    number = str(int(number))
    string = ''
    while number:
        string = number[-1] + string
        number = number[:-1]
        if number and not (len(string) + 1) % 4:
            string = sep + string
    return string

if __name__ == '__main__':
    main()
