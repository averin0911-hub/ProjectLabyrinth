"""Проверки консоли без ручного ввода и без настоящего ожидания."""

import pytest

import main as app
from core.maze import Maze


@pytest.mark.parametrize("text, expected", [
    ("", 10), ("  ", 10), ("5", 5), (" 12 ", 12),
    (str(app.MAX_SIZE), app.MAX_SIZE),
])
def test_read_size(monkeypatch, text, expected):
    """Введённое число принимается; Enter и пробелы дают размер по умолчанию 10."""
    # monkeypatch временно заменяет input; после теста замена отменяется.
    monkeypatch.setattr("builtins.input", lambda prompt: text)

    assert app.read_size("Ширина") == expected


@pytest.mark.parametrize("bad_value", ["abc", "3.5", "-1", "4", str(app.MAX_SIZE + 1)])
def test_read_size_retries_after_bad_input(monkeypatch, capsys, bad_value):
    """После неверного ответа функция печатает подсказку и принимает следующий: 8."""
    answers = iter([bad_value, "8"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    assert app.read_size("Ширина") == 8
    # capsys позволяет проверить текст, который функция напечатала.
    assert "от 5 до" in capsys.readouterr().out


def test_show_maze_preserves_grid_and_draws_symbols(capsys):
    """Проверяем символы, их приоритет и размеры в выводе; матрица не меняется."""
    maze = Maze([[2, 0, 3], [1, 0, 0]], end=(0, 2))
    before = [row[:] for row in maze.grid]

    app.show_maze(
        maze,
        path=[(0, 0), (0, 1), (0, 2), (1, 0)],
        visited=[(0, 0), (0, 1), (0, 2), (1, 1)],
    )

    output = capsys.readouterr().out
    assert "S 0 E\n# .  \n" in output
    assert "3 × 2" in output
    assert maze.grid == before


def test_measure_algorithm_converts_seconds_to_milliseconds(monkeypatch):
    """Один вызов алгоритма, тот же результат; 0,125 секунды превращаются в 125 мс."""
    maze = Maze([[2, 3]])
    times = iter([10.0, 10.125])
    calls = []
    expected = {"distance": 1}

    def fake_algorithm(received_maze):
        calls.append(received_maze)
        return expected

    monkeypatch.setattr(app, "perf_counter", lambda: next(times))

    result, elapsed = app.measure_algorithm(maze, fake_algorithm)

    assert result is expected
    assert elapsed == 125
    assert calls == [maze]


def test_run_algorithm_prints_result_after_measurement(monkeypatch, capsys):
    """BFS даёт один шаг; показ поля идёт после замера, показатели печатаются."""
    maze = Maze([[2, 3]], end=(0, 1))
    times = iter([10.0, 10.125])
    events = []

    def fake_clock():
        events.append("clock")
        return next(times)

    def fake_show(*args):
        events.append("show")

    monkeypatch.setattr(app, "perf_counter", fake_clock)
    monkeypatch.setattr(app, "show_maze", fake_show)

    result, elapsed = app.run_algorithm(maze, "BFS", app.bfs)

    assert result["distance"] == 1
    assert elapsed == 125
    assert events == ["clock", "clock", "show"]
    output = capsys.readouterr().out
    assert "Длина пути: 1 шагов" in output
    assert "Количество обработанных клеток: 2" in output
    assert "125.000 мс" in output


def test_run_algorithm_handles_no_path(capsys):
    """При отсутствии пути печатается сообщение, а функция возвращает None."""
    result = app.run_algorithm(Maze([[2, 1, 3]]), "BFS", app.bfs)

    assert result is None
    assert "BFS: Путь до выхода не существует" in capsys.readouterr().out


def test_compare_calls_each_algorithm_once_on_same_maze(monkeypatch, capsys):
    """Четыре замера на одном поле; таблица содержит подставленные показатели."""
    maze = Maze([[2, 3]])
    calls = []

    def fake_measure(received_maze, algorithm):
        calls.append((received_maze, algorithm))
        return {"distance": 12, "visited_count": 23}, 34.5

    monkeypatch.setattr(app, "measure_algorithm", fake_measure)

    app.compare_algorithms(maze)

    assert calls == [
        (maze, app.bfs), (maze, app.bidirectional_bfs),
        (maze, app.dijkstra), (maze, app.A_star),
    ]
    output = capsys.readouterr().out
    assert "Всего клеток: 2; проходимых: 2" in output
    for name in ["BFS", "Двунаправленный BFS", "Дейкстра", "A*"]:
        rows = [line for line in output.splitlines() if line.startswith(name + " ")]
        assert len(rows) == 1
        assert rows[0].split()[-3:] == ["12", "23", "34.500"]


def test_compare_handles_no_path(capsys):
    """Сравнение перехватывает ошибку BFS и печатает сообщение об отсутствии пути."""
    app.compare_algorithms(Maze([[2, 1, 3]]))

    assert "BFS: Путь до выхода не существует" in capsys.readouterr().out


@pytest.mark.parametrize("choice, name, algorithm", [
    ("1", "BFS", app.bfs),
    ("2", "Двунаправленный BFS", app.bidirectional_bfs),
    ("3", "Дейкстра", app.dijkstra),
    ("4", "A*", app.A_star),
])
def test_menu_starts_selected_algorithm(monkeypatch, choice, name, algorithm):
    """Пункты 1–4 вызывают нужный алгоритм один раз с текущим лабиринтом."""
    maze = Maze([[2, 3]])
    answers = iter([choice, "0"])
    calls = []
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.setattr(app, "generate_maze", lambda width, height: maze)
    monkeypatch.setattr(app, "run_algorithm", lambda *args: calls.append(args))

    app.main()

    assert calls == [(maze, name, algorithm)]


def test_menu_generates_shows_and_compares_maze(monkeypatch):
    """Меню создаёт поле 8×6; последующие показ и сравнение используют новое поле."""
    first = Maze([[2, 3]])
    second = Maze([[2, 0, 3]])
    answers = iter(["5", "8", "6", "6", "7", "0"])
    generated = []
    shown = []
    compared = []

    def fake_generate(width, height):
        generated.append((width, height))
        return first if len(generated) == 1 else second

    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.setattr(app, "generate_maze", fake_generate)
    monkeypatch.setattr(app, "show_maze", lambda maze: shown.append(maze))
    monkeypatch.setattr(app, "compare_algorithms", lambda maze: compared.append(maze))

    app.main()

    assert generated == [(10, 10), (8, 6)]
    assert shown == [first, second, second]
    assert compared == [second]


def test_menu_handles_unknown_choice_and_exits(monkeypatch, capsys):
    """Неизвестный пункт даёт подсказку, затем пункт 0 завершает программу."""
    answers = iter(["unknown", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.setattr(app, "generate_maze", lambda w, h: Maze([[2, 3]]))

    app.main()

    output = capsys.readouterr().out
    assert "Неизвестный пункт меню" in output
    assert "Программа завершена." in output


@pytest.mark.parametrize("error", [EOFError, KeyboardInterrupt])
def test_menu_exits_on_interruption(monkeypatch, capsys, error):
    """EOF и Ctrl+C при вводе пункта меню приводят к обычному сообщению о выходе."""
    def interrupted_input(prompt):
        raise error()

    monkeypatch.setattr("builtins.input", interrupted_input)
    monkeypatch.setattr(app, "generate_maze", lambda w, h: Maze([[2, 3]]))

    app.main()

    assert "Программа завершена." in capsys.readouterr().out
