from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from Kernel.product_service import ProductService
from Kernel.inventory_service import InventoryService


class StatCard(QFrame):
    """A small KPI card widget."""

    def __init__(self, title: str, value: str, color: str):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2a3142;
                border-radius: 10px;
                border-left: 4px solid {color};
            }}
        """)
        self.setMinimumHeight(90)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)

        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #ffffff;")

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #9aa5b1; font-size: 12px;")

        layout.addWidget(self.value_label)
        layout.addWidget(title_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class DashboardView(QWidget):
    """Dashboard tab: shows KPIs, low stock alerts, and recent movements."""

    def __init__(self, product_service: ProductService, inventory_service: InventoryService):
        super().__init__()
        self.product_service = product_service
        self.inventory_service = inventory_service
        self._alert_shown_this_session = False
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QLabel("Dashboard")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)

        # KPI cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)
        self.total_products_card = StatCard("Total Products", "0", "#3b82f6")
        self.total_stock_card = StatCard("Total Stock", "0", "#22c55e")
        self.low_stock_card = StatCard("Low Stock Alerts", "0", "#ef4444")
        cards_layout.addWidget(self.total_products_card)
        cards_layout.addWidget(self.total_stock_card)
        cards_layout.addWidget(self.low_stock_card)
        layout.addLayout(cards_layout)

        # Low stock + recent movements tables side by side
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(14)

        # Low stock table
        low_stock_box = QVBoxLayout()
        low_stock_title = QLabel("Low Stock Products")
        low_stock_title.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        self.low_stock_table = QTableWidget(0, 3)
        self.low_stock_table.setHorizontalHeaderLabels(["ID", "Name", "Quantity"])
        self._style_table(self.low_stock_table)
        low_stock_box.addWidget(low_stock_title)
        low_stock_box.addWidget(self.low_stock_table)

        # Recent movements table
        recent_box = QVBoxLayout()
        recent_title = QLabel("Recent Movements")
        recent_title.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        self.recent_table = QTableWidget(0, 4)
        self.recent_table.setHorizontalHeaderLabels(["Date", "Product", "Type", "Quantity"])
        self._style_table(self.recent_table)
        recent_box.addWidget(recent_title)
        recent_box.addWidget(self.recent_table)

        tables_layout.addLayout(low_stock_box)
        tables_layout.addLayout(recent_box)
        layout.addLayout(tables_layout)

    @staticmethod
    def _style_table(table: QTableWidget):
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2a3142;
                color: #e5e7eb;
                border: none;
                border-radius: 8px;
                gridline-color: #3a4256;
            }
            QHeaderView::section {
                background-color: #1e2530;
                color: #9aa5b1;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 6px;
            }
        """)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

    def refresh(self):
        """Reload all dashboard data from services."""
        try:
            total_products = self.product_service.get_total_products()
            total_stock = self.product_service.get_total_stock()
            low_stock_products = self.product_service.get_low_stock_products()
            expiring_products = self.product_service.get_expiring_soon_products()
            recent_movements = self.inventory_service.get_recent_movements(10)

            self.total_products_card.set_value(str(total_products))
            self.total_stock_card.set_value(str(total_stock))
            self.low_stock_card.set_value(str(len(low_stock_products)))

            self.low_stock_table.setRowCount(0)
            for p in low_stock_products:
                row = self.low_stock_table.rowCount()
                self.low_stock_table.insertRow(row)
                self.low_stock_table.setItem(row, 0, QTableWidgetItem(str(p.id)))
                self.low_stock_table.setItem(row, 1, QTableWidgetItem(p.name))
                qty_item = QTableWidgetItem(str(p.quantity))
                qty_item.setForeground(Qt.GlobalColor.red)
                self.low_stock_table.setItem(row, 2, qty_item)

            self.recent_table.setRowCount(0)
            for m in recent_movements:
                row = self.recent_table.rowCount()
                self.recent_table.insertRow(row)
                self.recent_table.setItem(row, 0, QTableWidgetItem(m.date))
                self.recent_table.setItem(row, 1, QTableWidgetItem(m.product_name))
                type_item = QTableWidgetItem(m.movement_type.value)
                type_item.setForeground(Qt.GlobalColor.green if m.movement_type.value == "IN" else Qt.GlobalColor.red)
                self.recent_table.setItem(row, 2, type_item)
                self.recent_table.setItem(row, 3, QTableWidgetItem(str(m.quantity)))

            if not self._alert_shown_this_session:
                self._alert_shown_this_session = True
                self._show_startup_alert(low_stock_products, expiring_products)
        except Exception as e:
            print(f"Dashboard refresh error: {e}")

    def _show_startup_alert(self, low_stock_products, expiring_products):
        """Shows a one-time popup summarizing low stock and expiring products."""
        if not low_stock_products and not expiring_products:
            return

        lines = []
        if low_stock_products:
            lines.append(f"⚠ {len(low_stock_products)} product(s) are low on stock:")
            for p in low_stock_products[:5]:
                lines.append(f"   • {p.name} (qty: {p.quantity})")
            if len(low_stock_products) > 5:
                lines.append(f"   ...and {len(low_stock_products) - 5} more")

        if expiring_products:
            if lines:
                lines.append("")
            lines.append(f"⏳ {len(expiring_products)} product(s) are expired or expiring soon:")
            for p in expiring_products[:5]:
                days = p.days_until_expiration()
                status = "EXPIRED" if days is not None and days < 0 else f"in {days} day(s)"
                lines.append(f"   • {p.name} — {status} ({p.expiration_date})")
            if len(expiring_products) > 5:
                lines.append(f"   ...and {len(expiring_products) - 5} more")

        QMessageBox.warning(self, "Inventory Alerts", "\n".join(lines))