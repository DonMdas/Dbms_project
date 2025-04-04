import sqlite3
import sys
from user import UserManager
from category import CategoryManager
from payment import PaymentManager
from expense import ExpenseManager
from csv_operations import CSVOperations
from reporting import ReportManager
from parser import CommandParser

def main():
    # Connect to the database
    conn = sqlite3.connect("ExpenseReport")  # Creates/opens a database file
    cursor = conn.cursor()  # Creates a cursor object to execute SQL commands
    
    # Initialize managers
    user_manager = UserManager(cursor, conn)
    category_manager = CategoryManager(cursor, conn)
    payment_manager = PaymentManager(cursor, conn)
    expense_manager = ExpenseManager(cursor, conn)
    
    # Initialize managers that depend on other managers
    csv_operations = CSVOperations(cursor, conn, expense_manager)
    report_manager = ReportManager(cursor, conn)
    
    # Create command parser
    command_parser = CommandParser(
        user_manager, 
        category_manager, 
        payment_manager, 
        expense_manager, 
        csv_operations, 
        report_manager
    )
    
    print("Expense Reporting App")
    
    # Main loop
    while True:
        try:
            cmd_string = input()
            if cmd_string.strip().lower() == "exit":
                print("Exiting ........")
                break
            command_parser.parse(cmd_string)
        except KeyboardInterrupt:
            print("\nExiting due to keyboard interrupt...")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    main()



