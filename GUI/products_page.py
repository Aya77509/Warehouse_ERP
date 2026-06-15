from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QLabel
)


from Infrastructure.product_repository import ProductRepository



class ProductsPage(QWidget):


    def __init__(self):

        super().__init__()


        self.repo = ProductRepository()

        self.selected_id = None



        layout = QVBoxLayout()



        # ==========================
        # FORM
        # ==========================

        form = QHBoxLayout()


        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(
            "Product name"
        )


        self.qty_input = QLineEdit()
        self.qty_input.setPlaceholderText(
            "Quantity"
        )


        self.add_btn = QPushButton(
            "Add Product"
        )


        self.add_btn.clicked.connect(
            self.add_product
        )


        form.addWidget(
            QLabel("Name:")
        )

        form.addWidget(
            self.name_input
        )


        form.addWidget(
            QLabel("Quantity:")
        )


        form.addWidget(
            self.qty_input
        )


        form.addWidget(
            self.add_btn
        )


        layout.addLayout(form)




        # ==========================
        # ACTION BUTTONS
        # ==========================

        actions = QHBoxLayout()


        self.update_btn = QPushButton(
            "Update Selected"
        )


        self.delete_btn = QPushButton(
            "Delete Selected"
        )


        self.update_btn.clicked.connect(
            self.update_product
        )


        self.delete_btn.clicked.connect(
            self.delete_product
        )


        actions.addWidget(
            self.update_btn
        )


        actions.addWidget(
            self.delete_btn
        )


        layout.addLayout(actions)




        # ==========================
        # TABLE
        # ==========================


        self.table = QTableWidget()

        self.table.setColumnCount(3)


        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Name",
                "Quantity"
            ]
        )


        self.table.itemSelectionChanged.connect(
            self.get_selected_row
        )


        layout.addWidget(
            self.table
        )



        self.setLayout(layout)



        self.load_data()




    # ==========================
    # ADD
    # ==========================

    def add_product(self):

        name = self.name_input.text()

        quantity = self.qty_input.text()



        if not name or not quantity:
            return



        quantity = int(quantity)



        self.repo.insert(
            name,
            quantity
        )


        self.name_input.clear()

        self.qty_input.clear()


        self.load_data()





    # ==========================
    # LOAD TABLE
    # ==========================


    def load_data(self):

        products = self.repo.get_all()


        self.table.setRowCount(
            len(products)
        )


        for row, product in enumerate(products):


            self.table.setItem(
                row,
                0,
                QTableWidgetItem(
                    str(product.id)
                )
            )


            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    product.name
                )
            )


            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    str(product.quantity)
                )
            )





    # ==========================
    # SELECT PRODUCT
    # ==========================


    def get_selected_row(self):

        row = self.table.currentRow()


        if row >= 0:


            self.selected_id = int(
                self.table.item(row,0).text()
            )


            self.name_input.setText(
                self.table.item(row,1).text()
            )


            self.qty_input.setText(
                self.table.item(row,2).text()
            )





    # ==========================
    # UPDATE
    # ==========================


    def update_product(self):

        if self.selected_id is None:
            return


        self.repo.update(
            self.selected_id,
            self.name_input.text(),
            int(self.qty_input.text())
        )


        self.load_data()





    # ==========================
    # DELETE
    # ==========================


    def delete_product(self):

        if self.selected_id is None:
            return


        self.repo.delete(
            self.selected_id
        )


        self.selected_id = None


        self.name_input.clear()

        self.qty_input.clear()


        self.load_data()