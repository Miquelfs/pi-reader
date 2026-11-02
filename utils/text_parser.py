import re
import textwrap

WRAP_WIDTH = 52        # character fallback when no pixel measure is given
HEADING_MAX_LEN = 60  # longer than this can't be a heading even if uppercase
_CHAPTER_RE = re.compile(r'^(chapter|part|book|prologue|epilogue)\b[^.!?]{0,40}$', re.IGNORECASE)


class Line:
    """A single rendered line with a type tag for layout decisions."""
    __slots__ = ('text', 'kind')

    def __init__(self, text, kind='body'):
        self.text = text
        self.kind = kind  # 'body' | 'heading' | 'gap'


def _is_heading(paragraph):
    """True if this paragraph looks like a chapter/section title."""
    stripped = paragraph.strip()
    if not stripped or len(stripped) > HEADING_MAX_LEN:
        return False
    # All-caps words (ignoring punctuation and short connectors)
    words = stripped.split()
    if len(words) == 0:
        return False
    if _CHAPTER_RE.match(stripped):
        return True
    # Numerals don't count either way, so "CHAPTER 1" or "IV. THE STORM" qualify
    alpha_words = [w for w in words if any(c.isalpha() for c in w)]
    upper_words = sum(1 for w in alpha_words if w.replace(',', '').replace('.', '').replace(':', '').isupper() and len(w) > 1)
    return upper_words >= max(1, len(alpha_words) * 0.6)


def wrap_px(text, measure, max_w):
    """Greedy wrap so that sum(word widths) + one space per gap fits max_w.
    measure(word) must return the same integer widths the renderer uses,
    otherwise justified lines can end up with negative gaps."""
    space_w = measure(' ')
    out, current, current_w = [], [], 0
    for word in text.split():
        w = measure(word)
        if current and current_w + space_w + w > max_w:
            out.append(' '.join(current))
            current, current_w = [word], w
        else:
            current_w += (space_w if current else 0) + w
            current.append(word)
    if current:
        out.append(' '.join(current))
    return out


def parse(text, wrap_width=WRAP_WIDTH, measure=None, max_w=None, heading_measure=None):
    """
    Split raw book text into a list of Line objects.

    Rules:
    - Blank lines in source → one 'gap' Line (rendered as vertical space)
    - Short ALL-CAPS paragraphs → 'heading' Lines (rendered larger)
    - Everything else → word-wrapped 'body' Lines

    With measure + max_w, lines are wrapped by pixel width; otherwise by
    wrap_width characters.
    """
    def _wrap(t, m):
        if m and max_w:
            return wrap_px(t, m, max_w)
        return textwrap.wrap(t, width=wrap_width)

    lines = []
    paragraphs = text.split('\n')

    i = 0
    while i < len(paragraphs):
        raw = paragraphs[i].rstrip()

        if raw == '':
            # Collapse consecutive blank lines into one gap
            if not lines or lines[-1].kind != 'gap':
                lines.append(Line('', 'gap'))
            i += 1
            continue

        if _is_heading(raw):
            # Emit a gap before heading if not already present
            if lines and lines[-1].kind != 'gap':
                lines.append(Line('', 'gap'))
            for h in _wrap(raw.strip(), heading_measure or measure):
                lines.append(Line(h, 'heading'))
            lines.append(Line('', 'gap'))
            i += 1
            continue

        # Accumulate a multi-line paragraph (lines with no blank between them).
        # Calibre txt output often hard-wraps at 80 chars — we detect mid-sentence
        # line breaks (line doesn't end with sentence-ending punctuation) and join them.
        para_parts = [raw]
        i += 1
        while i < len(paragraphs):
            next_raw = paragraphs[i].rstrip()
            if next_raw == '':
                break
            # Join if previous line ends mid-word/mid-sentence (no terminal punctuation)
            prev = para_parts[-1]
            if prev and prev[-1] not in '.!?:"”’':
                para_parts.append(next_raw)
                i += 1
            else:
                break

        paragraph_text = ' '.join(para_parts)
        for w in _wrap(paragraph_text, measure):
            lines.append(Line(w, 'body'))

    # Strip leading/trailing gaps
    while lines and lines[0].kind == 'gap':
        lines.pop(0)
    while lines and lines[-1].kind == 'gap':
        lines.pop()

    return lines
