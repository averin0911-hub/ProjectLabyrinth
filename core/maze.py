class Maze:
    def __init__(self, grid: list[list[int]], start: tuple[int, int] | None = None, end: tuple[int, int] | None = None):
        """Создаёт лабиринт по матрице клеток.

        Args:
            grid: Двумерный список, где 0 — проход, 1 — стена.
            start: Координаты стартовой клетки в формате (row, col).
            end: Координаты конечной клетки в формате (row, col).
        """
        self.grid = grid  # Матрица лабиринта
        self.rows = len(grid)  # Кол-во строк в матрице
        self.cols = len(grid[0]) if grid else 0  # Кол-во столбцов в матрице

        self.start = None
        self.end = None

        if start is not None: # Если стартовая клетка указана, устанавливаем её
            self.set_start(start)
        if end is not None: # Если конечная клетка указана, устанавливаем её
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
        """Проверяет, является ли клетка проходом и не выходит за границы."""
        return self.in_bounds(row, col) and self.grid[row][col] == 0

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

            # Добавляем только те клетки, которые являются проходом
            if self.is_free(nr, nc):
                result.append((nr, nc))

        return result
