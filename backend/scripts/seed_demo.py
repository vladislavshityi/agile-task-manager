"""Fill a running instance with demo data through the public API.

    uv run python scripts/seed_demo.py [--api http://localhost:8000/api]

Creates five demo accounts (one per role) sharing the workspace «Команда Альфа»,
two boards with labelled, assigned and commented tasks, and a wiki tree.
Safe to re-run: if the demo owner already exists, nothing is changed.
"""

import argparse
import sys
from datetime import date, timedelta

import httpx

PASSWORD = "demo12345"

# email, full name, role in the demo workspace
ACCOUNTS = [
    ("anna@example.com", "Анна Петрова", "owner"),
    ("ivan@example.com", "Иван Смирнов", "admin"),
    ("maria@example.com", "Мария Кузнецова", "member"),
    ("oleg@example.com", "Олег Волков", "member"),
    ("olga@example.com", "Ольга Новикова", "viewer"),
]

LABELS = [
    ("bug", "#FF3B30"),
    ("фича", "#34C759"),
    ("бэкенд", "#007AFF"),
    ("фронтенд", "#AF52DE"),
    ("дизайн", "#FF9500"),
    ("документация", "#8E8E93"),
]

# Board -> columns (name, color) -> tasks:
# (title, description, priority, due in days or None, assignees, labels, comments)
BOARDS = {
    ("Разработка MVP", "Спринт 14: личный кабинет и уведомления"): [
        (
            ("Бэклог", "#8E8E93"),
            [
                (
                    "Экспорт задач в CSV",
                    "Выгрузка задач доски с фильтрами.",
                    "low",
                    14,
                    ["oleg"],
                    ["фича", "бэкенд"],
                    [],
                ),
                ("Тёмная тема для писем", "", "low", None, [], ["дизайн"], []),
                (
                    "Интеграция с Telegram",
                    "Уведомления о назначении и сроках в Telegram-бот.",
                    "medium",
                    21,
                    ["ivan"],
                    ["фича", "бэкенд"],
                    [("ivan", "Нужен отдельный токен бота на стенд, запрошу у DevOps.")],
                ),
            ],
        ),
        (
            ("В работе", "#007AFF"),
            [
                (
                    "Страница профиля",
                    "Аватар, имя, смена пароля.\n\n- [x] Вёрстка\n- [ ] API",
                    "high",
                    2,
                    ["maria"],
                    ["фронтенд"],
                    [
                        ("anna", "Макеты в Figma обновлены, смотри вкладку v2."),
                        ("maria", "Взяла, к среде будет на ревью."),
                    ],
                ),
                (
                    "Падает сохранение фильтров",
                    "Шаги: открыть доску → фильтр по метке → F5.",
                    "urgent",
                    -1,
                    ["oleg"],
                    ["bug", "фронтенд"],
                    [("oleg", "Воспроизвёл, проблема в сериализации URL.")],
                ),
                ("Rate limit для API", "", "medium", 5, ["ivan"], ["бэкенд"], []),
            ],
        ),
        (
            ("Ревью", "#FF9500"),
            [
                (
                    "Email-уведомления о дедлайнах",
                    "Ежедневный дайджест в 9:00 по времени пользователя.",
                    "high",
                    0,
                    ["ivan", "oleg"],
                    ["фича", "бэкенд"],
                    [("anna", "Проверь часовые пояса — у нас есть пользователи из Владивостока.")],
                ),
            ],
        ),
        (
            ("Готово", "#34C759"),
            [
                ("Регистрация по приглашению", "", "medium", -5, ["maria"], ["фича"], []),
                ("Ошибка 500 при пустом названии", "", "high", -3, ["oleg"], ["bug", "бэкенд"], []),
            ],
        ),
    ],
    ("Маркетинг запуска", "Подготовка публичного релиза"): [
        (
            ("Идеи", "#8E8E93"),
            [
                (
                    "Статья на Хабр",
                    "История о том, как мы перешли на канбан.",
                    "low",
                    30,
                    ["anna"],
                    ["документация"],
                    [],
                ),
            ],
        ),
        (
            ("В работе", "#007AFF"),
            [
                (
                    "Лендинг",
                    "Первый экран, тарифы, отзывы.",
                    "high",
                    7,
                    ["maria", "anna"],
                    ["дизайн", "фронтенд"],
                    [("maria", "Нужны скриншоты продукта в тёмной теме.")],
                ),
                ("Видео-демо на 2 минуты", "", "medium", 10, ["anna"], [], []),
            ],
        ),
        (
            ("Готово", "#34C759"),
            [
                ("Название и логотип", "", "medium", -10, ["anna"], ["дизайн"], []),
            ],
        ),
    ],
}

# (title, content, children)
WIKI = [
    (
        "Добро пожаловать",
        """# Команда Альфа

Здесь собрано всё, что нужно для работы: процессы, документация и полезные ссылки.

- **Новичкам** — начните с раздела «Онбординг»
- **Разработчикам** — «Техническая документация»
- Вопросы — в чат *#team-alpha*""",
        [],
    ),
    (
        "Онбординг",
        "Чек-лист первой недели нового сотрудника.",
        [
            (
                "Первый день",
                """## Первый день

- [x] Получить ноутбук
- [ ] Настроить почту и календарь
- [ ] Познакомиться с наставником
- [ ] Прочитать «Процессы»""",
                [],
            ),
            (
                "Доступы",
                """| Система | Кто выдаёт | Срок |
| --- | --- | --- |
| GitHub | Иван | 1 день |
| Figma | Анна | 1 день |
| Стенд | DevOps | 2 дня |""",
                [],
            ),
        ],
    ),
    (
        "Процессы",
        "Как мы работаем.",
        [
            (
                "Спринты",
                """## Спринты

Длительность — **2 недели**.

1. Планирование — понедельник, 11:00
2. Дейли — каждый день, 10:30, 15 минут
3. Демо и ретро — последняя пятница спринта""",
                [],
            ),
            (
                "Код-ревью",
                """## Правила код-ревью

- PR не больше 400 строк
- Минимум **один** апрув
- Автор сам мержит после апрува

> Ревью — это про код, а не про человека.""",
                [],
            ),
        ],
    ),
    (
        "Техническая документация",
        "Архитектура и запуск проекта.",
        [
            (
                "Архитектура",
                """## Стек

- Бэкенд: FastAPI, SQLAlchemy, PostgreSQL
- Фронтенд: React, TypeScript, shadcn/ui
- ИИ: Ollama, модель `qwen2.5:3b`""",
                [],
            ),
            (
                "Локальный запуск",
                """```bash
docker compose up -d db
cd backend && uv run uvicorn app.main:app --reload
cd frontend && npm run dev
```""",
                [],
            ),
        ],
    ),
]


class Api:
    def __init__(self, base_url: str) -> None:
        self.http = httpx.Client(base_url=base_url, timeout=30)
        self.tokens: dict[str, str] = {}
        self.ids: dict[str, str] = {}

    def call(self, method: str, path: str, who: str | None = None, **kwargs) -> dict | list | None:
        headers = {"Authorization": f"Bearer {self.tokens[who]}"} if who else {}
        response = self.http.request(method, path, headers=headers, **kwargs)
        if response.status_code >= 400:
            sys.exit(f"{method} {path} -> {response.status_code}: {response.text}")
        return response.json() if response.content else None

    def register(self, key: str, email: str, name: str) -> None:
        body = self.call(
            "POST",
            "/auth/register",
            json={"email": email, "password": PASSWORD, "full_name": name},
        )
        self.tokens[key] = body["access_token"]
        self.ids[key] = body["user"]["id"]


def seed(api: Api) -> None:
    for email, name, _ in ACCOUNTS:
        api.register(email.split("@")[0], email, name)

    workspace = api.call("GET", "/workspaces", "anna")[0]["id"]
    api.call("PATCH", f"/workspaces/{workspace}", "anna", json={"name": "Команда Альфа"})
    for email, _, role in ACCOUNTS[1:]:
        invite = api.call("POST", f"/workspaces/{workspace}/invites", "anna", json={"role": role})
        api.call("POST", f"/invites/{invite['token']}/accept", email.split("@")[0])

    labels = {
        name: api.call(
            "POST", f"/workspaces/{workspace}/labels", "anna", json={"name": name, "color": color}
        )["id"]
        for name, color in LABELS
    }

    today = date.today()
    for (board_name, description), columns in BOARDS.items():
        board = api.call(
            "POST",
            f"/workspaces/{workspace}/boards",
            "anna",
            json={"name": board_name, "description": description},
        )
        existing = [c["id"] for c in board["columns"]]
        for index, ((column_name, color), tasks) in enumerate(columns):
            if index < len(existing):
                column = existing[index]
                api.call(
                    "PATCH",
                    f"/columns/{column}",
                    "anna",
                    json={"name": column_name, "color": color},
                )
            else:
                column = api.call(
                    "POST",
                    f"/boards/{board['id']}/columns",
                    "anna",
                    json={"name": column_name, "color": color},
                )["id"]
            for title, text, priority, due, assignees, task_labels, comments in tasks:
                task = api.call(
                    "POST",
                    f"/columns/{column}/tasks",
                    "anna",
                    json={
                        "title": title,
                        "description": text,
                        "priority": priority,
                        "due_date": (today + timedelta(days=due)).isoformat()
                        if due is not None
                        else None,
                        "assignee_ids": [api.ids[a] for a in assignees],
                        "label_ids": [labels[label] for label in task_labels],
                    },
                )
                for author, body in comments:
                    api.call("POST", f"/tasks/{task['id']}/comments", author, json={"body": body})
        for column in existing[len(columns) :]:
            api.call("DELETE", f"/columns/{column}", "anna")

    def add_pages(pages: list, parent: str | None, author: str) -> None:
        for title, content, children in pages:
            page = api.call(
                "POST",
                f"/workspaces/{workspace}/wiki",
                author,
                json={"title": title, "content": content, "parent_id": parent},
            )
            add_pages(children, page["id"], "maria" if author == "anna" else "anna")

    add_pages(WIKI, None, "anna")

    # Ivan also gets a personal workspace of his own.
    personal = api.call("GET", "/workspaces", "ivan")
    own = next(w for w in personal if w["role"] == "owner")
    api.call(
        "PATCH", f"/workspaces/{own['id']}", "ivan", json={"name": "Личное пространство Ивана"}
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://localhost:8000/api")
    args = parser.parse_args()

    api = Api(args.api)
    owner_email = ACCOUNTS[0][0]
    probe = api.http.post("/auth/login", json={"email": owner_email, "password": PASSWORD})
    if probe.status_code == 200:
        print("Demo data already exists, nothing to do.")
        return

    seed(api)
    print(f"Done. Accounts (password: {PASSWORD}):")
    for email, name, role in ACCOUNTS:
        print(f"  {email:<20} {name:<18} {role}")


if __name__ == "__main__":
    main()
