import sqlite3
import shlex
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import os

list_of_privileges = {
    "admin": {
        "add_user": "add_user <username> <password> <role>",
        "list_payment_methods": "list_payment_methods",
        "add_payment_method": "add_payment_method <payment_method_name>",
        "list_categories": "list_categories",
        "add_category": "add_category <category_name>",
        "list_users": "list_users",
        "list_expenses": "list_expenses [<field> <operator> <value>, ...]",
        "report": {
            "top_expenses": "report top_expenses <N> <start_date> <end_date>",
            "category_spending": "report category_spending <category>",
            "above_average_expenses": "report above_average_expenses",
            "monthly_category_spending": "report monthly_category_spending",
            "highest_spender_per_month": "report highest_spender_per_month",
            "frequent_category": "report frequent_category",
            "tag_expenses": "report tag_expenses"
        }
    },
    "user": {
        "list_categories": "list_categories",
        "list_payment_methods": "list_payment_methods",
        "add_expense": "add_expense <amount> <category> <payment_method> <date> <description> <tag>",
        "update_expense": "update_expense <expense_id> <field> <new_value>",
        "delete_expense": "delete_expense <expense_id>",
        "list_expenses": "list_expenses [<field> <operator> <value>, ...]",
        "import_expenses": "import_expenses <file_path>",
        "export_csv": "export_csv <file_path> [, sort-on <field_name>]",
        "report": {
            "top_expenses": "report top_expenses <N> <start_date> <end_date>",
            "category_spending": "report category_spending <category>",
            "above_average_expenses": "report above_average_expenses",
            "monthly_category_spending": "report monthly_category_spending",
            "payment_method_usage": "report payment_method_usage",
            "frequent_category": "report frequent_category",
            "tag_expenses": "report tag_expenses"
        }
    }
}



class ExpenseApp:
    def __init__(self,cursor,conn):
        #sqlite connection code
        self.conn = conn
        self.cursor = cursor
        #current session details
        self.current_user = None
        self.privileges = None
    
    def authenticate(self,username,password):
        # Step 1: Check if the username exists
        self.cursor.execute("SELECT password FROM User WHERE username = ?", (username,))
        user = self.cursor.fetchone()

        if user is None:
            print("Error: Username does not exist.")  # Username not found
            return

        stored_password = user[0]  # Get stored password

        # Step 2: Check if password matches
        if stored_password == password:
            print("Login successful!")
        else:
            print("Error: Incorrect password.")  # Password mismatch
            return
        
        self.current_user = username
        self.cursor.execute("SELECT r.role_name FROM user_role u,Role r WHERE u.username = ? and u.role_id = r.role_id", (username,))
        role = self.cursor.fetchone()[0]
        self.privileges = role      
        
    def logout(self):
        self.current_user = None
        self.privileges = None
        print("Logging Out.....")
            
    def register(self,username,password,role):
        self.cursor.execute("SELECT role_id FROM Role WHERE role_name = ?", (role,))
        result = self.cursor.fetchone()
        if result is None:
            print(f"Error: Role '{role}' does not exist. Registration failed!")
            return  # Stop execution if role is not found
        
        role_id = result[0]  # Extract role_id

        try:
            self.cursor.execute("INSERT INTO User (username, password) VALUES (?, ?)", (username, password))
            self.cursor.execute("INSERT INTO user_role (username, role_id) VALUES (?, ?)", (username, role_id))
            print("User added successfully!")
            self.conn.commit()
        except sqlite3.IntegrityError:  # Catches duplicate username errors
            print("Error: Username already exists!")
            return
        

    def list_users(self):
        self.cursor.execute("Select username from User")
        users = self.cursor.fetchall()
        
        if not users:
            print("No users found!!")
        else:
            print("User:")
            print("-" * 20)
            for user in users:
                print(f"- {user[0]}")
        
        
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
            print("No Payment Mehod found.")
        else:
            print("Payment Methods:")
            print("-" * 20)
            for payement_method in payment_method_names:
                print(f"- {payement_method[0]}")


    def addexpense(self, amount, category, payment_method, date, description, tag, payment_detail_identifier="",import_fn = 0):
        # Try to convert amount to float
        try:
            amount = float(amount)
        except ValueError:
            print(f"Error: Invalid amount '{amount}'. Must be a number.")
            return False
        
        try:
            self.cursor.execute(
            "INSERT INTO Expense (date, amount, description) VALUES (?, ?, ?)", 
            (date, amount, description))

            expense_id = self.cursor.lastrowid
            
            # Check if category exists
            self.cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (category,))
            result = self.cursor.fetchone()
            if result is None:
                print(f"Error: Category '{category}' does not exist. Adding failed!")
                self.conn.rollback()
                return False
            
            category_id = result[0]  # Extract category_id
            self.cursor.execute(
            "INSERT INTO category_expense (category_id,expense_id) VALUES (?, ?)", 
            (category_id,expense_id))
            
            self.cursor.execute("SELECT tag_id FROM Tags WHERE tag_name = ?", (tag,))
            result = self.cursor.fetchone()
            if result is None:
                self.cursor.execute(
                "INSERT INTO Tags (tag_name) VALUES (?)", 
                (tag,))
                tag_id = self.cursor.lastrowid
            else:
                tag_id = result[0]
                
            self.cursor.execute(
            "INSERT INTO tag_expense (tag_id,expense_id) VALUES (?, ?)", 
            (tag_id,expense_id))
            
            
            self.cursor.execute("SELECT payment_method_id FROM Payment_Method WHERE Payment_Method_Name = ?", (payment_method,))
            result = self.cursor.fetchone()
            if result is None:
                print(f"Error: Payment Method '{payment_method}' does not exist. Adding failed!")
                self.conn.rollback()
                return False
            
            payment_method_id = result[0]  # Extract payment_method_id
            self.cursor.execute(
            "INSERT INTO payment_method_expense(payment_method_id,expense_id,payment_detail_identifier) VALUES (?, ?,?)", 
            (payment_method_id,expense_id,payment_detail_identifier))
            
            self.cursor.execute(
            "INSERT INTO user_expense(username,expense_id) VALUES (?, ?)", 
            (self.current_user,expense_id))
            
            self.conn.commit()
            if import_fn == 0:
                print("Expense Added Successfully")
            return True
            
        except sqlite3.Error as e:
            print(f"Database error adding expense: {e}")
            self.conn.rollback()
            return False
    
    def update_expense(self, expense_id, field, new_value):
        self.cursor.execute("SELECT COUNT(*) FROM user_expense WHERE expense_id = ? AND username = ?", (expense_id, self.current_user))
        exists = self.cursor.fetchone()[0] > 0  # True if count > 0, else False
        if not exists:
            print(f"Error: Expense ID {expense_id} doesn't exist or doesn't belong to the current user.")
            return

        field = field.lower()

        try:
            if field == 'amount':
                self.cursor.execute("UPDATE Expense SET amount = ? WHERE expense_id = ?", (new_value, expense_id))
            elif field == 'description':
                self.cursor.execute("UPDATE Expense SET description = ? WHERE expense_id = ?", (new_value, expense_id))
            elif field == 'date':
                self.cursor.execute("UPDATE Expense SET date = ? WHERE expense_id = ?", (new_value, expense_id))
            elif field == 'category':
                self.cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (new_value,))
                category = self.cursor.fetchone()
                if category is None:
                    print(f"Error: Category '{new_value}' does not exist.")
                    return
                category_id = category[0]
                self.cursor.execute("UPDATE category_expense SET category_id = ? WHERE expense_id = ?", (category_id, expense_id))
            elif field == 'tag':
                self.cursor.execute("SELECT tag_id FROM Tags WHERE tag_name = ?", (new_value,))
                tag = self.cursor.fetchone()
                if tag is None:
                    self.cursor.execute("INSERT INTO Tags (tag_name) VALUES (?)", (new_value,))
                    tag_id = self.cursor.lastrowid
                else:
                    tag_id = tag[0]
                self.cursor.execute("UPDATE tag_expense SET tag_id = ? WHERE expense_id = ?", (tag_id, expense_id))
            elif field == 'payment_method':
                self.cursor.execute("SELECT payment_method_id FROM Payment_Method WHERE payment_method_name = ?", (new_value,))
                payment_method = self.cursor.fetchone()
                if payment_method is None:
                    print(f"Error: Payment Method '{new_value}' doesn't exist.")
                    return
                payment_method_id = payment_method[0]
                self.cursor.execute("UPDATE payment_method_expense SET payment_method_id = ? WHERE expense_id = ?", (payment_method_id, expense_id))
            else:
                print(f"Error: Field '{field}' is not valid for updating.")
                return

            self.conn.commit()
            print(f"Expense ID {expense_id} updated successfully.")
        except sqlite3.Error as e:
            print(f"Error: Failed to update expense. {e}")
    
    def delete_expense(self, expense_id):
        self.cursor.execute("SELECT COUNT(*) FROM user_expense WHERE expense_id = ? AND username = ?", (expense_id, self.current_user))
        exists = self.cursor.fetchone()[0] > 0  # True if count > 0, else False
        if not exists:
            print(f"Error: Expense ID {expense_id} doesn't exist or doesn't belong to the current user.")
            return

        try:
            # Delete from related tables
            self.cursor.execute("DELETE FROM category_expense WHERE expense_id = ?", (expense_id,))
            self.cursor.execute("DELETE FROM tag_expense WHERE expense_id = ?", (expense_id,))
            self.cursor.execute("DELETE FROM payment_method_expense WHERE expense_id = ?", (expense_id,))
            self.cursor.execute("DELETE FROM user_expense WHERE expense_id = ?", (expense_id,))
            
            # Delete from the main Expense table
            self.cursor.execute("DELETE FROM Expense WHERE expense_id = ?", (expense_id,))
            
            self.conn.commit()
            print(f"Expense ID {expense_id} deleted successfully.")
        except sqlite3.Error as e:
            print(f"Error: Failed to delete expense. {e}")
    
    def list_expenses(self, filters={}):
        try:
            # Initial query to connect all required tables
            query = """
            SELECT e.expense_id, e.date, e.amount, e.description, 
                c.category_name, t.tag_name, pm.payment_method_name, ue.username
            FROM Expense e
            LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
            LEFT JOIN Categories c ON ce.category_id = c.category_id
            LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
            LEFT JOIN Tags t ON te.tag_id = t.tag_id
            LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
            LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
            LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
            """
            
            params = []
            
            # Check if current user is admin or regular user
            if self.privileges == "admin":
                # Admin can see all expenses - no username filter needed
                pass
            else:
                # Regular user can only see their own expenses
                query += """
                WHERE e.expense_id IN (
                    SELECT expense_id FROM user_expense WHERE username = ?
                )
                """
                params.append(self.current_user)
            
            # Define operation fields
            op_fields = {"and": ["amount", "date"], 
                        "or": ["category", "tag", "payment_method", "month"]}
            
            # Month name to number mapping
            month_mapping = {
                "january": "01", "february": "02", "march": "03", "april": "04",
                "may": "05", "june": "06", "july": "07", "august": "08",
                "september": "09", "october": "10", "november": "11", "december": "12"
            }
            
            # Process filters
            for field in filters:
                if not filters[field]:  # Skip empty filter lists
                    continue
                    
                if field in op_fields["and"]:
                    op = "AND"
                else:
                    op = "OR"
                    
                # Special handling for month
                if field == "month":
                    connector = "WHERE" if "WHERE" not in query else "AND"
                    query += f" {connector} ("
                    first = True
                    for constraint in filters[field]:
                        op_type, value = constraint
                        if not first:
                            query += f" {op} "
                        first = False
                        
                        # Handle month name conversion
                        if isinstance(value, str) and value.lower() in month_mapping:
                            month_num = month_mapping[value.lower()]
                            query += f"strftime('%m', e.date) {op_type} ?"
                            params.append(month_num)
                        else:
                            # Assume it's a number
                            query += f"strftime('%m', e.date) {op_type} ?"
                            # Ensure month is zero-padded
                            if isinstance(value, str) and len(value) == 1:
                                params.append(value.zfill(2))
                            else:
                                params.append(value)
                    query += ")"
                    continue
                    
                # Handle regular fields with mapping to actual DB columns
                field_mapping = {
                    "amount": "e.amount",
                    "date": "e.date",
                    "category": "c.category_name",
                    "tag": "t.tag_name",
                    "payment_method": "pm.payment_method_name"
                }
                
                db_field = field_mapping.get(field, field)
                
                connector = "WHERE" if "WHERE" not in query else "AND"
                query += f" {connector} ("
                first = True
                for constraint in filters[field]:
                    op_type, value = constraint
                    if not first:
                        query += f" {op} "
                    first = False
                    query += f"{db_field} {op_type} ?"
                    params.append(value)
                query += ")"
            
            # Execute the query and display results
            self.cursor.execute(query, params)
            expenses = self.cursor.fetchall()
            
            if not expenses:
                print("No expenses found matching the criteria.")
                return
            
            # Display results in a formatted table
            print("\nExpense List:")
            print("-" * 95)
            
            # Add username column for admin view
            if self.privileges == "admin":
                print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Category':<15} {'Tag':<15} {'Payment Method':<15} {'Username':<10} {'Description':<25}")
                print("-" * 95)
                
                for expense in expenses:
                    expense_id, date, amount, description, category, tag, payment_method, username = expense
                    # Handle NULL values from LEFT JOINs
                    category = category or "N/A"
                    tag = tag or "N/A"
                    payment_method = payment_method or "N/A"
                    username = username or "N/A"
                    description = (description[:22] + "...") if description and len(description) > 25 else (description or "")
                    
                    print(f"{expense_id:<5} {date:<12} {amount:<10.2f} {category:<15} {tag:<15} {payment_method:<15} {username:<10} {description:<25}")
            else:
                # Original display for regular users
                print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Category':<15} {'Tag':<15} {'Payment Method':<15} {'Description':<30}")
                print("-" * 95)
                
                for expense in expenses:
                    expense_id, date, amount, description, category, tag, payment_method, _ = expense
                    # Handle NULL values from LEFT JOINs
                    category = category or "N/A"
                    tag = tag or "N/A"
                    payment_method = payment_method or "N/A"
                    description = (description[:27] + "...") if description and len(description) > 30 else (description or "")
                    
                    print(f"{expense_id:<5} {date:<12} {amount:<10.2f} {category:<15} {tag:<15} {payment_method:<15} {description:<30}")
            
            print("-" * 95)
            print(f"Total: {len(expenses)} expense(s) found")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
        except Exception as e:
            print(f"Error listing expenses: {e}")
            
    def import_expenses(self, file_path):
        try:
            with open(file_path, newline="") as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                expected_header = ["amount", "category", "payment_method", "date", "description", "tag","payment_detail_identifier"]
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
                    payment_detail_identifier = ""
                    if len(row) == 7:
                        payment_detail_identifier = row[6]
                        
                    # Call addexpense and check return value
                    result = self.addexpense(amount, category.strip().lower(), payment_method.strip().lower(),
                                            date, description, tag.strip().lower(), payment_detail_identifier,import_fn=1)
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                        print(f"Failed to import row {i}")
                        
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
        except Exception as e:
            print(f"Error while exporting CSV: {e}")
    
    def parser(self, cmd_str):
        cmd_str = cmd_str.strip()
        try:
            cmd_str_lst = shlex.split(cmd_str)  # Use shlex.split for parsing
        except ValueError as e:
            print(f"Error: {e}")  # Handle quote-closing errors
            return
        
        if not cmd_str_lst:
            print("Error: No command entered.")
            return
        
        cmd = cmd_str_lst[0]
        
        # Handling help -  available for all users
        if cmd == "help":
            if len(cmd_str_lst) != 1:
                print("Error: No arguments required")
            else:
                self.help()
            return
        
        # Handling login
        elif cmd == "login":
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
                print("Error: Insufficient number of arguments")
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
        if cmd not in list_of_privileges[self.privileges]:
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
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['admin']['add_user']}")

        # Handling list_categories
        elif cmd == "list_categories":
            if len(cmd_str_lst) != 1:
                print("Error: No arguments required")
            else:
                self.list_categories()

        # Handling add_category (Admin only)
        elif cmd == "add_category":
            if len(cmd_str_lst) != 2:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['admin']['add_category']}")
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
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['admin']['add_payment_method']}")
            else:
                payment_method_name = cmd_str_lst[1]
                self.add_payment_method(payment_method_name)

        # Handling addexpense
        elif cmd == "add_expense":
            if len(cmd_str_lst) == 6 or len(cmd_str_lst) == 7 :  #  description is optional. Therefore 6 arguments are also fine
                amount = cmd_str_lst[1]
                category_name = cmd_str_lst[2]
                payment_method_name = cmd_str_lst[3]
                date_txt = cmd_str_lst[4]
                tag_name = cmd_str_lst[-1]
                
                # Handle optional description
                if len(cmd_str_lst) == 6:  # No description provided
                    description = ""
                else:  # Description is provided
                    description = cmd_str_lst[5]
                    
                payment_detail_identifier = ""
                choice = input("Would you like to add payment method details?(y/n) [Type more to display more info]: ")
                if choice.lower() == "more":
                    print("This detail can be used by the used by the user to generate reports based on specific payment method")
                    print("The details will be masked")
                    choice = input("Would you like to add payment method details?(y/n): ")
                if choice.lower() == "y":
                    payment_detail_identifier = input("Enter the details: ")
                self.addexpense(amount, category_name, payment_method_name, date_txt, description, tag_name, payment_detail_identifier)    
                
            else:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['add_expense']}")
                return

        # Handling update_expense
        elif cmd == "update_expense":
            if len(cmd_str_lst) == 4:
                expense_id = cmd_str_lst[1]
                field = cmd_str_lst[2]
                new_value = cmd_str_lst[3]
                self.update_expense(expense_id, field, new_value)
            else:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['update_expense']}")

        # Handling delete_expense
        elif cmd == "delete_expense":
            if len(cmd_str_lst) == 2:
                expense_id = cmd_str_lst[1]
                self.delete_expense(expense_id)
            else:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['delete_expense']}")
        
        elif cmd == "list_expenses":
            field_dict = {
                "amount": [],
                "date": [],
                "category": [],
                "tag": [],
                "payment_method": [],
                "month": []
            }
            
            field_op = ["<",">","=","<=",">="]
            if len(cmd_str_lst)>1:
                constraint_list = cmd_str[len(cmd):].split(',')
                for constraint in constraint_list:
                    constraint = shlex.split(constraint)
                    if len(constraint)!=3:
                        print("Error : Filter Incomplete!!")
                        return
                    if constraint[0] not in field_dict:
                        print("Error : Invalid Filter !!")
                        return
                    if constraint[1] not in field_op:
                        print("Error : Invalid Operator for filter!!")
                    
                    field_dict[constraint[0]].append([constraint[1],constraint[2]])
                
                self.list_expenses(field_dict)
            else:
                self.list_expenses()
                    
        elif cmd == "import_expenses":
            if len(cmd_str_lst) != 2:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['import_expenses']}")
            else:
                file_path = cmd_str_lst[1]
                self.import_expenses(file_path)

        elif cmd == "export_csv":
            # Split by comma to check for optional sort-on parameter
            parts = cmd_str.strip().split(',', 1)
            export_cmd = parts[0].strip()
            
            # Get file path based on whether it's quoted or not
            if '"' in export_cmd or "'" in export_cmd:
                # If quoted, use shlex for proper quote handling
                cmd_parts = shlex.split(export_cmd)
                if len(cmd_parts) < 2:
                    print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['export_csv']}")
                    return
                file_path = cmd_parts[1]
            else:
                # If not quoted, use string slicing approach
                if export_cmd.startswith("export_csv "):
                    file_path = export_cmd[len("export_csv "):].strip()
                else:
                    print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['export_csv']}")
                    return
            
            if not file_path:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['export_csv']}")
                return
            
            # Check for optional sort-on parameter
            if len(parts) > 1:
                sort_part = parts[1].strip()
                sort_parts = shlex.split(sort_part)
                
                if len(sort_parts) != 2 or sort_parts[0].lower() != "sort-on":
                    print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['export_csv']}")
                    return
                    
                sort_field = sort_parts[1].lower()
                self.export_csv(file_path, sort_field)
            else:
                # No sorting specified
                self.export_csv(file_path)
                
        # Handling list_users (Admin only)
        elif cmd == "list_users":
            if len(cmd_str_lst) != 1:
                print("Error: No arguments required")
            else:
                self.list_users()

        # Handling report commands
        elif cmd == "report":
            if len(cmd_str_lst) < 2:
                print("Error: Report type not specified")
                print("Available report types for your role:")
                for report_type, syntax in list_of_privileges[self.privileges]["report"].items():
                    print(f"- {syntax}")
                return
                
            report_type = cmd_str_lst[1]
            
            # Check if the report type is valid for the user's role
            if report_type not in list_of_privileges[self.privileges]["report"]:
                print(f"Error: Invalid or unauthorized report type '{report_type}'")
                return
            
            # Handle different report types
            if report_type == "top_expenses":
                if len(cmd_str_lst) != 5:
                    print(f"Error: Incorrect syntax. Usage: {list_of_privileges[self.privileges]['report']['top_expenses']}")
                else:
                    n = cmd_str_lst[2]
                    start_date = cmd_str_lst[3]
                    end_date = cmd_str_lst[4]
                    self.generate_report_top_expenses(n, start_date, end_date)
                    
            elif report_type == "category_spending":
                if len(cmd_str_lst) != 3:
                    print(f"Error: Incorrect syntax. Usage: {list_of_privileges[self.privileges]['report']['category_spending']}")
                else:
                    category = cmd_str_lst[2]
                    self.generate_report_category_spending(category)
                    
            elif report_type == "above_average_expenses":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.generate_report_above_average_expenses()
                    
            elif report_type == "monthly_category_spending":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.generate_report_monthly_category_spending()
                    
            elif report_type == "highest_spender_per_month":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.generate_report_highest_spender_per_month()
                    
            elif report_type == "frequent_category":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.generate_report_frequent_category()
                    
            elif report_type == "payment_method_usage":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.generate_report_payment_method_usage()
                    
            elif report_type == "tag_expenses":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.generate_report_tag_expenses()

        else:
            print("Error: Invalid command")

    
    def help(self):
        if self.current_user is None:
            print("Available commands:")
            print("- login <username> <password>")
            print("- help")
        else:
            print("Available commands:")
            # Display regular commands
            for command, syntax in list_of_privileges[self.privileges].items():
                if command != "report":  # Handle report separately
                    print(f"- {syntax}")
            
            # Display report commands if available
            if "report" in list_of_privileges[self.privileges]:
                print("\nReport commands:")
                for _, syntax in list_of_privileges[self.privileges]["report"].items():
                    print(f"- {syntax}")
                    
            print("\nOther commands:")
            print("- logout")
            print("- help")

    def generate_report_top_expenses(self, n, start_date, end_date):
        """Report top N expenses for a given date range"""
        try:
            n = int(n)
            if n <= 0:
                print("Error: N must be a positive integer")
                return

            # Validate date format
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                print("Error: Dates must be in the format YYYY-MM-DD")
                return

            # Base query
            query = """
            SELECT e.expense_id, e.date, e.amount, e.description, 
                c.category_name, t.tag_name, pm.payment_method_name, ue.username
            FROM Expense e
            LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
            LEFT JOIN Categories c ON ce.category_id = c.category_id
            LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
            LEFT JOIN Tags t ON te.tag_id = t.tag_id
            LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
            LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
            LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
            WHERE e.date BETWEEN ? AND ?
            """

            params = [start_date, end_date]

            # Apply user filtering for regular users
            if self.privileges != "admin":
                query += " AND ue.username = ?"
                params.append(self.current_user)

            # Order by amount and limit results
            query += " ORDER BY e.amount DESC LIMIT ?"
            params.append(n)

            self.cursor.execute(query, params)
            expenses = self.cursor.fetchall()

            if not expenses:
                print(f"No expenses found between {start_date} and {end_date}")
                return

            # Display results
            print(f"\nTop {n} Expenses from {start_date} to {end_date}:")
            print("-" * 95)
            
            # Different headers based on user role
            if self.privileges == "admin":
                print(f"{'ID':<5} {'Username':<15} {'Date':<12} {'Amount':<10} {'Category':<15} {'Tag':<15} {'Payment Method':<15} {'Description':<25}")
                print("-" * 95)
                
                for expense in expenses:
                    expense_id, date, amount, description, category, tag, payment_method, username = expense
                    category = category or "N/A"
                    tag = tag or "N/A"
                    username = username or "N/A"
                    payment_method = payment_method or "N/A"
                    description = (description[:22] + "...") if description and len(description) > 25 else (description or "")
                    
                    print(f"{expense_id:<5} {username:<15} {date:<12} {amount:<10.2f} {category:<15} {tag:<15} {payment_method:<15} {description:<25}")
            else:
                print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Category':<15} {'Tag':<15} {'Payment Method':<15} {'Description':<25}")
                print("-" * 95)
                
                for expense in expenses:
                    expense_id, date, amount, description, category, tag, payment_method, _ = expense
                    category = category or "N/A"
                    tag = tag or "N/A"
                    payment_method = payment_method or "N/A"
                    description = (description[:22] + "...") if description and len(description) > 25 else (description or "")
                    
                    print(f"{expense_id:<5} {date:<12} {amount:<10.2f} {category:<15} {tag:<15} {payment_method:<15} {description:<25}")
            
            print("-" * 95)
            print(f"Total: {len(expenses)} expense(s) found. Total amount: {sum(expense[2] for expense in expenses):.2f}")
            
            # Create a line chart showing just expense amounts
            if expenses:
                plt.figure(figsize=(12, 6))
                
                # Extract data for plotting
                ids = [str(exp[0]) for exp in expenses]
                amounts = [exp[2] for exp in expenses]
                
                # Create line chart
                plt.plot(ids, amounts, marker='o', linestyle='-', color='red', linewidth=2, markersize=8)
                
                # Add amount labels above each point
                for i, amount in enumerate(amounts):
                    plt.text(i, amount + (max(amounts) * 0.02), f'{amount:.2f}', 
                            ha='center', va='bottom', fontsize=9)
                
                plt.xlabel('Expense ID')
                plt.ylabel('Amount')
                
                # Add username information for admin users
                if self.privileges == "admin":
                    # Add username labels below each point
                    usernames = [exp[7] or "N/A" for exp in expenses]
                    plt.title(f'Top {n} Expenses - Line Chart (With User Info)')
                    
                    # Add custom x-tick labels with ID and username
                    plt.xticks(range(len(ids)), [f"ID:{id}\n{user}" for id, user in zip(ids, usernames)], rotation=45)
                else:
                    plt.title(f'Top {n} Expenses - Line Chart')
                    plt.xticks(rotation=45)
                
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                plt.show(block=False)  # Non-blocking display
                plt.pause(0.001)  # Small pause to render the plot
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    def generate_report_category_spending(self, category):
        """Report total spending for a specific category"""
        try:
            # Normalize category name
            category = category.strip().lower()
            
            # Check if category exists
            self.cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (category,))
            result = self.cursor.fetchone()
            if result is None:
                print(f"Error: Category '{category}' does not exist.")
                return
                
            category_id = result[0]
            
            # Base query for total spending stats (not monthly breakdown)
            query = """
            SELECT SUM(e.amount) as total_amount, 
                   COUNT(e.expense_id) as count, 
                   MAX(e.amount) as max_expense, 
                   MIN(e.amount) as min_expense,
                   AVG(e.amount) as avg_expense
            FROM Expense e
            JOIN category_expense ce ON e.expense_id = ce.expense_id
            JOIN user_expense ue ON e.expense_id = ue.expense_id
            WHERE ce.category_id = ?
            """
            
            params = [category_id]
            
            # Apply user filtering for regular users
            if self.privileges != "admin":
                query += " AND ue.username = ?"
                params.append(self.current_user)
            
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            
            if not result or result[0] is None:
                print(f"No expenses found for category '{category}'")
                return
                
            total, count, max_exp, min_exp, avg_exp = result
            
            # Display results
            print(f"\nSummary Statistics for Category: {category}")
            print("-" * 60)
            print(f"Total spending: {total:.2f}")
            print(f"Number of expenses: {count}")
            print(f"Highest expense: {max_exp:.2f}")
            print(f"Lowest expense: {min_exp:.2f}")
            print(f"Average expense: {avg_exp:.2f}")
            print("-" * 60)
            
            # After displaying text results, add visualization:
            if result and result[0] is not None:
                total, count, max_exp, min_exp, avg_exp = result
                
                # First, get data for category proportion calculation
                if self.privileges != "admin":
                    self.cursor.execute("SELECT SUM(e.amount) FROM Expense e JOIN user_expense ue ON e.expense_id = ue.expense_id WHERE ue.username = ?", 
                                       (self.current_user,))
                else:
                    self.cursor.execute("SELECT SUM(e.amount) FROM Expense e")
                    
                total_all_expenses = self.cursor.fetchone()[0] or 0
                percentage = (total / total_all_expenses * 100) if total_all_expenses > 0 else 0
                
                # Create a dashboard layout with multiple subplots
                fig = plt.figure(figsize=(12, 8))
                plt.suptitle(f'Dashboard: {category.capitalize()} Category', fontsize=16)
                
                # Grid spec for custom layout
                gs = fig.add_gridspec(2, 3)
                
                # First subplot: Key Metrics display
                ax1 = fig.add_subplot(gs[0, 0])
                ax1.axis('off')  # No axes for text display
                ax1.text(0.5, 0.9, f"Key Metrics", ha='center', fontsize=14, fontweight='bold')
                ax1.text(0.5, 0.7, f"Total Spending: ${total:.2f}", ha='center')
                ax1.text(0.5, 0.5, f"Number of Expenses: {count}", ha='center')
                ax1.text(0.5, 0.3, f"Average Expense: ${avg_exp:.2f}", ha='center')
                
                # Second subplot: Value comparison bar chart
                ax2 = fig.add_subplot(gs[0, 1:])
                metrics = ['Total', 'Maximum', 'Minimum', 'Average']
                values = [total, max_exp, min_exp, avg_exp]
                colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
                bars = ax2.bar(metrics, values, color=colors)
                ax2.set_title('Expense Values')
                ax2.set_ylabel('Amount ($)')
                
                # Add value labels to the bars
                for bar in bars:
                    height = bar.get_height()
                    ax2.annotate(f'${height:.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')
                
                # Third subplot: Pie chart showing proportion
                ax3 = fig.add_subplot(gs[1, 0])
                sizes = [total, total_all_expenses - total]
                labels = [f'{category.capitalize()}\n(${total:.2f})', f'Other Categories\n(${total_all_expenses - total:.2f})']
                colors = ['#3498db', '#e6e6e6']
                explode = (0.1, 0)  # explode the first slice
                
                # Only create pie if there are other expenses
                if total_all_expenses > 0:
                    ax3.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                           shadow=True, startangle=90)
                    ax3.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                    ax3.set_title('Proportion of Total Spending')
                else:
                    ax3.axis('off')
                    ax3.text(0.5, 0.5, "No data for proportion", ha='center')
                
                # Fourth subplot: Gauge chart for percentage of total
                ax4 = fig.add_subplot(gs[1, 1:])
                gauge_colors = ['#f1c40f', '#e67e22', '#e74c3c']
                
                # Create a semi-circle gauge
                theta = np.linspace(0, np.pi, 100)
                r = 1.0
                
                # Draw the gauge background
                for i, color in enumerate(gauge_colors):
                    ax4.fill_between(theta, 0.8, 1.0, 
                                    color=color, 
                                    alpha=0.3,
                                    where=((i/3)*np.pi <= theta) & (theta <= ((i+1)/3)*np.pi))
                
                # Draw the gauge needle
                needle_theta = np.pi * min(percentage/100, 1.0)
                ax4.plot([0, np.cos(needle_theta)], [0, np.sin(needle_theta)], 'k-', lw=2)
                
                # Add a center circle for gauge aesthetics
                circle = plt.Circle((0, 0), 0.1, color='k', fill=True)
                ax4.add_artist(circle)
                
                # Set gauge labels
                ax4.text(-0.2, -0.15, '0%', fontsize=10)
                ax4.text(1.1, -0.15, '100%', fontsize=10)
                ax4.text(0.5, 0.5, f'{percentage:.1f}%', ha='center', fontsize=14)
                
                # Clean up gauge appearance
                ax4.set_xlim(-1.1, 1.1)
                ax4.set_ylim(-0.2, 1.1)
                ax4.axis('off')
                ax4.set_title('Percentage of Total Spending')
                
                plt.tight_layout()
                plt.subplots_adjust(top=0.9)  # Adjust for main title
                
                # Display the dashboard
                plt.show()
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    def generate_report_above_average_expenses(self):
        """Report expenses that are above the category average, grouped by category"""
        try:
            # Subquery to get category averages - keep this part the same
            query = """
            WITH CategoryAverages AS (
                SELECT ce.category_id, c.category_name, AVG(e.amount) as avg_amount
                FROM category_expense ce
                JOIN Expense e ON ce.expense_id = e.expense_id
                JOIN Categories c ON ce.category_id = c.category_id
                JOIN user_expense ue ON e.expense_id = ue.expense_id
            """
            
            params = []
            
            # Apply user filtering for regular users
            if self.privileges != "admin":
                query += " WHERE ue.username = ?"
                params.append(self.current_user)
                
            query += """
                GROUP BY ce.category_id
            )
            SELECT e.expense_id, e.date, e.amount, e.description, 
                   c.category_name, ca.avg_amount, t.tag_name, 
                   pm.payment_method_name, ue.username
            FROM Expense e
            JOIN category_expense ce ON e.expense_id = ce.expense_id
            JOIN Categories c ON ce.category_id = c.category_id
            JOIN CategoryAverages ca ON ce.category_id = ca.category_id
            LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
            LEFT JOIN Tags t ON te.tag_id = t.tag_id
            LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
            LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
            JOIN user_expense ue ON e.expense_id = ue.expense_id
            WHERE e.amount > ca.avg_amount
            """
            
            # Additional filtering for regular users
            if self.privileges != "admin":
                query += " AND ue.username = ?"
                params.append(self.current_user)
                
            # No ORDER BY in main query - we'll sort by category and diff% later
            
            self.cursor.execute(query, params)
            expenses = self.cursor.fetchall()
            
            if not expenses:
                print("No above-average expenses found.")
                return
            
            # Organize results by category
            category_expenses = {}
            
            for expense in expenses:
                expense_id, date, amount, description, category, avg_amount, tag, payment_method, username = expense
                # Calculate percentage difference
                percentage_diff = ((amount - avg_amount) / avg_amount) * 100
                
                # Add percentage diff to the expense data
                expense_with_diff = expense + (percentage_diff,)
                
                if category not in category_expenses:
                    category_expenses[category] = []
                category_expenses[category].append(expense_with_diff)
            
            # Sort each category's expenses by percentage diff (descending)
            for category in category_expenses:
                category_expenses[category].sort(key=lambda x: x[9], reverse=True)
            
            # Display results by category
            print("\nExpenses Above Category Average (By Category):")
            
            # Get total count for summary
            total_above_avg = 0
            
            # Display a table for each category
            for category in sorted(category_expenses.keys()):
                cat_expenses = category_expenses[category]
                total_above_avg += len(cat_expenses)
                
                print(f"\n{category.upper()} CATEGORY:")
                print("-" * 110)
                
                # Different headers based on user role
                if self.privileges == "admin":
                    print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Avg Amount':<12} {'Diff %':<10} {'Username':<12} {'Description':<25}")
                    print("-" * 110)
                    
                    for expense in cat_expenses:
                        expense_id, date, amount, description, _, avg_amount, _, _, username, percentage_diff = expense
                        description = (description[:22] + "...") if description and len(description) > 25 else (description or "")
                        
                        print(f"{expense_id:<5} {date:<12} {amount:<10.2f} {avg_amount:<12.2f} {percentage_diff:>+10.2f}% {username:<12} {description:<25}")
                else:
                    print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Avg Amount':<12} {'Diff %':<10} {'Payment Method':<15} {'Description':<25}")
                    print("-" * 110)
                    
                    for expense in cat_expenses:
                        expense_id, date, amount, description, _, avg_amount, _, payment_method, _, percentage_diff = expense
                        description = (description[:22] + "...") if description and len(description) > 25 else (description or "")
                        
                        print(f"{expense_id:<5} {date:<12} {amount:<10.2f} {avg_amount:<12.2f} {percentage_diff:>+10.2f}% {payment_method:<15} {description:<25}")
                
                print("-" * 110)
                print(f"Category total: {len(cat_expenses)} expense(s) above average")
            
            # Display overall summary
            print("\nSUMMARY:")
            print("-" * 60)
            print(f"Total: {total_above_avg} expense(s) above their category average")
            print(f"Categories with above-average expenses: {len(category_expenses)}")
            
            # Create visualization showing expenses by category
            if category_expenses:
                plt.figure(figsize=(14, 10))
                
                # Create a scatter plot with categories on x-axis
                all_categories = list(category_expenses.keys())
                category_indices = {cat: i for i, cat in enumerate(all_categories)}
                
                # Plot points for each expense
                x_values = []
                y_values = []
                sizes = []
                colors = []
                annotations = []
                
                # Color map for percentage differences
                cmap = plt.cm.get_cmap('RdYlGn_r')
                
                for cat, expenses in category_expenses.items():
                    cat_idx = category_indices[cat]
                    for exp in expenses:
                        amount = exp[2]
                        avg = exp[5]
                        diff_pct = exp[9]
                        
                        # Add jitter to x position to avoid overlapping points
                        jitter = (np.random.random() - 0.5) * 0.3
                        x_values.append(cat_idx + jitter)
                        y_values.append(amount)
                        
                        # Size based on amount
                        sizes.append(50 + (amount/max(exp[2] for exp in expenses)) * 100)
                        
                        # Color based on percentage difference (normalize to 0-1 range)
                        norm_diff = min(1.0, diff_pct / 200)  # Cap at 200% difference
                        colors.append(cmap(norm_diff))
                        
                        # Annotation with expense ID and diff%
                        annotations.append(f"ID:{exp[0]}\n+{diff_pct:.1f}%")
                
                # Draw scatter plot
                scatter = plt.scatter(x_values, y_values, s=sizes, c=colors, alpha=0.7)
                
                # Draw category average lines
                for cat, expenses in category_expenses.items():
                    cat_idx = category_indices[cat]
                    avg = expenses[0][5]  # All expenses in a category have the same average
                    plt.hlines(avg, cat_idx - 0.4, cat_idx + 0.4, colors='blue', linestyles='dashed', 
                               label='Category Average' if cat == list(category_expenses.keys())[0] else "")
                
                # Add hover annotations
                from matplotlib.offsetbox import OffsetImage, AnnotationBbox
                
                # Label axes and title
                plt.xlabel('Category')
                plt.ylabel('Amount')
                plt.title('Above-Average Expenses by Category')
                plt.xticks(range(len(all_categories)), all_categories)
                plt.grid(True, linestyle='--', alpha=0.3)
                
                # Add legend
                plt.colorbar(scatter, label='Percentage Above Average')
                plt.legend()
                
                # Display the plot
                plt.tight_layout()
                plt.show()
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    def generate_report_monthly_category_spending(self):
        """Report total spending per category for each month"""
        try:
            # Base query
            query = """
            SELECT strftime('%Y-%m', e.date) as month, 
                   c.category_name, 
                   SUM(e.amount) as total,
                   COUNT(e.expense_id) as count
            FROM Expense e
            JOIN category_expense ce ON e.expense_id = ce.expense_id
            JOIN Categories c ON ce.category_id = c.category_id
            JOIN user_expense ue ON e.expense_id = ue.expense_id
            """
            
            params = []
            
            # Apply user filtering for regular users
            if self.privileges != "admin":
                query += " WHERE ue.username = ?"
                params.append(self.current_user)
                
            query += " GROUP BY month, c.category_name ORDER BY month, total DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            if not results:
                print("No expenses found to generate monthly category spending report.")
                return
                
            # Organize data by month
            months = {}
            for month, category, total, count in results:
                if month not in months:
                    months[month] = []
                months[month].append((category, total, count))
                
            # Display results
            print("\nMonthly Category Spending Report:")
            
            for month in sorted(months.keys()):
                print(f"\n{month} Breakdown:")
                print("-" * 60)
                print(f"{'Category':<20} {'Amount':<15} {'Count':<10} {'Avg per Expense':<15}")
                print("-" * 60)
                
                month_total = 0
                for category, total, count in months[month]:
                    avg_per_expense = total / count
                    month_total += total
                    print(f"{category:<20} {total:<15.2f} {count:<10} {avg_per_expense:<15.2f}")
                    
                print("-" * 60)
                print(f"Month Total: {month_total:.2f}")
                
            # Create a stacked bar chart
            plt.figure(figsize=(14, 8))
            
            # Get unique months and categories
            all_months = sorted(months.keys())
            all_categories = sorted(set(category for month_data in months.values() 
                                   for category, _, _ in month_data))
            
            # Create data structure for plotting
            data = {}
            for category in all_categories:
                data[category] = []
                for month in all_months:
                    amount = next((total for cat, total, _ in months[month] if cat == category), 0)
                    data[category].append(amount)
            
            # Create the stacked bar chart
            bottom = np.zeros(len(all_months))
            for category in all_categories:
                plt.bar(all_months, data[category], bottom=bottom, label=category)
                bottom += np.array(data[category])
            
            plt.xlabel('Month')
            plt.ylabel('Amount')
            plt.title('Monthly Spending by Category')
            plt.legend(title='Categories', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save plot to a temporary file and show path
            plot_path = os.path.join(os.getcwd(), 'monthly_category_spending.png')
            plt.savefig(plot_path)
            plt.close()
            
            print(f"\nPlot saved to: {plot_path}")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    def generate_report_highest_spender_per_month(self):
        """Report the user with highest spending for each month (admin only)"""
        if self.privileges != "admin":
            print("Error: This report is only available for administrators.")
            return
            
        try:
            query = """
            WITH MonthlyUserSpending AS (
                SELECT 
                    strftime('%Y-%m', e.date) as month,
                    ue.username,
                    SUM(e.amount) as total_spending
                FROM Expense e
                JOIN user_expense ue ON e.expense_id = ue.expense_id
                GROUP BY month, ue.username
            ),
            RankedSpending AS (
                SELECT 
                    month,
                    username,
                    total_spending,
                    RANK() OVER (PARTITION BY month ORDER BY total_spending DESC) as spending_rank
                FROM MonthlyUserSpending
            )
            SELECT 
                month,
                username,
                total_spending
            FROM RankedSpending
            WHERE spending_rank = 1
            ORDER BY month
            """
            
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            if not results:
                print("No data available to generate highest spender report.")
                return
                
            # Display results in table format
            print("\nHighest Spender per Month:")
            print("-" * 50)
            print(f"{'Month':<15} {'Username':<20} {'Total Spending':<15}")
            print("-" * 50)
            
            for month, username, total in results:
                print(f"{month:<15} {username:<20} {total:<15.2f}")
                
            print("-" * 50)
            
            # Create enhanced visualization
            plt.figure(figsize=(14, 8))
            
            # Extract data for plotting
            months = [result[0] for result in results]
            amounts = [result[2] for result in results]
            usernames = [result[1] for result in results]
            
            # Create a custom colormap with gradient for visual appeal
            unique_users = list(set(usernames))
            cmap = plt.cm.viridis
            colors = cmap(np.linspace(0.1, 0.9, len(unique_users)))
            user_colors = {user: colors[i] for i, user in enumerate(unique_users)}
            
            # Plot the bars with enhanced styling
            bars = plt.bar(
                months, 
                amounts, 
                color=[user_colors[user] for user in usernames],
                width=0.6,
                edgecolor='white',
                linewidth=1.5,
                alpha=0.8
            )
            
            # Add annotations for each bar
            for bar, username, amount in zip(bars, usernames, amounts):
                # Username at the top of the bar
                plt.text(
                    bar.get_x() + bar.get_width()/2, 
                    bar.get_height() + (max(amounts) * 0.03), 
                    username,
                    ha='center',
                    fontsize=10,
                    fontweight='bold'
                )
                
                # Amount inside the bar
                plt.text(
                    bar.get_x() + bar.get_width()/2,
                    bar.get_height()/2,
                    f'${amount:.2f}',
                    ha='center',
                    va='center',
                    fontsize=9,
                    fontweight='bold',
                    color='white'
                )
            
            # Enhance the plot styling
            plt.xlabel('Month', fontsize=12, fontweight='bold')
            plt.ylabel('Total Spending ($)', fontsize=12, fontweight='bold')
            plt.title('Highest Spender Per Month', fontsize=16, fontweight='bold', pad=20)
            
            # Add a subtle grid for easier reading
            plt.grid(axis='y', linestyle='--', alpha=0.3)
            
            # Style the axis
            plt.xticks(rotation=45, fontsize=10)
            plt.yticks(fontsize=10)
            
            # Create legend for users
            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor=user_colors[user], label=user, edgecolor='white', linewidth=1) 
                              for user in unique_users]
            plt.legend(
                handles=legend_elements, 
                title="Users", 
                title_fontsize=12,
                loc='upper right',
                frameon=True,
                framealpha=0.95,
                edgecolor='lightgray'
            )
            
            # Add a note about the data
            plt.figtext(
                0.5, 0.01, 
                "Note: Shows only the top spender for each month", 
                ha='center', fontsize=9, fontstyle='italic'
            )
            
            plt.tight_layout()
            plt.show()  # Display the plot instead of saving
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    def generate_report_frequent_category(self):
        """Report the most frequently used expense category"""
        try:
            # Base query
            query = """
            SELECT c.category_name, COUNT(ce.expense_id) as usage_count, SUM(e.amount) as total_amount
            FROM Categories c
            JOIN category_expense ce ON c.category_id = ce.category_id
            JOIN Expense e ON ce.expense_id = e.expense_id
            JOIN user_expense ue ON e.expense_id = ue.expense_id
            """
            
            params = []
            
            # Apply user filtering for regular users
            if self.privileges != "admin":
                query += " WHERE ue.username = ?"
                params.append(self.current_user)
                
            query += " GROUP BY c.category_name ORDER BY usage_count DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            if not results:
                print("No expenses found to generate frequent category report.")
                return
                
            # Display results
            print("\nCategory Usage Report:")
            print("-" * 60)
            print(f"{'Category':<20} {'Usage Count':<15} {'Total Amount':<15} {'Avg Amount':<15}")
            print("-" * 60)
            
            for category, count, total in results:
                avg_amount = total / count
                print(f"{category:<20} {count:<15} {total:<15.2f} {avg_amount:<15.2f}")
                
            print("-" * 60)
            print(f"Most frequently used category: {results[0][0]} ({results[0][1]} uses)")
            
            # Create a horizontal bar chart
            if len(results) > 0:
                plt.figure(figsize=(10, max(6, len(results) * 0.4)))
                
                # Extract data for plotting
                categories = [result[0] for result in results]
                counts = [result[1] for result in results]
                
                # Sort data for better visualization
                categories.reverse()
                counts.reverse()
                
                # Create horizontal bar chart
                bars = plt.barh(categories, counts, color='purple')
                
                # Add count labels
                for i, v in enumerate(counts):
                    plt.text(v + 0.5, i, str(v), va='center')
                
                plt.xlabel('Usage Count')
                plt.title('Category Usage Frequency')
                plt.tight_layout()
                
                # Save plot to a temporary file and show path
                plot_path = os.path.join(os.getcwd(), 'frequent_category.png')
                plt.savefig(plot_path)
                plt.close()
                
                print(f"\nPlot saved to: {plot_path}")
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    def generate_report_payment_method_usage(self):
        """Report spending breakdown by payment method (user only)"""
        if self.privileges == "admin":
            print("Error: Payment method details are not available for administrators.")
            return
            
        try:
            query = """
            SELECT pm.payment_method_name, COUNT(pme.expense_id) as usage_count, 
                   SUM(e.amount) as total_amount
            FROM Payment_Method pm
            JOIN payment_method_expense pme ON pm.payment_method_id = pme.payment_method_id
            JOIN Expense e ON pme.expense_id = e.expense_id
            JOIN user_expense ue ON e.expense_id = ue.expense_id
            WHERE ue.username = ?
            GROUP BY pm.payment_method_name
            ORDER BY total_amount DESC
            """
            
            self.cursor.execute(query, (self.current_user,))
            results = self.cursor.fetchall()
            
            if not results:
                print("No payment method usage data available.")
                return
                
            # Display results
            print("\nPayment Method Usage Report:")
            print("-" * 60)
            print(f"{'Payment Method':<20} {'Usage Count':<15} {'Total Amount':<15} {'Avg Amount':<15}")
            print("-" * 60)
            
            for method, count, total in results:
                avg_amount = total / count
                print(f"{method:<20} {count:<15} {total:<15.2f} {avg_amount:<15.2f}")
                
            print("-" * 60)
            
            # Create a pie chart
            if results:
                plt.figure(figsize=(10, 8))
                
                # Extract data for plotting
                methods = [result[0] for result in results]
                amounts = [result[2] for result in results]
                
                # Create pie chart
                plt.pie(amounts, labels=methods, autopct='%1.1f%%', startangle=90, shadow=True)
                plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                plt.title('Spending by Payment Method')
                plt.tight_layout()
                
                # Save plot to a temporary file and show path
                plot_path = os.path.join(os.getcwd(), 'payment_method_usage.png')
                plt.savefig(plot_path)
                plt.close()
                
                print(f"\nPlot saved to: {plot_path}")
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    def generate_report_tag_expenses(self):
        """Report number of expenses for each tag"""
        try:
            # Base query
            query = """
            SELECT t.tag_name, COUNT(te.expense_id) as usage_count, SUM(e.amount) as total_amount
            FROM Tags t
            JOIN tag_expense te ON t.tag_id = te.tag_id
            JOIN Expense e ON te.expense_id = e.expense_id
            JOIN user_expense ue ON e.expense_id = ue.expense_id
            """
            
            params = []
            
            # Apply user filtering for regular users
            if self.privileges != "admin":
                query += " WHERE ue.username = ?"
                params.append(self.current_user)
                
            query += " GROUP BY t.tag_name ORDER BY usage_count DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            if not results:
                print("No tag usage data available.")
                return
                
            # Display results
            print("\nTag Usage Report:")
            print("-" * 60)
            print(f"{'Tag':<20} {'Usage Count':<15} {'Total Amount':<15} {'Avg Amount':<15}")
            print("-" * 60)
            
            for tag, count, total in results:
                avg_amount = total / count
                print(f"{tag:<20} {count:<15} {total:<15.2f} {avg_amount:<15.2f}")
                
            print("-" * 60)
            
            # Create a horizontal bar chart for counts and a separate pie chart for amounts
            if results:
                # Create figure with two subplots
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
                
                # Extract data for plotting
                tags = [result[0] for result in results]
                counts = [result[1] for result in results]
                amounts = [result[2] for result in results]
                
                # Sort data by count for better visualization
                sorted_data = sorted(zip(tags, counts, amounts), key=lambda x: x[1])
                tags = [x[0] for x in sorted_data]
                counts = [x[1] for x in sorted_data]
                amounts = [x[2] for x in sorted_data]
                
                # Bar chart for usage count
                ax1.barh(tags, counts, color='teal')
                ax1.set_xlabel('Usage Count')
                ax1.set_title('Tag Usage Frequency')
                
                # Add count labels
                for i, v in enumerate(counts):
                    ax1.text(v + 0.1, i, str(v), va='center')
                
                # Pie chart for amounts
                wedges, texts, autotexts = ax2.pie(amounts, labels=tags, autopct='%1.1f%%', startangle=90)
                ax2.axis('equal')
                ax2.set_title('Spending by Tag')
                
                # Adjust text properties for better readability
                plt.setp(autotexts, size=8, weight='bold')
                plt.setp(texts, size=8)
                
                plt.tight_layout()
                
                # Save plot to a temporary file and show path
                plot_path = os.path.join(os.getcwd(), 'tag_expenses.png')
                plt.savefig(plot_path)
                plt.close()
                
                print(f"\nPlot saved to: {plot_path}")
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

def main():
    conn = sqlite3.connect("ExpenseReport") # Creates/opens a database file
    cursor = conn.cursor()  # Creates a cursor object to execute SQL commands
    app = ExpenseApp(cursor,conn)
    print("Expense Reporting App")
    while True:
        cmd_string = input()
        if cmd_string.strip().lower() == "exit":
            print("Exiting ........")
            return 
        app.parser(cmd_string)
    # Close the connection
    conn.close()



main()



