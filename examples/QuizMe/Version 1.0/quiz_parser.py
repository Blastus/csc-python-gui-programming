#! /usr/bin/env python3
from xml.sax import parse
from xml.sax.handler import ContentHandler

################################################################################

class QuizParser(ContentHandler):

    def __init__(self):
        super().__init__()
        self.context = []

    def startElement(self, name, attrs):
        if name == 'databank':
            # Validate
            assert len(self.context) == 0
            self.context.append(name)
            # Specific
            self.databank = DataBank()
        elif name == 'chapter':
            # Validate
            assert len(self.context) == 1
            assert self.context[0] == 'databank'
            self.context.append(name)
            # Specific
            chapter_value = int(attrs.getValue('value'))
            self.chapter = Chapter(chapter_value)
        elif name == 'section':
            # Validate
            assert len(self.context) == 2
            assert self.context[0] == 'databank'
            assert self.context[1] == 'chapter'
            self.context.append(name)
            # Specific
            section_value = int(attrs.getValue('value'))
            self.section = Section(section_value)
        elif name == 'question':
            # Validate
            assert len(self.context) == 3
            assert self.context[0] == 'databank'
            assert self.context[1] == 'chapter'
            assert self.context[2] == 'section'
            self.context.append(name)
            # Specific
            self.key = Key()
        elif name == 'answer':
            # Validate
            assert len(self.context) == 4
            assert self.context[0] == 'databank'
            assert self.context[1] == 'chapter'
            assert self.context[2] == 'section'
            assert self.context[3] == 'question'
            self.context.append(name)
            # Specific
            # There is no "specific" code here.
        else:
            raise ValueError(name)

    def characters(self, content):
        if content and len(self.context) > 3:
            if self.context[-1] == 'question':
                self.key.add_question(content)
            elif self.context[-1] == 'answer':
                self.key.add_answer(content)
            else:
                raise SyntaxError(content)

    def endElement(self, name):
        if name == 'databank':
            # Validate
            assert len(self.context) == 1
            assert self.context[0] == name
            self.context.pop()
            # Specific
            # There is no "specific" code here.
        elif name == 'chapter':
            # Validate
            assert len(self.context) == 2
            assert self.context[0] == 'databank'
            assert self.context[1] == name
            self.context.pop()
            # Specific
            self.databank.add(self.chapter)
        elif name == 'section':
            # Validate
            assert len(self.context) == 3
            assert self.context[0] == 'databank'
            assert self.context[1] == 'chapter'
            assert self.context[2] == name
            self.context.pop()
            # Specific
            self.chapter.add(self.section)
        elif name == 'question':
            # Validate
            assert len(self.context) == 4
            assert self.context[0] == 'databank'
            assert self.context[1] == 'chapter'
            assert self.context[2] == 'section'
            assert self.context[3] == name
            self.context.pop()
            # Specific
            self.section.add(self.key)
        elif name == 'answer':
            # Validate
            assert len(self.context) == 5
            assert self.context[0] == 'databank'
            assert self.context[1] == 'chapter'
            assert self.context[2] == 'section'
            assert self.context[3] == 'question'
            assert self.context[4] == name
            self.context.pop()
            # Specific
            # There is no "specific" code here.
        else:
            raise ValueError(name)

################################################################################

class DataBank:

    def __init__(self):
        self.chapters = []

    def __repr__(self):
        return '\n'.join(map(repr, self.chapters))

    def add(self, chapter):
        self.chapters.append(chapter)

class Chapter:

    def __init__(self, number):
        self.number = number
        self.sections = []

    def __repr__(self):
        lines = '\n'.join(map(repr, self.sections))
        lines = lines.split('\n')
        lines = map(lambda line: '    ' + line, lines)
        lines = '\n'.join(lines)
        return 'Chapter {}:\n{}'.format(self.number, lines)

    def add(self, section):
        self.sections.append(section)

class Section:

    def __init__(self, number):
        self.number = number
        self.keys = []

    def __repr__(self):
        lines = '\n\n'.join(map(repr, self.keys))
        lines = lines.split('\n')
        lines = map(lambda line: '    ' + line, lines)
        lines = '\n'.join(lines)
        return 'Section {}:\n{}'.format(self.number, lines)

    def add(self, key):
        self.keys.append(key)

class Key:

    def __init__(self):
        self.question = ''
        self.answer = ''

    def __repr__(self):
        return 'Question: {}\nAnswer: {}'.format(self.question, self.answer)

    def add_question(self, string):
        self.question = string

    def add_answer(self, string):
        self.answer = string

################################################################################

def parse_databank(filename):
    parser = QuizParser()
    parse(filename, parser)
    return parser.databank
