from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from Kernel.entities import User
from Kernel.product_service import ProductService
from Kernel.inventory_service import InventoryService
from Kernel.supplier_service import SupplierService
from Kernel.report_service import ReportService

from GUI.dashboard_view import DashboardView
from GUI.product_view import ProductView
from GUI.inventory_view import InventoryView
from GUI.supplier_view import SupplierView
from GUI.report_view import ReportView


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""

    def __init__(self, user: User, product_service: ProductService,
                 inventory_service: InventoryService, supplier_service: SupplierService,
                 report_service: ReportService, on_logout_callback):
        super().__init__()
        self.user = user
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.supplier_service = supplier_service
        self.report_service = report_service
        self.on_logout_callback = on_logout_callback

        self.setWindowTitle("Warehouse Management ERP")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet("background-color: #1e2530;")

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background-color: #161b26;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo / title
        logo_box = QFrame()
        logo_box.setFixedHeight(70)
        logo_layout = QVBoxLayout(logo_box)
        logo_label = QLabel("Warehouse ERP")
        logo_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        logo_label.setStyleSheet("color: #ffffff;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        sidebar_layout.addWidget(logo_box)

        # User info
        user_label = QLabel(f"{self.user.username}\n({self.user.role.value.upper()})")
        user_label.setStyleSheet("color: #9aa5b1; font-size: 12px; padding: 10px 20px;")
        sidebar_layout.addWidget(user_label)

        # Navigation list
        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #161b26;
                border: none;
                outline: none;
            }
            QListWidget::item {
                color: #9aa5b1;
                padding: 14px 20px;
                font-size: 13px;
            }
            QListWidget::item:selected {
                background-color: #2a3142;
                color: #ffffff;
                border-left: 3px solid #3b82f6;
            }
            QListWidget::item:hover {
                background-color: #1e2530;
            }
        """)

        nav_items = ["Dashboard", "Products", "Inventory", "Suppliers", "Reports"]
        for item_text in nav_items:
            item = QListWidgetItem(item_text)
            self.nav_list.addItem(item)

        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        sidebar_layout.addWidget(self.nav_list)

        sidebar_layout.addStretch()

        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                padding: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        logout_btn.clicked.connect(self._handle_logout)
        sidebar_layout.addWidget(logout_btn)

        root_layout.addWidget(sidebar)

        # Stacked content area
        self.stack = QStackedWidget()

        self.dashboard_view = DashboardView(self.product_service, self.inventory_service)
        self.product_view = ProductView(self.product_service, self.supplier_service, self._on_data_change)
        self.inventory_view = InventoryView(self.product_service, self.inventory_service, self._on_data_change)
        self.supplier_view = SupplierView(self.supplier_service, self._on_data_change)
        self.report_view = ReportView(self.report_service)

        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.product_view)
        self.stack.addWidget(self.inventory_view)
        self.stack.addWidget(self.supplier_view)
        self.stack.addWidget(self.report_view)

        root_layout.addWidget(self.stack)

        self.nav_list.setCurrentRow(0)

    def _on_nav_changed(self, index: int):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.dashboard_view.refresh()
        elif index == 1:
            self.product_view.refresh()
        elif index == 2:
            self.inventory_view.refresh()
        elif index == 3:
            self.supplier_view.refresh()

    def _on_data_change(self):
        """Called whenever data changes anywhere to keep dashboard fresh."""
        self.dashboard_view.refresh()

    def _handle_logout(self):
        self.close()
        self.on_logout_callback()