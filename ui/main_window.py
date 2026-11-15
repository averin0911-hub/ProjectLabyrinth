from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QScrollArea,
    QComboBox,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from core.maze import generate_maze
from ui.canvas import MazeCanvas
import json


class MainWindow(QMainWindow):
    def __init__(self):
        # Инициализация родительского класса QMainWindow.
        super().__init__()

        self.setWindowTitle("ProjectLabyrinth")
        self.resize(1200, 800)

        # Текущий лабиринт; пока не создан.
        self.maze = None

        # Общий контейнер для трёх панелей.
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Размещаем панели слева направо внутри контейнера.
        layout = QHBoxLayout(central_widget)

        # Отступы от краёв и расстояние между панелями.
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self.controls_panel = QGroupBox("Управление")
        self.maze_panel = QGroupBox("Лабиринт")
        self.results_panel = QGroupBox("Результаты")

        # Пропорции ширины панелей — примерно 1 : 2 : 1.
        layout.addWidget(self.controls_panel, 1)
        layout.addWidget(self.maze_panel, 2)
        layout.addWidget(self.results_panel, 1)

        # Блоки левой панели располагаются сверху вниз.
        self.controls_layout = QVBoxLayout(self.controls_panel)

        parameters_box = QGroupBox("Параметры лабиринта")
        # Форма: подпись слева, поле ввода справа.
        parameters_layout = QFormLayout(parameters_box)

        # Поля целых чисел от 5 до 600; начальный размер — 20 × 20.
        self.width_input = QSpinBox()
        self.width_input.setRange(5, 600)
        self.width_input.setValue(21)

        self.height_input = QSpinBox()
        self.height_input.setRange(5, 600)
        self.height_input.setValue(21)

        parameters_layout.addRow("Ширина:", self.width_input)
        parameters_layout.addRow("Высота:", self.height_input)

        self.generate_button = QPushButton("Сгенерировать")
        parameters_layout.addRow(self.generate_button)

        # По нажатию вызываем метод; передаём его без скобок.
        self.generate_button.clicked.connect(self.generate_new_maze)

        self.controls_layout.addWidget(parameters_box)
        # Пустое место снизу прижимает блок параметров к верху.
        self.controls_layout.addStretch()

        self.canvas = MazeCanvas()

        # Прокрутка позволяет просматривать большие лабиринты.
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.canvas)

        # Центрируем поле по горизонтали и вертикали.
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Размещаем область прокрутки в центральной панели.
        maze_layout = QVBoxLayout(self.maze_panel)
        maze_layout.addWidget(scroll_area)

        self.zoom_input = QSpinBox()
        self.zoom_input.setRange(5, 200)
        self.zoom_input.setSingleStep(5)
        self.zoom_input.setSuffix(" %")
        self.zoom_input.setValue(100)

        parameters_layout.addRow("Масштаб:", self.zoom_input)

        # При изменении числа передаём его методу поля.
        self.zoom_input.valueChanged.connect(self.canvas.set_zoom)

        editor_box = QGroupBox("Редактор")
        editor_layout = QFormLayout(editor_box)

        self.edit_mode_input = QComboBox()
        self.edit_mode_input.addItems(["Стены / проходы", "Старт", "Выход"])
        editor_layout.addRow("Инструмент:", self.edit_mode_input)

        # Передаём название выбранного инструмента полю.
        self.edit_mode_input.currentTextChanged.connect(
            self.canvas.set_edit_mode
        )

        clear_button = QPushButton("Очистить поле")
        clear_button.clicked.connect(self.canvas.clear_maze)
        editor_layout.addRow(clear_button)

        undo_button = QPushButton("Откатить клетку")
        undo_button.clicked.connect(self.canvas.undo_last_change)
        editor_layout.addRow(undo_button)

        # Вставляем редактор после параметров, перед пустым местом.
        self.controls_layout.insertWidget(1, editor_box)

        files_box = QGroupBox("Файлы")
        files_layout = QVBoxLayout(files_box)

        save_button = QPushButton("Сохранить в файл")
        save_button.clicked.connect(self.save_maze_to_file)
        files_layout.addWidget(save_button)

        # Размещаем блок после редактора.
        self.controls_layout.insertWidget(2, files_box)

        # Создаём и показываем начальный лабиринт.
        self.generate_new_maze()

    def generate_new_maze(self):
        width = self.width_input.value()
        height = self.height_input.value()

        # Создаём лабиринт и передаём его полю.
        self.maze = generate_maze(width, height)
        self.canvas.set_maze(self.maze)

        self.statusBar().showMessage(
            f"Сгенерирован лабиринт: {self.maze.cols} × {self.maze.rows}"
        )


    def save_maze_to_file(self):
        if self.maze is None:
            return

        # Открываем окно выбора имени и места сохранения.
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить лабиринт",
            "labyrinth.json",
            "Файлы JSON (*.json)",
        )

        # Пользователь нажал «Отмена».
        if not filename:
            return

        data = {
            "version": 1,
            "grid": self.maze.grid,
            "start": self.maze.start,
            "end": self.maze.end,
        }

        try:
            # Записываем данные без лишних пробелов.
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(data, file, separators=(",", ":"))
        except OSError as error:
            QMessageBox.warning(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить файл:\n{error}",
            )
            return

        self.statusBar().showMessage("Лабиринт сохранён")