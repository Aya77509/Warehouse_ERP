import sys

from PyQt6.QtWidgets import QApplication

from GUI.main_window import MainWindow
from Infrastructure.product_repository import ProductRepository


def main():

    repo = ProductRepository()

    repo.create_table()
    repo.create_movement_table()


    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()