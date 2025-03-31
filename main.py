import sqlite3
import shlex

list_of_privileges = {"admin":["add_user","list_payment_methods","add_payment_method","list_categories","add_category"],
                      "user":["list_categories","list_payment_methods","add_expense"]}


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
        self.privileges =  list_of_privileges[role]      
        
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


    def addexpense(self,amount,category,payment_method,date,description,tag,payment_method_details = ""):
        self.cursor.execute(
        "INSERT INTO Expense (date, amount, description) VALUES (?, ?, ?)", 
        (date, amount, description))

        expense_id = self.cursor.lastrowid
        self.cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (category,))
        result = self.cursor.fetchone()
        if result is None:
            print(f"Error: Category '{category}' does not exist. Adding failed!")
            self.conn.rollback()
            return  # Stop execution if role is not found
        
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
            return  # Stop execution if role is not found
        
        payment_method_id = result[0]  # Extract payment_method_id
        self.cursor.execute(
        "INSERT INTO payment_method_expense(payment_method_id,expense_id,payment_detail_identifier) VALUES (?, ?,?)", 
        (payment_method_id,expense_id,payment_method_details))
        
        self.cursor.execute(
        "INSERT INTO user_expense(username,expense_id) VALUES (?, ?)", 
        (self.current_user,expense_id))
        
        self.conn.commit()
        print("Expense Added Successfully")
        
        
    
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

        # Handling addexpense (To be implemented)
        elif cmd == "add_expense":
            if len(cmd_str_lst) >= 7:
                amount = cmd_str_lst[1]
                category_name = cmd_str_lst[2]
                payment_method_name = cmd_str_lst[3]
                date_txt = cmd_str_lst[4]
                description = cmd_str_lst[5]
                tag_name = cmd_str_lst[-1]
                payment_method_details = ""
                choice = input("Would you like to add payment method details?(y/n) [Type more to display more info]: ")
                if choice.lower() == "more":
                    print("This detail can be used by the used by the user to generate reports based on specific payment method")
                    print("The details will be masked")
                    choice = input("Would you like to add payment method details?(y/n): ")
                if choice.lower() == "y":
                    payment_method_details = input("Enter the details: ")
                self.addexpense(amount, category_name, payment_method_name, date_txt, description, tag_name, payment_method_details)    
                
            else:
                print("Error: Insufficient no of arguments!!")
                return
                
                
        else:
            print("Error: Invalid command")

    
    def help(self):
        pass
    
        
        

def main():
    conn = sqlite3.connect("prject/ExpenseReport") # Creates/opens a database file
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



