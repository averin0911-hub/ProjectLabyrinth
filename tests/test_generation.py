"""Проверки случайного генератора лабиринтов."""

import random

import pytest

from core.maze import generate_maze


@pytest.mark.parametrize("width, height", [(5, 5), (6, 6), (9, 9), (10, 10), (5, 8), (8, 5)])
def test_generated_size(width, height):
    """Генератор соблюдает размеры, длины строк и допустимые значения клеток."""
    maze = generate_maze(width, height, seed=42)

    assert maze.rows == height
    assert maze.cols == width
    assert all(len(row) == width for row in maze.grid)
    assert all(cell in (0, 1, 2, 3) for row in maze.grid for cell in row)


@pytest.mark.parametrize("width, height", [(4, 5), (5, 4), (0, 0), (-1, 10)])
def test_too_small_size_is_rejected(width, height):
    """Если ширина или высота меньше 5, ожидаем ValueError с пояснением."""
    with pytest.raises(ValueError, match="не меньше 5"):
        generate_maze(width, height)


@pytest.mark.parametrize("seed", [0, 1, 42])
def test_outer_border_is_closed(seed):
    """Все четыре внешние стороны сгенерированного поля состоят из стен."""
    maze = generate_maze(10, 8, seed=seed)

    assert all(cell == 1 for cell in maze.grid[0])
    assert all(cell == 1 for cell in maze.grid[-1])
    assert all(row[0] == 1 and row[-1] == 1 for row in maze.grid)


def test_exactly_one_start_and_exit():
    """На поле ровно один старт и выход; их координаты различны и верны."""
    maze = generate_maze(10, 10, seed=42)
    cells = [cell for row in maze.grid for cell in row]

    assert cells.count(2) == 1
    assert cells.count(3) == 1
    assert maze.start != maze.end
    assert maze[maze.start] == 2
    assert maze[maze.end] == 3


@pytest.mark.parametrize("width, height", [(5, 5), (6, 6), (9, 9), (10, 8), (8, 10)])
def test_all_passages_are_connected(width, height):
    """От старта можно дойти до каждого прохода, включая выход."""
    maze = generate_maze(width, height, seed=42)

    # Обходим проходы самостоятельно, не используя проверяемые алгоритмы.
    reached = {maze.start}
    pending = [maze.start]
    while pending:
        row, col = pending.pop()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < height and 0 <= nc < width:
                if maze.grid[nr][nc] != 1 and (nr, nc) not in reached:
                    reached.add((nr, nc))
                    pending.append((nr, nc))

    passages = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if maze.grid[row][col] != 1
    }
    assert reached == passages
    assert maze.end in reached


def test_same_seed_does_not_depend_on_global_random(monkeypatch):
    """Один seed должен дать одно поле при разных ответах глобального random."""
    # Принудительно меняем ответы глобального random.
    # При собственном rng с одинаковым seed результат должен остаться тем же.
    monkeypatch.setattr(random, "randint", lambda a, b: 0)
    first = generate_maze(10, 10, seed=42)

    monkeypatch.setattr(random, "randint", lambda a, b: 1)
    second = generate_maze(10, 10, seed=42)

    assert first.grid == second.grid
    assert first.start == second.start
    assert first.end == second.end
