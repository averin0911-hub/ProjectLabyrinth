from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget


class MazeCanvas(QWidget):
    def __init__(self):
        super().__init__()

        self.maze = None
        self.cell_size = 24  # Размер стороны клетки в пикселях.

        # До генерации поле почти не занимает места.
        self.setFixedSize(1, 1)

    def set_maze(self, maze):
        self.maze = maze

        # Размер поля зависит от числа клеток.
        self.setFixedSize(
            maze.cols * self.cell_size,
            maze.rows * self.cell_size,
        )

        self.update()  # Просим Qt перерисовать поле.

    def set_zoom(self, percent):
        # Переводим проценты в размер клетки, минимум — один пиксель.
        self.cell_size = max(1, round(24 * percent / 100))

        if self.maze is not None:
            # Обновляем размеры поля и запрашиваем перерисовку.
            self.set_maze(self.maze)

    def paintEvent(self, event):
        if self.maze is None:
            return

        painter = QPainter(self)
        size = self.cell_size

        # На маленьких клетках убираем промежутки.
        gap = 1 if size >= 8 else 0

        # Серый фон будет виден в промежутках между клетками.
        painter.fillRect(event.rect(), QColor("#cbd5e1"))

        # Определяем клетки в области, которую нужно перерисовать.
        first_row = event.rect().top() // size
        last_row = min(self.maze.rows, event.rect().bottom() // size + 1)
        first_col = event.rect().left() // size
        last_col = min(self.maze.cols, event.rect().right() // size + 1)

        for row in range(first_row, last_row):
            for col in range(first_col, last_col):
                position = (row, col)

                if position == self.maze.start:
                    color = "#22c55e"  # Старт — зелёный.
                elif position == self.maze.end:
                    color = "#ef4444"  # Выход — красный.
                elif self.maze[row, col] == 1:
                    color = "#1e293b"  # Стена — тёмная.
                else:
                    color = "#ffffff"  # Проход — белый.

                # Столбец задаёт x, строка задаёт y.
                painter.fillRect(
                    col * size,
                    row * size,
                    size - gap,
                    size - gap,
                    QColor(color),
                )

        painter.end()