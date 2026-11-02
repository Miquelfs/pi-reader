import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.text_parser import parse, wrap_px, _is_heading


def measure(word):
    return 4 if word == ' ' else 10 * len(word)


class WrapTest(unittest.TestCase):
    def test_lines_fit_with_minimum_gap(self):
        text = ' '.join(['ab', 'abcdef', 'a', 'abcd'] * 30)
        for line in wrap_px(text, measure, 200):
            words = line.split()
            width = sum(measure(w) for w in words) + (len(words) - 1) * measure(' ')
            self.assertLessEqual(width, 200)

    def test_no_words_lost(self):
        text = ' '.join(f'w{i}' for i in range(500))
        lines = wrap_px(text, measure, 180)
        self.assertEqual(' '.join(lines).split(), text.split())

    def test_overlong_word_gets_own_line(self):
        self.assertEqual(wrap_px('a ' + 'x' * 50 + ' b', measure, 100), ['a', 'x' * 50, 'b'])


class HeadingTest(unittest.TestCase):
    def test_headings(self):
        for h in ['CHAPTER 1', 'CHAPTER ONE', 'Chapter 12', 'PART II', 'IV. THE STORM', 'Prologue']:
            self.assertTrue(_is_heading(h), h)

    def test_not_headings(self):
        for p in ['He said hello.', 'Chapter one was over, he thought.', '1984', 'I', 'A']:
            self.assertFalse(_is_heading(p), p)


class ParseTest(unittest.TestCase):
    def test_joins_hard_wrapped_lines_and_marks_headings(self):
        text = 'CHAPTER 1\n\nIt was a dark and\nstormy night.\n\nThe end.'
        kinds = [(l.kind, l.text) for l in parse(text, measure=measure, max_w=1000)]
        self.assertEqual(kinds, [
            ('heading', 'CHAPTER 1'),
            ('gap', ''),
            ('body', 'It was a dark and stormy night.'),
            ('gap', ''),
            ('body', 'The end.'),
        ])

    def test_long_heading_wraps(self):
        lines = parse('CHAPTER FIVE: A VERY LONG TITLE', measure=measure, max_w=150)
        self.assertGreater(len([l for l in lines if l.kind == 'heading']), 1)


if __name__ == '__main__':
    unittest.main()
