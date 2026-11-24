import re
import unicodedata
from typing import NamedTuple

MAX_FRAGMENT_CHARS = 1200
PATH_SEPARATOR = " → "

_MD_HEADING = re.compile(r"^#{1,6}\s+\S")
_LEADING_NUMBER = re.compile(r"^(\d+(?:\.\d+)*)\.?(?=\s|$)")
_NUMBERED_LINE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+\S")
_LIST_MARKER = re.compile(r"^(?:[-*•–—]|\d+[.)]|[a-zа-яё][)])\s")
_WHITESPACE = re.compile(r"\s+")
_SENTENCE_BREAK = re.compile(r"(?<=[.!?…])\s+")
_NOT_HEADING_ENDINGS = ".;:,!?"
_MAX_NUMBERED_HEADING_CHARS = 120


class Fragment(NamedTuple):
    kind: str
    section: str
    heading_path: str
    context: str
    text: str
    start: int
    end: int


class _Line(NamedTuple):
    start: int
    end: int
    text: str


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _blocks(text: str) -> list[list[_Line]]:
    blocks: list[list[_Line]] = []
    current: list[_Line] = []
    offset = 0
    for raw in text.split("\n"):
        stripped = raw.strip()
        if stripped:
            start = offset + len(raw) - len(raw.lstrip())
            current.append(_Line(start, start + len(stripped), stripped))
        elif current:
            blocks.append(current)
            current = []
        offset += len(raw) + 1
    if current:
        blocks.append(current)
    return blocks


def _split_long(text: str, start: int) -> list[tuple[str, int, int]]:
    """Cut an over-long paragraph into parts of at most MAX_FRAGMENT_CHARS."""
    if len(text) <= MAX_FRAGMENT_CHARS:
        return [(text, start, start + len(text))]

    spans: list[tuple[int, int]] = []
    position = 0
    for match in _SENTENCE_BREAK.finditer(text):
        spans.append((position, match.start()))
        position = match.end()
    spans.append((position, len(text)))

    pieces: list[tuple[int, int]] = []
    for begin, finish in spans:
        while finish - begin > MAX_FRAGMENT_CHARS:
            window = text[begin + 1 : begin + MAX_FRAGMENT_CHARS + 1]
            gaps = list(_WHITESPACE.finditer(window))
            cut = begin + 1 + gaps[-1].start() if gaps else -1
            if cut == -1:
                pieces.append((begin, begin + MAX_FRAGMENT_CHARS))
                begin += MAX_FRAGMENT_CHARS
            else:
                pieces.append((begin, cut))
                begin = cut + 1
            while begin < finish and text[begin].isspace():
                begin += 1
        if begin < finish:
            pieces.append((begin, finish))

    parts: list[tuple[int, int]] = []
    for begin, finish in pieces:
        if parts and finish - parts[-1][0] <= MAX_FRAGMENT_CHARS:
            parts[-1] = (parts[-1][0], finish)
        else:
            parts.append((begin, finish))
    return [(text[b:e], start + b, start + e) for b, e in parts]


class _Splitter:
    def __init__(self, text: str) -> None:
        self.text = text
        self.fragments: list[Fragment] = []
        self.section = ""
        self.path = ""
        self.stack: list[tuple[int, str]] = []
        self.counters: list[int] = []

    def run(self) -> list[Fragment]:
        for block in _blocks(self.text):
            if len(block) == 1:
                self._single_line(block[0])
            else:
                self._block(block)
        return self.fragments

    def _single_line(self, line: _Line) -> None:
        if _MD_HEADING.match(line.text):
            self._md_heading(line)
            return
        numbered = _NUMBERED_LINE.match(line.text)
        if (
            numbered
            and len(line.text) <= _MAX_NUMBERED_HEADING_CHARS
            and line.text[-1] not in _NOT_HEADING_ENDINGS
        ):
            number = numbered.group(1)
            self._heading(line.start, line.end, line.text, number.count(".") + 1, number)
            return
        self._block([line])

    def _block(self, block: list[_Line]) -> None:
        segment: list[_Line] = []
        for line in block:
            if _MD_HEADING.match(line.text):
                self._content(segment)
                segment = []
                self._md_heading(line)
            else:
                segment.append(line)
        self._content(segment)

    def _md_heading(self, line: _Line) -> None:
        hashes = len(line.text) - len(line.text.lstrip("#"))
        body = line.text[hashes:]
        title = body.strip()
        start = line.start + hashes + (len(body) - len(body.lstrip()))
        number = _LEADING_NUMBER.match(title)
        self._heading(start, start + len(title), title, hashes, number.group(1) if number else "")

    def _heading(self, start: int, end: int, title: str, level: int, number: str) -> None:
        if number:
            self.counters = [int(part) for part in number.split(".")]
        else:
            del self.counters[level:]
            while len(self.counters) < level:
                self.counters.append(1 if len(self.counters) < level - 1 else 0)
            self.counters[level - 1] += 1
            number = ".".join(str(n) for n in self.counters)
        while self.stack and self.stack[-1][0] >= level:
            self.stack.pop()
        path = PATH_SEPARATOR.join(t for _, t in self.stack)
        self.stack.append((level, title))
        self.fragments.append(Fragment("heading", number, path, "", title, start, end))
        self.section = number
        self.path = PATH_SEPARATOR.join(t for _, t in self.stack)

    def _span(self, lines: list[_Line]) -> tuple[str, int, int]:
        start, end = lines[0].start, lines[-1].end
        return self.text[start:end], start, end

    def _content(self, lines: list[_Line]) -> None:
        if not lines:
            return
        first_item = next((i for i, ln in enumerate(lines) if _LIST_MARKER.match(ln.text)), None)
        if first_item is None:
            self._paragraph(lines)
            return
        intro = lines[:first_item]
        context = ""
        if intro and intro[-1].text.endswith(":"):
            context = self._span(intro)[0]
        elif intro:
            self._paragraph(intro)
        items: list[list[_Line]] = []
        for line in lines[first_item:]:
            if _LIST_MARKER.match(line.text):
                items.append([line])
            else:
                items[-1].append(line)
        for item in items:
            text, start, end = self._span(item)
            self.fragments.append(
                Fragment("list_item", self.section, self.path, context, text, start, end)
            )

    def _paragraph(self, lines: list[_Line]) -> None:
        text, start, _ = self._span(lines)
        for part, begin, finish in _split_long(text, start):
            self.fragments.append(
                Fragment("paragraph", self.section, self.path, "", part, begin, finish)
            )


def split(text: str) -> list[Fragment]:
    return _Splitter(text).run()
