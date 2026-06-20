from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox,
    QSpinBox, QDoubleSpinBox, QDialog, QFormLayout, QDialogButtonBox,
    QDateEdit, QCheckBox, QFrame, QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QDate, QTimer, QPropertyAnimation
from PyQt6.QtGui import QColor

from Kernel.product_service import ProductService
from Kernel.supplier_service import SupplierService
from Kernel.category_service import CategoryService
from Kernel.entities import Product

from GUI.theme import (
    BG, SURFACE, TEXT, TEXT_MUTED, DANGER,
    Icons, primary_button, input_style, style_table,
    status_badge, page_header,
)


EXPIRY_WARNING_DAYS = 30  # configurable warning window


# ---------- Toast notification ----------
class Toast(QFrame):
    """Small auto-dismissing notification banner."""
    PALETTE = {
        "success": ("#e8f7ee", "#bfe6cb", "#1f7a3a"),
        "error":   ("#fdecec", "#f5c2c2", "#a4202b"),
        "info":    ("#eaf2fd", "#c7dcf7", "#1f4e8a"),
        "warning": ("#fff6e5", "#f5d99a", "#8a5b0a"),
    }

    def __init__(self, parent, message: str, kind: str = "success", duration_ms: int = 2500):
        super().__init__(parent)
        bg, border, fg = self.PALETTE.get(kind, self.PALETTE["info"])
        self.setStyleSheet(
            f"background-color:{bg}; border:1px solid {border};"
            f"border-radius:8px; color:{fg}; font-weight:600;"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lbl = QLabel(message)
        lbl.setStyleSheet(f"color:{fg}; background:transparent; border:none;")
        lay.addWidget(lbl)
        self.adjustSize()
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)
        self._fade_in = QPropertyAnimation(self._effect, b"opacity", self)
        self._fade_in.setDuration(180); self._fade_in.setStartValue(0.0); self._fade_in.setEndValue(1.0)
        self._fade_out = QPropertyAnimation(self._effect, b"opacity", self)
        self._fade_out.setDuration(220); self._fade_out.setStartValue(1.0); self._fade_out.setEndValue(0.0)
        self._fade_out.finished.connect(self.deleteLater)
        self._fade_in.start()
        QTimer.singleShot(duration_ms, self._fade_out.start)


# ---------- Product dialog ----------
class ProductDialog(QDialog):
    def __init__(self, supplier_service: SupplierService, category_service: CategoryService,
                 product: Product | None = None):
        super().__init__()
        self.supplier_service = supplier_service
        self.category_service = category_service
        self.product = product
        self.setWindowTitle("Edit Product" if product else "Add Product")
        self.setMinimumWidth(440)
        self.setStyleSheet(f"background-color: {SURFACE}; color: {TEXT}; {input_style()}")
        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(12)

        self.name_input = QLineEdit()
        self.quantity_input = QSpinBox(); self.quantity_input.setRange(0, 1_000_000)
        self.threshold_input = QSpinBox(); self.threshold_input.setRange(0, 1_000_000)
        self.threshold_input.setValue(10)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.0, 1_000_000.0); self.price_input.setDecimals(2)
        self.price_input.setSingleStep(0.5); self.price_input.setPrefix("$ ")

        self.category_combo = QComboBox(); self.category_combo.addItem("None", None)
        for c in self.category_service.list_categories():
            self.category_combo.addItem(c.name, c.id)

        self.supplier_combo = QComboBox(); self.supplier_combo.addItem("None", None)
        for s in self.supplier_service.list_suppliers():
            self.supplier_combo.addItem(s.name, s.id)

        self.no_expiration_checkbox = QCheckBox("No expiration date")
        self.no_expiration_checkbox.setChecked(True)
        self.no_expiration_checkbox.stateChanged.connect(self._toggle_expiration_input)
        self.expiration_input = QDateEdit()
        self.expiration_input.setCalendarPopup(True)
        self.expiration_input.setDisplayFormat("yyyy-MM-dd")
        self.expiration_input.setDate(QDate.currentDate())
        self.expiration_input.setEnabled(False)

        if self.product:
            self.name_input.setText(self.product.name)
            self.quantity_input.setValue(self.product.quantity)
            self.threshold_input.setValue(self.product.low_stock_threshold)
            self.price_input.setValue(self.product.price)
            if self.product.category_id is not None:
                idx = self.category_combo.findData(self.product.category_id)
                if idx >= 0: self.category_combo.setCurrentIndex(idx)
            if self.product.supplier_id is not None:
                idx = self.supplier_combo.findData(self.product.supplier_id)
                if idx >= 0: self.supplier_combo.setCurrentIndex(idx)
            if self.product.expiration_date:
                self.no_expiration_checkbox.setChecked(False)
                qd = QDate.fromString(self.product.expiration_date, "yyyy-MM-dd")
                if qd.isValid(): self.expiration_input.setDate(qd)

        layout.addRow("Name *", self.name_input)
        layout.addRow("Category", self.category_combo)
        layout.addRow("Price", self.price_input)
        layout.addRow("Quantity", self.quantity_input)
        layout.addRow("Low Stock Threshold", self.threshold_input)
        layout.addRow("Supplier", self.supplier_combo)
        layout.addRow("", self.no_expiration_checkbox)
        layout.addRow("Expiration Date", self.expiration_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _toggle_expiration_input(self, _):
        self.expiration_input.setEnabled(not self.no_expiration_checkbox.isChecked())

    def _on_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation", "Product name is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        expiration_date = None
        if not self.no_expiration_checkbox.isChecked():
            expiration_date = self.expiration_input.date().toString("yyyy-MM-dd")
        return {
            "name": self.name_input.text().strip(),
            "quantity": self.quantity_input.value(),
            "low_stock_threshold": self.threshold_input.value(),
            "supplier_id": self.supplier_combo.currentData(),
            "category_id": self.category_combo.currentData(),
            "expiration_date": expiration_date,
            "price": round(self.price_input.value(), 2),
        }


# ---------- Product view ----------
class ProductView(QWidget):
    def __init__(self, product_service: ProductService, supplier_service: SupplierService,
                 category_service: CategoryService, on_change_callback=None):
        super().__init__()
        self.product_service = product_service
        self.supplier_service = supplier_service
        self.category_service = category_service
        self.on_change_callback = on_change_callback
        self.setStyleSheet(f"background-color: {BG};")
        self._build_ui()
        self.refresh()

    # ---------- UI build ----------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24); layout.setSpacing(16)
        layout.addWidget(page_header("Products", "Manage your product catalog"))

        # Toast host (floating area at top)
        self._toast_host = QVBoxLayout(); self._toast_host.setSpacing(6)
        layout.addLayout(self._toast_host)

        # Toolbar
        toolbar = QHBoxLayout(); toolbar.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or category…")
        self.search_input.setStyleSheet(input_style())
        self.search_input.setMinimumWidth(280)

        # Debounced search for snappy UX
        self._search_timer = QTimer(self); self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(150)
        self._search_timer.timeout.connect(self.refresh)
        self.search_input.textChanged.connect(lambda _=None: self._search_timer.start())

        self.expiry_filter = QComboBox()
        self.expiry_filter.addItems(["All", "Expiring soon", "Expired", "No expiration"])
        self.expiry_filter.setStyleSheet(input_style())
        self.expiry_filter.currentIndexChanged.connect(self.refresh)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Sort: Name", "Sort: Expiration ↑", "Sort: Quantity ↑", "Sort: Price ↑"])
        self.sort_combo.setStyleSheet(input_style())
        self.sort_combo.currentIndexChanged.connect(self.refresh)

        add_btn    = primary_button("Add Product", Icons.ADD,    "success")
        edit_btn   = primary_button("Edit",        Icons.EDIT,   "primary")
        delete_btn = primary_button("Delete",      Icons.DELETE, "danger")
        add_btn.clicked.connect(self._add_product)
        edit_btn.clicked.connect(self._edit_product)
        delete_btn.clicked.connect(self._delete_product)

        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.expiry_filter)
        toolbar.addWidget(self.sort_combo)
        toolbar.addStretch()
        toolbar.addWidget(add_btn); toolbar.addWidget(edit_btn); toolbar.addWidget(delete_btn)
        layout.addLayout(toolbar)

        # Main products table
        title = QLabel("All Products")
        title.setStyleSheet(f"color:{TEXT}; font-size:14px; font-weight:700;")
        layout.addWidget(title)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Category", "Price", "Quantity", "Threshold",
             "Supplier", "Expiration", "Status"]
        )
        style_table(self.table)
        layout.addWidget(self.table)

        # Low-stock table
        low_title = QLabel("⚠  Low Stock Products")
        low_title.setStyleSheet(f"color:{TEXT}; font-size:14px; font-weight:700; margin-top:6px;")
        layout.addWidget(low_title)

        self.low_table = QTableWidget(0, 5)
        self.low_table.setHorizontalHeaderLabels(
            ["Name", "Category", "Stock", "Price", "Expiration"]
        )
        style_table(self.low_table)
        self.low_table.setMaximumHeight(220)
        layout.addWidget(self.low_table)

    # ---------- Toast helper ----------
    def show_toast(self, message: str, kind: str = "success"):
        toast = Toast(self, message, kind)
        self._toast_host.addWidget(toast, 0, Qt.AlignmentFlag.AlignHCenter)

    # ---------- Expiration helpers ----------
    @staticmethod
    def _parse_date(s: str | None):
        if not s: return None
        try: return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception: return None

    def _expiry_state(self, p) -> str:
        """Returns 'expired' | 'soon' | 'ok' | 'none'."""
        d = self._parse_date(getattr(p, "expiration_date", None))
        if d is None: return "none"
        today = datetime.today().date()
        if d < today: return "expired"
        if (d - today).days <= EXPIRY_WARNING_DAYS: return "soon"
        return "ok"

    # ---------- Refresh ----------
    def refresh(self):
        try:
            keyword = self.search_input.text().strip().lower()
            products = self.product_service.search_products("")  # get all, filter locally
            suppliers = {s.id: s.name for s in self.supplier_service.list_suppliers()}
            categories = {c.id: c.name for c in self.category_service.list_categories()}

            # name + category filter
            if keyword:
                def match(p):
                    name = (p.name or "").lower()
                    cat = (categories.get(p.category_id, "") or "").lower()
                    return keyword in name or keyword in cat
                products = [p for p in products if match(p)]

            # expiry filter
            f = self.expiry_filter.currentText()
            if f == "Expiring soon":
                products = [p for p in products if self._expiry_state(p) == "soon"]
            elif f == "Expired":
                products = [p for p in products if self._expiry_state(p) == "expired"]
            elif f == "No expiration":
                products = [p for p in products if not getattr(p, "expiration_date", None)]

            # sort
            mode = self.sort_combo.currentText()
            if mode == "Sort: Name":
                products.sort(key=lambda p: (p.name or "").lower())
            elif mode == "Sort: Expiration ↑":
                far = datetime(9999, 12, 31).date()
                products.sort(key=lambda p: self._parse_date(getattr(p, "expiration_date", None)) or far)
            elif mode == "Sort: Quantity ↑":
                products.sort(key=lambda p: p.quantity)
            elif mode == "Sort: Price ↑":
                products.sort(key=lambda p: p.price)

            # ----- main table -----
            self.table.setRowCount(0)
            for p in products:
                row = self.table.rowCount(); self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(p.id)))
                self.table.setItem(row, 1, QTableWidgetItem(p.name))
                self.table.setItem(row, 2, QTableWidgetItem(categories.get(p.category_id, "") or "—"))

                price_item = QTableWidgetItem(f"${p.price:,.2f}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, price_item)

                qty_item = QTableWidgetItem(str(p.quantity))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if p.is_low_stock(): qty_item.setForeground(QColor(DANGER))
                self.table.setItem(row, 4, qty_item)

                th_item = QTableWidgetItem(str(p.low_stock_threshold))
                th_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 5, th_item)

                supplier_name = suppliers.get(p.supplier_id, "—") if p.supplier_id else "—"
                self.table.setItem(row, 6, QTableWidgetItem(supplier_name))

                # Expiration cell — highlight red when expired/soon
                state = self._expiry_state(p)
                exp_text = p.expiration_date or "—"
                if state == "expired": exp_text = f"{p.expiration_date}  (EXPIRED)"
                exp_item = QTableWidgetItem(exp_text)
                if state in ("expired", "soon"):
                    exp_item.setForeground(QColor(DANGER))
                self.table.setItem(row, 7, exp_item)

                # status badge
                if state == "expired":
                    badge = status_badge("EXPIRED", "danger")
                elif p.is_low_stock():
                    badge = status_badge("LOW STOCK", "warning")
                elif state == "soon":
                    badge = status_badge("EXPIRING", "warning")
                else:
                    badge = status_badge("IN STOCK", "success")
                self.table.setCellWidget(row, 8, badge)

            # ----- low stock table -----
            low = [p for p in products if p.is_low_stock()]
            self.low_table.setRowCount(0)
            for p in low:
                r = self.low_table.rowCount(); self.low_table.insertRow(r)
                self.low_table.setItem(r, 0, QTableWidgetItem(p.name))
                self.low_table.setItem(r, 1, QTableWidgetItem(categories.get(p.category_id, "") or "—"))
                qi = QTableWidgetItem(str(p.quantity))
                qi.setForeground(QColor(DANGER))
                qi.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.low_table.setItem(r, 2, qi)
                self.low_table.setItem(r, 3, QTableWidgetItem(f"${p.price:,.2f}"))
                state = self._expiry_state(p)
                ei = QTableWidgetItem(p.expiration_date or "—")
                if state in ("expired", "soon"): ei.setForeground(QColor(DANGER))
                self.low_table.setItem(r, 4, ei)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {e}")

    # ---------- selection ----------
    def _get_selected_product_id(self) -> int | None:
        sel = self.table.currentRow()
        if sel < 0: return None
        return int(self.table.item(sel, 0).text())

    # ---------- CRUD ----------
    def _add_product(self):
        dialog = ProductDialog(self.supplier_service, self.category_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.product_service.create_product(**data)
                self.refresh(); self._notify_change()
                self.show_toast(f"Product “{data['name']}” added successfully", "success")
            except ValueError as e:
                self.show_toast(f"Validation: {e}", "error")
            except Exception as e:
                self.show_toast(f"Failed to add product: {e}", "error")

    def _edit_product(self):
        pid = self._get_selected_product_id()
        if pid is None:
            self.show_toast("Select a product to edit", "info"); return
        try:
            product = self.product_service.get_product(pid)
            dialog = ProductDialog(self.supplier_service, self.category_service, product)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                product.name = data["name"]
                product.quantity = data["quantity"]
                product.low_stock_threshold = data["low_stock_threshold"]
                product.price = data["price"]
                product.supplier_id = data["supplier_id"]
                product.category_id = data["category_id"]
                product.expiration_date = data["expiration_date"]
                self.product_service.update_product(product)
                self.refresh(); self._notify_change()
                self.show_toast(f"Product “{data['name']}” updated", "success")
        except ValueError as e:
            self.show_toast(f"Validation: {e}", "error")
        except Exception as e:
            self.show_toast(f"Failed to edit product: {e}", "error")

    def _delete_product(self):
        pid = self._get_selected_product_id()
        if pid is None:
            self.show_toast("Select a product to delete", "info"); return
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete product ID {pid}? This will also delete its movement history.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.product_service.delete_product(pid)
                self.refresh(); self._notify_change()
                self.show_toast("Product deleted", "success")
            except ValueError as e:
                self.show_toast(str(e), "error")
            except Exception as e:
                self.show_toast(f"Failed to delete product: {e}", "error")

    def _notify_change(self):
        if self.on_change_callback: self.on_change_callback()
