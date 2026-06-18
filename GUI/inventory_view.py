from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QComboBox, QSpinBox, QLineEdit, QTabWidget,
)
from PyQt6.QtCore import Qt

from Kernel.product_service import ProductService
from Kernel.inventory_service import InventoryService

from GUI.theme import (
    BG, SURFACE, SURFACE_2, BORDER, TEXT, TEXT_MUTED, PRIMARY,
    FS_BODY, RADIUS_MD, RADIUS_LG,
    Icons, qicon, primary_button, input_style, style_table,
    status_badge, page_header, card_frame,
)


class StockMovementForm(QWidget):
    def __init__(self, movement_type: str, product_service: ProductService,
                 inventory_service: InventoryService, on_change_callback=None):
        super().__init__()
        self.movement_type = movement_type
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.on_change_callback = on_change_callback
        self.setStyleSheet(f"background-color: {SURFACE};")
        self._build_ui()
        self.refresh_products()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24); outer.setSpacing(16)

        card = card_frame(padding=22)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(22, 22, 22, 22); inner.setSpacing(14)

        is_in = self.movement_type == "IN"
        title = QLabel("Record Stock IN" if is_in else "Record Stock OUT")
        title.setStyleSheet(f"color:{TEXT}; font-size:16px; font-weight:700;")
        subtitle = QLabel("Incoming inventory from suppliers" if is_in else "Outgoing inventory for orders / usage")
        subtitle.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px;")
        inner.addWidget(title); inner.addWidget(subtitle)

        # Form grid
        form = QHBoxLayout(); form.setSpacing(10)
        self.product_combo = QComboBox(); self.product_combo.setMinimumWidth(220)
        self.product_combo.setStyleSheet(input_style())
        self.quantity_input = QSpinBox(); self.quantity_input.setRange(1, 1_000_000)
        self.quantity_input.setStyleSheet(input_style())
        self.note_input = QLineEdit(); self.note_input.setPlaceholderText("Note (optional)")
        self.note_input.setStyleSheet(input_style())

        variant = "success" if is_in else "danger"
        action_btn = primary_button(
            f"Stock {self.movement_type}",
            Icons.STOCK_IN if is_in else Icons.STOCK_OUT,
            variant=variant,
        )
        action_btn.clicked.connect(self._perform_movement)

        for lbl_text, w in (("Product", self.product_combo),
                            ("Quantity", self.quantity_input),
                            ("Note", self.note_input)):
            box = QVBoxLayout(); box.setSpacing(4)
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px; font-weight:700; letter-spacing:0.5px;")
            box.addWidget(lbl); box.addWidget(w)
            form.addLayout(box, 1)
        form.addWidget(action_btn, 0, Qt.AlignmentFlag.AlignBottom)
        inner.addLayout(form)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        inner.addWidget(self.info_label)

        outer.addWidget(card)
        outer.addStretch()
        self.product_combo.currentIndexChanged.connect(self._update_info)

    def refresh_products(self):
        try:
            current_id = self.product_combo.currentData()
            self.product_combo.clear()
            for p in self.product_service.list_products():
                self.product_combo.addItem(f"{p.name}  (ID {p.id})", p.id)
            if current_id is not None:
                idx = self.product_combo.findData(current_id)
                if idx >= 0: self.product_combo.setCurrentIndex(idx)
            self._update_info()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {e}")

    def _update_info(self):
        pid = self.product_combo.currentData()
        if pid is None: self.info_label.setText(""); return
        try:
            p = self.product_service.get_product(pid)
            self.info_label.setText(
                f"Current stock: {p.quantity}    ·    Low-stock threshold: {p.low_stock_threshold}"
            )
        except ValueError:
            self.info_label.setText("")

    def _perform_movement(self):
        pid = self.product_combo.currentData()
        if pid is None:
            QMessageBox.information(self, "No Product", "No products available. Please add a product first."); return
        qty = self.quantity_input.value(); note = self.note_input.text()
        try:
            if self.movement_type == "IN":
                self.inventory_service.stock_in(pid, qty, note)
            else:
                self.inventory_service.stock_out(pid, qty, note)
            QMessageBox.information(self, "Success", f"Stock {self.movement_type} recorded successfully.")
            self.note_input.clear(); self._update_info()
            if self.on_change_callback: self.on_change_callback()
        except ValueError as e: QMessageBox.warning(self, "Operation Failed", str(e))
        except Exception as e: QMessageBox.critical(self, "Error", f"Unexpected error: {e}")


class HistoryTable(QWidget):
    def __init__(self, inventory_service: InventoryService):
        super().__init__()
        self.inventory_service = inventory_service
        self.setStyleSheet(f"background-color: {SURFACE};")
        self._build_ui(); self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Date", "Product", "Type", "Quantity", "Note"])
        style_table(self.table)
        layout.addWidget(self.table)

    def refresh(self):
        try:
            movements = self.inventory_service.get_history()
            self.table.setRowCount(0)
            for m in movements:
                row = self.table.rowCount(); self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(m.date))
                self.table.setItem(row, 1, QTableWidgetItem(m.product_name))
                mtype = m.movement_type.value
                self.table.setCellWidget(row, 2,
                    status_badge(mtype, "success" if mtype == "IN" else "danger"))
                qty_item = QTableWidgetItem(str(m.quantity))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, qty_item)
                self.table.setItem(row, 4, QTableWidgetItem(m.note))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load history: {e}")


class InventoryView(QWidget):
    def __init__(self, product_service: ProductService, inventory_service: InventoryService,
                 on_change_callback=None):
        super().__init__()
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.on_change_callback = on_change_callback
        self.setStyleSheet(f"background-color: {BG};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24); layout.setSpacing(18)
        layout.addWidget(page_header("Inventory", "Stock movements and history"))

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                border-radius: {RADIUS_LG}px;
                background: {SURFACE};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {TEXT_MUTED};
                padding: 10px 20px;
                border: 1px solid transparent;
                border-top-left-radius: {RADIUS_MD}px;
                border-top-right-radius: {RADIUS_MD}px;
                margin-right: 4px;
                font-weight: 600;
                font-size: {FS_BODY}px;
            }}
            QTabBar::tab:selected {{
                background-color: {SURFACE};
                color: {PRIMARY};
                border: 1px solid {BORDER};
                border-bottom-color: {SURFACE};
            }}
            QTabBar::tab:hover:!selected {{ color: {TEXT}; }}
        """)

        self.stock_in_form  = StockMovementForm("IN",  self.product_service, self.inventory_service, self._on_movement)
        self.stock_out_form = StockMovementForm("OUT", self.product_service, self.inventory_service, self._on_movement)
        self.history_table  = HistoryTable(self.inventory_service)

        self.tabs.addTab(self.stock_in_form,  qicon(Icons.STOCK_IN),  "  Stock IN")
        self.tabs.addTab(self.stock_out_form, qicon(Icons.STOCK_OUT), "  Stock OUT")
        self.tabs.addTab(self.history_table,  qicon(Icons.HISTORY),   "  History")
        layout.addWidget(self.tabs)

    def _on_movement(self):
        self.history_table.refresh()
        self.stock_in_form.refresh_products()
        self.stock_out_form.refresh_products()
        if self.on_change_callback: self.on_change_callback()

    def refresh(self):
        self.stock_in_form.refresh_products()
        self.stock_out_form.refresh_products()
        self.history_table.refresh()
