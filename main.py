import sqlite3
import shlex
import csv

# Extend privileges to include CSV import/export commands
list_of_privileges = {
    "admin": [
        "add_user", "list_payment_methods", "add_payment_method",
        "list_categories", "add_category", "import_expenses", "export_csv"
    ],
    "user": [
        "list_categories", "list_payment_methods", "add_expense",
        "import_expenses", "export_csv"
    ]
}


class ExpenseApp:
    def __init__(self, cursor, conn):
        # sqlite connection code
        self.conn = conn
        self.cursor = cursor
        # current session details
        self.current_user = None
        self.privileges = None

    def authenticate(self, username, password):
        # Step 1: Check if the username exists
        self.cursor.execute("SELECT password FROM User WHERE username = ?", (username,))
        user = self.cursor.fetchone()

        if user is None:
            print("Error: Username does not exist.")
            return

        stored_password = user[0]  # Get stored password

        # Step 2: Check if password matches
        if stored_password == password:
            print("Login successful!")
        else:
            print("Error: Incorrect password.")
            return

        self.current_user = username
        self.cursor.execute(
            "SELECT r.role_name FROM user_role u, Role r WHERE u.username = ? and u.role_id = r.role_id",
            (username,))
        role = self.cursor.fetchone()[0]
        self.privileges = list_of_privileges[role]

    def logout(self):
        self.current_user = None
        self.privileges = None
        print("Logging Out.....")

    def register(self, username, password, role):
        self.cursor.execute("SELECT role_id FROM Role WHERE role_name = ?", (role,))
        result = self.cursor.fetchone()
        if result is None:
            print(f"Error: Role '{role}' does not exist. Registration failed!")
            return

        role_id = result[0]

        try:
            self.cursor.execute("INSERT INTO User (username, password) VALUES (?, ?)", (username, password))
            self.cursor.execute("INSERT INTO user_role (username, role_id) VALUES (?, ?)", (username, role_id))
            print("User added successfully!")
            self.conn.commit()
        except sqlite3.IntegrityError:
            print("Error: Username already exists!")
            return

    def add_category(self, category_name):
        category_name = category_name.strip().lower()

        try:
            self.cursor.execute("INSERT INTO categories (category_name) VALUES (?)", (category_name,))
            self.conn.commit()
            print(f"Category '{category_name}' added successfully.")
        except sqlite3.IntegrityError:
            print(f"Error: Category '{category_name}' already exists.")

    def list_categories(self):
        self.cursor.execute("SELECT category_name FROM categories")
        categories = self.cursor.fetchall()

        if not categories:
            print("No categories found.")
        else:
            print("Categories:")
            print("-" * 20)
            for category in categories:
                print(f"- {category[0]}")

    def add_payment_method(self, payment_method_name):
        payment_method_name = payment_method_name.strip().lower()

        try:
            self.cursor.execute("INSERT INTO Payment_Method (payment_method_name) VALUES (?)", (payment_method_name,))
            self.conn.commit()
            print(f"Payment Method '{payment_method_name}' added successfully.")
        except sqlite3.IntegrityError:
            print(f"Error: Payment Method '{payment_method_name}' already exists.")

    def list_payment_methods(self):
        self.cursor.execute("SELECT payment_method_name FROM Payment_Method")
        payment_method_names = self.cursor.fetchall()

        if not payment_method_names:
            print("No Payment Method found.")
        else:
            print("Payment Methods:")
            print("-" * 20)
            for payment_method in payment_method_names:
                print(f"- {payment_method[0]}")

    def add_expense_from_data(self, amount, category, payment_method, date, description, tag, payment_method_details=""):
        # Insert into Expense table
        self.cursor.execute(
            "INSERT INTO Expense (date, amount, description) VALUES (?, ?, ?)",
            (date, amount, description))
        expense_id = self.cursor.lastrowid

        # Handle category insertion
        self.cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (category,))
        result = self.cursor.fetchone()
        if result is None:
            print(f"Error: Category '{category}' does not exist. Adding failed!")
            return
        category_id = result[0]
        self.cursor.execute(
            "INSERT INTO category_expense (category_id, expense_id) VALUES (?, ?)",
            (category_id, expense_id))

        # Handle tag insertion
        self.cursor.execute("SELECT tag_id FROM Tags WHERE tag_name = ?", (tag,))
        result = self.cursor.fetchone()
        if result is None:
            self.cursor.execute("INSERT INTO Tags (tag_name) VALUES (?)", (tag,))
            tag_id = self.cursor.lastrowid
        else:
            tag_id = result[0]
        self.cursor.execute(
            "INSERT INTO tag_expense (tag_id, expense_id) VALUES (?, ?)",
            (tag_id, expense_id))

        # Handle payment method insertion
        self.cursor.execute("SELECT payment_method_id FROM Payment_Method WHERE payment_method_name = ?", (payment_method,))
        result = self.cursor.fetchone()
        if result is None:
            print(f"Error: Payment Method '{payment_method}' does not exist. Adding failed!")
            return
        payment_method_id = result[0]
        self.cursor.execute(
            "INSERT INTO payment_method_expense(payment_method_id, expense_id, payment_detail_identifier) VALUES (?, ?, ?)",
            (payment_method_id, expense_id, payment_method_details))

        # Map expense to user
        self.cursor.execute(
            "INSERT INTO user_expense(username, expense_id) VALUES (?, ?)",
            (self.current_user, expense_id))

        self.conn.commit()
        print("Expense Added Successfully")

    def addexpense(self, amount, category, payment_method, date, description, tag, payment_method_details=""):
        # This interactive function calls our common helper after possibly prompting for extra details.
        # In interactive mode, we ask if the user wants to add extra details.
        payment_detail = payment_method_details
        if payment_method_details == "":
            choice = input("Would you like to add payment method details?(y/n) [Type more to display more info]: ")
            if choice.lower() == "more":
                print("This detail can be used by the user to generate reports based on specific payment method")
                print("The details will be masked")
                choice = input("Would you like to add payment method details?(y/n): ")
            if choice.lower() == "y":
                payment_detail = input("Enter the details: ")
        self.add_expense_from_data(amount, category, payment_method, date, description, tag, payment_detail)

    def import_expenses(self, file_path):
        try:
            with open(file_path, newline="") as csvfile:
                reader = csv.reader(csvfile)
                # Expecting a header row; if not, remove next(reader)
                header = next(reader)
                expected_header = ["amount", "category", "payment_method", "date", "description", "tag", "payment_method_details"]
                if [col.strip().lower() for col in header] != expected_header:
                    print("Error: CSV header does not match expected format.")
                    return
                count = 0
                for row in reader:
                    if len(row) != 7:
                        print(f"Skipping row {row}: Incorrect number of fields.")
                        continue
                    amount, category, payment_method, date, description, tag, payment_method_details = row
                    self.add_expense_from_data(amount, category.strip().lower(), payment_method.strip().lower(),
                                               date, description, tag.strip().lower(), payment_method_details)
                    count += 1
                print(f"Imported {count} expenses successfully.")
        except FileNotFoundError:
            print("Error: File not found.")
        except Exception as e:
            print(f"Error while importing CSV: {e}")

    def export_csv(self, file_path, sort_field):
        # Mapping allowed sort fields to actual SQL columns
        sort_fields = {
            "amount": "e.amount",
            "category": "c.category_name",
            "payment_method": "pm.payment_method_name",
            "date": "e.date",
            "description": "e.description",
            "tag": "t.tag_name",
            "payment_method_details": "pme.payment_detail_identifier"
        }
        if sort_field not in sort_fields:
            print("Error: Invalid sort field.")
            return

        query = f"""
            SELECT e.amount, c.category_name, pm.payment_method_name, e.date, e.description, t.tag_name, pme.payment_detail_identifier
            FROM Expense e
            JOIN category_expense ce ON e.expense_id = ce.expense_id
            JOIN Categories c ON ce.category_id = c.category_id
            JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
            JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
            JOIN tag_expense te ON e.expense_id = te.expense_id
            JOIN Tags t ON te.tag_id = t.tag_id
            ORDER BY {sort_fields[sort_field]}
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        if not rows:
            print("No expenses found to export.")
            return

        try:
            with open(file_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                # Write header row
                writer.writerow(["amount", "category", "payment_method", "date", "description", "tag", "payment_method_details"])
                for row in rows:
                    writer.writerow(row)
            print(f"Exported expenses successfully to {file_path}.")
        except Exception as e:
            print(f"Error while exporting CSV: {e}")

    def parser(self, cmd_str):
        cmd_str = cmd_str.strip()
        try:
            cmd_str_lst = shlex.split(cmd_str)  # Use shlex.split for parsing
        except ValueError as e:
            print(f"Error: {e}")
            return

        if not cmd_str_lst:
            print("Error: No command entered.")
            return

        cmd = cmd_str_lst[0]

        # Handling login
        if cmd == "login":
            if len(cmd_str_lst) != 3:
                print("Error: Insufficient number of arguments")
                return
            if self.current_user is None:
                username = cmd_str_lst[1]
                password = cmd_str_lst[2]
                self.authenticate(username, password)
            else:
                print("Error: Another session is live!")
            return

        # Handling logout
        elif cmd == "logout":
            if len(cmd_str_lst) != 1:
                print("Error: No arguments required")
                return
            if self.current_user is not None:
                self.logout()
            else:
                print("Error: User not logged in!")
            return

        # Ensure user is logged in for further commands
        if self.current_user is None:
            print("Error: Please login!")
            return

        # Ensure the command exists in privileges
        if cmd not in list_of_privileges['admin'] and cmd not in list_of_privileges["user"]:
            print("Error: Invalid command")
            return

        # Ensure the user has permission
        if cmd not in self.privileges:
            print("Error: Unauthorized command")
            return

        # Handling add_user (Admin only)
        if cmd == "add_user":
            if len(cmd_str_lst) == 4:
                username = cmd_str_lst[1]
                password = cmd_str_lst[2]
                role = cmd_str_lst[3]
                self.register(username, password, role)
            else:
                print("Error: Insufficient number of arguments")

        # Handling list_categories
        elif cmd == "list_categories":
            if len(cmd_str_lst) != 1:
                print("Error: No arguments required")
            else:
                self.list_categories()

        # Handling add_category (Admin only)
        elif cmd == "add_category":
            if len(cmd_str_lst) != 2:
                print("Error: Provide category name")
            else:
                category_name = cmd_str_lst[1]
                self.add_category(category_name)

        # Handling list_payment_methods
        elif cmd == "list_payment_methods":
            if len(cmd_str_lst) != 1:
                print("Error: No arguments required")
            else:
                self.list_payment_methods()

        # Handling add_payment_method (Admin only)
        elif cmd == "add_payment_method":
            if len(cmd_str_lst) != 2:
                print("Error: Provide payment method name")
            else:
                payment_method_name = cmd_str_lst[1]
                self.add_payment_method(payment_method_name)

        # Handling addexpense
        elif cmd == "add_expense":
            if len(cmd_str_lst) >= 7:
                amount = cmd_str_lst[1]
                category_name = cmd_str_lst[2]
                payment_method_name = cmd_str_lst[3]
                date_txt = cmd_str_lst[4]
                description = cmd_str_lst[5]
                tag_name = cmd_str_lst[-1]
                self.addexpense(amount, category_name, payment_method_name, date_txt, description, tag_name)
            else:
                print("Error: Insufficient number of arguments!")
                return

        # Handling import_expenses
        elif cmd == "import_expenses":
            if len(cmd_str_lst) != 2:
                print("Error: Provide file path for CSV import")
            else:
                file_path = cmd_str_lst[1]
                self.import_expenses(file_path)

        # Handling export_csv
        elif cmd == "export_csv":
            if len(cmd_str_lst) != 4:
                print("Error: Command format: export_csv <file_path>, sort-on <field_name>")
            else:
                file_path = cmd_str_lst[1].rstrip(',')  # remove any trailing comma
                if cmd_str_lst[2] != "sort-on":
                    print("Error: Expected 'sort-on' keyword")
                    return
                sort_field = cmd_str_lst[3]
                self.export_csv(file_path, sort_field)

        else:
            print("Error: Invalid command")

    def help(self):
        pass



   
    


def main():
    conn = sqlite3.connect("ExpenseReport")  # Creates/opens a database file
    cursor = conn.cursor()  # Creates a cursor object to execute SQL commands
    app = ExpenseApp(cursor, conn)
    print("Expense Reporting App")
    while True:
        cmd_string = input(">> ")
        if cmd_string.strip().lower() == "exit":
            print("Exiting ........")
            break
        app.parser(cmd_string)
    # Close the connection
    conn.close()


main()
