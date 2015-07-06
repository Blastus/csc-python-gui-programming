import datetime
import os
import time
import tkinter
import tkinter.filedialog
import tkinter.messagebox

################################################################################

class Cancel(Exception): pass

class Error(Exception):

    def __init__(self, message):
        self.__message = str(message)

    def __str__(self):
        return self.__message

################################################################################

class Application:

    def __init__(self):
        # Create the main window.
        self.__root = root = tkinter.Tk()
        root.resizable(False, False)
        root.title('Schedule Printer')
        # Create a directory dialog.
        self.__directory_dialog = tkinter.filedialog.Directory(root, parent=root, title='Please select a destination directory.', mustexist=True)
        # Create the entry labels.
        start_label = tkinter.Label(root, text='Start Date:')
        end_label = tkinter.Label(root, text='End Date:')
        days_label = tkinter.Label(root, text='Days per Page:')
        events_label = tkinter.Label(root, text='Events per Day:')
        # Create the entry boxes.
        self.__start_entry = start_entry = tkinter.Entry(root)
        self.__end_entry = end_entry = tkinter.Entry(root)
        self.__days_entry = days_entry = tkinter.Entry(root)
        self.__events_entry = events_entry = tkinter.Entry(root)
        # Create the push button.
        create_button = tkinter.Button(root, text='Create Schedule', command=self.__run)
        # Create widget bindings.
        root.bind_class('Entry', '<Control-Key-a>', self.__select_all)
        create_button.bind('<Return>', self.__run)
        # Arrange the widgets on the screen.
        start_label.grid(row=0, column=0, padx=5, pady=5, sticky=tkinter.E)
        start_entry.grid(row=0, column=1, padx=5, pady=5)
        end_label.grid(row=1, column=0, padx=5, pady=5, sticky=tkinter.E)
        end_entry.grid(row=1, column=1, padx=5, pady=5)
        days_label.grid(row=2, column=0, padx=5, pady=5, sticky=tkinter.E)
        days_entry.grid(row=2, column=1, padx=5, pady=5)
        events_label.grid(row=3, column=0, padx=5, pady=5, sticky=tkinter.E)
        events_entry.grid(row=3, column=1, padx=5, pady=5)
        create_button.grid(row=4, column=0, padx=5, pady=5, sticky=tkinter.EW, columnspan=2)
        # Execute tkinter's main loop.
        root.mainloop()

    def __select_all(self, event):
        event.widget.selection_range(0, tkinter.END)
        return 'break'

    def __run(self, event=None):
        try:
            start_date = self.__date(self.__start_entry.get(), 'Start Date')
            end_date = self.__date(self.__end_entry.get(), 'End Date')
            self.__validate(start_date, end_date)
            days_per_page = self.__number(self.__days_entry.get(), 'Days per Page', 7)
            events_per_day = self.__number(self.__events_entry.get(), 'Events per Day', 50)
            destination = self.__get_destination()
            self.__root.withdraw()
            try:
                self.__create_schedule(start_date, end_date, days_per_page, events_per_day, destination)
            except:
                self.__root.deiconify()
                tkinter.messagebox.showerror('Error', 'Schedule could not be created.')
                raise
            else:
                self.__root.deiconify()
        except Error as problem:
            tkinter.messagebox.showwarning('Warning', str(problem))
        except Cancel:
            pass

    def __date(self, string, name):
        if not string:
            raise Error('Please fill out the "{}."\nToday\'s date is {}.'.format(name, time.strftime('%x')))
        try:
            return datetime.date(*time.strptime(string, '%x')[:3])
        except:
            raise Error('"{}" was not understood.\nToday\'s date is {}.'.format(name, time.strftime('%x')))

    def __validate(self, start_date, end_date):
        if (end_date - start_date).days < 0:
            raise Error('"Start Date" may not be after "End Date."')

    def __number(self, string, name, most):
        if not string:
            raise Error('Please fill out the "{}."\nYou may enter a value between 1 and {}.'.format(name, most))
        try:
            number = int(string)
        except:
            raise Error('"{}" was not understood.\nYou may enter a value between 1 and {}.'.format(name, most))
        if not 1 <= number <= most:
            raise Error('"{}" was out of range.\nYou may enter a value between 1 and {}.'.format(name, most))
        return number

    def __get_destination(self):
        destination = self.__directory_dialog.show()
        if not destination:
            raise Cancel
        return destination

    def __create_schedule(self, start_date, end_date, days_per_page, events_per_day, destination):
        # Prepare structures for processing.
        dates = [start_date + datetime.timedelta(offset) for offset in range((end_date - start_date).days + 1)]
        pages = [dates[index:index+days_per_page] for index in range(0, len(dates), days_per_page)]
        sheets = (len(pages) + 3) // 4
        # Create a book and populate it with pages.
        schedule = Book(sheets)
        for page in pages:
            schedule.add(page)
        # Create directories for the schedule.
        start_string = start_date.strftime('%m-%d-%y')
        end_string = end_date.strftime('%m-%d-%y')
        main_folder = '{} to {}'.format(start_string, end_string)
        full_path = os.path.join(destination, main_folder)
        front_pages = os.path.join(full_path, 'Front Pages')
        back_pages = os.path.join(full_path, 'Back Pages')
        try:
            os.mkdir(full_path)
        except:
            pass
        try:
            os.mkdir(front_pages)
        except:
            pass
        try:
            os.mkdir(back_pages)
        except:
            pass
        # Process the front and back pages.
        for path, iterator in zip((front_pages, back_pages), (schedule.front_pages(), schedule.back_pages())):
            self.__process_spread(path, iterator, days_per_page, events_per_day)

    def __process_spread(self, path, iterator, days_per_page, events_per_day):
        # Create static HTML.
        events = '\n<p>\n'.join('<hr color="black">' for event in range(events_per_day))
        # Create the pages.
        for number, spread in enumerate(iterator):
            # Create the HTML for this spread.
            toplevel = HTML_Table(1, 2, 2, '    ')
            toplevel.set_table(width='100%', height='100%').set_row(height='100%').set_cell(width='50%')
            for column, page in enumerate(spread):
                if page is not None:
                    # Create the HTML for the page.
                    page_html = HTML_Table(days_per_page, 1, 0, '    ')
                    page_html.set_table(width='100%', height='100%').set_row(height='{}%'.format(100 // days_per_page)).set_cell(width='100%')
                    for row, date in enumerate(page):
                        if date is not None:
                            # Create the HTML for date.
                            date_html = HTML_Table(2, 1, 0, '    ')
                            date_html.set_table(width='100%', height='100%')
                            # Create the HTML for heading.
                            heading_html = HTML_Table(1, 1, 0, '    ')
                            heading_html.set_table(width='100%', border=1).set_cell(bgcolor='gray')
                            heading_html.mutate(0, 0, '<b>{}</b>'.format(date.strftime('%A, %B %d, %Y')))
                            date_html.mutate(0, 0, heading_html.html())
                            # Process the HTML for events.
                            date_html.mutate(1, 0, events)
                            # Save the date to the page.
                            page_html.mutate(row, 0, date_html.html())
                    toplevel.mutate(0, column, page_html.html())
            html = '''\
<html>
    <body>
{}
    </body>
</html>'''.format(toplevel.html())
            open(os.path.join(path, 'Spread {}.htm'.format(number + 1)), 'w').write(html)

################################################################################

class Book:

    def __init__(self, sheets):
        self.__sheets = [Sheet() for sheet in range(sheets)]
        self.__max_pages = sheets * 4
        self.__pages = 0
        self.__sheet_index = 0
        self.__up_stack = True

    def add(self, page):
        assert self.__pages < self.__max_pages
        self.__sheets[self.__sheet_index].add(page)
        self.__pages += 1
        if self.__pages % 2 == 0:
            if self.__up_stack:
                self.__sheet_index += 1
                if self.__sheet_index == len(self.__sheets):
                    self.__sheet_index -= 1
                    self.__up_stack = False
            else:
                self.__sheet_index -= 1

    def sheets(self):
        return iter(self.__sheets)

    def front_pages(self):
        for sheet in self.sheets():
            yield sheet.front()

    def back_pages(self):
        for sheet in self.sheets():
            yield sheet.back()

################################################################################

class Sheet:

    def __init__(self):
        self.__pages = []

    def __repr__(self):
        return repr(self.__pages)

    def add(self, page):
        assert len(self.__pages) < 4
        self.__pages.append(page)

    def front(self):
        pages = self.__pages[:]
        pages.extend([None] * (4 - len(pages)))
        return pages[3], pages[0]

    def back(self):
        pages = self.__pages[:]
        pages.extend([None] * (4 - len(pages)))
        return pages[1], pages[2]

################################################################################

class Array:

    'Array(length[, value]) -> Array'

    def __init__(self, length, value=None):
        'Initialize the Array object.'
        assert isinstance(length, int) and length > 0
        self.__data = [value] * length

    def __repr__(self):
        'Return the object\'s representation.'
        return repr(self.__data)

    def __len__(self):
        'Return the object\'s length.'
        return len(self.__data)

    def __getitem__(self, key):
        'Return the specified item.'
        return self.__data[key]

    def __setitem__(self, key, value):
        'Assign the value to the key.'
        self.__data[key] = value

    def __delitem__(self, key):
        'Delete the specified item.'
        self.__data[key] = None

    def __itet__(self):
        'Return the object\'s iterator.'
        return iter(self.__data)

    def __contains__(self, item):
        'Return the item\'s membership status.'
        return item in self.__data

################################################################################

class Matrix:

    'Matrix(rows, columns[, value]) -> Matrix'

    def __init__(self, rows, columns, value=None):
        'Initialize the Matrix object.'
        assert isinstance(rows, int) and rows > 0
        self.__data = [Array(columns, value) for row in range(rows)]
        
    def __repr__(self):
        'Return the object\'s representation.'
        return repr(self.__data)

    def __len__(self):
        'Return the object\'s length.'
        return len(self.__data)

    def __getitem__(self, key):
        'Return the specified item.'
        return self.__data[key]

    def __setitem__(self, key, value):
        'Assign the value to the key.'
        self.__data[key] = Array(len(self.__data[key]), value)

    def __delitem__(self, key):
        'Delete the specified item.'
        self.__data[key] = Array(len(self.__data[key]))

    def __iter__(self):
        'Return the object\'s iterator.'
        return iter(self.__data)

    def __contains__(self, item):
        'Return the item\'s membership status.'
        for row in self.__data:
            if item in row:
                return True
        return False

################################################################################

class HTML_Table:

    'HTML_Table(rows, columns, indent_level, indent_style) -> new HTML_Table'

    def __init__(self, rows, columns, indent_level, indent_style):
        'x.__init__(...) initializes x'
        self.__matrix = Matrix(rows, columns, '')
        self.__special = Matrix(rows, columns, False)
        self.__indent_level = indent_level
        self.__indent_style = indent_style
        self.__table_attributes = ''
        self.__row_attributes = ''
        self.__cell_attributes = ''

    def mutate(self, row, column, text):
        'Mutates a cell in the HTML table.'
        assert type(text) is str
        self.__matrix[row][column] = text
        return self

    def access(self, row, column):
        'Accesses a cell in the HTML table.'
        return self.__matrix[row][column]

    def special(self, row, column, special):
        self.__special[row][column] = special

    def set_table(self, **attributes):
        'Sets the attributes for the table.'
        self.__table_attributes = self.__parse(attributes)
        return self

    def set_row(self, **attributes):
        'Sets the attributes for each row.'
        self.__row_attributes = self.__parse(attributes)
        return self

    def set_cell(self, **attributes):
        'Sets the attributes for each cell.'
        self.__cell_attributes = self.__parse(attributes)
        return self

    def __parse(self, attributes):
        'Parses the attributes into a string.'
        return ''.join([' {}="{}"'.format(key, attributes[key]) for key in sorted(attributes)])

    def html(self):
        'Returns the HTML code for the current table.'
        html = self.__indent_style * self.__indent_level + '<table' + self.__table_attributes + '>\n'
        for row, s_row in zip(self.__matrix, self.__special):
            html += self.__indent_style * (self.__indent_level + 1) + '<tr' + self.__row_attributes + '>\n'
            for cell, special in zip(row, s_row):
                html += self.__indent_style * (self.__indent_level + 2) + '<td' + self.__cell_attributes + '>\n'
                if special:
                    html += cell + '\n'
                else:
                    html += ''.join([self.__indent_style * (self.__indent_level  + 3) + line + '\n' for line in cell.splitlines()])
                html += self.__indent_style * (self.__indent_level + 2) + '</td>\n'
            html += self.__indent_style * (self.__indent_level + 1) + '</tr>\n'
        return html + self.__indent_style * self.__indent_level + '</table>'

################################################################################

if __name__ == '__main__':
    Application()
