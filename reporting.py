import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import os

class ReportManager:
    def __init__(self, cursor, conn):
        self.conn = conn
        self.cursor = cursor
        self.current_user = None
        self.privileges = None
    
    def set_user_info(self, username, privileges):
        self.current_user = username
        self.privileges = privileges
    
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
                plt.show(block=False)  # Non-blocking display
                plt.pause(0.001)  # Small pause to render the plot
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    def generate_report_payment_method_details_expense(self):
        """Report on expenses with payment method details - analyzing frequency, total, and average amounts"""
        try:
            # Base query to aggregate payment details data
            query = """
            SELECT pme.payment_detail_identifier, 
                   COUNT(e.expense_id) as usage_count, 
                   SUM(e.amount) as total_amount,
                   AVG(e.amount) as avg_amount,
                   pm.payment_method_name
            FROM Expense e
            JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
            JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
            JOIN user_expense ue ON e.expense_id = ue.expense_id
            WHERE pme.payment_detail_identifier IS NOT NULL 
            AND pme.payment_detail_identifier != ''
            AND ue.username = ?
            GROUP BY pme.payment_detail_identifier ORDER BY usage_count DESC"""
            
            
            params = [self.current_user]
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            if not results:
                print("No expenses with payment method details found.")
                return
                
            # Display results
            print("\nPayment Method Details Usage Report:")
            print("-" * 80)
            print(f"{'Payment Detail':<20} {'Usage Count':<12} {'Total Amount':<15} {'Avg Amount':<15} {'Payment Method':<20}")
            print("-" * 80)
            
            total_transactions = 0
            total_amount = 0
            
            for row in results:
                detail, count, total, avg, method = row
                total_transactions += count
                total_amount += total
                
                # Mask sensitive payment details for privacy
                if method[-4:] == "card":
                    masked_detail = self._mask_payment_details(detail)
                else:
                    masked_detail = detail
                
                print(f"{masked_detail:<20} {count:<12} {total:<15.2f} {avg:<15.2f} {method:<20}")
            
            print("-" * 80)
            print(f"Overall Total: {total_transactions} transactions, ${total_amount:.2f}")
            print(f"Overall Average: ${total_amount/total_transactions:.2f} per transaction")
            
            # Create visualizations if we have data
            if results:
                import matplotlib.pyplot as plt
                import numpy as np
                from matplotlib.ticker import FuncFormatter
                
                # Prepare data for plotting
                details = [self._mask_payment_details(r[0]) if r[4][-4:] == "card" else r[0] for r in results]
                counts = [r[1] for r in results]
                totals = [r[2] for r in results]
                avgs = [r[3] for r in results]
                methods = [r[4] for r in results]
                
                # If too many details, limit to top 10 for readability
                if len(details) > 10:
                    details = details[:10]
                    counts = counts[:10]
                    totals = totals[:10]
                    avgs = avgs[:10]
                    methods = methods[:10]
                
                # Create figure with 3 subplots (removed 4th plot)
                fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 6))
                
                # 1. Bar chart showing frequency of usage
                bars1 = ax1.bar(details, counts, color='skyblue')
                ax1.set_title('Frequency of Usage')
                ax1.set_xlabel('Payment Detail (masked)')
                ax1.set_ylabel('Number of Transactions')
                ax1.tick_params(axis='x', rotation=45)
                
                # Add count labels with slanted text
                for bar in bars1:
                    height = bar.get_height()
                    ax1.annotate(f'{height}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom',
                                rotation=45)
                
                # 2. Bar chart showing total amount spent
                bars2 = ax2.bar(details, totals, color='lightgreen')
                ax2.set_title('Total Amount Spent')
                ax2.set_xlabel('Payment Detail (masked)')
                ax2.set_ylabel('Total Amount ($)')
                ax2.tick_params(axis='x', rotation=45)
                
                # Format y-axis as currency
                ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:.0f}'))
                
                # Add amount labels with slanted text
                for bar in bars2:
                    height = bar.get_height()
                    ax2.annotate(f'${height:.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom',
                                rotation=45)
                
                # 3. Bar chart showing average transaction amount
                bars3 = ax3.bar(details, avgs, color='salmon')
                ax3.set_title('Average Transaction Amount')
                ax3.set_xlabel('Payment Detail (masked)')
                ax3.set_ylabel('Average Amount ($)')
                ax3.tick_params(axis='x', rotation=45)
                
                # Format y-axis as currency
                ax3.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:.0f}'))
                
                # Add amount labels with slanted text
                for bar in bars3:
                    height = bar.get_height()
                    ax3.annotate(f'${height:.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom',
                                rotation=45)
                
                plt.tight_layout()
                plt.suptitle('Payment Method Details Analysis', fontsize=16, y=1.05)
                
                plt.show(block=False)
                plt.pause(0.001)
                
        except Exception as e:
            print(f"Error generating report: {e}")

    def _mask_payment_details(self, details):
        """Mask payment method details for privacy"""
        if not details:
            return ""
        
        # Keep first and last characters, mask the rest
        if len(details) <= 4:
            return '*' * len(details)
        else:
            return details[0:2] + '*' * (len(details) - 4) + details[-2:]
