#! /usr/bin/env python3
import functools, random, string
import tkinter, tkinter.font, widgets

DIGIT = functools.partial(random.SystemRandom().choice, string.digits)

def luhn_test(account):
    array = [int(x) for x in str(account) if x.isdigit()][::-1]
    return not (sum(sum(divmod(x * 2, 10)) for x in array[1::2]) \
                + sum(array[0::2])) % 10

def generate():
    card = random.choice(('4', '5', '6011'))    # Visa, Mastercard, Discover
    while len(card) != 15:
        card += DIGIT()
    for digit in map(str, range(10)):
        if luhn_test(card + digit):
            return card + digit

def main():
    tkinter.NoDefaultRoot()
    root = tkinter.Tk()
    root.resizable(False, False)
    root.title('Credit Card Number')
    font = tkinter.font.Font(root, family='Arial Black', size=14)
    note = widgets.DiacriticalEntry(root, font=font)
    note.grid()
    note.insert(0, generate())
    def command():
        note.delete(0, tkinter.END)
        note.insert(0, generate())
    button = tkinter.Button(root, text='Next', command=command)
    button.grid(sticky=tkinter.EW)
    root.mainloop()

if __name__ == '__main__':
    main()
