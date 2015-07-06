#! /usr/bin/env python3
import quiz_parser
import random
import textwrap

DATABANK = 'databank.xml'

def main(source):
    databank = quiz_parser.parse_databank(source)
    questions_asked = 0
    questions_right = 0
    questions_wrong = []
    for chapter in databank.chapters:
        for section in chapter.sections:
            title = 'Chapter {}.{}'.format(chapter.number, section.number)
            print('REVIEWING -', title)
            # Create a database of answers.
            answers = tuple(map(lambda key: key.answer, section.keys))
            # Create a shuffled database of questions (keys).
            questions = random.sample(section.keys, len(section.keys))
            # Start asking questions.
            for key in questions:
                longest_line = 0
                for line in textwrap.wrap(key.question, 40):
                    print(line)
                    longest_line = max(longest_line, len(line))
                print('=' * longest_line)
                questions_asked += 1
                # Create some choices.
                copy = list(answers)
                while key.answer in copy:
                    copy.remove(key.answer)
                choices = random.sample(copy, 3)
                choices.append(key.answer)
                random.shuffle(choices)
                # Display those choices.
                for letter, choice in zip('abcd', choices):
                    print('({}) {}'.format(letter, choice))
                # Prompt for an answer.
                while True:
                    string = input('Choice: ')
                    if string in tuple('abcd'):
                        index = ord(string) - ord('a')
                        if choices[index] == key.answer:
                            print('Correct!')
                            questions_right += 1
                        else:
                            print('Wrong!')
                            questions_wrong.append(key)
                        break
                    else:
                        print('You must enter "a", "b", "c", or "d"')
                print()
    # Display the resuls.
    percentage = int(100 * questions_right / questions_asked)
    print('You got {}% right.'.format(percentage))
    # If there were answers wrong, review them.
    if questions_wrong:
        print('These were answered incorrectly:')
        for key in questions_wrong:
            print(repr(key))
    # Let people read the results.
    input('\nPress the return key to terminate ...')

if __name__ == '__main__':
    main(DATABANK)
