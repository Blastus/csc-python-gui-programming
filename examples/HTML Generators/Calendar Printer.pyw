import os
import time
import tkinter
import calendar
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
        root.title('Calendar Printer')
        # Create a directory dialog.
        self.__directory_dialog = tkinter.filedialog.Directory(root, parent=root, title='Please select a destination directory.', mustexist=True)
        # Create the entry labels.
        start_label = tkinter.Label(root, text='Start Date:')
        end_label = tkinter.Label(root, text='End Date:')
        # Create the entry boxes.
        self.__start_entry = start_entry = tkinter.Entry(root)
        self.__end_entry = end_entry = tkinter.Entry(root)
        # Create the push button.
        create_button = tkinter.Button(root, text='Create Calendar', command=self.__run)
        # Create widget bindings.
        root.bind_class('Entry', '<Control-Key-a>', self.__select_all)
        create_button.bind('<Return>', self.__run)
        # Arrange the widgets on the screen.
        start_label.grid(row=0, column=0, padx=5, pady=5, sticky=tkinter.E)
        start_entry.grid(row=0, column=1, padx=5, pady=5)
        end_label.grid(row=1, column=0, padx=5, pady=5, sticky=tkinter.E)
        end_entry.grid(row=1, column=1, padx=5, pady=5)
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
            destination = self.__get_destination()
            self.__root.withdraw()
            try:
                self.__create_files(destination, start_date, end_date)
            except:
                self.__root.deiconify()
                tkinter.messagebox.showerror('Error', 'Calendar could not be created.')
            else:
                self.__root.deiconify()
        except Error as problem:
            tkinter.messagebox.showwarning('Warning', str(problem))
        except Cancel:
            pass

    def __date(self, string, name):
        if not string:
            raise Error('Please fill out the "{}."\nToday\'s date is {}.'.format(name, time.strftime('%m/%Y')))
        try:
            return list(reversed(time.strptime(string, '%m/%Y')))[-2:]
        except:
            raise Error('"{}" was not understood.\nToday\'s date is {}.'.format(name, time.strftime('%m/%Y')))

    def __validate(self, start_date, end_date):
        if start_date[0] + start_date[1] * 12 > end_date[0] + end_date[1] * 12:
            raise Error('"Start Date" may not be after "End Date."')

    def __get_destination(self):
        destination = self.__directory_dialog.show()
        if not destination:
            raise Cancel
        return destination

    def __create_files(self, path, start, end):
        path = os.path.join(path, 'Calendar')
        try: os.mkdir(path)
        except: pass
        while start[0] + start[1] * 12 <= end[0] + end[1] * 12:
            self.__create_file(path, start[0], start[1])
            start[0] += 1
            if start[0] == 13: start[0], start[1] = 1, start[1] + 1

    def __create_file(self, path, month, year):
        m_a_y = '{} {}'.format(calendar.month_name[month], year)
        h_month = HTML_Month(month, year, 0, '\t')
        h_month.set_month(height='100%', width='100%', border=1)
        h_month.set_week(valign='top')
        h_month.set_day(width='14%')
        h_table = HTML_Table(1, 1, 2, '\t')
        h_table.mutate(0, 0, '<b>{}</b>\n{}'.format(m_a_y, h_month.html()))
        h_table.set_table(width='100%', height='100%')
        data = '''\
<html>
\t<head>
\t\t<title>
\t\t\t{}
\t\t</title>
\t</head>
\t<body>
{}
\t</body>
</html>'''.format(m_a_y, h_table.html())
        open(os.path.join(path, m_a_y + '.html'), 'w').write(data)

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

class HTML_Month:

    'HTML_Month(month, year, indent_level, indent_style) -> new HTML_Month'

    def __init__(self, month, year, indent_level, indent_style):
        'x.__init__(...) initializes x'
        calendar.setfirstweekday(calendar.SUNDAY)
        matrix = calendar.monthcalendar(year, month)
        self.__table = HTML_Table(len(matrix) + 1, 7, indent_level, indent_style)
        for column, text in enumerate(calendar.day_name[-1:] + calendar.day_name[:-1]):
            self.__table.mutate(0, column, '<b>{}</b>'.format(text))
        for row, week in enumerate(matrix):
            for column, day in enumerate(week):
                if day:
                    self.__table.mutate(row + 1, column, '<b>{:02}</b>\n<hr>\n'.format(day))
        self.__weekday, self.__alldays = calendar.monthrange(year, month)
        self.__weekday = ((self.__weekday + 1) % 7) + 6

    def mutate(self, day, text):
        'Mutates a day in the HTML month.'
        row, column = self.__row_column(day)
        self.__table.mutate(row, column, '<b>{:02}</b>\n<hr>\n{}'.format(day, text))
        return self

    def access(self, day):
        'Accesses a day in the HTML month.'
        row, column = self.__row_column(day)
        return self.__table.access(row, column)[15:]

    def special(self, day, special):
        row, column = self.__row_column(day)
        self.__table.special(row, column, special)

    def __row_column(self, day):
        'Calculates the row and column of day.'
        assert 1 <= day <= self.__alldays
        index = day + self.__weekday
        return index / 7, index % 7

    def set_month(self, **attributes):
        'Set the attributes for the month.'
        self.__table.set_table(**attributes)
        return self

    def set_week(self, **attributes):
        'Set the attributes for each week.'
        self.__table.set_row(**attributes)
        return self

    def set_day(self, **attributes):
        'Set the attributes for each day.'
        self.__table.set_cell(**attributes)
        return self

    def html(self):
        'Returns the HTML code for the current month.'
        return self.__table.html()

################################################################################

if __name__ == '__main__':
    Application()
