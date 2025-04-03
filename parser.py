import shlex
from constants import list_of_privileges

class CommandParser:
    def __init__(self, user_manager, category_manager, payment_manager, expense_manager, csv_operations, report_manager):
        self.user_manager = user_manager
        self.category_manager = category_manager
        self.payment_manager = payment_manager
        self.expense_manager = expense_manager
        self.csv_operations = csv_operations
        self.report_manager = report_manager
    
    def parse(self, cmd_str):
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
                self.user_manager.help(self.user_manager.privileges or "user", list_of_privileges)
            return
        
        # Handling login
        elif cmd == "login":
            if len(cmd_str_lst) != 3:
                print("Error: Insufficient number of arguments")
                return
            if self.user_manager.current_user is None:
                username = cmd_str_lst[1]
                password = cmd_str_lst[2]
                if self.user_manager.authenticate(username, password):
                    # Update user info in other managers
                    self.expense_manager.set_current_user(username)
                    self.csv_operations.set_current_user(username)
                    self.report_manager.set_user_info(username, self.user_manager.privileges)
            else:
                print("Error: Another session is live!")
            return

        # Handling logout
        elif cmd == "logout":
            if len(cmd_str_lst) != 1:
                print("Error: Insufficient number of arguments")
                return
            if self.user_manager.current_user is not None:
                self.user_manager.logout()
                # Clear user info in other managers
                self.expense_manager.set_current_user(None)
                self.csv_operations.set_current_user(None)
                self.report_manager.set_user_info(None, None)
            else:
                print("Error: User not logged in!")
            return

        # Ensure user is logged in for further commands
        if self.user_manager.current_user is None:
            print("Error: Please login!")
            return

        # Ensure the command exists in privileges
        if cmd not in list_of_privileges['admin'] and cmd not in list_of_privileges["user"]:
            print("Error: Invalid command")
            return

        # Ensure the user has permission
        if cmd not in list_of_privileges[self.user_manager.privileges]:
            print("Error: Unauthorized command")
            return

        # Handling add_user (Admin only)
        if cmd == "add_user":
            if len(cmd_str_lst) == 4:
                username = cmd_str_lst[1]
                password = cmd_str_lst[2]
                role = cmd_str_lst[3]
                self.user_manager.register(username, password, role)
            else:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['admin']['add_user']}")

        # Handling list_categories
        elif cmd == "list_categories":
            if len(cmd_str_lst) != 1:
                print("Error: No arguments required")
            else:
                self.category_manager.list_categories()

        # Handling add_category (Admin only)
        elif cmd == "add_category":
            if len(cmd_str_lst) != 2:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['admin']['add_category']}")
            else:
                category_name = cmd_str_lst[1]
                self.category_manager.add_category(category_name)

        # Handling list_payment_methods
        elif cmd == "list_payment_methods":
            if len(cmd_str_lst) != 1:
                print("Error: No arguments required")
            else:
                self.payment_manager.list_payment_methods()

        # Handling add_payment_method (Admin only)
        elif cmd == "add_payment_method":
            if len(cmd_str_lst) != 2:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['admin']['add_payment_method']}")
            else:
                payment_method_name = cmd_str_lst[1]
                self.payment_manager.add_payment_method(payment_method_name)

        # Handling addexpense
        elif cmd == "add_expense":
            if len(cmd_str_lst) == 6 or len(cmd_str_lst) == 7:  #  description is optional. Therefore 6 arguments are also fine
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
                self.expense_manager.addexpense(amount, category_name, payment_method_name, date_txt, description, tag_name, payment_detail_identifier)    
                
            else:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['add_expense']}")
                return

        # Handling update_expense
        elif cmd == "update_expense":
            if len(cmd_str_lst) == 4:
                expense_id = cmd_str_lst[1]
                field = cmd_str_lst[2]
                new_value = cmd_str_lst[3]
                self.expense_manager.update_expense(expense_id, field, new_value)
            else:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['update_expense']}")

        # Handling delete_expense
        elif cmd == "delete_expense":
            if len(cmd_str_lst) == 2:
                expense_id = cmd_str_lst[1]
                self.expense_manager.delete_expense(expense_id)
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
            
            field_op = ["<=",">=","=","<",">"]
            if len(cmd_str_lst) > 1:
                # Extract the part after the command
                filter_part = cmd_str[len(cmd):].strip()
                # Split by comma to get individual constraints
                constraint_list = filter_part.split(',')
                
                for constraint in constraint_list:
                    constraint = constraint.strip()
                    operator_found = False
                    
                    # Try each operator to see if it exists in the constraint
                    for op in field_op:
                        if op in constraint:
                            # Split by operator
                            parts = constraint.split(op, 1)  # Split only on first occurrence
                            if len(parts) == 2:
                                field = parts[0].strip()
                                value = parts[1].strip()
                                
                                # Validate field
                                if field not in field_dict:
                                    print(f"Error: Invalid field '{field}'")
                                    return
                                
                                # Add to field_dict
                                field_dict[field].append([op, value])
                                operator_found = True
                                break
                    
                    if not operator_found:
                        print(f"Error: No valid operator found in filter '{constraint}'")
                        return
                
                self.expense_manager.list_expenses(field_dict, self.user_manager.privileges)
            else:
                self.expense_manager.list_expenses(user_role=self.user_manager.privileges)
                    
        elif cmd == "import_expenses":
            if len(cmd_str_lst) != 2:
                print(f"Error: Incorrect syntax. Usage: {list_of_privileges['user']['import_expenses']}")
            else:
                file_path = cmd_str_lst[1]
                self.csv_operations.import_expenses(file_path)

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
                self.csv_operations.export_csv(file_path, sort_field)
            else:
                # No sorting specified
                self.csv_operations.export_csv(file_path)
                
        # Handling list_users (Admin only)
        elif cmd == "list_users":
            if len(cmd_str_lst) != 1:
                print("Error: No arguments required")
            else:
                self.user_manager.list_users()

        # Handling report commands
        elif cmd == "report":
            if len(cmd_str_lst) < 2:
                print("Error: Report type not specified")
                print("Available report types for your role:")
                for report_type, syntax in list_of_privileges[self.user_manager.privileges]["report"].items():
                    print(f"- {syntax}")
                return
                
            report_type = cmd_str_lst[1]
            
            # Check if the report type is valid for the user's role
            if report_type not in list_of_privileges[self.user_manager.privileges]["report"]:
                print(f"Error: Invalid or unauthorized report type '{report_type}'")
                return
            
            # Handle different report types
            if report_type == "top_expenses":
                if len(cmd_str_lst) != 5:
                    print(f"Error: Incorrect syntax. Usage: {list_of_privileges[self.user_manager.privileges]['report']['top_expenses']}")
                else:
                    n = cmd_str_lst[2]
                    start_date = cmd_str_lst[3]
                    end_date = cmd_str_lst[4]
                    self.report_manager.generate_report_top_expenses(n, start_date, end_date)
                    
            elif report_type == "category_spending":
                if len(cmd_str_lst) != 3:
                    print(f"Error: Incorrect syntax. Usage: {list_of_privileges[self.user_manager.privileges]['report']['category_spending']}")
                else:
                    category = cmd_str_lst[2]
                    self.report_manager.generate_report_category_spending(category)
                    
            elif report_type == "above_average_expenses":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.report_manager.generate_report_above_average_expenses()
                    
            elif report_type == "monthly_category_spending":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.report_manager.generate_report_monthly_category_spending()
                    
            elif report_type == "highest_spender_per_month":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.report_manager.generate_report_highest_spender_per_month()
                    
            elif report_type == "frequent_category":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.report_manager.generate_report_frequent_category()
                    
            elif report_type == "payment_method_usage":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.report_manager.generate_report_payment_method_usage()
                    
            elif report_type == "tag_expenses":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.report_manager.generate_report_tag_expenses()
                    
            elif report_type == "payment_method_details_expense":
                if len(cmd_str_lst) != 2:
                    print("Error: No additional arguments required")
                else:
                    self.report_manager.generate_report_payment_method_details_expense()

        else:
            print("Error: Invalid command")
