from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QStackedWidget
)

from GUI.products_page import ProductsPage
from GUI.dashboard_page import DashboardPage
from GUI.stock_page import StockPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Warehouse ERP")
        self.setGeometry(100, 100, 1100, 650)

        # -------------------------
        # MAIN CONTAINER
        # -------------------------
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # -------------------------
        # SIDEBAR (NAVIGATION)
        # -------------------------
        sidebar = QVBoxLayout()

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_products = QPushButton("Products")
        self.btn_stock = QPushButton("Stock Movement")

        sidebar.addWidget(self.btn_dashboard)
        sidebar.addWidget(self.btn_products)
        sidebar.addWidget(self.btn_stock)

        sidebar.addStretch()

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)

        # -------------------------
        # STACKED PAGES SYSTEM
        # -------------------------
        self.pages = QStackedWidget()

        self.dashboard_page = DashboardPage()
        self.products_page = ProductsPage()
        self.stock_page = StockPage()

        self.pages.addWidget(self.dashboard_page)  # index 0
        self.pages.addWidget(self.products_page)    # index 1
        self.pages.addWidget(self.stock_page)       # index 2

        # -------------------------
        # BUTTON CONNECTIONS
        # -------------------------
        self.btn_dashboard.clicked.connect(self.show_dashboard)
        self.btn_products.clicked.connect(self.show_products)
        self.btn_stock.clicked.connect(self.show_stock)

        # -------------------------
        # FINAL LAYOUT
        # -------------------------
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(self.pages)

        # Default page
        self.pages.setCurrentIndex(0)

    # -------------------------
    # NAVIGATION METHODS
    # -------------------------
    def show_dashboard(self):
        self.pages.setCurrentIndex(0)

    def show_products(self):
        self.pages.setCurrentIndex(1)

    def show_stock(self):
        self.pages.setCurrentIndex(2)