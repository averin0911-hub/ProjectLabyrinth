from __future__ import annotations

from ..maze import Maze


class DFS:
    """Поиск пути в лабиринте с помощью алгоритма поиска в глубину (DFS).

    В отличие от волнового поиска, алгоритм упрямо идет по коридору до упора
    и не гарантирует нахождение кратчайшего пути. Если `maze.end` не задан,
    выход ищется по клетке со значением 3.

    Для визуализации используются:
    - visited_order — порядок обхода клеток,
    - path — найденный путь от старта до выхода.
    """

    def __init__(
        self,
        maze: Maze,
        start: tuple[int, int] | None = None,
        end: tuple[int, int] | None = None,
    ):
        # Сохраняем ссылку на лабиринт и начальные координаты.
        self.maze = maze
        self.start = start if start is not None else maze.start
        self.end = end if end is not None else maze.end

        if self.start is None:
            raise ValueError("Не задана стартовая клетка")

    def _resolve_end(self) -> tuple[int, int]:
        """Возвращает координаты выхода: либо переданные явно, либо метку 3."""
        if self.end is not None:
            return self.end

        exit_position = self.maze.find_exit()
        if exit_position is None:
            raise ValueError("Выход не найден: в лабиринте нет клетки со значением 3")

        self.end = exit_position
        self.maze.end = exit_position
        return exit_position

    def solve(
        self,
        start: tuple[int, int] | None = None,
        end: tuple[int, int] | None = None,
    ) -> dict[str, object]:
        """Находит путь и формирует данные для визуализации.

        Возвращаемые поля:
        - distance: длина найденного пути до выхода
        - path: список координат от старта до выхода
        - visited_order: список посещённых клеток в порядке обхода
        - visited_count: количество просмотренных клеток
        - steps: то же значение, что и distance
        - start: стартовая клетка
        - end: конечная клетка
        """
        start_cell = start if start is not None else self.start
        if start_cell is None:
            raise ValueError("Не задана стартовая клетка")

        end_cell = end if end is not None else self._resolve_end()

        # Проверяем проходимость обеих граничных точек.
        if not self.maze.is_free(*start_cell):
            raise ValueError("Начальная клетка недопустима")

        if not self.maze.is_free(*end_cell):
            raise ValueError("Конечная клетка недопустима")

        # Если старт совпадает с финишем, возвращаем нулевой путь.
        if start_cell == end_cell:
            return {
                "distance": 0,
                "steps": 0,
                "path": [start_cell],
                "visited_order": [start_cell],
                "visited_count": 1,
                "start": start_cell,
                "end": end_cell,
            }

        # Стек LIFO для погружения в глубину и словарь предков.
        stack: list[tuple[int, int]] = [start_cell]
        previous: dict[tuple[int, int], tuple[int, int] | None] = {start_cell: None}

        # Хронологический список для пошаговой анимации и множество посещённых.
        visited_order: list[tuple[int, int]] = []
        visited_set: set[tuple[int, int]] = {start_cell}

        while stack:
            # Снимаем последнюю добавленную клетку с вершины стека.
            current = stack.pop()
            visited_order.append(current)

            # Если наткнулись на финиш — прекращаем поиск.
            if current == end_cell:
                break

            # Проверяем соседей.
            for neighbor in self.maze.neighbors(current[0], current[1]):
                if neighbor not in visited_set:
                    visited_set.add(neighbor)
                    previous[neighbor] = current
                    stack.append(neighbor)

        # Если до выхода так и не дошли — пути нет.
        if end_cell not in previous:
            raise ValueError("Путь до выхода не существует")

        # Восстанавливаем найденный маршрут по родительским ячейкам.
        path: list[tuple[int, int]] = []
        current: tuple[int, int] | None = end_cell

        while current is not None:
            path.append(current)
            current = previous.get(current)

        path.reverse()
        distance = len(path) - 1

        return {
            "distance": distance,
            "steps": distance,
            "path": path,
            "visited_order": visited_order,
            "visited_count": len(visited_order),
            "start": start_cell,
            "end": end_cell,
        }

    def shortest_path(
        self,
        start: tuple[int, int] | None = None,
        end: tuple[int, int] | None = None,
    ) -> dict[str, object]:
        """Синоним метода solve для поддержки единого интерфейса."""
        return self.solve(start=start, end=end)


def dfs(
    maze: Maze,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> dict[str, object]:
    """Удобная обёртка над классом DFS."""
    return DFS(maze, start=start, end=end).solve()