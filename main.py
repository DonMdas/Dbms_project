    import sqlite3
    import shlex
    import csv

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
                    c.category_name, t.tag_name, pm.payment_method_name
                FROM Expense e
                LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                LEFT JOIN Categories c ON ce.category_id = c.category_id
                LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                LEFT JOIN Tags t ON te.tag_id = t.tag_id
                LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                WHERE e.expense_id IN (
                    SELECT expense_id FROM user_expense WHERE username = ?
                )
                """
                params = [self.current_user]
                
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
                        query += " AND ("
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
                    
                    query += " AND ("
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
                print("-" * 80)
                print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Category':<15} {'Tag':<15} {'Payment Method':<15} {'Description':<30}")
                print("-" * 80)
                
                for expense in expenses:
                    expense_id, date, amount, description, category, tag, payment_method = expense
                    # Handle NULL values from LEFT JOINs
                    category = category or "N/A"
                    tag = tag or "N/A"
                    payment_method = payment_method or "N/A"
                    description = (description[:27] + "...") if description and len(description) > 30 else (description or "")
                    
                    print(f"{expense_id:<5} {date:<12} {amount:<10.2f} {category:<15} {tag:<15} {payment_method:<15} {description:<30}")
                
                print("-" * 80)
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

        def export_csv(self, file_path, sort_field):
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
            if sort_field not in sort_fields:
                print("Error: Invalid sort field.")
                return

            query = f"""
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

            # Handling addexpense (To be implemented)
            elif cmd == "add_expense":
                if len(cmd_str_lst) >= 7:
                    amount = cmd_str_lst[1]
                    category_name = cmd_str_lst[2]
                    payment_method_name = cmd_str_lst[3]
                    date_txt = cmd_str_lst[4]
                    description = cmd_str_lst[5]
                    tag_name = cmd_str_lst[-1]
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
                if len(cmd_str_lst) != 3:
                    print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['export_csv']}")
                else:
                    file_path = cmd_str_lst[1]
                    sort_field = cmd_str_lst[2].lower()
                    self.export_csv(file_path, sort_field)
                    
            # Handling list_users (Admin only)
            elif cmd == "list_users":
                if len(cmd_str_lst) != 1:
                    print("Error: No arguments required")
                else:
                    self.list_users()

            else:
                print("Error: Invalid command")

        
        def help(self):
            if self.current_user is None:
                print("Available commands:")
                print("- login <username> <password>")
                print("- help")
            else:
                print("Available commands:")
                for command, syntax in list_of_privileges[self.privileges].items():
                    print(f"- {syntax}")
                print("- logout")
                print("- help")

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



