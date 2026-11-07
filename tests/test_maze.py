"""Проверки модели: 0 — проход, 1 — стена, 2 — старт, 3 — выход."""

import pytest

from core.maze import Maze


def test_size_and_cell_access():
    """Поле 2×3: размеры верны, по координатам читаются стена и выход."""
    maze = Maze([[2, 1, 0], [0, 0, 3]])

    assert maze.rows == 2
    assert maze.cols == 3
    assert maze[0, 1] == 1
    assert maze[1, 2] == 3


@pytest.mark.parametrize("row, col, expected", [
    (0, 0, True), (1, 2, True),
    (-1, 0, False), (0, -1, False),
    (2, 0, False), (0, 3, False),
])
def test_bounds(row, col, expected):
    """Для каждой координаты проверяем: внутри она поля 2×3 или за границей."""
    maze = Maze([[0, 0, 0], [0, 0, 0]])

    assert maze.in_bounds(row, col) == expected


@pytest.mark.parametrize("value, expected", [(0, True), (1, False), (2, True), (3, True)])
def test_passable_cells(value, expected):
    """Проход, старт и выход доступны для движения, стена — нет."""
    maze = Maze([[value]])

    assert maze.is_free(0, 0) == expected


def test_cells_outside_maze_are_not_free():
    """За каждой из четырёх границ поля 1×1 клетка считается недоступной."""
    maze = Maze([[0]])

    for row, col in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
        assert not maze.is_free(row, col)


def test_neighbors_have_no_walls_or_diagonals():
    """У центра три свободных соседа; стену слева и диагонали не возвращаем."""
    maze = Maze([
        [0, 2, 0],
        [1, 0, 3],
        [0, 0, 0],
    ])

    assert set(maze.neighbors(1, 1)) == {(0, 1), (1, 2), (2, 1)}


def test_neighbors_at_corner_stay_inside_maze():
    """У верхнего левого угла только два соседа: справа и снизу."""
    maze = Maze([[0, 0], [0, 0]])

    assert set(maze.neighbors(0, 0)) == {(0, 1), (1, 0)}


def test_find_start_and_exit():
    """В строке [2, 0, 3] находим старт в (0, 0), выход в (0, 2)."""
    maze = Maze([[2, 0, 3]])

    assert maze.start == (0, 0)
    assert maze.find_start() == (0, 0)
    assert maze.find_exit() == (0, 2)


def test_missing_start_and_exit():
    """Если маркеров 2 и 3 нет, методы поиска возвращают None."""
    maze = Maze([[0, 1]])

    assert maze.find_start() is None
    assert maze.find_exit() is None


def test_set_start_and_end():
    """Установка точек сохраняет координаты и помечает выход числом 3."""
    maze = Maze([[0, 0]])

    maze.set_start((0, 0))
    maze.set_end((0, 1))

    assert maze.start == (0, 0)
    assert maze.end == (0, 1)
    assert maze[0, 1] == 3


@pytest.mark.parametrize("position", [(0, 1), (-1, 0), (0, -1), (1, 0), (0, 2)])
def test_cannot_set_start_or_end_in_wall_or_outside_maze(position):
    """Стена и координаты вне поля вызывают ValueError для обеих точек."""
    maze = Maze([[0, 1]])

    # raises означает: в этом блоке ожидается указанная ошибка.
    with pytest.raises(ValueError):
        maze.set_start(position)
    with pytest.raises(ValueError):
        maze.set_end(position)


def test_empty_maze():
    """У пустого поля нулевые размеры, нет конечных точек и соседей."""
    maze = Maze([])

    assert maze.rows == 0
    assert maze.cols == 0
    assert maze.start is None
    assert maze.end is None
    assert not maze.is_free(0, 0)
    assert maze.neighbors(0, 0) == []
