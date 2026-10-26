from collections.abc import Callable
from time import perf_counter

from core.algorithms.bfs import bfs
from core.algorithms.dijkstra import dijkstra
from core.maze import Maze, generate_maze


MAX_SIZE = 500**10


def read_size(prompt: str, default: int = 10) -> int:
    """Читает размер поля; Enter оставляет значение по умолчанию."""
    while True:
        value = input(f"{prompt} [{default}]: ").strip()
        if not value:
            return default
        try:
            size = int(value)
        except ValueError:
            print(f"Введите целое число от 5 до {MAX_SIZE}.")
            continue
        if 5 <= size <= MAX_SIZE:
            return size
        print(f"Размер должен быть от 5 до {MAX_SIZE}, включая внешние стены.")


def show_maze(
    maze: Maze,
    path: list[tuple[int, int]] | None = None,
    visited: list[tuple[int, int]] | None = None,
) -> None:
    """Рисует результат поверх поля, не меняя исходную матрицу лабиринта."""
    path_cells = set(path or [])
    visited_cells = set(visited or [])
    print(f"\nЛабиринт: {maze.cols} × {maze.rows}")
    for row in range(maze.rows):
        line = []
        for col in range(maze.cols):
            cell = (row, col)
            if cell == maze.start:
                symbol = "S"
            elif cell == maze.end:
                symbol = "E"
            elif maze[row, col] == 1:
                symbol = "#"
            elif cell in path_cells:
                symbol = "*"
            elif cell in visited_cells:
                symbol = "."
            else:
                symbol = " "
            line.append(symbol)
        print(" ".join(line))
    print("# — стена, S — старт, E — выход, пробел — проход")
    if path is not None:
        print("* — найденный путь, . — обработанная клетка вне пути")
    print(f"Старт: {maze.start}; выход: {maze.end}")
    print("Координаты: (строка, столбец), отсчёт с нуля.")


def measure_algorithm(
    maze: Maze,
    algorithm: Callable[[Maze], dict[str, object]],
) -> tuple[dict[str, object], float]:
    """Измеряет поиск вместе со сбором результата, без ввода и печати."""
    started = perf_counter()
    result = algorithm(maze)
    elapsed_ms = (perf_counter() - started) * 1000
    return result, elapsed_ms


def run_algorithm(
    maze: Maze,
    name: str,
    algorithm: Callable[[Maze], dict[str, object]],
) -> tuple[dict[str, object], float] | None:
    """Замеряет только поиск: ввод и печать не входят во время работы."""
    try:
        result, elapsed_ms = measure_algorithm(maze, algorithm)
    except ValueError as error:
        print(f"\n{name}: {error}")
        return None
    print(f"\n{name}")
    show_maze(maze, result["path"], result["visited_order"])
    print(f"Длина пути: {result['distance']} шагов")
    print(f"Количество обработанных клеток: {result['visited_count']}")
    print(f"Время поиска: {elapsed_ms:.3f} мс")
    return result, elapsed_ms


def compare_algorithms(maze: Maze) -> None:
    """Запускает каждый алгоритм один раз на одном лабиринте."""
    measurements = []
    free_cells = sum(cell in (0, 2, 3) for row in maze.grid for cell in row)
    print(f"\nСравнение на одном лабиринте {maze.cols} × {maze.rows}:")
    print(f"Всего клеток: {maze.rows * maze.cols}; проходимых: {free_cells}")
    print(f"Старт: {maze.start}; выход: {maze.end}")

    for name, algorithm in (("BFS", bfs), ("Дейкстра", dijkstra)):
        try:
            result, elapsed_ms = measure_algorithm(maze, algorithm)
        except ValueError as error:
            print(f"{name}: {error}")
            return
        # Сохраняем только числа и освобождаем полный результат перед следующим поиском.
        measurements.append(
            (name, result["distance"], result["visited_count"], elapsed_ms)
        )
        del result

    print(
        f"{'Алгоритм':<12} {'Длина пути':>12} {'Обработано клеток':>19} "
        f"{'Время, мс':>13}"
    )
    for name, distance, visited_count, elapsed_ms in measurements:
        print(
            f"{name:<12} {distance:>12} {visited_count:>19} "
            f"{elapsed_ms:>13.3f}"
        )
    print("Обработано клеток — число уникальных извлечённых клеток, включая старт и выход.")
    print("Время включает поиск и сбор результата; генерация и печать не учитываются.")
    print("Все шаги стоят 1: оба алгоритма находят кратчайший путь.")
    print("При равных расстояниях порядок обработки клеток может отличаться.")


def main() -> None:
    print("Поиск пути в лабиринте — консольная демонстрация")
    maze = generate_maze(10, 10)
    show_maze(maze)

    try:
        while True:
            print("\n1 — Поиск в ширину (BFS)")
            print("2 — Алгоритм Дейкстры")
            print("3 — Сравнить оба алгоритма")
            print("4 — Сгенерировать новый лабиринт")
            print("5 — Показать исходный лабиринт")
            print("0 — Выход")
            choice = input("Выберите действие: ").strip()

            if choice == "0":
                break
            if choice == "1":
                run_algorithm(maze, "BFS", bfs)
            elif choice == "2":
                run_algorithm(maze, "Дейкстра", dijkstra)
            elif choice == "3":
                compare_algorithms(maze)
            elif choice == "4":
                width = read_size("Ширина")
                height = read_size("Высота")
                maze = generate_maze(width, height)
                show_maze(maze)
            elif choice == "5":
                show_maze(maze)
            else:
                print("Неизвестный пункт меню. Введите число от 0 до 5.")
    except (EOFError, KeyboardInterrupt):
        print()
    print("Программа завершена.")


if __name__ == '__main__':
    main()
