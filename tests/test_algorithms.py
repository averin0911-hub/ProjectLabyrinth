"""Пять основных сценариев проверки алгоритмов поиска пути."""

import pytest

from core.algorithms.a_star import A_STAR
from core.algorithms.bfs import BFS
from core.algorithms.bidirectional_bfs import BidirectionalBFS
from core.algorithms.dfs import DFS
from core.algorithms.dijkstra import Dijkstra
from core.maze import Maze


ALL_ALGORITHMS = [BFS, BidirectionalBFS, Dijkstra, A_STAR, DFS]
SHORTEST_PATH_ALGORITHMS = [BFS, BidirectionalBFS, Dijkstra, A_STAR]


@pytest.mark.parametrize("algorithm", ALL_ALGORITHMS)
def test_valid_path(algorithm):
    # Единственный маршрут обходит стену снизу.
    maze = Maze([[2, 1, 3], [0, 0, 0]])
    before = [row[:] for row in maze.grid]

    result = algorithm(maze).solve()
    path = result["path"]

    assert path[0] == (0, 0)
    assert path[-1] == (0, 2)
    assert result["distance"] == result["steps"] == len(path) - 1 == 4
    assert len(path) == len(set(path))

    for row, col in path:
        # Проверяем границы и стены независимо от методов Maze.
        assert 0 <= row < maze.rows
        assert 0 <= col < maze.cols
        assert maze.grid[row][col] != 1

    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        # Каждый переход ведёт в соседнюю клетку по стороне.
        assert abs(r1 - r2) + abs(c1 - c2) == 1

    assert maze.grid == before  # Поиск не изменяет клетки лабиринта.


@pytest.mark.parametrize("algorithm", SHORTEST_PATH_ALGORITHMS)
def test_shortest_path(algorithm):
    # До выхода можно дойти за 3 шага напрямую или за 7 в обход.
    maze = Maze([
        [2, 0, 0, 3],
        [0, 1, 1, 0],
        [0, 0, 0, 0],
    ])

    result = algorithm(maze).solve()

    assert result["distance"] == 3
    assert result["path"] == [(0, 0), (0, 1), (0, 2), (0, 3)]


@pytest.mark.parametrize("algorithm", ALL_ALGORITHMS)
def test_no_path(algorithm):
    maze = Maze([[2, 1, 3]])

    result = algorithm(maze).solve()

    assert result["path"] == []
    assert result["distance"] is None
    assert result["steps"] is None
    # Данные поиска нужны для анимации даже при отсутствии пути.
    assert result["visited_order"]
    assert result["events"]


@pytest.mark.parametrize("algorithm", ALL_ALGORITHMS)
def test_start_equals_end(algorithm):
    maze = Maze([[2]])

    result = algorithm(maze).solve(end=(0, 0))

    assert result["path"] == [(0, 0)]
    assert result["distance"] == result["steps"] == 0
    assert result["visited_order"] == [(0, 0)]
    assert result["visited_count"] == 1


@pytest.mark.parametrize("algorithm", ALL_ALGORITHMS)
def test_invalid_coordinates(algorithm):
    maze = Maze([[2, 1, 3]])

    # Старт на стене недопустим.
    with pytest.raises(ValueError):
        algorithm(maze).solve(start=(0, 1))

    # Выход за пределами поля также недопустим.
    with pytest.raises(ValueError):
        algorithm(maze).solve(end=(-1, 0))
