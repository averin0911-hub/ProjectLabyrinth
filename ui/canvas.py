from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt


class MazeCanvas(QWidget):
    def __init__(self):
        super().__init__()

        self.maze = None
        self.edit_mode = "Стены / проходы"
        self.cell_size = 24  # Размер стороны клетки в пикселях.

        # До генерации поле почти не занимает места.
        self.setFixedSize(1, 1)

        self.drag_value = None  # Что рисуем: 0 — проход, 1 — стена.
        self.last_cell = None   # Предыдущая клетка движения.

        self.history = []  # История изменений.

    def set_maze(self, maze):
        # Новый лабиринт начинает новую историю; масштаб её сохраняет.
        if maze is not self.maze:
            self.history.clear()

        self.drag_value = None
        self.last_cell = None
        
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


    def set_edit_mode(self, mode):
        self.edit_mode = mode

        # Смена инструмента завершает текущее рисование.
        self.drag_value = None
        self.last_cell = None



    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self.maze is None:
            return

        # Переводим координаты мыши в координаты клетки.
        col = int(event.position().x() // self.cell_size)
        row = int(event.position().y() // self.cell_size)
        position = (row, col)

        if not self.maze.in_bounds(row, col):
            return

        if not self.maze.in_bounds(row, col):
            return

        # Старт и выход можно ставить только на проходы.
        if self.edit_mode in ("Старт", "Выход"):
            if not self.maze.is_free(row, col):
                return

        # Щелчок по существующему маркеру ничего не меняет.
        if position in (self.maze.start, self.maze.end):
            return

        # Запоминаем состояние до изменения.
        self.remember_change(row, col)

        if self.edit_mode == "Стены / проходы":
            if position in (self.maze.start, self.maze.end):
                return

            # Первое нажатие определяет действие для всего движения.
            self.drag_value = 0 if self.maze[row, col] == 1 else 1
            self.last_cell = position
            self.maze.grid[row][col] = self.drag_value

        elif self.edit_mode == "Старт":
            if position == self.maze.end:
                return

            # Убираем прежний маркер старта.
            if self.maze.start is not None:
                old_row, old_col = self.maze.start
                self.maze.grid[old_row][old_col] = 0

            # Новый старт становится проходимой клеткой.
            self.maze.grid[row][col] = 2
            self.maze.set_start(position)

        elif self.edit_mode == "Выход":
            if position == self.maze.start:
                return

            # Убираем прежний маркер выхода.
            if self.maze.end is not None:
                old_row, old_col = self.maze.end
                self.maze.grid[old_row][old_col] = 0

            # set_end сам записывает маркер выхода в матрицу.
            self.maze.grid[row][col] = 0
            self.maze.set_end(position)

        self.update()


    def mouseMoveEvent(self, event):
        # Рисуем только с зажатой левой кнопкой.
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if self.maze is None or self.drag_value is None:
            return

        col = int(event.position().x() // self.cell_size)
        row = int(event.position().y() // self.cell_size)

        if not self.maze.in_bounds(row, col):
            self.last_cell = None
            return

        old_row, old_col = self.last_cell or (row, col)

        # Заполняем промежуточные клетки при быстром движении.
        steps = max(1, abs(row - old_row), abs(col - old_col))

        for step in range(steps + 1):
            r = round(old_row + (row - old_row) * step / steps)
            c = round(old_col + (col - old_col) * step / steps)

            if (r, c) not in (self.maze.start, self.maze.end):
                # Не записываем повторное закрашивание тем же значением.
                if self.maze[r, c] != self.drag_value:
                    self.remember_change(r, c)
                    self.maze.grid[r][c] = self.drag_value

        self.last_cell = (row, col)
        self.update()

    def mouseReleaseEvent(self, event):
        # Отпускание кнопки завершает рисование.
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_value = None
            self.last_cell = None


    def remember_change(self, row, col):
        # Сохраняем значение клетки и положение маркеров.
        self.history.append((
            row, col, self.maze[row, col],
            self.maze.start, self.maze.end,
        ))

    def undo_last_change(self):
        if self.maze is None or not self.history:
            return

        self.drag_value = None
        self.last_cell = None

        # Извлекаем последнее сохранённое изменение.
        row, col, value, start, end = self.history.pop()

        # Убираем текущие маркеры.
        for position in (self.maze.start, self.maze.end):
            if position is not None:
                r, c = position
                self.maze.grid[r][c] = 0

        # Восстанавливаем клетку и прежние координаты маркеров.
        self.maze.grid[row][col] = value
        self.maze.start = start
        self.maze.end = end

        if start is not None:
            r, c = start
            self.maze.grid[r][c] = 2

        if end is not None:
            r, c = end
            self.maze.grid[r][c] = 3

        self.update()

    def clear_maze(self):
        if self.maze is None:
            return

        self.drag_value = None
        self.last_cell = None

        # Убираем стены, сохраняя каждую для возможного отката.
        for row in range(self.maze.rows):
            for col in range(self.maze.cols):
                if self.maze[row, col] == 1:
                    self.remember_change(row, col)
                    self.maze.grid[row][col] = 0

        self.update()