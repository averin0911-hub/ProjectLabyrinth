from time import perf_counter

from PyQt6.QtCore import QThread


class TaskThread(QThread):
    # Универсальный поток: выполняет переданную функцию с её аргументами.
    def __init__(self, function, args=(), kwargs=None, parent=None):
        super().__init__(parent)

        self.function = function
        self.args = args
        # Создаём отдельный словарь, если именованные аргументы не переданы.
        self.kwargs = kwargs if kwargs is not None else {}

        self.result = None
        self.error = None
        self.elapsed_ms = 0

    def run(self):
        # Этот метод выполняется в фоне; виджеты обновляет главное окно после finished.
        started = perf_counter()

        try:
            # Вызываем функцию с переданными аргументами.
            self.result = self.function(*self.args, **self.kwargs)
        except Exception as error:
            # Передаём текст ошибки окну вместо показа диалога из фонового потока.
            self.error = str(error)
        finally:
            # Замер завершаем и при успехе, и при ошибке; секунды переводим в миллисекунды.
            self.elapsed_ms = (perf_counter() - started) * 1000


def calculate_comparison(maze, algorithms):
    # Все алгоритмы получают один лабиринт, а в результате остаются строки таблицы.
    rows = []

    for name, algorithm in algorithms:
        started = perf_counter()

        try:
            result = algorithm(maze)
        except Exception as error:
            # Название помогает понять, на каком алгоритме прервалось сравнение.
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
