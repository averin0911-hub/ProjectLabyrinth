from __future__ import annotations

from collections import deque

from ..maze import Maze



class BidirectionalBFS:
    """Поиск кратчайшего пути в лабиринте с помощью двунаправленного BFS.

    Алгоритм одновременно пускает две волны: навстречу от старта и от выхода.
    Поиск останавливается, когда волны встречаются в общей свободной клетке.
    Если `maze.end` не задан, выход ищется по клетке со значением 3.

    Для визуализации используются:
    - visited_order — порядок обхода клеток обеими волнами,
    - path — итоговый кратчайший путь между стартом и выходом.
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
        - distance: длина кратчайшего пути до выхода
        - path: список координат от старта до выхода
        - visited_order: список посещённых клеток обеими волнами в порядке обхода
        - visited_count: суммарное количество просмотренных клеток
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

        # Очереди и словари предков для каждого из двух направлений.
        queue_start: deque[tuple[int, int]] = deque([start_cell])
        queue_end: deque[tuple[int, int]] = deque([end_cell])

        previous_start: dict[tuple[int, int], tuple[int, int] | None] = {start_cell: None}
        previous_end: dict[tuple[int, int], tuple[int, int] | None] = {end_cell: None}

        visited_start: set[tuple[int, int]] = {start_cell}
        visited_end: set[tuple[int, int]] = {end_cell}

        # Хронологический список для пошаговой анимации.
        visited_order: list[tuple[int, int]] = []
        meeting_cell: tuple[int, int] | None = None
        found = False

        while queue_start and queue_end:
            # Шаг со стороны меньшей очереди сохраняет баланс волновых фронтов.
            if len(queue_start) <= len(queue_end):
                current = queue_start.popleft()
                visited_order.append(current)

                if current in visited_end:
                    meeting_cell = current
                    found = True
                    break

                for neighbor in self.maze.neighbors(current[0], current[1]):
                    if neighbor not in visited_start:
                        visited_start.add(neighbor)
                        previous_start[neighbor] = current
                        queue_start.append(neighbor)

                        # Пересечение с обратным волновым фронтом.
                        if neighbor in visited_end:
                            meeting_cell = neighbor
                            found = True
                            break
                if found:
                    break
            else:
                current = queue_end.popleft()
                visited_order.append(current)

                if current in visited_start:
                    meeting_cell = current
                    found = True
                    break

                for neighbor in self.maze.neighbors(current[0], current[1]):
                    if neighbor not in visited_end:
                        visited_end.add(neighbor)
                        previous_end[neighbor] = current
                        queue_end.append(neighbor)

                        # Пересечение с прямым волновым фронтом.
                        if neighbor in visited_start:
                            meeting_cell = neighbor
                            found = True
                            break
                if found:
                    break

        if not found or meeting_cell is None:
            raise ValueError("Путь до выхода не существует")

        if meeting_cell not in visited_order:
            visited_order.append(meeting_cell)

        # Собираем первую половину пути: от старта до точки встречи.
        path_from_start: list[tuple[int, int]] = []
        step: tuple[int, int] | None = meeting_cell
        while step is not None:
            path_from_start.append(step)
            step = previous_start.get(step)
        path_from_start.reverse()

        # Дописываем вторую половину: от точки встречи до выхода.
        path_to_end: list[tuple[int, int]] = []
        step = previous_end.get(meeting_cell)
        while step is not None:
            path_to_end.append(step)
            step = previous_end.get(step)

        path = path_from_start + path_to_end
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
        """Синоним метода solve для удобного вызова."""
        return self.solve(start=start, end=end)


def bidirectional_bfs(
    maze: Maze,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> dict[str, object]:
    """Удобная обёртка над классом BidirectionalBFS."""
    return BidirectionalBFS(maze, start=start, end=end).solve()