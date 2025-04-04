import sqlite3

class UserManager:
    def __init__(self, cursor, conn):
        self.conn = conn
        self.cursor = cursor
        self.current_user = None
        self.privileges = None
    
    def authenticate(self, username, password):
        # Step 1: Check if the username exists
        self.cursor.execute("SELECT password FROM User WHERE username = ?", (username,))
        user = self.cursor.fetchone()

        if user is None:
            print("Error: Username does not exist.")  # Username not found
            return False

        stored_password = user[0]  # Get stored password

        # Step 2: Check if password matches
        if stored_password == password:
            print("Login successful!")
        else:
            print("Error: Incorrect password.")  # Password mismatch
            return False
        
        self.current_user = username
        self.cursor.execute("SELECT r.role_name FROM user_role u,Role r WHERE u.username = ? and u.role_id = r.role_id", (username,))
        role = self.cursor.fetchone()[0]
        self.privileges = role
        return True
        
    def logout(self):
        self.current_user = None
        self.privileges = None
        print("Logging Out.....")
        return True
            
    def register(self, username, password, role):
        self.cursor.execute("SELECT role_id FROM Role WHERE role_name = ?", (role,))
        result = self.cursor.fetchone()
        if result is None:
            print(f"Error: Role '{role}' does not exist. Registration failed!")
            return False
        
        role_id = result[0]  # Extract role_id

        try:
            self.cursor.execute("INSERT INTO User (username, password) VALUES (?, ?)", (username, password))
            self.cursor.execute("INSERT INTO user_role (username, role_id) VALUES (?, ?)", (username, role_id))
            print("User added successfully!")
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:  # Catches duplicate username errors
            print("Error: Username already exists!")
            return False
        
    def list_users(self):
        self.cursor.execute("SELECT username, role_name FROM user_role u, role r WHERE u.role_id = r.role_id")
        users = self.cursor.fetchall()
        
        if not users:
            print("No users found!!")
        else:
            print("\nUser List:")
            print("-" * 35)
            print(f"{'Username':<20} {'Role':<15}")
            print("-" * 35)
            for user in users:
                username, role = user
                print(f"{username:<20} {role:<15}")
            print("-" * 35)
        return True
        
    def help(self, current_privileges, list_of_privileges):
        if self.current_user is None:
            print("Available commands:")
            print("- login <username> <password>")
            print("- help")
        else:
            print("Available commands:")
            # Display regular commands
            for command, syntax in list_of_privileges[current_privileges].items():
                if command != "report":  # Handle report separately
                    print(f"- {syntax}")
            
            # Display report commands if available
            if "report" in list_of_privileges[current_privileges]:
                print("\nReport commands:")
                for _, syntax in list_of_privileges[current_privileges]["report"].items():
                    print(f"- {syntax}")
                    
            print("\nOther commands:")
            print("- logout")
            print("- help")
        return True
