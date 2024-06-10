from user import User
import mariadb
from typing import List
from products import Product

class Customer(User):
    INSERT_CUSTOMER_INTO_DB_TEMPLATE = """INSERT INTO Customer (username, password, name, surname, email, date_of_birth, shipping_address, credit_card_number) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    GET_ALL_CUSTOMERS_IN_DB_TEMPLATE = """SELECT username, password, name, surname, email, date_of_birth, shipping_address, credit_card_number FROM Customer"""
    DELETE_CUSTOMER_FROM_DB_TEMPLATE = """DELETE FROM Customer WHERE username = %s"""
    UPDATE_CUSTOMER_IN_DB_TEMPLATE = """UPDATE Customer SET name = %s, surname = %s, date_of_birth = %s, shipping_address = %s, credit_card_number = %s WHERE username = %s"""
    DELETE_ORDERS_OF_CUSTOMER_TEMPLATE = """DELETE FROM Orders WHERE customer_username = %s"""

    def __init__(self, username, password, name, surname, email, date_of_birth, shipping_address, credit_card_number):
        super().__init__(username, password)
        self.name = name
        self.surname = surname
        self.email = email
        self.date_of_birth = date_of_birth
        self.shipping_address = shipping_address
        self.credit_card_number = credit_card_number

    def insert_into_db(self, connection):
        cursor = connection.cursor()
        try:
            cursor.execute(self.INSERT_CUSTOMER_INTO_DB_TEMPLATE, (self.username, self.password, self.name, self.surname, self.email, self.date_of_birth, self.shipping_address, self.credit_card_number))
            connection.commit()
        except mariadb.IntegrityError as e:
            raise

    def remove_from_db(self, connection):
        cursor = connection.cursor()
        try:
            # First, delete all orders of the customer
            cursor.execute(self.DELETE_ORDERS_OF_CUSTOMER_TEMPLATE, (self.username,))
            # Then, delete the customer
            cursor.execute(self.DELETE_CUSTOMER_FROM_DB_TEMPLATE, (self.username,))
            connection.commit()
        except mariadb.Error as e:
            raise

    def update_in_db(self, connection, name=None, surname=None, date_of_birth=None, shipping_address=None, credit_card_number=None):
        cursor = connection.cursor()
        try:
            # Ensure email is not updated by not including it in the update statement
            update_fields = {
                "name": name or self.name,
                "surname": surname or self.surname,
                "date_of_birth": date_of_birth or self.date_of_birth,
                "shipping_address": shipping_address or self.shipping_address,
                "credit_card_number": credit_card_number or self.credit_card_number
            }
            cursor.execute(self.UPDATE_CUSTOMER_IN_DB_TEMPLATE, (update_fields["name"], update_fields["surname"], update_fields["date_of_birth"], update_fields["shipping_address"], update_fields["credit_card_number"], self.username))
            connection.commit()
            # Update the instance attributes
            self.name = update_fields["name"]
            self.surname = update_fields["surname"]
            self.date_of_birth = update_fields["date_of_birth"]
            self.shipping_address = update_fields["shipping_address"]
            self.credit_card_number = update_fields["credit_card_number"]
        except mariadb.Error as e:
            raise

    @classmethod
    def get_all_customers_in_db(cls, connection) -> List['Customer']:
        cursor = connection.cursor()
        cursor.execute(cls.GET_ALL_CUSTOMERS_IN_DB_TEMPLATE)
        return [
            Customer(username, password, name, surname, email, date_of_birth, shipping_address, credit_card_number)
            for username, password, name, surname, email, date_of_birth, shipping_address, credit_card_number in cursor
        ]
    
    # Wishlist Implementation
    ADD_TO_WISHLIST_TEMPLATE = """INSERT INTO Wishlist (username, product_id) VALUES (%s, %s)"""
    REMOVE_FROM_WISHLIST_TEMPLATE = """DELETE FROM Wishlist WHERE username = %s AND product_id = %s"""
    GET_WISHLIST_TEMPLATE = """SELECT p.product_id, p.name, p.category, p.price_per_unit, p.expiry_date, p.available_units, p.max_units, p.supplier_id FROM Wishlist w JOIN Product p ON w.product_id = p.product_id WHERE w.customer_username = %s AND p.expiry_date > CURDATE() AND p.available_units > 0"""

    def add_to_wishlist(self, connection, product_id: int):
        cursor = connection.cursor()
        try:
            cursor.execute(self.ADD_TO_WISHLIST_TEMPLATE, (self.username, product_id))
            connection.commit()
        except mariadb.Error as e:
            raise

    def remove_from_wishlist(self, connection, product_id: int):
        cursor = connection.cursor()
        try:
            cursor.execute(self.REMOVE_FROM_WISHLIST_TEMPLATE, (self.username, product_id))
            connection.commit()
        except mariadb.Error as e:
            raise

    def get_wishlist(self, connection) -> List[int]:
        cursor = connection.cursor()
        cursor.execute(self.GET_WISHLIST_TEMPLATE, (self.username,))
        return [
            Product(product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id)
            for product_id, name, category, price_per_unit, expiry_date, available_units, max_units, supplier_id in cursor
        ]
