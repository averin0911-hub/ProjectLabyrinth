from time import perf_counter

from PyQt6.QtCore import QThread


class SearchThread(QThread):
    def __init__(self, maze, algorithm, parent=None):
        super().__init__(parent)

        self.maze = maze
        self.algorithm = algorithm

        self.result = None   # Результат поиска.
        self.error = None    # Сообщение об ошибке.
        self.elapsed_ms = 0  # Время расчёта.

    def run(self):
        started = perf_counter()

        try:
            # Выполняем переданную функцию поиска.
            self.result = self.algorithm(self.maze)
        except Exception as error:
            # Сохраняем ошибку для последующего показа в окне.
            self.error = str(error)
        finally:
            self.elapsed_ms = (perf_counter() - started) * 1000