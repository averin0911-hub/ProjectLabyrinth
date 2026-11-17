from time import perf_counter

from PyQt6.QtCore import QThread


class TaskThread(QThread):
    def __init__(self, function, args=(), kwargs=None, parent=None):
        super().__init__(parent)

        self.function = function
        self.args = args
        self.kwargs = kwargs if kwargs is not None else {}

        self.result = None
        self.error = None
        self.elapsed_ms = 0

    def run(self):
        started = perf_counter()

        try:
            # Вызываем функцию с переданными аргументами.
            self.result = self.function(*self.args, **self.kwargs)
        except Exception as error:
            self.error = str(error)
        finally:
            self.elapsed_ms = (perf_counter() - started) * 1000


def calculate_comparison(maze, algorithms):
    rows = []

    for name, algorithm in algorithms:
        started = perf_counter()

        try:
            result = algorithm(maze)
        except Exception as error:
            raise ValueError(f"{name}: {error}") from error

        elapsed_ms = (perf_counter() - started) * 1000

        if result["distance"] is None:
            distance = "Нет пути"
        else:
            distance = str(result["distance"])

        # Сохраняем только данные для таблицы.
        rows.append([
            name,
            distance,
            str(result["visited_count"]),
            f"{elapsed_ms:.3f}",
        ])

        # Освобождаем историю перед следующим алгоритмом.
        del result

    return rows