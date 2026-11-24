from app.modules.analysis.splitter import MAX_FRAGMENT_CHARS, normalize, split

MIXED = """# Требования к системе

Система предназначена для учёта задач.

## 1.1 Роли
Доступны роли:
- администратор
  с полным доступом;
- наблюдатель.

2 Интеграции
Поддерживаются варианты:
1. почта
2) чат
Без вводной строки.

3. Отчёты

### Формат
Отчёты выгружаются в PDF. Дата указывается в шапке.
"""


def test_markdown_headings_generate_hierarchical_numbers():
    fragments = split(normalize("# A\n\n## B\n\n## C\n\n# D\n\n### E"))
    assert [(f.kind, f.section, f.text) for f in fragments] == [
        ("heading", "1", "A"),
        ("heading", "1.1", "B"),
        ("heading", "1.2", "C"),
        ("heading", "2", "D"),
        ("heading", "2.1.1", "E"),
    ]


def test_markdown_heading_offsets_skip_hashes_and_numbers_are_kept():
    text = normalize("## 3.2 Безопасность\n\nТекст.")
    heading, paragraph = split(text)
    assert (heading.section, heading.text) == ("3.2", "3.2 Безопасность")
    assert text[heading.start : heading.end] == "3.2 Безопасность"
    assert (paragraph.section, paragraph.heading_path) == ("3.2", "3.2 Безопасность")


def test_numbered_single_line_is_heading_but_multiline_block_is_list():
    text = normalize("2.1 Авторизация\n\n1. Войти\n2. Выйти\n\n3. Завершить работу.")
    fragments = split(text)
    assert [(f.kind, f.text) for f in fragments] == [
        ("heading", "2.1 Авторизация"),
        ("list_item", "1. Войти"),
        ("list_item", "2. Выйти"),
        ("list_item", "3. Завершить работу."),
    ]
    assert fragments[0].section == "2.1"


def test_intro_line_goes_to_context_and_is_not_a_fragment():
    fragments = split(normalize("Система должна:\n- хранить данные\n- быстро работать"))
    assert [f.kind for f in fragments] == ["list_item", "list_item"]
    assert all(f.context == "Система должна:" for f in fragments)


def test_intro_without_colon_is_paragraph():
    fragments = split(normalize("Система умеет многое\n- хранить данные"))
    assert [(f.kind, f.context) for f in fragments] == [("paragraph", ""), ("list_item", "")]


def test_list_item_continuation_is_part_of_item():
    text = normalize("Требования:\n- первый пункт\n  продолжение\n- второй")
    first, second = split(text)
    assert first.text == "- первый пункт\n  продолжение"
    assert text[first.start : first.end] == first.text
    assert second.text == "- второй"


def test_long_paragraph_is_split_by_sentences():
    sentence = "Это предложение средней длины для проверки деления текста. "
    text = normalize(sentence * 60)
    fragments = split(text)
    assert len(fragments) > 1
    assert all(f.kind == "paragraph" and len(f.text) <= MAX_FRAGMENT_CHARS for f in fragments)
    assert all(f.text.endswith(".") for f in fragments)


def test_overlong_sentence_is_cut_at_spaces():
    text = normalize("слово " * 500)
    fragments = split(text)
    assert len(fragments) > 1
    assert all(len(f.text) <= MAX_FRAGMENT_CHARS for f in fragments)
    assert " ".join(f.text for f in fragments) == text


def test_normalize():
    assert normalize("\n\n  a\tb  \r\nc\rd\n\n  \n") == "  a b\nc\nd"
    assert normalize("é") == "é"


def test_offsets_invariant_on_mixed_document():
    text = normalize(MIXED.replace("\n", "\r\n").replace("  с полным", "\t с полным"))
    fragments = split(text)
    assert len(fragments) > 8
    for f in fragments:
        assert text[f.start : f.end] == f.text
        assert f.text == f.text.strip()
    kinds = [f.kind for f in fragments]
    assert {"heading", "paragraph", "list_item"} <= set(kinds)


def test_section_and_path_of_paragraphs():
    fragments = split(normalize(MIXED))
    intro = next(f for f in fragments if f.text.startswith("Система предназначена"))
    assert (intro.section, intro.heading_path) == ("1", "Требования к системе")
    formats = next(f for f in fragments if f.text.startswith("Отчёты выгружаются"))
    assert formats.section == "3.1.1"
    assert formats.heading_path.endswith("Формат")
    roles = next(f for f in fragments if f.text.startswith("- администратор"))
    assert roles.section == "1.1"
    assert roles.heading_path == "Требования к системе → 1.1 Роли"
    heading_roles = next(f for f in fragments if f.text == "1.1 Роли")
    assert heading_roles.heading_path == "Требования к системе"


def test_text_before_first_heading_has_empty_section():
    first = split(normalize("Вступление.\n\n# Раздел"))[0]
    assert (first.section, first.heading_path) == ("", "")
