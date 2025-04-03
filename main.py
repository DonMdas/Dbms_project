import sqlite3
""" sqlite3 in Python allows you to create, manage, 
    and interact with SQLite databases—storing, retrieving, updating, and deleting data 
    using SQL commands—all within a lightweight, file-based database system.
"""

#-------------------------------------------------------------------------------------

import shlex
"""shlex in Python is used to split and parse shell-like command strings safely, handling quotes
    and special characters properly."""
import csv
""" importing, manipulating and exporting csv."""


import bcrypt

#--------------------------------------------------------------------------------------

""" In list of privileges we have added the function/command names which are allowed to the admin and user"""
list_of_privileges = {
    "admin": {
        "add_user": "add_user <username> <password> <role>",
        "list_payment_methods": "list_payment_methods",
        "add_payment_method": "add_payment_method <payment_method_name>",
        "list_categories": "list_categories",
        "add_category": "add_category <category_name>",
        "list_users": "list_users",
        "help":"help"
    },
    "user": {
        "list_categories": "list_categories",
        "list_payment_methods": "list_payment_methods",
        "add_expense": "add_expense <amount> <category> <payment_method> <date> <description> <tag>",
        "update_expense": "update_expense <expense_id> <field> <new_value>",
        "delete_expense": "delete_expense <expense_id>",
        "list_expenses": "list_expenses [<field> <operator> <value>, ...]",
        "import_expenses": "import_expenses <file_path>",
        "export_csv": "export_csv <file_path> <sort_field>",
        "help":"help"
    }
}
#-----------------------------------------------------------------------------------------
"""
    # conn (Connection Object): Connects to the SQLite database, allows committing (conn.commit()) and 
    closing (conn.close()) the connection.
    # cursor (Cursor Object): Executes SQL queries (cursor.execute()), fetches results 
    (cursor.fetchall()), and manages database interactions.
"""


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
        password_credentials = self.cursor.fetchone()

        if password_credentials is None:
            print("Error: Username does not exist.")
            return

        stored_hashed_password = password_credentials[0]  # Get stored hashed password (from DB)

        # Step 2: Check if password matches (using bcrypt)
        if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
            print("Login successful!")
        else:
            print("Error: Incorrect password.")
            return

        self.current_user = username

        # Fetch user role
        self.cursor.execute(
            "SELECT r.role_name FROM user_role u, Role r WHERE u.username = ? and u.role_id = r.role_id",
            (username,))
        role = self.cursor.fetchone()[0]
        self.privileges = role


    def logout(self):
        self.current_user = None
        self.privileges = None
        print(f"Logging out {self.current_user}...")
        print("Successfully logged out.")

    def register(self, username, password, role):
        # Step 1: Get role_id (Convert role to lowercase for consistency)
        self.cursor.execute("SELECT role_id FROM Role WHERE LOWER(role_name) = LOWER(?)", (role,))
        result = self.cursor.fetchone()
        
        if result is None:
            print(f"Error: Role '{role}' does not exist. Registration failed!")
            return

        role_id = result[0]

        # Step 2: Check if the username already exists
        self.cursor.execute("SELECT username FROM User WHERE username = ?", (username,))
        if self.cursor.fetchone():
            print("Error: Username already exists!")
            return

        # Step 3: Hash the password before storing it
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            # Step 4: Insert user into the database
            self.cursor.execute("INSERT INTO User (username, password) VALUES (?, ?)", (username, hashed_password))
            self.cursor.execute("INSERT INTO user_role (username, role_id) VALUES (?, ?)", (username, role_id))
            self.conn.commit()
            print("User registered successfully!")
        except sqlite3.Error as e:
            print(f"Database error: {e}")


    def add_category(self, category_name):
        category_name = category_name.strip().lower()

        # Step 1: Check if the category already exists
        self.cursor.execute("SELECT category_id FROM categories WHERE category_name = ?", (category_name,))
        if self.cursor.fetchone():
            print(f"Error: Category '{category_name}' already exists.")
            return

        try:
            # Step 2: Insert category
            self.cursor.execute("INSERT INTO categories (category_name) VALUES (?)", (category_name,))
            self.conn.commit()
            print(f"Category '{category_name}' added successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def list_categories(self):
        try:
            self.cursor.execute("SELECT category_name FROM categories")
            categories = self.cursor.fetchall() # here categories will return a list 

            if len(categories) == 0:          # so here we will check the length of the list
                print("No categories found.")
                return

            print("\nAvailable Categories:")
            print("=" * 30)
            for category in categories:
                print(f"• {category[0]}")
            print("=" * 30)

        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def add_payment_method(self, payment_method_name):
        payment_method_name = payment_method_name.strip().lower()

        try:
            # Check if payment method already exists
            self.cursor.execute("SELECT payment_method_id FROM Payment_Method WHERE payment_method_name = ?", (payment_method_name,))
            if self.cursor.fetchone():
                print(f"Error: Payment Method '{payment_method_name}' already exists.")
                return
            
            # Insert new payment method
            self.cursor.execute("INSERT INTO Payment_Method (payment_method_name) VALUES (?)", (payment_method_name,))
            self.conn.commit()
            print(f"Payment Method '{payment_method_name}' added successfully.")

        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def list_payment_methods(self):
        try:
            self.cursor.execute("SELECT payment_method_name FROM Payment_Method")
            payment_method_names = self.cursor.fetchall()

            if len(payment_method_names) == 0:
                print("No Payment Methods found.")
                return

            print("\nAvailable Payment Methods:")
            print("=" * 30)
            for method in payment_method_names:
                print(f"• {method[0]}")
            print("=" * 30)

        except sqlite3.Error as e:
            print(f"Database error: {e}")



    def addexpense(self, amount, category, payment_method, date, description, tag, payment_detail_identifier="", import_fn=0):
        # Try to convert amount to float
        try:
            amount = float(amount)
        except ValueError:
            print(f"Error: Invalid amount '{amount}'. Must be a number.")
            return False
        
        try:
            self.cursor.execute(
                "INSERT INTO Expense (date, amount, description) VALUES (?, ?, ?)", 
                (date, amount, description)
            )
            expense_id = self.cursor.lastrowid  # Get the last inserted expense ID
            
            # Check if category exists
            self.cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (category,))
            result = self.cursor.fetchone()
            if result is None:
                print(f"Error: Category '{category}' does not exist. Adding failed!")
                self.conn.rollback()
                return False
            
            category_id = result[0]  # Extract category_id
            self.cursor.execute(
                "INSERT INTO category_expense (category_id, expense_id) VALUES (?, ?)", 
                (category_id, expense_id)
            )
            
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
                (tag_id, expense_id)
            )
            
        
            self.cursor.execute("SELECT payment_method_id FROM Payment_Method WHERE Payment_Method_Name = ?", (payment_method,))
            result = self.cursor.fetchone()
            if result is None:
                print(f"Error: Payment Method '{payment_method}' does not exist. Adding failed!")
                self.conn.rollback()
                return False
            
            payment_method_id = result[0]  # Extract payment_method_id
            self.cursor.execute(
                "INSERT INTO payment_method_expense (payment_method_id, expense_id, payment_detail_identifier) VALUES (?, ?, ?)", 
                (payment_method_id, expense_id, payment_detail_identifier)
            )
            
            # Associate expense with user
            self.cursor.execute(
                "INSERT INTO user_expense (username, expense_id) VALUES (?, ?)", 
                (self.current_user, expense_id)
            )
            
            self.conn.commit()
            if import_fn == 0:
                print("Expense Added Successfully")
            return True

        except sqlite3.Error as e:
            print(f"Database error adding expense: {e}")
            self.conn.rollback()
            return False


    def import_expenses(self, file_path):
        try:
            with open(file_path, newline="") as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                expected_header = ["amount", "category", "payment_method", "date", "description", "tag", "payment_detail_identifier"]
                
                if [col.strip().lower() for col in header] != expected_header:
                    print("Error: CSV header does not match expected format.")
                    return
                    
                success_count = 0
                error_count = 0
                
                for i, row in enumerate(reader, 2):  # Start counting from line 2 (after header)
                    if len(row) < 6:
                        print(f"Skipping row {i}: Incorrect number of fields.")
                        error_count += 1
                        continue
                        
                    amount, category, payment_method, date, description, tag = row[:6]
                    payment_detail_identifier = row[6] if len(row) == 7 else ""
                    
                    # Call addexpense and check return value
                    result = self.addexpense(
                        amount.strip(), category.strip(), payment_method.strip(), 
                        date.strip(), description.strip(), tag.strip(), 
                        payment_detail_identifier.strip(), import_fn=1
                    )
                    
                    if result:
                        success_count += 1
                    else:
                        print(f"Failed to import row {i}: Error in adding expense.")
                        error_count += 1
                        
                print(f"Import complete: {success_count} successful, {error_count} failed.")
                
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
        except Exception as e:
            print(f"Error while importing CSV: {e}")
            
            
    def export_csv(self, file_path, sort_field=None):
        # Mapping allowed sort fields to actual SQL columns
        sort_fields = {
            "amount": "e.amount",
            "category": "c.category_name",
            "payment_method": "pm.payment_method_name",
            "date": "e.date",
            "description": "e.description",
            "tag": "t.tag_name",
            "payment_detail_identifier": "pme.payment_detail_identifier"
        }
        
        query = """
            SELECT e.amount,
                c.category_name,
                pm.payment_method_name,
                e.date,
                e.description,
                t.tag_name,
                pme.payment_detail_identifier
            FROM Expense e
            JOIN category_expense ce ON e.expense_id = ce.expense_id
            JOIN Categories c ON ce.category_id = c.category_id
            JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
            JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
            JOIN tag_expense te ON e.expense_id = te.expense_id
            JOIN Tags t ON te.tag_id = t.tag_id
        """
        
        # Add sorting only if sort_field is provided and valid
        if sort_field:
            if sort_field not in sort_fields:
                print("Error: Invalid sort field.")
                return
            query += f" ORDER BY {sort_fields[sort_field]}"

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        if not rows:
            print("No expenses found to export.")
            return

        try:
            with open(file_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                # Write header row
                writer.writerow(["amount", "category", "payment_method", "date", "description", "tag", "payment_detail_identifier"])

                for row in rows:
                    # row = (amount, category_name, payment_method_name, date, description, tag_name, payment_detail_identifier)
                    amount, category_name, payment_method_name, date, description, tag_name, payment_detail_identifier = row

                    # If payment_method ends with "card", mask all but last 4 chars of payment_detail_identifier
                    if payment_method_name.lower().endswith("card") and payment_detail_identifier:
                        masked_length = max(0, len(payment_detail_identifier) - 4)
                        payment_detail_identifier = ("*" * masked_length) + payment_detail_identifier[-4:]

                    writer.writerow([
                        amount,
                        category_name,
                        payment_method_name,
                        date,
                        description,
                        tag_name,
                        payment_detail_identifier
                    ])
            print(f"Exported expenses successfully to {file_path}.")
        except PermissionError:
            print(f"Error: Permission denied. Please close the file if it's open and try again.")
        except Exception as e:
            print(f"Error while exporting CSV: {e}")
            
            
            
            
#-------------------------------------------------------------------------------------------------------------------------------------------


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
