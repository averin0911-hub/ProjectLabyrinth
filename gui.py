import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    # Создаём приложение Qt и передаём аргументы запуска.
    app = QApplication(sys.argv)

    # Создаём и показываем главное окно.
    window = MainWindow()
    window.show()

    # Обрабатываем события до закрытия окна, затем завершаем программу.
    sys.exit(app.exec())


# Запускаем main только при прямом запуске этого файла.
if __name__ == "__main__":
    main()
