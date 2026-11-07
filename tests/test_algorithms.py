"""Одни и те же небольшие примеры для четырёх алгоритмов."""

import pytest

from core.algorithms.a_star import A_STAR, A_star
from core.algorithms.bfs import BFS, bfs
from core.algorithms.bidirectional_bfs import BidirectionalBFS, bidirectional_bfs
from core.algorithms.dijkstra import Dijkstra, dijkstra
from core.maze import Maze


@pytest.fixture(params=[BFS, BidirectionalBFS, Dijkstra, A_STAR])
def solver_class(request):
    """pytest повторит каждый использующий эту фикстуру тест для 4 алгоритмов."""
    return request.param


def assert_valid_path(maze, result, start, end, distance):
    """Общие проверки маршрута, чтобы не копировать их в каждый тест."""
    path = result["path"]
    assert path[0] == start
    assert path[-1] == end
    assert result["start"] == start
    assert result["end"] == end
    assert result["distance"] == result["steps"] == distance == len(path) - 1
    assert len(path) == len(set(path))

    # Проверяем координаты прямо по матрице, независимо от Maze.neighbors().
    for row, col in path + result["visited_order"]:
        assert 0 <= row < maze.rows
        assert 0 <= col < maze.cols
        assert maze.grid[row][col] in (0, 2, 3)
    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        assert abs(r1 - r2) + abs(c1 - c2) == 1

    assert result["visited_count"] == len(result["visited_order"])
    assert len(result["visited_order"]) == len(set(result["visited_order"]))


@pytest.mark.parametrize("grid, end, distance", [
    ([[2, 0, 0, 3]], (0, 3), 3),                    # Прямой коридор.
    ([[2, 3]], (0, 1), 1),                          # Соседние точки.
    ([[2, 1, 3], [0, 0, 0]], (0, 2), 4),           # Обход стены.
    ([[2, 0, 0], [0, 0, 0], [0, 0, 3]], (2, 2), 4),  # Равные пути и циклы.
    ([[2, 0, 0, 3], [0, 1, 1, 0], [0, 0, 0, 0]], (0, 3), 3),  # Длинный обход.
    ([[2, 0, 0], [1, 0, 1], [3, 0, 0]], (2, 0), 4),  # Тупики.
])
def test_shortest_path(solver_class, grid, end, distance):
    """На каждом из шести полей получаем ожидаемую длину и допустимый путь."""
    # Копируем строки: тесты разных алгоритмов получают независимые матрицы.
    maze = Maze([row[:] for row in grid])
    before = [row[:] for row in maze.grid]

    result = solver_class(maze).solve()

    assert_valid_path(maze, result, (0, 0), end, distance)
    assert maze.grid == before


def test_start_equals_end(solver_class):
    """Старт уже является выходом: ноль шагов, одна клетка в результате."""
    maze = Maze([[2]])

    result = solver_class(maze).solve(end=(0, 0))

    assert_valid_path(maze, result, (0, 0), (0, 0), 0)
    assert result["path"] == [(0, 0)]
    assert result["visited_order"] == [(0, 0)]
    assert result["visited_count"] == 1


def test_no_path(solver_class):
    """В строке [2, 1, 3] стену не обойти: ожидаем ошибку отсутствия пути."""
    maze = Maze([[2, 1, 3]])

    with pytest.raises(ValueError, match="Путь до выхода не существует"):
        solver_class(maze).solve()


def test_missing_start(solver_class):
    """Без старта объект алгоритма должен сообщить об ошибке ValueError."""
    with pytest.raises(ValueError, match="Не задана стартовая клетка"):
        solver_class(Maze([[0, 3]]))


def test_missing_exit(solver_class):
    """Без выхода поиск должен сообщить об ошибке ValueError."""
    with pytest.raises(ValueError, match="Выход не найден"):
        solver_class(Maze([[2, 0]])).solve()


@pytest.mark.parametrize("point", [(0, 1), (-1, 0), (0, -1), (1, 0), (0, 3)])
def test_invalid_start_and_end(solver_class, point):
    """Стена или точка вне поля недопустима и как старт, и как выход."""
    maze = Maze([[2, 1, 3]])
    solver = solver_class(maze)

    with pytest.raises(ValueError, match="Начальная клетка недопустима"):
        solver.solve(start=point)
    with pytest.raises(ValueError, match="Конечная клетка недопустима"):
        solver.solve(end=point)


def test_explicit_points_override_maze_points(solver_class):
    """Явные точки конструктора важнее точек поля, а аргументы solve — важнее их."""
    maze = Maze([[2, 0, 0, 0, 3]], end=(0, 4))
    solver = solver_class(maze, start=(0, 1), end=(0, 3))

    result = solver.solve()
    assert_valid_path(maze, result, (0, 1), (0, 3), 2)

    # Аргументы solve() имеют приоритет над аргументами конструктора.
    result = solver.solve(start=(0, 2), end=(0, 1))
    assert_valid_path(maze, result, (0, 2), (0, 1), 1)


def test_solver_can_be_reused(solver_class):
    """Поиск назад не портит следующий поиск с исходными точками объекта."""
    maze = Maze([[2, 0, 3]])
    solver = solver_class(maze)

    first = solver.solve()
    solver.solve(start=(0, 2), end=(0, 0))
    again = solver.solve()

    assert again == first
    assert solver.shortest_path() == first


@pytest.mark.parametrize("solver_class, function", [
    (BFS, bfs), (BidirectionalBFS, bidirectional_bfs),
    (Dijkstra, dijkstra), (A_STAR, A_star),
])
def test_function_wrapper(solver_class, function):
    """Функция-обёртка и соответствующий класс дают одинаковый результат."""
    maze = Maze([[0, 0, 0]])

    expected = solver_class(maze, start=(0, 0), end=(0, 2)).solve()

    assert function(maze, start=(0, 0), end=(0, 2)) == expected


def test_algorithms_agree_on_a_maze_with_cycles():
    """Все четыре алгоритма на контрольном поле находят путь длиной 5."""
    grid = [[2, 0, 0, 0], [0, 1, 0, 1], [0, 0, 0, 3]]

    for algorithm in [bfs, bidirectional_bfs, dijkstra, A_star]:
        maze = Maze([row[:] for row in grid])
        result = algorithm(maze)
        assert_valid_path(maze, result, (0, 0), (2, 3), 5)


def test_a_star_heuristic():
    """На открытом поле 3×3 проверяем оценки расстояния A* и соседних клеток."""
    maze = Maze([[2, 0, 0], [0, 0, 0], [0, 0, 3]])
    solver = A_STAR(maze)
    goal = (2, 2)

    assert solver.heuristic(goal, goal) == 0
    assert solver.heuristic((0, 0), goal) == 4

    # На открытом поле кратчайший путь равен манхэттенскому расстоянию.
    for row in range(3):
        for col in range(3):
            estimate = solver.heuristic((row, col), goal)
            assert 0 <= estimate <= (2 - row) + (2 - col)
            for neighbor in maze.neighbors(row, col):
                assert estimate <= 1 + solver.heuristic(neighbor, goal)
