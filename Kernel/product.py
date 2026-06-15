class Product:

    def __init__(self, id, name, quantity):
        self.id = id
        self.name = name
        self.quantity = quantity


    def is_low_stock(self):
        return self.quantity < 5