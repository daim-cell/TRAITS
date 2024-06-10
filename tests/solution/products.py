import mariadb

class Product:
    INSERT_PRODUCT_INTO_DB_TEMPLATE = """INSERT INTO Product (name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    DELETE_PRODUCT_FROM_DB_TEMPLATE = """DELETE FROM Product WHERE product_id = %s"""
    RESTOCK_PRODUCT_TEMPLATE = """UPDATE Product SET available_units = available_units + %s WHERE product_id = %s AND (available_units + %s) <= max_units"""
    GET_PRODUCT_BY_ID_TEMPLATE = """SELECT product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id FROM Product WHERE product_id = %s"""
    
    def __init__(self, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id):
    
        self.name = name
        self.category = category
        self.price_per_unit = price_per_unit
        self.expiry_date = expiry_date
        self.available_units = available_units
        self.max_units = max_units
        self.supplier_id = supplier_id

    def insert_into_db(self, connection):
        cursor = connection.cursor()
        try:
            cursor.execute(self.INSERT_PRODUCT_INTO_DB_TEMPLATE, (self.name, self.category, self.price_per_unit, self.expiry_date, self.available_units, self.max_units, self.supplier_id))
            connection.commit()
            self.product_id = cursor.lastrowid  # Get the auto-incremented ID
        except mariadb.Error as e:
            raise

    def delete_from_db(self, connection):
        cursor = connection.cursor()
        try:
            cursor.execute(self.DELETE_PRODUCT_FROM_DB_TEMPLATE, (self.product_id))
            connection.commit()
        except mariadb.Error as e:
            raise

    def restock(self, connection, additional_units):
        cursor = connection.cursor()
        try:
            cursor.execute(self.RESTOCK_PRODUCT_TEMPLATE, (additional_units, self.product_id, additional_units))
            connection.commit()
        except mariadb.Error as e:
            raise

    

    @classmethod
    def get_product_by_id(cls, connection, product_id):
        cursor = connection.cursor()
        cursor.execute(cls.GET_PRODUCT_BY_ID_TEMPLATE, (product_id,))
        result = cursor.fetchone()
        if result:
            return Product(*result)
        return None
    

    # Lookup functionality
    GET_PRODUCTS_BY_NAME_TEMPLATE = """SELECT product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id FROM Product WHERE name LIKE %s AND expiry_date > CURDATE() AND available_units > 0"""
    GET_PRODUCTS_BY_CATEGORY_TEMPLATE = """SELECT product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id FROM Product WHERE category LIKE %s AND expiry_date > CURDATE() AND available_units > 0"""
    GET_AVAILABLE_PRODUCTS_TEMPLATE = """SELECT product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id FROM Product WHERE expiry_date > CURDATE() AND available_units > 0"""

    @classmethod
    def get_products_by_name(cls, connection, name):
        cursor = connection.cursor()
        cursor.execute(cls.GET_PRODUCTS_BY_NAME_TEMPLATE, (name,))
        return [
            Product(product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id)
            for product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id in cursor
        ]

    @classmethod
    def get_products_by_category(cls, connection, category):
        cursor = connection.cursor()
        cursor.execute(cls.GET_PRODUCTS_BY_CATEGORY_TEMPLATE, (category,))
        return [
            Product(product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id)
            for product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id in cursor
        ]

    @classmethod
    def get_available_products(cls, connection):
        cursor = connection.cursor()
        cursor.execute(cls.GET_AVAILABLE_PRODUCTS_TEMPLATE)
        return [
            Product(product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id)
            for product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id in cursor
        ]