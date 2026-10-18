from __future__ import annotations

# Очередь с приоритетом: выбирает клетку с минимальным расстоянием первой.
from heapq import heappop, heappush

from ..maze import Maze


class Dijkstra:
    """Поиск кратчайшего пути в лабиринте по алгоритму Дейкстры.

    Если `maze.end` не задан, алгоритм автоматически ищет выход по клетке со
    значением 2. Для визуализации удобно использовать:
    - `visited_order` — порядок обхода клеток (жёлтый),
    - `path` — кратчайший путь до выхода (синий).
    """

    def __init__(
        self,
        maze: Maze,
        start: tuple[int, int] | None = None,
        end: tuple[int, int] | None = None,
    ):
        # Сохраняем лабиринт и стартовую позицию.
        self.maze = maze
        self.start = start if start is not None else maze.start
        self.end = end if end is not None else maze.end

        if self.start is None:
            raise ValueError("Не задана стартовая клетка")

    def _resolve_end(self) -> tuple[int, int]:
        """Возвращает клетку выхода: либо `end`, либо клетку 2 в лабиринте."""
        # Если цель уже задана явно — используем её.
        if self.end is not None:
            return self.end

        # Иначе находим выход по метке 2.
        exit_position = self.maze.find_exit()
        if exit_position is None:
            raise ValueError("Выход не найден: в лабиринте нет клетки со значением 2")

        self.end = exit_position
        self.maze.end = exit_position
        return exit_position

    def solve(
        self,
        start: tuple[int, int] | None = None,
        end: tuple[int, int] | None = None,
    ) -> dict[str, object]:
        """Возвращает кратчайший путь и информацию для визуализации.

        Возвращаемые поля:
        - distance: длина кратчайшего пути до выхода
        - path: список координат от старта до выхода
        - visited_order: список посещённых клеток в порядке обхода
        - visited_count: количество просмотренных клеток
        - steps: то же значение, что и distance
        - start: стартовая клетка
        - end: конечная клетка
        """
        # Берём стартовую точку либо из объекта, либо из аргумента.
        start_cell = start if start is not None else self.start
        if start_cell is None:
            raise ValueError("Не задана стартовая клетка")

        # Определяем конечную цель: либо переданную, либо найденную по 2.
        end_cell = end if end is not None else self._resolve_end()

        # Проверка корректности начальной и конечной клеток.
        if not self.maze.is_free(*start_cell):
            raise ValueError("Начальная клетка недопустима")

        if not self.maze.is_free(*end_cell):
            raise ValueError("Конечная клетка недопустима")

        # Если старт совпадает с финишем, сразу возвращаем результат.
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

        # distances: минимальная известная дистанция до каждой клетки.
        distances: dict[tuple[int, int], int] = {start_cell: 0}

        # previous: какую клетку использовали, чтобы попасть в текущую.
        previous: dict[tuple[int, int], tuple[int, int] | None] = {start_cell: None}

        # Очередь из пар (расстояние, координаты). heapq выберет ближайшую.
        queue: list[tuple[int, tuple[int, int]]] = [(0, start_cell)]

        # Для визуализации — порядок обработки клеток.
        visited_order: list[tuple[int, int]] = []
        visited_set: set[tuple[int, int]] = set()

        while queue:
            # Берём ближайшую клетку из очереди.
            current_distance, current = heappop(queue)

            # Если клетку уже обработали — пропускаем.
            if current in visited_set:
                continue

            visited_set.add(current)
            visited_order.append(current)

            # Если дошли до цели — можно прекращать поиск.
            if current == end_cell:
                break

            # Проверяем соседей.
            for neighbor in self.maze.neighbors(current[0], current[1]):
                candidate_distance = current_distance + 1

                # Обновляем расстояние, если нашли более короткий путь.
                if neighbor not in distances or candidate_distance < distances[neighbor]:
                    distances[neighbor] = candidate_distance
                    previous[neighbor] = current
                    heappush(queue, (candidate_distance, neighbor))

        # Если целевая клетка не достигнута — пути нет.
        if end_cell not in distances:
            raise ValueError("Путь до выхода не существует")

        # Восстанавливаем путь по предыдущим клеткам.
        path: list[tuple[int, int]] = []
        current: tuple[int, int] | None = end_cell

        while current is not None:
            path.append(current)
            current = previous.get(current)

        path.reverse()
        distance = distances[end_cell]

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
        """Синоним метода solve для удобного вызова."""
        return self.solve(start=start, end=end)


def dijkstra(
    maze: Maze,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> dict[str, object]:
    """Удобная обёртка над классом Dijkstra."""
    return Dijkstra(maze, start=start, end=end).solve()