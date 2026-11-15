import json

from core.maze import Maze


MAX_FILE_SIZE = 10 * 1024 * 1024  # Максимум 10 МиБ.


def load_maze(filename):
    # Читаем файл с ограничением размера.
    with open(filename, "rb") as file:
        content = file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("Файл слишком большой: максимум 10 МиБ")

    data = json.loads(content)

    if not isinstance(data, dict):
        raise ValueError("В файле должен находиться объект JSON")

    if type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("Неподдерживаемая версия формата")

    grid = data.get("grid")

    if not isinstance(grid, list) or not 5 <= len(grid) <= 600:
        raise ValueError("Высота должна быть от 5 до 600 клеток")

    if not isinstance(grid[0], list) or not 5 <= len(grid[0]) <= 600:
        raise ValueError("Ширина должна быть от 5 до 600 клеток")

    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        raise ValueError("Все строки должны иметь одинаковую длину")

    maze = Maze(grid)
    markers = {2: None, 3: None}

    # Проверяем клетки, рамку и количество маркеров.
    for row in range(maze.rows):
        for col in range(maze.cols):
            value = grid[row][col]

            if type(value) is not int or value not in (0, 1, 2, 3):
                raise ValueError("Клетки должны содержать числа 0, 1, 2 или 3")

            if maze.is_border(row, col) and value != 1:
                raise ValueError("Внешняя рамка должна состоять из стен")

            if value in markers:
                if markers[value] is not None:
                    raise ValueError("Старт и выход должны встречаться по одному разу")
                markers[value] = (row, col)

    if markers[2] is None or markers[3] is None:
        raise ValueError("В лабиринте должны быть старт и выход")

    # Сверяем сохранённые координаты с маркерами матрицы.
    for name, marker in (("start", 2), ("end", 3)):
        point = data.get(name)

        if (
            not isinstance(point, list)
            or len(point) != 2
            or any(type(value) is not int for value in point)
            or tuple(point) != markers[marker]
        ):
            raise ValueError(f"Некорректные координаты {name}")

    maze.set_start(markers[2])
    maze.set_end(markers[3])
    return maze