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
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt
from core.maze import generate_maze
from ui.canvas import MazeCanvas
import json
from core.storage import load_maze
from core.algorithms.bfs import bfs
from core.algorithms.bidirectional_bfs import bidirectional_bfs
from core.algorithms.dijkstra import dijkstra
from core.algorithms.a_star import A_star
from core.algorithms.dfs import dfs
from time import perf_counter


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

        self.wall_removal_input = QSpinBox()
        self.wall_removal_input.setRange(0, 100)
        self.wall_removal_input.setSuffix(" %")
        self.wall_removal_input.setValue(5)

        parameters_layout.addRow("Удаление стен:", self.wall_removal_input)

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

        undo_button = QPushButton("Откатить клетку (Ctrl+Z)")

        undo_button.clicked.connect(self.canvas.undo_last_change)
        editor_layout.addRow(undo_button)

        # Напрямую связываем Ctrl+Z с методом отката.
        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.canvas.undo_last_change)

        # Вставляем редактор после параметров, перед пустым местом.
        self.controls_layout.insertWidget(1, editor_box)

        files_box = QGroupBox("Файлы")
        files_layout = QVBoxLayout(files_box)


        load_button = QPushButton("Загрузить из файла")
        load_button.clicked.connect(self.load_maze_from_file)
        files_layout.addWidget(load_button)


        save_button = QPushButton("Сохранить в файл")
        save_button.clicked.connect(self.save_maze_to_file)
        files_layout.addWidget(save_button)

        # Размещаем блок после редактора.
        self.controls_layout.insertWidget(2, files_box)


        algorithm_box = QGroupBox("Алгоритм")
        algorithm_layout = QVBoxLayout(algorithm_box)

        self.algorithm_input = QComboBox()

        # Каждый пункт хранит название и соответствующую функцию.
        self.algorithm_input.addItem("BFS", bfs)
        self.algorithm_input.addItem("Двунаправленный BFS", bidirectional_bfs)
        self.algorithm_input.addItem("Дейкстра", dijkstra)
        self.algorithm_input.addItem("A*", A_star)
        self.algorithm_input.addItem("DFS", dfs)

        algorithm_layout.addWidget(self.algorithm_input)

        self.playback_mode_input = QComboBox()
        self.playback_mode_input.addItems([
            "Анимация",
            "Пошагово",
            "Мгновенно",
        ])
        algorithm_layout.addWidget(self.playback_mode_input)

        self.animation_delay_input = QSpinBox()
        self.animation_delay_input.setRange(0, 1000)
        self.animation_delay_input.setSuffix(" мс")
        self.animation_delay_input.setValue(100)

        algorithm_layout.addWidget(QLabel("Задержка между шагами:"))
        algorithm_layout.addWidget(self.animation_delay_input)

        # Изменение значения сразу меняет интервал таймера.
        self.animation_delay_input.valueChanged.connect(
            self.canvas.set_animation_interval
        )

        # Передаём начальное значение таймеру.
        self.canvas.set_animation_interval(
            self.animation_delay_input.value()
        )

        run_button = QPushButton("Запустить")
        run_button.clicked.connect(self.run_selected_algorithm)
        algorithm_layout.addWidget(run_button)

        step_button = QPushButton("Шаг")
        step_button.clicked.connect(self.canvas.make_manual_step)
        algorithm_layout.addWidget(step_button)

        pause_button = QPushButton("Пауза / Продолжить")
        pause_button.clicked.connect(self.canvas.toggle_animation_pause)
        algorithm_layout.addWidget(pause_button)

        # Размещаем выбор алгоритма сразу после параметров.
        self.controls_layout.insertWidget(1, algorithm_box)

        # Справа показываем результат последнего запуска.
        self.results_panel.setTitle("Результаты")

        self.stats_label = QLabel("Алгоритм ещё не запускался")
        self.stats_label.setWordWrap(True)


        # Создание сводной таблицы
        results_layout = QVBoxLayout(self.results_panel)
        results_layout.addWidget(self.stats_label)

        comparison_box = QGroupBox("Последнее сравнение")
        comparison_layout = QVBoxLayout(comparison_box)

        compare_button = QPushButton("Сравнить алгоритмы")
        compare_button.clicked.connect(self.compare_algorithms)
        comparison_layout.addWidget(compare_button)

        # Сначала строк нет; столбцов — четыре.
        self.comparison_table = QTableWidget(0, 4)
        self.comparison_table.setHorizontalHeaderLabels([
            "Алгоритм",
            "Длина",
            "Клетки",
            "Время, мс",
        ])

        # Запрещаем вручную менять результаты.
        self.comparison_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        # Выделяем строку целиком (при щелчке мышью).
        self.comparison_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        # Убираем номера строк и подбираем ширину столбцов по содержимому.
        self.comparison_table.verticalHeader().hide()
        self.comparison_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

        comparison_layout.addWidget(self.comparison_table)
        results_layout.addWidget(comparison_box)
        results_layout.addStretch()

        # Создаём и показываем начальный лабиринт.
        self.generate_new_maze()

    def generate_new_maze(self):
        width = self.width_input.value()
        height = self.height_input.value()

        
        # Переводим проценты в вероятность: например, 5 → 0.05.
        chance = self.wall_removal_input.value() / 100

        # Создаём лабиринт и передаём его полю.
        self.maze = generate_maze(
            width,
            height,
            wall_removal_chance=chance,
        )
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


    def load_maze_from_file(self):
        # Выбираем существующий файл.
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить лабиринт",
            "",
            "Файлы JSON (*.json)",
        )

        if not filename:
            return

        try:
            maze = load_maze(filename)
        except (OSError, ValueError, RecursionError) as error:
            QMessageBox.warning(self, "Ошибка загрузки", str(error))
            return

        # Заменяем текущее поле только после успешной проверки.
        self.maze = maze
        self.canvas.set_maze(maze)

        self.width_input.setValue(maze.cols)
        self.height_input.setValue(maze.rows)

        self.statusBar().showMessage(
            f"Загружен лабиринт: {maze.cols} × {maze.rows}"
        )




    def run_selected_algorithm(self):
        if self.maze is None:
            return

        # Получаем функцию и название выбранного алгоритма.
        algorithm = self.algorithm_input.currentData()
        name = self.algorithm_input.currentText()

        self.canvas.clear_search_result()

        started = perf_counter()

        try:
            result = algorithm(self.maze)
        except ValueError as error:
            self.stats_label.setText(f"Алгоритм: {name}\n{error}")
            return

        # Переводим длительность из секунд в миллисекунды.
        elapsed_ms = (perf_counter() - started) * 1000

        mode = self.playback_mode_input.currentText()

        if mode == "Анимация":
            self.canvas.start_animation(result)
        elif mode == "Пошагово":
            self.canvas.start_animation(result, autoplay=False)
        else:
            self.canvas.show_result(result)

        if result["distance"] is None:
            path_text = "Путь не найден"
        else:
            path_text = f"Длина пути: {result['distance']} шагов"

        self.stats_label.setText(
            f"Алгоритм: {name}\n"
            f"{path_text}\n"
            f"Обработано клеток: {result['visited_count']}\n"
            f"Время: {elapsed_ms:.3f} мс"
        )


    def compare_algorithms(self):
        if self.maze is None:
            return

        # Завершаем прежнее воспроизведение и очищаем таблицу.
        self.canvas.clear_search_result()
        self.comparison_table.setRowCount(0)

        for index in range(self.algorithm_input.count()):
            # Получаем название и функцию каждого алгоритма из списка.
            name = self.algorithm_input.itemText(index)
            algorithm = self.algorithm_input.itemData(index)

            started = perf_counter()

            try:
                result = algorithm(self.maze)
            except ValueError as error:
                self.comparison_table.setRowCount(0)
                QMessageBox.warning(
                    self,
                    "Ошибка сравнения",
                    f"{name}:\n{error}",
                )
                return

            elapsed_ms = (perf_counter() - started) * 1000

            if result["distance"] is None:
                distance_text = "Нет пути"
            else:
                distance_text = str(result["distance"])

            values = [
                name,
                distance_text,
                str(result["visited_count"]),
                f"{elapsed_ms:.3f}",
            ]

            # Добавляем строку в конец таблицы.
            row = self.comparison_table.rowCount()
            self.comparison_table.insertRow(row)

            # Заполняем четыре ячейки новой строки.
            for column, value in enumerate(values):
                self.comparison_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

            # Не храним историю поиска между запусками алгоритмов.
            del result

        self.statusBar().showMessage("Сравнение завершено")