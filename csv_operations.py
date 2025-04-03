import csv
import sqlite3

class CSVOperations:
    def __init__(self, cursor, conn, expense_manager=None):
        self.conn = conn
        self.cursor = cursor
        self.expense_manager = expense_manager
        self.current_user = None
    
    def set_current_user(self, username):
        self.current_user = username
        if self.expense_manager:
            self.expense_manager.set_current_user(username)
    
    def import_expenses(self, file_path):
        try:
            with open(file_path, newline="") as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                expected_header = ["amount", "category", "payment_method", "date", "description", "tag", "payment_detail_identifier"]
                if [col.strip().lower() for col in header] != expected_header:
                    print("Error: CSV header does not match expected format.")
                    return False
                    
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
                    result = self.expense_manager.addexpense(amount, category.strip().lower(), payment_method.strip().lower(),
                                            date, description, tag.strip().lower(), payment_detail_identifier, import_fn=1)
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                        print(f"Failed to import row {i}")
                        
                print(f"Import complete: {success_count} successful, {error_count} failed.")
                return True
                
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            return False
        except Exception as e:
            print(f"Error while importing CSV: {e}")
            return False

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
                return False
            query += f" ORDER BY {sort_fields[sort_field]}"

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        if not rows:
            print("No expenses found to export.")
            return False

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
            return True
        except Exception as e:
            print(f"Error while exporting CSV: {e}")
            return False
