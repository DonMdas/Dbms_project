import sqlite3

class CategoryManager:
    def __init__(self, cursor, conn):
        self.conn = conn
        self.cursor = cursor
    
    def add_category(self, category_name):
        category_name = category_name.strip().lower()
        
        try:
            self.cursor.execute("INSERT INTO categories (category_name) VALUES (?)", (category_name,))
            self.conn.commit()
            print(f"Category '{category_name}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            print(f"Error: Category '{category_name}' already exists.")
            return False
    
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
        return True
