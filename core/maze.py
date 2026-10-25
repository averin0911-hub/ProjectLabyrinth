import random


class Maze:
    def __init__(self, grid: list[list[int]], start: tuple[int, int] | None = None, end: tuple[int, int] | None = None):
        """Создаёт лабиринт по матрице клеток.

        Args:
            grid: Двумерный список, где 0 — проход, 1 — стена, 2 — старт,
                3 — выход.
            start: Координаты стартовой клетки в формате (row, col).
            end: Координаты конечной клетки в формате (row, col).
        """
        self.grid = grid  # Матрица лабиринта
        self.rows = len(grid)  # Кол-во строк в матрице
        self.cols = len(grid[0]) if grid else 0  # Кол-во столбцов в матрице

        self.start = None
        self.end = None

        if start is not None:  # Если стартовая клетка указана, устанавливаем её
            self.set_start(start)
        else:
            self.start = self.find_start()
        if end is not None:  # Если конечная клетка указана, устанавливаем её
            self.set_end(end)

    def __getitem__(self, position: tuple[int, int]) -> int:
        """Возвращает значение клетки по координатам (row, col).

        Пример:
            maze = Maze([[0, 1], [0, 0]], (0, 0))
            maze[0, 1]  # 1
        """
        row, col = position
        return self.grid[row][col]

    def in_bounds(self, row: int, col: int) -> bool:
        """Проверяет, находится ли клетка внутри лабиринта."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_free(self, row: int, col: int) -> bool:
        """Проверяет, является ли клетка проходом и не выходит за границы.

        Клетки со значениями 0, 2 и 3 проходимы: 2 — старт, 3 — выход.
        """
        return self.in_bounds(row, col) and self.grid[row][col] in (0, 2, 3)

    def find_start(self, value: int = 2) -> tuple[int, int] | None:
        """Ищет координаты старта, отмеченного заданным значением."""
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == value:
                    return (row, col)
        return None

    def find_exit(self, value: int = 3) -> tuple[int, int] | None:
        """Ищет координаты выхода в лабиринте.

        По умолчанию выход помечен числом 3.
        """
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == value:
                    return (row, col)
        return None

    def set_start(self, position: tuple[int, int]) -> None:
        """Устанавливает стартовую клетку.

        Raises:
            ValueError: Если позиция выходит за границы или отмечена как стена.
        """
        row, col = position

        if not self.is_free(row, col):
            raise ValueError("Недопустимая начальная точка")

        self.start = position

    def set_end(self, position: tuple[int, int]) -> None:
        """Устанавливает конечную клетку.

        Raises:
            ValueError: Если позиция выходит за границы или отмечена как стена.
        """
        row, col = position

        if not self.is_free(row, col):
            raise ValueError("Недопустимая конечная точка")

        self.end = position
        self.grid[row][col] = 3  # Отмечаем клетку как выход

    def neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        """Возвращает список свободных соседних клеток вокруг заданной позиции.

        Поиск идёт только в 4 направлениях: вверх, вниз, влево, вправо.
        """
        directions = [
            (-1, 0),  # вверх
            (1, 0),   # вниз
            (0, -1),  # влево
            (0, 1)    # вправо
        ]

        result: list[tuple[int, int]] = []

        for dr, dc in directions:
            nr = row + dr
            nc = col + dc

            # Добавляем только те клетки, которые являются проходом.
            # Маркеры старта (2) и выхода (3) тоже считаются проходимыми.
            if self.is_free(nr, nc):
                result.append((nr, nc))

        return result

    def __str__(self) -> str:
        return "\n".join("  ".join(str(cell) for cell in row) for row in self.grid)



def generate_maze(width: int, height: int, seed: int | None = None) -> Maze:
    """Создаёт случайный лабиринт алгоритмом Randomized DFS.

    Размеры включают внешнюю стену. После прокладки связного лабиринта
    каждая оставшаяся внутренняя стена с вероятностью 50% превращается
    в проход. `seed` позволяет повторно получить тот же лабиринт.
    """
    if width < 5 or height < 5:
        raise ValueError("Ширина и высота должны быть не меньше 5")

    rng = random.Random(seed)
    grid = [[1 for _ in range(width)] for _ in range(height)]
    start = (
        rng.randrange(1, height - 1, 2),
        rng.randrange(1, width - 1, 2),
    )
    grid[start[0]][start[1]] = 2

    # DFS ходит между узловыми клетками через одну клетку.
    stack = [start]
    visited = {start}
    directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]

    while stack:
        row, col = stack[-1]
        unvisited_neighbors = []

        # Ищем соседние клетки, которые ещё не посещены.
        for row_step, col_step in directions:
            next_row = row + row_step
            next_col = col + col_step
            next_cell = (next_row, next_col)

            if (
                0 < next_row < height - 1
                and 0 < next_col < width - 1
                and next_cell not in visited
            ):
                unvisited_neighbors.append(next_cell)

        if not unvisited_neighbors:
            stack.pop()
            continue

        next_row, next_col = rng.choice(unvisited_neighbors)
        wall_row = (row + next_row) // 2
        wall_col = (col + next_col) // 2
        grid[wall_row][wall_col] = 0
        grid[next_row][next_col] = 0
        visited.add((next_row, next_col))
        stack.append((next_row, next_col))

    # Случайно открываем часть внутренних стен, добавляя обходные пути.
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] == 1 and \
                (grid[row - 1][col] == 0 and grid[row + 1][col] == 0 and \
                    not (grid[row][col - 1] == 0 or grid[row][col + 1] == 0) or \
                        grid[row][col - 1] == 0 and grid[row][col + 1] == 0 and \
                            not (grid[row - 1][col] == 0 or grid[row +1][col] == 0)):
                                grid[row][col] = random.randint(0, 1)

    maze = Maze(grid, start=start)

    # Манхэттенские расстояния до всех проходов.
    distances = {
        (row, col): abs(row - start[0]) + abs(col - start[1])
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 0
    }

    # Желаемое минимальное манхэттенское расстояние от старта до выхода.
    min_distance = max(2, (width + height) // 2)
    # Ограничиваем порог максимальным расстоянием среди проходов,
    # чтобы список кандидатов для rng.choice не оказался пустым.
    min_distance = min(min_distance, max(distances.values()))

    end = rng.choice([
        cell
        for cell, distance in distances.items()
        if distance >= min_distance
    ])

    maze.set_end(end)
    return maze
