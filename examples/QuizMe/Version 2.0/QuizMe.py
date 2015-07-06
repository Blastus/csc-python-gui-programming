#! /usr/bin/env python3
import sys
import textwrap
import xml.sax._exceptions
import testbank
import teach_me

################################################################################

def main():
    welcome()
    testbank = get_testbank()
    execute_quiz(testbank)
    input('Exiting ...\n')

################################################################################

def welcome():
    print('  Welcome to QuizMe  ')
    print('/===================\\')
    print('|  by Evan Wolting  |')
    print('|        and        |')
    print('|  Stephen Chappell |')
    print('\\-------------------/')
    print()
          

def get_testbank():
    print('Please enter the testbank filename.')
    while True:
        try:
            path = input('Path: ')
        except:
            sys.exit(0)
        try:
            return testbank.parse(path)
        except xml.sax._exceptions.SAXParseException as error:
            args = error.getLineNumber(), error.getColumnNumber()
            print('Parse Error: Line {}, Column {}'.format(*args))
        except ValueError as error:
            print(error.args[0].capitalize())
        print('Please try again.')

def execute_quiz(testbank):
    last_exit = None
    for event in teach_me.FAQ(testbank):
        print()
        if isinstance(event, teach_me.Enter):
            print('Starting ...', event)
        elif isinstance(event, teach_me.Exit):
            print('Ending ...', event)
            last_exit = event.kind
        elif isinstance(event, teach_me.Question):
            ask_question(event)
        elif isinstance(event, teach_me.Report):
            if last_exit == 'Section' and event.wrong:
                review_problems(event)
            show_report(event)
            if event.final:
                print()
                print('/---------\\')
                print('| THE END |')
                print('\\---------/')
        else:
            raise TypeError(event)

################################################################################

def ask_question(question):
    print_question(question.category, question.question)
    get_answer(question.choices, question.answer)

def print_question(category, question):
    print(category.upper())
    lines = textwrap.wrap(question, 60)
    max_len = 0
    for line in lines:
        max_len = max(max_len, len(line))
    print('-' * max_len)
    for line in lines:
        print(line)
    print('-' * max_len)

def get_answer(choices, answer):
    letters = list(map(lambda i: chr(i + ord('a')), range(len(choices))))
    for letter, choice in zip(letters, choices):
        print('({}) {}'.format(letter, choice))
    while True:
        try:
            choice = input('Choice: ')
        except:
            sys.exit(0)
        if choice in letters:
            answer(letters.index(choice))
            return
        print('Please enter a choice.')

################################################################################
    

def review_problems(report):
    print('Questions Answered Incorrectly:')
    print('-------------------------------')
    print()
    for problem in report.problems():
        print_question(problem.category, problem.question)
        print('You answered:', problem.answer)
        print('Right answer:', problem.right)
        try: input()
        except: pass

def show_report(report):
    string = 'Cumulative score for previous {}:'.format(report.level)
    print(string + '\n' + '-' * len(string))
    print(report.right, 'of your answers are right.')
    print(report.wrong, 'of your answers are wrong.')
    percentage = int(100 * report.right / report.total + 0.5)
    print('Percetage correct: {}%'.format(percentage))

################################################################################
    
if __name__ == '__main__':
    main()
