import re
import textwrap
from pathlib import Path

import pytest

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


def _view(text, hints=None):
    text = normalize(text)
    fragments = split(text, hints)
    for f in fragments:
        assert text[f.start : f.end] == f.text
        assert f.text == f.text.strip()
    return fragments


def _kinds(text, hints=None):
    return [(f.kind, f.text) for f in _view(text, hints)]


def test_number_led_paragraph_without_dot_is_not_heading():
    assert _kinds("2024 год был успешным") == [("paragraph", "2024 год был успешным")]
    assert _kinds("Вступление.\n\n100 пользователей должны работать одновременно") == [
        ("paragraph", "Вступление."),
        ("paragraph", "100 пользователей должны работать одновременно"),
    ]
    assert _kinds("Итоги.\n\n10 пользователей онлайн\n\nКонец.")[1][0] == "paragraph"


def test_word_paste_without_blank_lines():
    text = (
        "1. Общие положения\nНастоящий документ определяет требования.\n"
        "1.1 Назначение\nСистема предназначена для учёта задач.\nОна проста в работе."
    )
    fragments = _view(text)
    assert [(f.kind, f.section, f.text) for f in fragments] == [
        ("heading", "1", "1. Общие положения"),
        ("paragraph", "1", "Настоящий документ определяет требования."),
        ("heading", "1.1", "1.1 Назначение"),
        ("paragraph", "1.1", "Система предназначена для учёта задач."),
        ("paragraph", "1.1", "Она проста в работе."),
    ]


def test_numbered_requirement_keeps_own_section_and_is_paragraph():
    fragments = _view("4. Требования\n4.1.2 Система должна хранить данные.\nПоясняющий текст.")
    assert [(f.kind, f.section) for f in fragments] == [
        ("heading", "4"),
        ("paragraph", "4.1.2"),
        ("paragraph", "4"),
    ]
    assert fragments[1].text == "4.1.2 Система должна хранить данные."


def test_decimal_number_in_prose_is_plain_paragraph():
    fragment = _view("Раздел\n\n1.5 млн рублей выделено на проект.")[1]
    assert (fragment.kind, fragment.section) == ("paragraph", "1")


def test_caps_and_named_and_roman_headings():
    text = (
        "ОБЩИЕ ПОЛОЖЕНИЯ\nТекст один.\n"
        "Раздел 3. Интеграции\nТекст два.\n"
        "Глава 2\nТекст три.\n"
        "Приложение Б\nТекст четыре.\n"
        "IV. Архитектура\nТекст пять."
    )
    heads = [(f.section, f.text) for f in _view(text) if f.kind == "heading"]
    assert heads == [
        ("1", "ОБЩИЕ ПОЛОЖЕНИЯ"),
        ("3", "Раздел 3. Интеграции"),
        ("2", "Глава 2"),
        ("ПБ", "Приложение Б"),
        ("IV", "IV. Архитектура"),
    ]


def test_sentence_starting_with_section_word_is_paragraph():
    assert _kinds("Раздел 5 описывает интеграции с другими системами") == [
        ("paragraph", "Раздел 5 описывает интеграции с другими системами")
    ]


def test_bold_line_is_heading_with_offsets_without_stars():
    text = normalize("# Документ\n\n**Роли**\n\nТекст.")
    fragments = split(text)
    bold = fragments[1]
    assert (bold.kind, bold.text, bold.section) == ("heading", "Роли", "2")
    assert text[bold.start : bold.end] == "Роли"
    assert _kinds("**Система должна работать быстро**\n\nТекст.")[0][0] == "paragraph"


def test_setext_headings_and_underline_is_not_a_fragment():
    fragments = _view("Заголовок\n=====\n\nТекст.\n\nПодраздел\n-----\n\nЕщё текст.")
    assert [(f.kind, f.section, f.text) for f in fragments] == [
        ("heading", "1", "Заголовок"),
        ("paragraph", "1", "Текст."),
        ("heading", "1.1", "Подраздел"),
        ("paragraph", "1.1", "Ещё текст."),
    ]


def test_typical_section_names_without_number():
    text = "Введение\nТекст.\nТермины и определения\nСлово — значение.\nТребования к приёмке\nЕщё."
    heads = [f.text for f in _view(text) if f.kind == "heading"]
    assert heads == ["Введение", "Термины и определения", "Требования к приёмке"]


def test_standalone_short_line_is_heading_only_between_blank_and_content():
    fragments = _view("Вступление.\n\nКонтекст проекта\n\nЗдесь живёт описание.\n\nКонец")
    assert [(f.kind, f.text) for f in fragments] == [
        ("paragraph", "Вступление."),
        ("heading", "Контекст проекта"),
        ("paragraph", "Здесь живёт описание."),
        ("paragraph", "Конец"),
    ]


def test_short_numbered_sequence_is_list_not_headings():
    assert _kinds("Шаги:\n1. Вход\n2. Выход\n3. Профиль\nДальше обычный текст.") == [
        ("list_item", "1. Вход"),
        ("list_item", "2. Выход"),
        ("list_item", "3. Профиль"),
        ("paragraph", "Дальше обычный текст."),
    ]


def test_hard_wrapped_lines_are_joined_but_not_across_sentences():
    text = "Первое предложение закончено.\nВторая строка\nпродолжается здесь.\n\nАбзац\nдва."
    assert _kinds(text) == [
        ("paragraph", "Первое предложение закончено."),
        ("paragraph", "Вторая строка\nпродолжается здесь."),
        ("paragraph", "Абзац\nдва."),
    ]


def test_heading_hints_override_classification():
    text = "Обычная строка без признаков\nТекст под ней.\nЕщё одна строка\nТекст."
    hints = {0: 1, text.index("Ещё одна"): 2}
    fragments = _view(text, hints)
    assert [(f.kind, f.section, f.text) for f in fragments] == [
        ("heading", "1", "Обычная строка без признаков"),
        ("paragraph", "1", "Текст под ней."),
        ("heading", "1.1", "Ещё одна строка"),
        ("paragraph", "1.1", "Текст."),
    ]


def test_hinted_numbered_line_keeps_number():
    text = "Текст.\n3.2 Безопасность\nАбзац."
    fragments = _view(text, {text.index("3.2"): 2})
    assert (fragments[1].kind, fragments[1].section) == ("heading", "3.2")


def test_long_list_item_is_split_and_keeps_kind_and_context():
    sentence = "Это предложение средней длины для проверки деления текста. "
    fragments = _view("Требования:\n- " + sentence * 60)
    assert len(fragments) > 1
    assert all(f.kind == "list_item" and f.context == "Требования:" for f in fragments)
    assert all(len(f.text) <= MAX_FRAGMENT_CHARS for f in fragments)


SPECS = Path(__file__).parent / "specs"
REQUIREMENT = re.compile(r"\b(?:должен|должна|должно|должны|необходимо|обязан|обязана)\b", re.I)

EXPECTED_HEADINGS = {
    "gost_plain.txt": [
        ("1", "1. Общие сведения"),
        ("1.1", "1.1 Полное наименование системы"),
        ("1.2", "1.2 Заказчик и исполнитель"),
        ("1.3", "1.3 Основания для разработки"),
        ("2", "2. Назначение и цели создания системы"),
        ("3", "3. Характеристика объекта автоматизации"),
        ("4", "4. Требования к системе"),
        ("4.1", "4.1 Требования к функциям"),
        ("4.2", "4.2 Требования к надёжности"),
        ("4.3", "4.3 Требования к безопасности"),
        ("5", "5. Порядок контроля и приёмки"),
        ("ПА", "Приложение А"),
    ],
    "agile.md": [
        ("1", "Планировщик спринтов"),
        ("1.1", "Цели продукта"),
        ("1.2", "Роли пользователей"),
        ("1.3", "Модель доступа"),
        ("2", "Обзор"),
        ("2.1.1", "Создание задачи"),
        ("2.2", "Отчёты"),
    ],
    "caps_email.txt": [
        ("1", "ОБЩИЕ ПОЛОЖЕНИЯ"),
        ("2", "ФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ"),
        ("3", "ТРЕБОВАНИЯ К БЕЗОПАСНОСТИ"),
        ("4", "СРОКИ"),
    ],
    "mixed_traps.txt": [
        ("1", "Раздел 1. Введение"),
        ("2", "Раздел 2. Интеграции"),
        ("II", "II. Архитектура"),
        ("ПБ", "Приложение Б. Список сокращений"),
    ],
    "no_headings.txt": [],
}


def _load(name):
    text = normalize((SPECS / name).read_text(encoding="utf-8"))
    return text, split(text)


@pytest.mark.parametrize("name", sorted(EXPECTED_HEADINGS))
def test_spec_samples_headings_offsets_and_requirements(name):
    text, fragments = _load(name)
    headings = [(f.section, f.text) for f in fragments if f.kind == "heading"]
    assert headings == EXPECTED_HEADINGS[name]
    for f in fragments:
        assert text[f.start : f.end] == f.text
        assert f.text == f.text.strip()
        assert len(f.text) <= MAX_FRAGMENT_CHARS
    content = " ".join(f.text for f in fragments if f.kind != "heading")
    assert not any(REQUIREMENT.search(f.text) for f in fragments if f.kind == "heading")
    assert len(REQUIREMENT.findall(content)) == len(REQUIREMENT.findall(text))


def test_spec_gost_plain_numbered_requirements_and_paragraphs():
    _, fragments = _load("gost_plain.txt")
    items = [(f.section, f.text[:5].strip()) for f in fragments if f.section.startswith("4.1.")]
    assert items == [
        ("4.1.1", "4.1.1"),
        ("4.1.2", "4.1.2"),
        ("4.1.3", "4.1.3"),
    ]
    assert all(f.kind == "paragraph" for f in fragments if f.section.startswith("4.1."))
    appendix = [f for f in fragments if f.section == "ПА"]
    assert [f.kind for f in appendix] == ["heading", "paragraph"]


def test_spec_agile_lists_have_context():
    _, fragments = _load("agile.md")
    items = [f for f in fragments if f.kind == "list_item"]
    assert [(f.section, f.context) for f in items] == [
        ("1.1", "Нужно решить три задачи:"),
        ("1.1", "Нужно решить три задачи:"),
        ("1.1", "Нужно решить три задачи:"),
        ("2.1.1", "Поддерживаются поля:"),
        ("2.1.1", "Поддерживаются поля:"),
        ("2.1.1", "Поддерживаются поля:"),
    ]
    assert not any(f.text.startswith(("===", "---", "**")) for f in fragments)


def test_spec_caps_email_wrapped_paragraphs_are_whole():
    _, fragments = _load("caps_email.txt")
    wrapped = next(f for f in fragments if f.text.startswith("Портал предназначен"))
    assert wrapped.text.endswith("организаций.")
    assert "\n" in wrapped.text
    assert sum(f.kind == "paragraph" for f in fragments) == 6


def test_spec_mixed_traps():
    _, fragments = _load("mixed_traps.txt")
    by_text = {f.text: f for f in fragments}
    assert (
        by_text["2024 год был успешным для компании, и объёмы заказов выросли."].kind == "paragraph"
    )
    assert by_text["100 пользователей должны работать одновременно без потери скорости."].kind == (
        "paragraph"
    )
    items = [f for f in fragments if f.kind == "list_item"]
    assert [f.text for f in items] == ["1. Вход", "2. Выход", "3. Профиль"]
    assert {f.context for f in items} == {"Основные сценарии работы пользователя:"}
    assert not any(f.text.endswith(":") for f in fragments)


def test_spec_no_headings():
    _, fragments = _load("no_headings.txt")
    assert {f.kind for f in fragments} == {"paragraph", "list_item"}
    assert {f.section for f in fragments} == {""}
    assert {f.heading_path for f in fragments} == {""}


def _wrap(text, width=70):
    return "\n".join(textwrap.wrap(text, width, break_long_words=False))


def _paragraphs(fragments):
    return [f for f in fragments if f.kind == "paragraph"]


def test_hard_wrap_joins_lines_before_capital_or_digit():
    sources = [
        "Обмен данными с внешней бухгалтерской системой выполняется по протоколу "
        "HTTPS каждые пятнадцать минут. Если связь недоступна, сервис повторяет "
        "Запрос через равные промежутки времени до успешной передачи данных.",
        "Максимальный размер загружаемого файла ограничен значением не более "
        "20 мегабайт на один документ, а общий объём архива одного клиента "
        "ограничен ста гигабайтами.",
        "Отчёты формируются по запросу пользователя и доступны для скачивания в "
        "течение тридцати дней. API отчётов доступен только авторизованным "
        "сотрудникам отдела аналитики компании.",
    ]
    first = "Система должна принимать документы в формате\nPDF или DOCX и сохранять их в архиве."
    text = normalize("\n\n".join([first, *(_wrap(s, 46) for s in sources)]) + "\n")
    fragments = split(text)
    paragraphs = _paragraphs(fragments)
    assert len(paragraphs) == 4
    assert paragraphs[0].text == first
    assert all(p.text.endswith(".") for p in paragraphs)
    for fragment in fragments:
        assert text[fragment.start : fragment.end] == fragment.text


def test_hard_wrap_at_seventy_chars_joins_lines_before_capital_or_digit():
    text = normalize(
        "Система должна принимать документы в формате PDF или DOCX и сохранять\n"
        "Их в архиве. Размер файла не более двадцати мегабайт на один документ,\n"
        "20 мегабайт для вложений и сто мегабайт для архивов.\n"
        "\n"
        "Обмен данными с внешней системой выполняется по протоколу HTTPS каждые\n"
        "Пятнадцать минут. Если связь недоступна, сервис повторяет запрос через\n"
        "равные промежутки времени до успешной передачи данных.\n"
        "\n"
        "Отчёты формируются по запросу пользователя и доступны для скачивания\n"
        "API отчётов доступен только авторизованным сотрудникам отдела\n"
        "аналитики компании в течение тридцати дней.\n"
    )
    fragments = split(text)
    assert len(_paragraphs(fragments)) == 3
    for fragment in fragments:
        assert text[fragment.start : fragment.end] == fragment.text


def test_word_paste_without_wrap_is_not_glued():
    text = normalize(
        "Система должна принимать документы в формате PDF и DOCX и хранить их.\n"
        "Пользователь может искать документы по названию и дате загрузки в архиве.\n"
        "Администратор управляет ролями и правами доступа сотрудников компании.\n"
        "Отчёт формируется автоматически каждый месяц и отправляется руководителю.\n"
        "Срок хранения документов составляет пять лет с момента их загрузки.\n"
    )
    fragments = split(text)
    assert [f.text for f in _paragraphs(fragments)] == text.split("\n")


def test_short_line_without_period_before_paragraph_is_not_glued():
    text = normalize(
        "Модуль отчётов\n"
        + _wrap(
            "Система формирует отчёты по задачам за выбранный период и позволяет "
            "выгрузить их в файл. Каждый отчёт содержит сводку по исполнителям."
        )
        + "\n\n"
        + _wrap(
            "Пользователь выбирает период и тип отчёта на отдельной странице модуля, "
            "после чего система строит таблицу. Результат можно сохранить."
        )
        + "\n"
    )
    fragments = split(text)
    texts = [f.text for f in _paragraphs(fragments)] + [
        f.text for f in fragments if f.kind == "heading"
    ]
    assert "Модуль отчётов" in texts
    assert not any(t.startswith("Модуль отчётов\n") for t in texts)
    for fragment in fragments:
        assert text[fragment.start : fragment.end] == fragment.text
