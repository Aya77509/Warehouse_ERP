class StockMovement:

    def __init__(self, id, product_id, movement_type, quantity, date):
        self.id = id
        self.product_id = product_id
        self.type = movement_type
        self.quantity = quantity
        self.date = date