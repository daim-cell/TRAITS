
from user import User
class Admin(User):
    def __init__(self, username, password):
        super().__init__(username, password)

    def add_product(self, product):
        # Implement logic to add a product to the database
        pass

    def remove_product(self, product):
        # Implement logic to remove a product from the database
        pass

    def update_product(self, product, new_info):
        # Implement logic to update product information in the database
        pass

    def add_supplier(self, supplier):
        # Implement logic to add a supplier to the database
        pass

    def update_supplier(self, supplier, new_info):
        # Implement logic to update supplier information in the database
        pass

    def generate_report(self, report_type, month):
        if report_type == "monthly_purchase_history":
            return self.get_monthly_purchase_history(month)
        elif report_type == "supplier_sales":
            return self.get_supplier_sales(month)
        elif report_type == "unavailable_items":
            return self.get_unavailable_items(month)
        elif report_type == "top_customers":
            return self.get_top_customers(month)
        else:
            raise ValueError("Invalid report type")

    def get_monthly_purchase_history(self, month):
        # Assuming orders have a date_of_purchase attribute
        return [order for order in Order.objects.filter(date_of_purchase__month=month)]

    def get_supplier_sales(self, month):
        # Assuming suppliers have a list of supplied_products
        sold_products = [product for supplier in Supplier.objects.all() for product in supplier.supplied_products if
                         product.date_of_purchase.month == month]
        return sorted(sold_products, key=lambda x: x.available_units, reverse=True)

    def get_unavailable_items(self, month):
        # Assuming products have an expiry_date attribute
        unavailable_items = [product for product in Product.objects.all() if
                              product.available_units == 0 or product.expiry_date.month == month]
        return unavailable_items

    def get_top_customers(self, month, n=5):
        # Assuming orders have a total attribute
        all_orders = Order.objects.filter(date_of_purchase__month=month)
        top_customers = sorted(all_orders, key=lambda x: x.total, reverse=True)[:n]
        return [(order.customer, order.total, len(order.products)) for order in top_customers]
