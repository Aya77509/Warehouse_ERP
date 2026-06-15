from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel
)

from Infrastructure.product_repository import ProductRepository


class StockPage(QWidget):

    def __init__(self):
        super().__init__()

        self.repo = ProductRepository()

        layout = QVBoxLayout()

        # --------------------
        # INPUTS
        # --------------------
        form = QHBoxLayout()

        self.product_id = QLineEdit()
        self.product_id.setPlaceholderText("Product ID")

        self.quantity = QLineEdit()
        self.quantity.setPlaceholderText("Quantity")

        form.addWidget(QLabel("Product ID"))
        form.addWidget(self.product_id)
        form.addWidget(QLabel("Qty"))
        form.addWidget(self.quantity)

        layout.addLayout(form)

        # --------------------
        # BUTTONS
        # --------------------
        self.btn_in = QPushButton("Stock IN")
        self.btn_out = QPushButton("Stock OUT")

        self.btn_in.clicked.connect(self.stock_in)
        self.btn_out.clicked.connect(self.stock_out)

        layout.addWidget(self.btn_in)
        layout.addWidget(self.btn_out)

        self.setLayout(layout)

    # --------------------
    # STOCK IN
    # --------------------
    def stock_in(self):
        pid = int(self.product_id.text())
        qty = int(self.quantity.text())

        self.repo.update_stock(pid, qty)
        self.repo.add_movement(pid, "IN", qty)

    # --------------------
    # STOCK OUT
    # --------------------
    def stock_out(self):
        pid = int(self.product_id.text())
        qty = int(self.quantity.text())

        self.repo.update_stock(pid, -qty)
        self.repo.add_movement(pid, "OUT", qty)