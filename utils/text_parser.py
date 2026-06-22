import textwrap

WRAP_WIDTH = 52        # character estimate — overridden by pixel-aware wrap in reader
HEADING_MAX_LEN = 60  # longer than this can't be a heading even if uppercase


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
    upper_words = sum(1 for w in words if w.replace(',', '').replace('.', '').replace(':', '').isupper() and len(w) > 1)
    return upper_words >= max(1, len(words) * 0.6)


def parse(text, wrap_width=WRAP_WIDTH):
    """
    Split raw book text into a list of Line objects.

    Rules:
    - Blank lines in source → one 'gap' Line (rendered as vertical space)
    - Short ALL-CAPS paragraphs → 'heading' Lines (rendered larger)
    - Everything else → word-wrapped 'body' Lines

    wrap_width: character count. Pass a pixel-derived value from the caller
    for accurate wrapping with proportional fonts.
    """
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
            lines.append(Line(raw.strip(), 'heading'))
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
        wrapped = textwrap.wrap(paragraph_text, width=wrap_width)
        for w in wrapped:
            lines.append(Line(w, 'body'))

    # Strip leading/trailing gaps
    while lines and lines[0].kind == 'gap':
        lines.pop(0)
    while lines and lines[-1].kind == 'gap':
        lines.pop()

    return lines
