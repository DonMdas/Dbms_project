import sqlite3

class PaymentManager:
    def __init__(self, cursor, conn):
        self.conn = conn
        self.cursor = cursor
    
    def add_payment_method(self, payment_method_name):
        payment_method_name = payment_method_name.strip().lower()
        
        try:
            self.cursor.execute("INSERT INTO Payment_Method (payment_method_name) VALUES (?)", (payment_method_name,))
            self.conn.commit()
            print(f"Payment Method '{payment_method_name}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            print(f"Error: Payment Method '{payment_method_name}' already exists.")
            return False
    
    def list_payment_methods(self):
        self.cursor.execute("SELECT payment_method_name FROM Payment_Method")
        payment_method_names = self.cursor.fetchall()

        if not payment_method_names:
            print("No Payment Mehod found.")
        else:
            print("Payment Methods:")
            print("-" * 20)
            for payement_method in payment_method_names:
                print(f"- {payement_method[0]}")
        return True
