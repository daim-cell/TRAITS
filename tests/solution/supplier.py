import mariadb
from user import User
from products import Product

class Supplier(User):
    INSERT_SUPPLIER_INTO_DB_TEMPLATE = """INSERT INTO Supplier (name, vat_id) VALUES (%s, %s)"""
    GET_SUPPLIER_BY_ID_TEMPLATE = """SELECT supplier_id, name, vat_id FROM Supplier WHERE supplier_id = %s"""
    GET_PRODUCTS_BY_SUPPLIER_TEMPLATE = """SELECT product_id, name, category, price_per_unit, expiry_date, available_units, max_units FROM Product WHERE supplier_id = %s"""

    def __init__(self, username, password, supplier_id, name, vat_id):
        super().__init__(username, password)
        self.supplier_id = supplier_id
        self.name = name
        self.vat_id = vat_id

    def insert_into_db(self, connection):
        cursor = connection.cursor()
        try:
            cursor.execute(self.INSERT_SUPPLIER_INTO_DB_TEMPLATE, (self.name, self.vat_id))
            connection.commit()
            self.supplier_id = cursor.lastrowid  # Get the auto-incremented ID
        except mariadb.IntegrityError as e:
            raise

    @classmethod
    def get_supplier_by_id(cls, connection, supplier_id):
        cursor = connection.cursor()
        cursor.execute(cls.GET_SUPPLIER_BY_ID_TEMPLATE, (supplier_id,))
        result = cursor.fetchone()
        if result:
            return Supplier(*result)
        return None

    def get_supplied_products(self, connection):
        cursor = connection.cursor()
        cursor.execute(self.GET_PRODUCTS_BY_SUPPLIER_TEMPLATE, (self.supplier_id,))
        return [
            Product(product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id)
            for product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id in cursor
        ]
    
