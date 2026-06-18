from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import Qt, QSize
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

from GUI.theme import (
    BG, SURFACE, SURFACE_3, BORDER, TEXT, TEXT_MUTED,
    PRIMARY, PRIMARY_SOFT, DANGER, DANGER_DK,
    FS_BODY, FS_MICRO, RADIUS_MD,
    Icons, qicon,
)


class MainWindow(QMainWindow):
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
        self.setMinimumSize(1200, 760)
        self.setStyleSheet(f"background-color: {BG};")
        self._build_ui()
        self.showMaximized()

    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # ---------- Sidebar ---------- #
        sidebar = QFrame()
        sidebar.setFixedWidth(248)
        sidebar.setStyleSheet(
            f"background-color: {SURFACE}; border-right: 1px solid {BORDER};"
        )
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0, 0, 0, 0); side.setSpacing(0)

        # Brand
        brand_box = QFrame(); brand_box.setFixedHeight(76)
        brand_box.setStyleSheet(f"background:{SURFACE}; border-bottom: 1px solid {BORDER};")
        brand_lay = QHBoxLayout(brand_box)
        brand_lay.setContentsMargins(22, 0, 22, 0); brand_lay.setSpacing(12)
        logo = QLabel()
        logo.setPixmap(qicon(Icons.BRAND).pixmap(QSize(26, 26)))
        logo.setStyleSheet("background: transparent;")
        name = QLabel("Warehouse <b>ERP</b>")
        name.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        name.setStyleSheet(f"color: {TEXT}; background: transparent;")
        brand_lay.addWidget(logo); brand_lay.addWidget(name); brand_lay.addStretch()
        side.addWidget(brand_box)

        # User chip
        user_box = QFrame()
        user_box.setStyleSheet(f"background:{SURFACE}; border-bottom: 1px solid {BORDER};")
        user_lay = QHBoxLayout(user_box)
        user_lay.setContentsMargins(20, 14, 20, 14); user_lay.setSpacing(12)
        avatar = QLabel()
        avatar.setPixmap(qicon(Icons.USER).pixmap(QSize(20, 20)))
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"background-color: {PRIMARY_SOFT}; border-radius: 20px;"
        )
        user_text = QLabel(
            f"<div style='color:{TEXT}; font-weight:600;'>{self.user.username}</div>"
            f"<div style='color:{TEXT_MUTED}; font-size:{FS_MICRO}px;'>"
            f"{self.user.role.value.upper()}</div>"
        )
        user_text.setStyleSheet("background: transparent;")
        user_lay.addWidget(avatar); user_lay.addWidget(user_text, 1)
        side.addWidget(user_box)

        # Nav label
        nav_label = QLabel("  MAIN MENU")
        nav_label.setStyleSheet(
            f"color: {TEXT_MUTED}; background:{SURFACE}; "
            f"padding: 16px 22px 6px 22px; font-size: 10px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )
        side.addWidget(nav_label)

        # Nav list
        self.nav_list = QListWidget()
        self.nav_list.setIconSize(QSize(18, 18))
        self.nav_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {SURFACE};
                border: none; outline: none;
                padding: 4px 12px;
            }}
            QListWidget::item {{
                color: {TEXT_MUTED};
                padding: 11px 14px;
                font-size: {FS_BODY}px;
                border-radius: {RADIUS_MD}px;
                margin: 3px 0;
            }}
            QListWidget::item:selected {{
                background-color: {PRIMARY_SOFT};
                color: {PRIMARY};
                font-weight: 600;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {SURFACE_3};
                color: {TEXT};
            }}
        """)

        nav_items = [
            ("Dashboard", Icons.DASHBOARD),
            ("Products",  Icons.PRODUCTS),
            ("Inventory", Icons.INVENTORY),
            ("Suppliers", Icons.SUPPLIERS),
            ("Reports",   Icons.REPORTS),
        ]
        for text, sp in nav_items:
            item = QListWidgetItem(qicon(sp), "  " + text)
            self.nav_list.addItem(item)

        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        side.addWidget(self.nav_list)
        side.addStretch()

        # Logout
        logout_btn = QPushButton("  Sign out")
        logout_btn.setIcon(qicon(Icons.LOGOUT))
        logout_btn.setIconSize(QSize(16, 16))
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE};
                color: {DANGER};
                border: none;
                border-top: 1px solid {BORDER};
                padding: 16px 22px;
                font-weight: 600;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: #fef2f2;
                color: {DANGER_DK};
            }}
        """)
        logout_btn.clicked.connect(self._handle_logout)
        side.addWidget(logout_btn)

        root.addWidget(sidebar)

        # ---------- Stacked content ---------- #
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {BG};")
        self.dashboard_view = DashboardView(self.product_service, self.inventory_service)
        self.product_view   = ProductView(self.product_service, self.supplier_service, self._on_data_change)
        self.inventory_view = InventoryView(self.product_service, self.inventory_service, self._on_data_change)
        self.supplier_view  = SupplierView(self.supplier_service, self._on_data_change)
        self.report_view    = ReportView(self.report_service)

        for w in (self.dashboard_view, self.product_view, self.inventory_view,
                  self.supplier_view, self.report_view):
            self.stack.addWidget(w)

        root.addWidget(self.stack, 1)
        self.nav_list.setCurrentRow(0)

    def _on_nav_changed(self, index: int):
        self.stack.setCurrentIndex(index)
        if index == 0:   self.dashboard_view.refresh()
        elif index == 1: self.product_view.refresh()
        elif index == 2: self.inventory_view.refresh()
        elif index == 3: self.supplier_view.refresh()

    def _on_data_change(self):
        self.dashboard_view.refresh()

    def _handle_logout(self):
        self.close()
        self.on_logout_callback()
