"""Split a requirements document into fragments (headings, paragraphs, list items).

Classification is line by line. Every non-empty physical line is a logical line, except
hard-wrapped text, where a line is glued to the previous one. Rules, in order; the first
that matches wins, and when in doubt a line stays a paragraph:

1. ``heading_hints`` (offset of line start -> level 1..6) from the document structure.
2. Markdown: ``# `` headings, setext underlines (``===`` / ``---``), a whole-line ``**bold**``.
3. Numbered or named heading: ``1.2 Title``, ``Раздел 3``, ``Глава 2``, ``Приложение Б``,
   ``IV. Title``. It must look like a heading (short, capitalised, no requirement words).
   A single-level ``1. Title`` is a heading only if content follows it and it does not
   continue a numbered list. A multi-level ``4.1.2 Система должна ...`` is a numbered
   paragraph that carries its own section number.
4. List item: ``-``, ``*``, ``•``, ``1.``, ``1)``, ``в)``.
5. Unnumbered heading, only if it looks like a heading: ALL CAPS, a typical section
   name ("Введение", "Требования к ..."), or a standalone line (blank line before it,
   content after it, not starting with a digit).
6. Everything else is a paragraph.

A line ending with ``:`` right before list items becomes their ``context``.
"""

import re
import unicodedata
from typing import NamedTuple

MAX_FRAGMENT_CHARS = 1200
PATH_SEPARATOR = " → "

MAX_HEADING_CHARS = 120
MAX_HEADING_WORDS = 14
MIN_HEADING_LETTER_SHARE = 0.5
MIN_CAPS_WORDS = 2
MIN_CAPS_SHARE = 0.8
NOT_HEADING_ENDINGS = ".,;:"
SENTENCE_ENDINGS = ".!?:;…"

_MD_HEADING = re.compile(r"^(#{1,6})\s+\S")
_BOLD = re.compile(r"^(\*\*|__)\s*(\S.*?)\s*\1$")
_UNDERLINE = re.compile(r"^(?:={3,}|-{3,})$")
_LEADING_NUMBER = re.compile(r"^(\d+(?:\.\d+)*)\.?(?=\s|$)")
_NUMBER_PREFIX = re.compile(r"(\d{1,2}(?:\.\d{1,2}){0,5})\.?\s+(?=\S)")
_SECTION_WORD = re.compile(r"(Раздел|Глава|Часть)\s+(\d{1,2})(?:[.:]?\s+(?=[А-ЯЁA-Z«\"])|[.:]?$)")
_APPENDIX = re.compile(r"Приложение\s+([А-ЯЁA-Z\d]{1,3})(?:\s*[.:—–-]\s*|\s+(?=[А-ЯЁA-Z«\"])|$)")
_ROMAN = re.compile(r"([IVX]{1,5})\.\s+(?=\S)")
_LIST_MARKER = re.compile(r"^(?:[-*•–—]|\d{1,2}[.)]|[a-zа-яё][)])\s")
_LIST_NUMBER = re.compile(r"^(\d{1,2})[.)]\s")
_WHITESPACE = re.compile(r"\s+")
_SENTENCE_BREAK = re.compile(r"(?<=[.!?…])\s+")
_WORD = re.compile(r"[^\W\d_]+")
_REQUIREMENT_WORDS = re.compile(
    r"\b(?:должен|должна|должно|должны|необходимо|обязан|обязана|обязаны|требуется"
    r"|может|могут|shall|must|should|will)\b",
    re.IGNORECASE,
)

_SECTION_NAMES = frozenset(
    {
        "введение",
        "общие положения",
        "общие сведения",
        "назначение",
        "назначение и цели создания системы",
        "цели",
        "термины и определения",
        "глоссарий",
        "требования к системе",
        "функциональные требования",
        "нефункциональные требования",
        "состав и содержание работ",
        "порядок контроля и приемки",
        "требования к документированию",
        "источники разработки",
        "сроки",
        "ограничения",
        "риски",
        "приложения",
    }
)
_SECTION_NAME_PREFIX = "требования к "


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
    indent: int
    blank_before: bool
    begin: int


class _Head(NamedTuple):
    level: int | None
    number: str
    resync: list[int] | None
    shift: int
    end: int
    form: str


class _Record(NamedTuple):
    kind: str
    line: _Line
    head: _Head | None = None
    section: str = ""


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _looks_like_heading(title: str) -> bool:
    if not title or "\n" in title or len(title) > MAX_HEADING_CHARS:
        return False
    if title[-1] in NOT_HEADING_ENDINGS or len(title.split()) > MAX_HEADING_WORDS:
        return False
    first = title.lstrip("«\"'(")[:1]
    if not (first.isalpha() and first.isupper()) or _REQUIREMENT_WORDS.search(title):
        return False
    letters = sum(ch.isalpha() for ch in title)
    return letters / len(_WHITESPACE.sub("", title)) >= MIN_HEADING_LETTER_SHARE


def _is_caps(title: str) -> bool:
    words = _WORD.findall(title)
    letters = "".join(words)
    if len(words) < MIN_CAPS_WORDS:
        return False
    return sum(ch.isupper() for ch in letters) / len(letters) >= MIN_CAPS_SHARE


def _is_section_name(title: str) -> bool:
    key = _WHITESPACE.sub(" ", title.lower().replace("ё", "е")).strip(" .:")
    return key in _SECTION_NAMES or key.startswith(_SECTION_NAME_PREFIX)


class _Prefix(NamedTuple):
    form: str
    level: int
    number: str
    resync: list[int] | None
    body: int


def _prefix(text: str) -> _Prefix | None:
    if match := _NUMBER_PREFIX.match(text):
        number = match.group(1)
        parts = [int(p) for p in number.split(".")]
        form = "multi" if len(parts) > 1 else "single"
        return _Prefix(form, len(parts), number, parts, match.end())
    if match := _SECTION_WORD.match(text):
        return _Prefix("named", 1, match.group(2), [int(match.group(2))], 0)
    if match := _APPENDIX.match(text):
        return _Prefix("named", 1, "П" + match.group(1), None, 0)
    if match := _ROMAN.match(text):
        return _Prefix("roman", 1, match.group(1), None, match.end())
    return None


def _head_of(text: str) -> _Head | None:
    """Heading recognised from the line alone (no neighbours, no hints)."""
    if "\n" in text:
        return None
    if match := _MD_HEADING.match(text):
        hashes = len(match.group(1))
        shift = hashes + len(text[hashes:]) - len(text[hashes:].lstrip())
        number = _LEADING_NUMBER.match(text[shift:])
        resync = [int(p) for p in number.group(1).split(".")] if number else None
        return _Head(hashes, number.group(1) if number else "", resync, shift, len(text), "md")
    if match := _BOLD.match(text):
        inner = match.group(2)
        if match.group(1) in inner or not _looks_like_heading(inner):
            return None
        prefix = _prefix(inner)
        level = prefix.level if prefix else None
        number = prefix.number if prefix else ""
        resync = prefix.resync if prefix else None
        return _Head(level, number, resync, match.start(2), match.end(2), "bold")
    if prefix := _prefix(text):
        if _looks_like_heading(text[prefix.body :]):
            return _Head(prefix.level, prefix.number, prefix.resync, 0, len(text), prefix.form)
        return None
    if _looks_like_heading(text) and (_is_caps(text) or _is_section_name(text)):
        return _Head(None, "", None, 0, len(text), "plain")
    return None


def _continues(prev: _Line, line: _Line, hints: dict[int, int]) -> bool:
    """True when `line` is a hard-wrapped continuation of `prev`."""
    if {prev.start, prev.begin, line.start, line.begin} & hints.keys():
        return False
    if _UNDERLINE.match(line.text) or _head_of(prev.text):
        return False
    if _LIST_MARKER.match(prev.text) and line.indent > prev.indent:
        return True
    return (
        prev.text[-1] not in SENTENCE_ENDINGS
        and line.text[0].islower()
        and not _LIST_MARKER.match(line.text)
    )


def _logical_lines(text: str, hints: dict[int, int]) -> list[_Line]:
    lines: list[_Line] = []
    offset = 0
    blank = True
    for raw in text.split("\n"):
        stripped = raw.strip()
        if stripped:
            indent = len(raw) - len(raw.lstrip())
            start = offset + indent
            line = _Line(start, start + len(stripped), stripped, indent, blank, offset)
            if lines and not blank and _continues(lines[-1], line, hints):
                prev = lines[-1]
                lines[-1] = prev._replace(end=line.end, text=text[prev.start : line.end])
            else:
                lines.append(line)
            blank = False
        else:
            blank = True
        offset += len(raw) + 1
    return lines


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
    def __init__(self, text: str, hints: dict[int, int]) -> None:
        self.text = text
        self.hints = hints
        self.fragments: list[Fragment] = []
        self.section = ""
        self.path = ""
        self.stack: list[tuple[int, str]] = []
        self.counters: list[int] = []
        self.last_level = 0

    def run(self) -> list[Fragment]:
        records = self._classify(_logical_lines(self.text, self.hints))
        context = ""
        for index, record in enumerate(records):
            line = record.line
            if record.kind == "heading":
                context = ""
                self._heading(record)
            elif record.kind == "list":
                if line.blank_before:
                    context = ""
                self._emit("list_item", self.section, context, line)
            else:
                following = records[index + 1] if index + 1 < len(records) else None
                if (
                    line.text.endswith(":")
                    and following
                    and following.kind == "list"
                    and not following.line.blank_before
                ):
                    context = line.text
                    continue
                context = ""
                self._emit("paragraph", record.section or self.section, "", line)
        return self.fragments

    def _classify(self, lines: list[_Line]) -> list[_Record]:
        records: list[_Record] = []
        previous_number: int | None = None
        index = 0
        while index < len(lines):
            line = lines[index]
            following = lines[index + 1] if index + 1 < len(lines) else None
            index += 1
            text = line.text
            hint = self.hints.get(line.start) or self.hints.get(line.begin)
            attached = following is not None and not following.blank_before
            underline = _UNDERLINE.match(text)
            if hint:
                head = self._explicit_head(text, min(max(hint, 1), 6))
            elif underline:
                continue
            elif (
                attached
                and following is not None
                and _UNDERLINE.match(following.text)
                and "\n" not in text
                and not _LIST_MARKER.match(text)
                and not text.startswith("#")
            ):
                head = self._explicit_head(text, 1 if following.text[0] == "=" else 2)
                index += 1
            else:
                head = _head_of(text)
            number = _LIST_NUMBER.match(text)
            if head and head.form in ("single",):
                value = int(head.number)
                if (
                    following is None
                    or re.match(r"^\d{1,2}[.)]\s", following.text)
                    or previous_number == value - 1
                ):
                    head = None
            if head:
                records.append(_Record("heading", line, head))
                previous_number = None
                continue
            prefix = _prefix(text)
            if prefix and prefix.form == "multi" and text[prefix.body :][:1].isupper():
                records.append(_Record("paragraph", line, section=prefix.number))
                previous_number = None
            elif _LIST_MARKER.match(text):
                records.append(_Record("list", line))
                previous_number = int(number.group(1)) if number else None
            elif self._standalone(line, following):
                records.append(
                    _Record("heading", line, _Head(None, "", None, 0, len(text), "plain"))
                )
                previous_number = None
            else:
                records.append(_Record("paragraph", line))
                previous_number = None
        return records

    def _explicit_head(self, text: str, level: int) -> _Head:
        if match := _MD_HEADING.match(text):
            head = _head_of(text)
            if head:
                return head._replace(level=level)
            return _Head(level, "", None, len(match.group(1)), len(text), "md")
        number = _LEADING_NUMBER.match(text)
        resync = [int(p) for p in number.group(1).split(".")] if number else None
        return _Head(level, number.group(1) if number else "", resync, 0, len(text), "hint")

    def _standalone(self, line: _Line, following: _Line | None) -> bool:
        if not line.blank_before or following is None or not _looks_like_heading(line.text):
            return False
        if not following.blank_before and _LIST_MARKER.match(following.text):
            return False
        if {following.start, following.begin} & self.hints.keys():
            return False
        return _head_of(following.text) is None

    def _heading(self, record: _Record) -> None:
        line, head = record.line, record.head
        assert head is not None
        start, end = line.start + head.shift, line.start + head.end
        title = self.text[start:end]
        level = head.level or self.last_level or 1
        number = head.number
        if number:
            if head.resync is not None:
                self.counters = list(head.resync)
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
        self.last_level = level
        self.path = PATH_SEPARATOR.join(t for _, t in self.stack)

    def _emit(self, kind: str, section: str, context: str, line: _Line) -> None:
        for part, begin, finish in _split_long(line.text, line.start):
            self.fragments.append(Fragment(kind, section, self.path, context, part, begin, finish))


def split(text: str, heading_hints: dict[int, int] | None = None) -> list[Fragment]:
    return _Splitter(text, heading_hints or {}).run()
