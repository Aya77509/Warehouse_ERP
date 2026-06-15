from Infrastructure.database import get_connection
from Kernel.product import Product


class ProductRepository:


    # ==========================
    # PRODUCTS TABLE
    # ==========================

    def create_table(self):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            quantity INTEGER NOT NULL
        )
        """)

        conn.commit()
        conn.close()



    # ==========================
    # STOCK MOVEMENTS TABLE
    # ==========================

    def create_movement_table(self):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_id INTEGER,

            type TEXT,

            quantity INTEGER,

            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()



    # ==========================
    # CREATE PRODUCT
    # ==========================

    def insert(self, name, quantity):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO products(name, quantity)

        VALUES (?, ?)

        """,
        (name, quantity))


        conn.commit()
        conn.close()



    # ==========================
    # READ PRODUCTS
    # ==========================

    def get_all(self):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute("""
        SELECT * FROM products
        """)


        rows = cursor.fetchall()


        conn.close()



        products = []


        for row in rows:

            product = Product(
                row[0],
                row[1],
                row[2]
            )


            products.append(product)



        return products



    # ==========================
    # UPDATE PRODUCT
    # ==========================

    def update(self, product_id, name, quantity):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute("""
        UPDATE products

        SET name = ?, quantity = ?

        WHERE id = ?

        """,
        (
            name,
            quantity,
            product_id
        ))


        conn.commit()
        conn.close()



    # ==========================
    # DELETE PRODUCT
    # ==========================

    def delete(self, product_id):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute("""
        DELETE FROM products

        WHERE id = ?

        """,
        (product_id,))


        conn.commit()
        conn.close()



    # ==========================
    # STOCK UPDATE
    # ==========================

    def update_stock(self, product_id, quantity_change):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute("""
        UPDATE products

        SET quantity = quantity + ?

        WHERE id = ?

        """,
        (
            quantity_change,
            product_id
        ))


        conn.commit()
        conn.close()



    # ==========================
    # ADD STOCK MOVEMENT RECORD
    # ==========================

    def add_movement(self, product_id, movement_type, quantity):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute("""
        INSERT INTO stock_movements
        (
            product_id,
            type,
            quantity
        )

        VALUES (?, ?, ?)

        """,
        (
            product_id,
            movement_type,
            quantity
        ))


        conn.commit()
        conn.close()



    # ==========================
    # GET STOCK HISTORY
    # ==========================

    def get_movements(self):

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute("""
        SELECT * FROM stock_movements
        ORDER BY date DESC
        """)


        movements = cursor.fetchall()


        conn.close()


        return movements