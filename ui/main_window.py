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
from PyQt6.QtGui import QKeySequence, QShortcut, QColor
from PyQt6.QtCore import Qt, QEvent
from core.maze import generate_maze
from ui.canvas import MazeCanvas
import json
from core.storage import load_maze, MAX_MAZE_SIZE
from core.algorithms.bfs import bfs
from core.algorithms.bidirectional_bfs import bidirectional_bfs
from core.algorithms.dijkstra import dijkstra
from core.algorithms.a_star import A_star
from core.algorithms.dfs import dfs
from time import perf_counter
from ui.task_thread import TaskThread, calculate_comparison





class MainWindow(QMainWindow):
    def __init__(self):
        # Инициализация родительского класса QMainWindow.
        super().__init__()

        self.setWindowTitle("ProjectLabyrinth")
        self.resize(1600, 800)

        # Текущий лабиринт; пока не создан.
        self.maze = None

        # Поток текущего поиска; пока поиск не запущен.
        self.search_thread = None

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
        self.width_input.setRange(5, MAX_MAZE_SIZE)
        self.width_input.setValue(21)

        self.height_input = QSpinBox()
        self.height_input.setRange(5, MAX_MAZE_SIZE)
        self.height_input.setValue(21)

        parameters_layout.addRow("Ширина:", self.width_input)
        parameters_layout.addRow("Высота:", self.height_input)

        self.wall_removal_input = QSpinBox()
        self.wall_removal_input.setRange(0, 100)
        self.wall_removal_input.setSuffix(" %")
        self.wall_removal_input.setValue(5)

        parameters_layout.addRow("Удаление стен:", self.wall_removal_input)

        self.seed_input = QSpinBox()
        self.seed_input.setRange(-1, 2_147_483_647)

        # Вместо минимального значения показываем подпись.
        self.seed_input.setSpecialValueText("Случайный")
        self.seed_input.setValue(-1)

        parameters_layout.addRow("Seed:", self.seed_input)

        self.generate_button = QPushButton("Сгенерировать")
        self.generate_button.setProperty("role", "primary")
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

        # Сохраняем область прокрутки.
        self.scroll_area = scroll_area

        # Перехватываем события над лабиринтом и свободной областью вокруг него.
        self.canvas.installEventFilter(self)
        self.scroll_area.viewport().installEventFilter(self)

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

        # При смене алгоритма сбрасываем прежнее воспроизведение.
        self.algorithm_input.currentIndexChanged.connect(
            self.canvas.clear_search_result
        )

        algorithm_layout.addWidget(self.algorithm_input)

        self.playback_mode_input = QComboBox()
        self.playback_mode_input.addItems([
            "Анимация",
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
        run_button.setProperty("role", "primary")
        run_button.clicked.connect(self.run_selected_algorithm)
        algorithm_layout.addWidget(run_button)

        step_button = QPushButton("Шаг")
        step_button.clicked.connect(self.make_search_step)
        algorithm_layout.addWidget(step_button)

        pause_button = QPushButton("Пауза / Продолжить")
        pause_button.clicked.connect(self.canvas.toggle_animation_pause)
        algorithm_layout.addWidget(pause_button)

        reset_button = QPushButton("Сбросить анимацию")
        # Останавливаем воспроизведение и убираем подсветку поиска.
        reset_button.clicked.connect(self.canvas.clear_search_result)
        algorithm_layout.addWidget(reset_button)

        # Размещаем выбор алгоритма сразу после параметров.
        self.controls_layout.insertWidget(1, algorithm_box)

        # Справа показываем результат последнего запуска.
        self.results_panel.setTitle("Результаты")

        # Оставляем достаточно места для результатов.
        self.results_panel.setMinimumWidth(430)

        stats_box = QGroupBox("Последний запуск")
        stats_layout = QVBoxLayout(stats_box)

        labels = ["Алгоритм", "Длина пути", "Обработано клеток", "Время"]

        self.stats_table = QTableWidget(len(labels), 2)
        self.style_table(self.stats_table)

        # У статистики нет заголовков столбцов.
        self.stats_table.horizontalHeader().hide()
        self.stats_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.stats_table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.stats_table.setAlternatingRowColors(False)
        self.stats_table.setShowGrid(False)
        self.stats_table.setFixedHeight(len(labels) * 34 + 2)

        for row, label in enumerate(labels):
            self.stats_table.setItem(row, 0, QTableWidgetItem(label))

            # Значения выравниваем вправо и выделяем фоном.
            value_item = QTableWidgetItem("—")
            value_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            value_item.setBackground(QColor("#eef2f7"))

            self.stats_table.setItem(row, 1, value_item)

        stats_layout.addWidget(self.stats_table)


        # Создание сводной таблицы
        results_layout = QVBoxLayout(self.results_panel)
        results_layout.addWidget(stats_box)

        comparison_box = QGroupBox("Последнее сравнение")
        comparison_layout = QVBoxLayout(comparison_box)

        compare_button = QPushButton("Сравнить алгоритмы")
        compare_button.setProperty("role", "primary")
        compare_button.clicked.connect(self.compare_algorithms)
        comparison_layout.addWidget(compare_button)

        # Сначала строк нет; столбцов — четыре.
        self.comparison_table = QTableWidget(0, 4)
        self.style_table(self.comparison_table)
        self.comparison_table.setMinimumHeight(220)

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


        legend_box = QGroupBox("Легенда")
        legend_layout = QVBoxLayout(legend_box)
        legend_layout.setSpacing(6)

        # Цвета совпадают с отрисовкой в MazeCanvas.
        legend_items = [
            ("#1e293b", "Стена"),
            ("#ffffff", "Свободная клетка"),
            ("#7c3aed", "Открытый список — ожидает обработки"),
            ("#60a5fa", "Закрытый список — обработана"),
            ("#fde047", "Найденный путь"),
            ("#22c55e", "Старт"),
            ("#ef4444", "Выход"),
        ]

        for color, text in legend_items:
            row = QHBoxLayout()

            # Пустая подпись служит цветным квадратом.
            color_square = QLabel()
            color_square.setFixedSize(20, 20)
            color_square.setStyleSheet(
                f"background-color: {color};"
                "border: 1px solid #94a3b8;"
                "border-radius: 4px;"
            )

            description = QLabel(text)
            description.setWordWrap(True)

            row.addWidget(color_square)
            row.addWidget(description, 1)

            legend_layout.addLayout(row)

        results_layout.addWidget(legend_box)

        self.apply_style() # Стиль оформления
        # Создаём и показываем начальный лабиринт.
        self.generate_new_maze()

    def generate_new_maze(self):
        if self.search_thread is not None:
            return

        width = self.width_input.value()
        height = self.height_input.value()

        if not self.confirm_large_maze(width, height):
            return

        chance = self.wall_removal_input.value() / 100
        seed = self.seed_input.value()

        # None позволяет генератору выбрать случайное начальное состояние.
        if seed == -1:
            seed = None
        
        self.canvas.clear_search_result()

        # Создаём лабиринт в фоне.
        self.search_thread = TaskThread(
            generate_maze,
            args=(width, height),
            kwargs={
                "wall_removal_chance": chance,
                "seed": seed,
            },
            parent=self,
        )

        self.search_thread.finished.connect(self.finish_generation)

        self.set_search_busy(True)
        self.statusBar().showMessage("Генерация лабиринта…")
        self.search_thread.start()

    def finish_generation(self):
        thread = self.search_thread
        self.search_thread = None

        self.set_search_busy(False)
        thread.deleteLater()

        if thread.error is not None:
            self.statusBar().showMessage("Ошибка генерации")
            QMessageBox.warning(self, "Ошибка генерации", thread.error)
            return

        # Передаём готовый лабиринт полю в главном потоке.
        self.maze = thread.result
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

        if not self.confirm_large_maze(maze.cols, maze.rows):
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
        # Обычный запуск кнопкой «Запустить».
        self.start_search()

    def make_search_step(self):
        if self.maze is None or self.search_thread is not None:
            return

        if self.canvas.animation_result is None:
            # Результата ещё нет — вычисляем его для ручного просмотра.
            self.start_search(manual_step=True)
        else:
            # Результат готов — показываем следующий шаг.
            self.canvas.make_manual_step()


    def start_search(self, manual_step=False):
        # Не запускаем поиск повторно, пока предыдущий не завершился.
        if self.maze is None or self.search_thread is not None:
            return

        algorithm = self.algorithm_input.currentData()

        # Запоминаем настройки этого запуска.
        self.search_name = self.algorithm_input.currentText()
        self.search_mode = self.playback_mode_input.currentText()

        # Запоминаем, нужно ли показать только один шаг.
        self.manual_step = manual_step

        self.canvas.clear_search_result()

        # Создаём поток и указываем, что сделать после его завершения.
        self.search_thread = TaskThread(
            algorithm,
            args=(self.maze,),
            parent=self,
        )
        self.search_thread.finished.connect(self.finish_search)

        self.set_search_busy(True)
        self.update_statistics([self.search_name, "Расчёт…", "—", "—"])
        self.statusBar().showMessage("Выполняется поиск…")

        # Запускаем run() в отдельном потоке.
        self.search_thread.start()


    def finish_search(self):
        # Сохраняем завершившийся поток в локальную переменную.
        thread = self.search_thread
        self.search_thread = None

        self.set_search_busy(False)

        # Просим Qt удалить объект после обработки текущего события.
        thread.deleteLater()

        if thread.error is not None:
            self.update_statistics([self.search_name, "Ошибка", "—", "—"])
            self.statusBar().showMessage("Ошибка поиска")
            QMessageBox.warning(self, "Ошибка поиска", thread.error)
            return

        result = thread.result

        # Показываем готовый результат выбранным способом.
        if self.manual_step:
            # Подготавливаем просмотр без автоматического воспроизведения.
            self.canvas.start_animation(result, autoplay=False)
            self.canvas.make_manual_step()
        elif self.search_mode == "Анимация":
            self.canvas.start_animation(result)
        else:
            self.canvas.show_result(result)

        if result["distance"] is None:
            distance_text = "Нет пути"
        else:
            distance_text = f"{result['distance']} шагов"

        self.update_statistics([
            self.search_name,
            distance_text,
            result["visited_count"],
            f"{thread.elapsed_ms:.3f} мс",
        ])

        self.statusBar().showMessage("Расчёт завершён")


    def compare_algorithms(self):
        if self.maze is None or self.search_thread is not None:
            return

        # Читаем список из виджета до запуска фонового потока.
        algorithms = []

        for index in range(self.algorithm_input.count()):
            name = self.algorithm_input.itemText(index)
            algorithm = self.algorithm_input.itemData(index)
            algorithms.append((name, algorithm))

        self.canvas.clear_search_result()
        self.comparison_table.setRowCount(0)

        self.search_thread = TaskThread(
            calculate_comparison,
            args=(self.maze, algorithms),
            parent=self,
        )

        self.search_thread.finished.connect(self.finish_comparison)

        self.set_search_busy(True)
        self.statusBar().showMessage("Выполняется сравнение…")
        self.search_thread.start()

    def finish_comparison(self):
        thread = self.search_thread
        self.search_thread = None

        self.set_search_busy(False)
        thread.deleteLater()

        if thread.error is not None:
            self.statusBar().showMessage("Ошибка сравнения")
            QMessageBox.warning(self, "Ошибка сравнения", thread.error)
            return

        # Заполняем таблицу после завершения расчётов.
        for row, values in enumerate(thread.result):
            self.comparison_table.insertRow(row)

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)

                if column > 0:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight
                        | Qt.AlignmentFlag.AlignVCenter
                    )

                self.comparison_table.setItem(row, column, item)

        self.statusBar().showMessage("Сравнение завершено")


    def style_table(self, table):
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().hide()
        table.verticalHeader().setDefaultSectionSize(34)
        table.setAlternatingRowColors(True)

        table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f5f8fc;
                color: #0f172a;
                font-size: 13px;
                border: 1px solid #d5deeb;
                border-radius: 6px;
                gridline-color: #dde5ef;
                selection-background-color: #dbeafe;
                selection-color: #0f172a;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #edf2f8;
                color: #0f172a;
                font-weight: 600;
                padding: 6px;
                border: none;
                border-right: 1px solid #d5deeb;
                border-bottom: 1px solid #d5deeb;
            }
        """)

    def update_statistics(self, values):
        for row, value in enumerate(values):
            item = self.stats_table.item(row, 1)
            item.setText(str(value))
            item.setToolTip(str(value))


    def confirm_large_maze(self, width, height):
        # Для небольших размеров подтверждение не требуется.
        if width <= 599 and height <= 599:
            return True

        answer = QMessageBox.warning(
            self,
            "Большой лабиринт",
            f"Размер: {width} × {height} ({width * height:,} клеток).\n\n"
            "Генерация и поиск могут занять много времени и потребовать "
            "большого объёма оперативной памяти. Во время расчёта окно "
            "может временно не отвечать.\n\n"
            "Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        return answer == QMessageBox.StandardButton.Yes



    def set_search_busy(self, busy):
        # Пока идёт расчёт, запрещаем менять лабиринт и запускать новый поиск.
        self.controls_panel.setEnabled(not busy)
        self.results_panel.setEnabled(not busy)
        self.canvas.setEnabled(not busy)

        # Сочетание клавиш блокируем отдельно.
        self.undo_shortcut.setEnabled(not busy)


    def closeEvent(self, event):
        if self.search_thread is not None:
            # Не закрываем окно, пока его поток ещё работает.
            event.ignore()
            self.statusBar().showMessage(
                "Дождитесь завершения расчёта перед закрытием окна"
            )
            return

        super().closeEvent(event)


    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Wheel:
            # Проверяем, что колёсико прокручено над областью лабиринта.
            over_maze = (
                watched is self.canvas
                or watched is self.scroll_area.viewport()
            )

            ctrl_pressed = (
                event.modifiers() & Qt.KeyboardModifier.ControlModifier
            )

            if over_maze and ctrl_pressed:
                # Направление и величина прокрутки колёсика по вертикали
                delta = event.angleDelta().y()

                # Во время фонового расчёта масштабирование заблокировано.
                if self.zoom_input.isEnabled() and delta != 0:
                    direction = 1 if delta > 0 else -1
                    self.zoom_input.stepBy(direction)

                # Событие обработано; прокручивать поле не нужно.
                return True

        # Остальные события обрабатываются обычным способом.
        return super().eventFilter(watched, event)


    def apply_style(self):
        # Имя позволяет отдельно оформить фон центрального контейнера.
        self.centralWidget().setObjectName("appCentral")

        self.setStyleSheet("""
            QWidget {
                color: #0f172a;
                font-size: 13px;
            }

            QWidget#appCentral {
                background-color: #eef2f7;
            }

            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #d5deeb;
                border-radius: 8px;
                margin-top: 10px;
                padding: 6px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #1e3a5f;
            }

            QPushButton {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 5px 10px;
                font-weight: 600;
            }

            QPushButton:hover:enabled {
                background-color: #e2e8f0;
                border-color: #94a3b8;
            }

            QPushButton:pressed:enabled {
                background-color: #cbd5e1;
            }

            QPushButton[role="primary"] {
                background-color: #2563eb;
                color: #ffffff;
                border-color: #2563eb;
            }

            QPushButton[role="primary"]:hover:enabled {
                background-color: #1d4ed8;
                border-color: #1d4ed8;
            }

            QPushButton[role="primary"]:pressed:enabled {
                background-color: #1e40af;
                border-color: #1e40af;
            }

            QPushButton:disabled,
            QPushButton[role="primary"]:disabled {
                background-color: #e2e8f0;
                color: #94a3b8;
                border-color: #d5deeb;
            }

            QComboBox {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 5px;
                padding: 3px;
            }

            QComboBox:focus, QPushButton:focus {
                border: 1px solid #60a5fa;
            }

            QStatusBar {
                background-color: #ffffff;
                border-top: 1px solid #d5deeb;
            }
        """)