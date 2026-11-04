import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.article import extract

PAGE = """<html><head><title>The Long Walk | Some Magazine</title><script>var x = 1;</script></head>
<body><nav><p>Home · Sections · Subscribe to our newsletter today please</p></nav>
<article><h1>The Long Walk</h1>
<p>It was early when we left the village, and the fog still lay over the rice fields.</p>
<p>Share</p>
<p>By noon the path had climbed &amp; narrowed into a ledge cut into the cliff above the river.</p>
<figure><p>Photo caption that should not appear in the text at all, really.</p></figure>
</article><footer><p>Copyright notice that is long enough to count as a paragraph here.</p></footer></body></html>"""


class ExtractTest(unittest.TestCase):
    def test_article_text_only(self):
        title, text = extract(PAGE)
        self.assertEqual(title, 'The Long Walk | Some Magazine')
        self.assertEqual(text.split('\n\n'), [
            'THE LONG WALK',
            'It was early when we left the village, and the fog still lay over the rice fields.',
            'By noon the path had climbed & narrowed into a ledge cut into the cliff above the river.',
        ])

    def test_falls_back_to_body(self):
        _, text = extract('<html><body><p>' + 'word ' * 20 + '</p></body></html>')
        self.assertTrue(text.startswith('word word'))


if __name__ == '__main__':
    unittest.main()
