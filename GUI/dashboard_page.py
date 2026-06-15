from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton
)

from Infrastructure.product_repository import ProductRepository


class DashboardPage(QWidget):

    def __init__(self):
        super().__init__()

        self.repo = ProductRepository()

        layout = QVBoxLayout()


        self.title = QLabel("Dashboard")
        self.title.setStyleSheet(
            "font-size: 22px; font-weight: bold;"
        )


        self.total_products = QLabel()

        self.total_stock = QLabel()

        self.low_stock = QLabel()


        self.refresh_btn = QPushButton(
            "Refresh Dashboard"
        )

        self.refresh_btn.clicked.connect(
            self.load_data
        )


        layout.addWidget(self.title)

        layout.addWidget(
            self.total_products
        )

        layout.addWidget(
            self.total_stock
        )

        layout.addWidget(
            self.low_stock
        )

        layout.addWidget(
            self.refresh_btn
        )


        layout.addStretch()


        self.setLayout(layout)


        self.load_data()



    def load_data(self):

        products = self.repo.get_all()


        total_products = len(products)


        total_stock = sum(
            product.quantity
            for product in products
        )


        low_stock_items = [
            product
            for product in products
            if product.quantity < 5
        ]



        self.total_products.setText(
            f"Total Products: {total_products}"
        )


        self.total_stock.setText(
            f"Total Stock Units: {total_stock}"
        )


        self.low_stock.setText(
            f"Low Stock Products: {len(low_stock_items)}"
        )