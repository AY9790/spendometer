import datetime
import sqlite3
from tkcalendar import DateEntry
from tkinter import *
import tkinter.messagebox as mb
from tkinter import simpledialog, messagebox
import tkinter.ttk as ttk
import tkinter as tk
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
from datetime import datetime,date
from tkinter import Toplevel, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import scrolledtext
import random
import re

def refresh_expenses():
    global selected_month, selected_year

    # Reset selected month & year to remove filters
    selected_month = None
    selected_year = None

    # Show all expenses
    list_all_expenses()

    # Reset total expenses display
    total_expenses_label.config(text="Total Expenses: $0.00")

    # Show confirmation message
    mb.showinfo("Refreshed", "Expense list has been refreshed to show all records.")

    
# Global variables for month and year selection
selected_month = None
selected_year = None

# Functions
def list_all_expenses():
    global connector, table

    # Clear the table before adding new data
    table.delete(*table.get_children())

    # Fetch all data from the database
    all_data = connector.execute('SELECT * FROM SPENDOMETER')
    data = all_data.fetchall()

    expenses = []  # List to store the fetched expenses

    # Insert data into the table with a manually assigned serial number
    for index, values in enumerate(data, start=1):  # Serial number starts from 1
        expense = {
            'DB_ID': values[0],# Real database ID
            'Date': values[1],
            'Payee': values[2],
            'Description': values[3],
            'Amount': values[4],
            'Mode of Payment': values[5]
        }
        expenses.append(expense)

        # Insert the manually assigned serial number AND store real DB_ID in the 'iid' field
        table.insert('', 'end', iid=values[0], values=(index, values[0], *values[1:]))

    return expenses  # Return the list of expenses


def calculate_total_expenses():
    global selected_month, selected_year, connector  # Global variables
    
    # Ensure that both month and year are selected
    if not selected_month or not selected_year:
        mb.showerror("No Selection", "Please select both a month and a year first!")
        return

    # Convert the selected month to its numeric representation
    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }
    selected_month_num = month_map.get(selected_month, "01")  # Default to "01" if month is invalid

    # Query the database to get the total expenses for the selected month and year
    query = """
        SELECT SUM(Amount)
        FROM SPENDOMETER
        WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
    """
    
    cursor = connector.execute(query, (selected_month_num, selected_year))
    total = cursor.fetchone()[0]

    # If no expenses are found, set the total to 0.00
    if total is None:
        total = 0.0

    # Update the Total Expenses button with the total for the selected month and year
    total_expenses_label.config(text=f"Total Expenses: ${total:.2f}")


def compare_expenses():
    # Define the month name to number mapping
    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    }

    # Ask the user for two months and years to compare
    month1 = simpledialog.askstring("Input", "Enter first month (jan, feb, etc.):", parent=root)
    if month1 is None:
        return
    month1 = month1.lower()

    year1 = simpledialog.askstring("Input", "Enter first year (YYYY):", parent=root)
    if year1 is None:
        return

    month2 = simpledialog.askstring("Input", "Enter second month (jan, feb, etc.):", parent=root)
    if month2 is None:
        return
    month2 = month2.lower()

    year2 = simpledialog.askstring("Input", "Enter second year (YYYY):", parent=root)
    if year2 is None:
        return

    # Validate input
    if not all([month1, year1, month2, year2]):
        messagebox.showerror("Error", "All fields are required!")
        return

    # Convert month names to numeric format (e.g., "jan" -> "01")
    month1_num = month_map.get(month1, None)
    month2_num = month_map.get(month2, None)

    if not month1_num or not month2_num:
        messagebox.showerror("Error", "Invalid month(s) entered. Use lowercase month names like jan, feb, etc.")
        return

    try:
        # Connect to the database
        conn = sqlite3.connect("SPENDOMETER.db")
        cursor = conn.cursor()

        # Fetch total expenses for both months using strftime('%m', Date) and strftime('%Y', Date)
        query_total = """
        SELECT SUM(Amount) FROM SPENDOMETER WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
        """
        
        cursor.execute(query_total, (month1_num, year1))
        total1 = cursor.fetchone()[0] or 0  # If no data, set total to 0

        cursor.execute(query_total, (month2_num, year2))
        total2 = cursor.fetchone()[0] or 0

        # Fetch highest and lowest expenses for each month
        query_highest = """
        SELECT Description, Amount FROM SPENDOMETER
        WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
        ORDER BY Amount DESC LIMIT 1
        """
        query_lowest = """
        SELECT Description, Amount FROM SPENDOMETER
        WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
        ORDER BY Amount ASC LIMIT 1
        """

        cursor.execute(query_highest, (month1_num, year1))
        highest1 = cursor.fetchone()

        cursor.execute(query_lowest, (month1_num, year1))
        lowest1 = cursor.fetchone()

        cursor.execute(query_highest, (month2_num, year2))
        highest2 = cursor.fetchone()

        cursor.execute(query_lowest, (month2_num, year2))
        lowest2 = cursor.fetchone()

        conn.close()

        # Create a new window for displaying the comparison
        comparison_window = Toplevel(root)
        comparison_window.title(f"Expense Comparison: {month1}/{year1} vs {month2}/{year2}")
        comparison_window.geometry("600x700")

        # Create a frame for the table
        table_frame = ttk.Frame(comparison_window)
        table_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Create a table for displaying results
        table = ttk.Treeview(table_frame, columns=("Metric", month1, month2), show="headings")
        table.heading("Metric", text="Expense Type")
        table.heading(month1, text=f"{month1}/{year1}")
        table.heading(month2, text=f"{month2}/{year2}")

        # Style the table for better appearance
        table.tag_configure("odd", background="#f2f2f2")  # Odd row color
        table.tag_configure("even", background="#ffffff")  # Even row color

        # Add data to the table (using lowercase months)
        table.insert("", "end", values=("Total Expense", f"₹{total1:.2f}", f"₹{total2:.2f}"), tags=("odd" if len(table.get_children()) % 2 == 0 else "even"))
        table.insert("", "end", values=("Highest Expense", f"{highest1[0]} (₹{highest1[1]:.2f})" if highest1 else "No Data", f"{highest2[0]} (₹{highest2[1]:.2f})" if highest2 else "No Data"), tags=("odd" if len(table.get_children()) % 2 == 0 else "even"))
        table.insert("", "end", values=("Lowest Expense", f"{lowest1[0]} (₹{lowest1[1]:.2f})" if lowest1 else "No Data", f"{lowest2[0]} (₹{lowest2[1]:.2f})" if lowest2 else "No Data"), tags=("odd" if len(table.get_children()) % 2 == 0 else "even"))

        # Show the table in the window
        table.pack(expand=True, fill="both")

        # Create a frame for the pie chart
        pie_chart_frame = ttk.Frame(comparison_window)
        pie_chart_frame.pack(pady=20)

        # Generate Pie Chart for visualization and embed it in the Tkinter window
        fig, ax = plt.subplots(figsize=(6, 6))
        labels = [f"{month1}/{year1}", f"{month2}/{year2}"]
        sizes = [total1, total2]
        colors = ["DeepPink", "Plum"]

        if sizes[0] > 0 or sizes[1] > 0:
            ax.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
            ax.set_title("Expense Comparison")

            # Embed the pie chart in the Tkinter window using FigureCanvasTkAgg
            canvas = FigureCanvasTkAgg(fig, master=pie_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack()
        else:
            messagebox.showinfo("No Data", "No expenses to compare for the selected months.")

        # Add a button to close the comparison window
        Button(comparison_window, text="Close", command=comparison_window.destroy).pack(pady=20)

    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred while fetching data: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")


# chat
# Global variable to store user's budget
user_budget = {}

# Month mapping
month_map = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12"
}

# List of money-saving tips
saving_tips = [
    "💰 Track your daily expenses to identify unnecessary spending.",
    "📊 Set a monthly budget and stick to it.",
    "🚫 Cancel unused subscriptions to save money.",
    "🛍️ Avoid impulse purchases by making a shopping list.",
    "🏠 Cook at home instead of ordering takeout.",
    "💡 Use energy-efficient appliances to lower electricity bills.",
    "🚗 Use public transport instead of taxis to cut costs.",
    "🎁 Buy items during seasonal sales and discounts.",
    "💳 Pay bills on time to avoid late fees.",
    "🔄 Reuse and recycle items instead of buying new ones."
]

# Chatbot Response Function
def chatbot_response(user_input):
    user_input = user_input.lower()
    greetings = ["hi", "hello", "hey", "good morning", "good evening"]
    motivational_quotes = [
        "💡 'A budget is telling your money where to go instead of wondering where it went.' – Dave Ramsey",
        "💰 'Save money and money will save you.'",
        "📊 'Do not save what is left after spending, but spend what is left after saving.' – Warren Buffett",
        "🚀 'Financial freedom is not a dream, it’s a priority.'"
    ]

    # Check for greetings & motivational messages
    if any(greet in user_input for greet in greetings):
        return f"🤖 Hello! How can I assist you today? 😊\n💡 {random.choice(motivational_quotes)}"

    # Provide 5 random saving tips
    elif "tips to save money" in user_input or "saving tips" in user_input:
        random.shuffle(saving_tips)  # Shuffle tips for variation
        selected_tips = "\n".join(saving_tips[:5])  # Pick 5 tips
        return f"💡 Here are 5 money-saving tips:\n{selected_tips}"

    # Set budget for a specific month & year
    elif "set my budget for" in user_input and "to" in user_input:
        return set_user_budget(user_input)

    # Check current month's spending vs budget
    elif "how much have i spent" in user_input or "remaining budget" in user_input:
        return check_budget_status(user_input)

    # Reduce expenses for a specific month & year
    elif "reduce" in user_input and "expenses" in user_input:
        return fetch_highest_expense_and_tips(user_input)

    return "🤖 I'm here to help! You can ask me about your expenses, budget, or money-saving tips."

# ✅ Function to Set User's Budget
def set_user_budget(user_input):
    words = user_input.split()
    month, year, budget_amount = None, None, None

    # Extract month and year from user input
    for i in range(len(words)):
        if words[i][:3] in month_map:
            month = words[i][:3].capitalize()
            year = words[i + 1] if i + 1 < len(words) and words[i + 1].isdigit() else str(datetime.now().year)
            break

    # Extract the budget amount (last number in the input)
    budget_match = re.findall(r"\d+", user_input)
    if budget_match:
        budget_amount = float(budget_match[-1])

    if month and year and budget_amount is not None:
        user_budget[f"{month} {year}"] = budget_amount
        return f"✅ Your budget for {month} {year} is set to ₹{budget_amount}. I'll notify you if you exceed it! 📢"
    else:
        return "⚠️ Please provide a valid budget format. Example: 'Set my budget for March 2025 to ₹10000'."

# ✅ Function to Check Budget Status (Fix Applied)
def check_budget_status(user_input):
    words = user_input.split()
    month, year = None, None

    # ✅ Extract month & year properly
    for i in range(len(words)):
        if words[i][:3].lower() in month_map:
            month = words[i][:3].capitalize()
            year = words[i + 1] if i + 1 < len(words) and words[i + 1].isdigit() else str(datetime.now().year)
            break

    if not month or not year:
        return "⚠️ Please specify the month and year. Example: 'How much have I spent in March 2025?' or 'Remaining budget for March 2025?'."

    return fetch_budget_and_spending(month, year)

# ✅ Function to Fetch Expenses & Budget from Database
def fetch_budget_and_spending(month, year):
    selected_month_num = month_map.get(month.lower())

    conn = sqlite3.connect("SPENDOMETER.db")
    cursor = conn.cursor()

    # ✅ Fetch total expenses for the selected month
    query = "SELECT SUM(Amount) FROM SPENDOMETER WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?"
    cursor.execute(query, (selected_month_num, year))
    total_expense = cursor.fetchone()[0] or 0.0  # If no data, return 0

    conn.close()

    # ✅ Check if budget exists for the given month & year
    budget_key = f"{month} {year}"
    if budget_key in user_budget:
        budget = user_budget[budget_key]
        remaining_budget = budget - total_expense
        if remaining_budget >= 0:
            return (f"📊 Your total expenses for {month} {year} are ₹{total_expense:.2f}.\n"
                    f"✅ You have ₹{remaining_budget:.2f} remaining in your budget of ₹{budget:.2f}. 🎯")
        else:
            return (f"⚠️ Your total expenses for {month} {year} are ₹{total_expense:.2f}.\n"
                    f"❌ You have exceeded your budget of ₹{budget:.2f} by ₹{-remaining_budget:.2f}! Try cutting unnecessary spending. 🚀")
    else:
        return f"⚠️ No budget is set for {month} {year}. You can set it using: 'Set my budget for {month} {year} to ₹10000'."


# ✅ Function to Fetch Highest Expense & Give Tips
def fetch_highest_expense_and_tips(user_input):
    words = user_input.split()
    month, year = None, None

    # Extract month and year
    for i in range(len(words)):
        if words[i][:3] in month_map:
            month = words[i][:3].capitalize()
            year = words[i + 1] if i + 1 < len(words) and words[i + 1].isdigit() else str(datetime.now().year)
            break

    if not month or not year:
        return "⚠️ Please specify the month and year. Example: 'How to reduce Jan 2025 expenses?'."

    return fetch_expense_and_suggestions(month, year)

# ✅ Function to Fetch Expenses & Highest Spending Category
def fetch_expense_and_suggestions(month, year):
    selected_month_num = month_map.get(month.lower())

    conn = sqlite3.connect("SPENDOMETER.db")
    cursor = conn.cursor()

    # Fetch total expenses for the selected month
    query_total = "SELECT SUM(Amount) FROM SPENDOMETER WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?"
    cursor.execute(query_total, (selected_month_num, year))
    total_expense = cursor.fetchone()[0] or 0.0

    # Fetch the highest expense category
    query_highest = """
        SELECT Description, MAX(Amount) 
        FROM SPENDOMETER 
        WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
    """
    cursor.execute(query_highest, (selected_month_num, year))
    highest_expense = cursor.fetchone()

    conn.close()

    if highest_expense and highest_expense[0]:
        highest_category = highest_expense[0]
        highest_amount = highest_expense[1]
    else:
        highest_category = "N/A"
        highest_amount = 0

    # Tips for reducing expenses by category
    category_tips = {
        "School Fee": "🎓 Look for scholarships or early payment discounts.",
        "Snack": "🍫 Buy snacks in bulk to save money.",
        "Theater": "🎭 Reduce movie outings or use discount codes.",
        "Entertainment": "🎮 Opt for free entertainment options like outdoor activities.",
        "Current Bill": "💡 Save electricity by using energy-efficient appliances.",
        "Shopping": "🛍️ Avoid impulse buying and use discount coupons.",
        "Dress": "👗 Buy clothes during sales or consider second-hand options."
    }

    expense_tip = category_tips.get(highest_category, "🔹 Try to limit unnecessary expenses.")

    return (f"📅 Your total expenses for {month} {year} are ₹{total_expense:.2f}.\n"
            f"💸 Your highest expense was **{highest_category}** (₹{highest_amount:.2f}).\n"
            f"💡 {expense_tip}")


# ✅ Chat Window UI
def open_chat_window():
    chat_window = Toplevel(root)
    chat_window.title("SpendSense Chatbot 🤖")
    chat_window.geometry("450x550")
    chat_window.configure(bg="#222831")

    Label(chat_window, text="SpendSense Chatbot 🤖", font=("Arial", 16, "bold"), fg="white", bg="#393E46").pack(fill=X)

    # Chat History Box
    chat_history = scrolledtext.ScrolledText(chat_window, wrap="word", state="disabled", width=50, height=20, bg="#EEEEEE")
    chat_history.pack(pady=10, padx=10)

    # User Input Box
    user_input = Entry(chat_window, width=40, font=("Arial", 12))
    user_input.pack(pady=5, padx=10, ipady=5, ipadx=5)

    # Function to Handle Sending Messages
    def send_message():
        message = user_input.get().strip()
        if message:
            chat_history.config(state="normal")
            
            # Display User Message (Blue)
            chat_history.insert("end", f"You: {message}\n", "user")
            
            # Display Bot Response (Green)
            chat_response = chatbot_response(message)
            chat_history.insert("end", f"Bot: {chat_response}\n\n", "bot")
            
            chat_history.config(state="disabled")
            chat_history.yview_moveto(1)  # Auto-scroll to latest message
            user_input.delete(0, "end")

    # Send Button
    send_button = Button(chat_window, text="Send", font=("Arial", 12, "bold"), bg="#00ADB5", fg="white", command=send_message)
    send_button.pack(pady=5)

    # Configure Message Formatting
    chat_history.tag_config("user", foreground="blue", font=("Arial", 12, "bold"))
    chat_history.tag_config("bot", foreground="green", font=("Arial", 12, "italic"))

    # Greet User When Chat Opens
    chat_history.config(state="normal")
    chat_history.insert("end", "Bot: Hello! I'm your SpendSense assistant. Ask me anything about expenses!\n\n", "bot")
    chat_history.config(state="disabled")

def generate_chart():
    global connector, selected_month, selected_year

    # Ensure month and year are selected
    if not selected_month or not selected_year:
        mb.showerror("No Selection", "Please select a month and year first!")
        return

    # Fetch data filtered by selected month and year
    query = """
        SELECT Payee, SUM(Amount) 
        FROM SPENDOMETER 
        WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
        GROUP BY Payee
    """
    cursor = connector.execute(query, (selected_month, selected_year))
    data = cursor.fetchall()

    if not data:
        mb.showerror("No Data", f"There is no data for {selected_month}/{selected_year}!")
        return

    # Prepare data for plotting
    payees = [row[0] for row in data]      # List of payees
    amounts = [row[1] for row in data]     # Corresponding total amounts

    # Plot Bar Chart
    plt.figure(figsize=(10, 6))
    plt.bar(payees, amounts, color='skyblue')
    plt.xlabel('Payees')
    plt.ylabel('Total Amount')
    plt.title(f'Expenses by Payee - {selected_month}/{selected_year}')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Show the chart
    plt.show()

def view_expense_details():
    global table, date, payee, desc, amnt, MoP

    # Ensure an expense is selected
    selected_item = table.focus()
    if not selected_item:
        mb.showerror('No expense selected', 'Please select an expense from the table to view its details.')
        return

    # Fetch data from the selected row
    values = table.item(selected_item)['values']

    # Ensure values are correctly extracted
    if not values or len(values) < 6:
        mb.showerror('Error', 'Unable to retrieve expense details.')
        return

    # Extracting data and setting fields
    expenditure_date = datetime.strptime(str(values[2]), '%Y-%m-%d').date()
    date.set_date(expenditure_date)
    payee.set(values[3])
    desc.set(values[4])
    amnt.set(values[5])
    MoP.set(values[6])



def clear_fields():
  global desc, payee, amnt, MoP, date, table

  today_date = datetime.now().date() 

  desc.set('') ; payee.set('') ; amnt.set(0.0) ; MoP.set('Cash'), date.set_date(today_date)
  table.selection_remove(*table.selection())

def remove_expense():
    global table, connector
    if not table.selection():
        mb.showerror('No expense selected!', 'Please select an expense to delete.')
        return

    selected_item = table.focus()
    expense_id = selected_item  # Get the real database ID

    if not expense_id:
        mb.showerror("Error", "Could not retrieve expense ID.")
        return

    try:
        # Check if the expense exists
        cursor = connector.execute("SELECT * FROM SPENDOMETER WHERE ID = ?", (expense_id,))
        existing_expense = cursor.fetchone()

        if not existing_expense:
            mb.showerror("Error", "Expense does not exist in the database!")
            return

        # Execute DELETE query
        connector.execute("DELETE FROM SPENDOMETER WHERE ID = ?", (expense_id,))
        connector.commit()

        # Refresh the table after deletion
        list_all_expenses()

        # Show success message
        mb.showinfo('Expense Deleted', 'The expense has been successfully deleted.')

    except sqlite3.Error as e:
        mb.showerror("Database Error", f"An error occurred: {e}")

def remove_all_expenses():
  surety = mb.askyesno('Are you sure?', 'Are you sure that you want to delete all the expense items from the database?', icon='warning')

  if surety:
     table.delete(*table.get_children())

     connector.execute('DELETE FROM SPENDOMETER')
     connector.commit()

     clear_fields()
     list_all_expenses()
     mb.showinfo('All Expenses deleted', 'All the expenses were successfully deleted')
  else:
     mb.showinfo('Ok then', 'The task was aborted and no expense was deleted!')

def add_another_expense():
  global date, payee, desc, amnt, MoP
  global connector

  if not date.get() or not payee.get() or not desc.get() or not amnt.get() or not MoP.get():
     mb.showerror('Fields empty!', "Please fill all the missing fields before pressing the add button!")
  else:
     connector.execute(
         'INSERT INTO SPENDOMETER (Date, Payee, Description, Amount, ModeOfPayment) VALUES (?, ?, ?, ?, ?)',
         (date.get_date().strftime("%Y-%m-%d"), payee.get(), desc.get(), amnt.get(), MoP.get())
)

     connector.commit()

     clear_fields()
     list_all_expenses()
     mb.showinfo('Expense added', 'The expense whose details you just entered has been added to the database')
     
def filter_by_month_year():
    global selected_month, selected_year

    def apply_filter():
        global selected_month, selected_year
        selected_month = month_combobox.get()
        selected_year = year_combobox.get()
     
        if not selected_month or not selected_year:
            mb.showerror("Selection Error", "Please select both month and year.")
            return

        # Convert selected month to numeric format (e.g., "Jan" -> "01")
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }
        selected_month_num = month_map.get(selected_month, None)

        if not selected_month_num:
            mb.showerror("Selection Error", "Invalid month selected.")
            return

        # Clear current table contents
        for row in table.get_children():
            table.delete(row)

        # Fetch and filter data from the database
        filtered = False
        query = """
            SELECT * FROM SPENDOMETER 
            WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
        """
        cursor = connector.execute(query, (selected_month_num, selected_year))
        data = cursor.fetchall()

        print(f"Selected Month (Num): {selected_month_num}")
        print(f"Selected Year: {selected_year}")
        print("Fetched Data:")
        for expense in data:
            print(expense)


        for index, expense in enumerate(data, start=1):
            table.insert("", "end", values=(index, *expense))
            filtered = True

        # Show message if no records match the filter
        if not filtered:
            mb.showinfo("No Records", f"No expenses found for {selected_month} {selected_year}.")

        # Close the filter window
        filter_window.destroy()

        # Debug: Print selected month and year
        print(f"Filter applied: {selected_month_num}/{selected_year}")

    # Create a new window for filter options
    filter_window = Toplevel(root)
    filter_window.title("Filter by Month and Year")
    filter_window.geometry("300x200")

    # Month and Year selection
    Label(filter_window, text="Select Month:", font=lbl_font).pack(pady=5)
    month_combobox = ttk.Combobox(
        filter_window, values=["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        state="readonly"
    )
    month_combobox.pack(pady=5)

    Label(filter_window, text="Select Year:", font=lbl_font).pack(pady=5)
    year_combobox = ttk.Combobox(
        filter_window, values=[str(year) for year in range(2000, 2101)], state="readonly"
    )
    year_combobox.pack(pady=5)

    # Apply filter button
    Button(filter_window, text="Apply Filter", command=apply_filter).pack(pady=20)

def edit_expense():
    global table, add_btn, edit_btn

    def edit_existing_expense():
        global date, amnt, desc, payee, MoP, table, connector, edit_btn, add_btn

        if not table.selection():
            mb.showerror('No expense selected!', 'Please select an expense to edit.')
            return

        # Get the selected expense using `iid` (real database ID)
        selected_item = table.focus()
        expense_id = selected_item  # This is now the real database ID

        if not expense_id:
            mb.showerror("Error", "Could not retrieve expense ID.")
            return

        # Get updated values from input fields
        updated_date = date.get_date().strftime('%Y-%m-%d')
        updated_payee = payee.get()
        updated_desc = desc.get()
        updated_amnt = amnt.get()
        updated_MoP = MoP.get()

        try:
            # Check if the expense exists
            cursor = connector.execute("SELECT * FROM SPENDOMETER WHERE ID = ?", (expense_id,))
            existing_expense = cursor.fetchone()

            if not existing_expense:
                mb.showerror("Error", "Expense does not exist in the database!")
                return

            # Execute UPDATE query
            connector.execute(
                '''UPDATE SPENDOMETER 
                   SET Date = ?, Payee = ?, Description = ?, Amount = ?, ModeOfPayment = ? 
                   WHERE ID = ?''',
                (updated_date, updated_payee, updated_desc, updated_amnt, updated_MoP, expense_id)
            )
            connector.commit()

            # Refresh the table
            list_all_expenses()

            # Clear data entry fields
            clear_fields()

            # Show success message
            mb.showinfo('Expense Updated', 'The expense has been successfully updated.')

            # **🔥 Remove Edit button & Restore Add button (only if it exists)**
            edit_btn.destroy()
            if 'add_btn' in globals():
                add_btn.destroy()
            
            # Create new Add Expense button
            add_btn = Button(data_entry_frame, text='Add Expense', font=btn_font, width=30,
                             bg=hlb_btn_bg, command=add_another_expense)
            add_btn.place(x=10, y=395)

        except sqlite3.Error as e:
            mb.showerror("Database Error", f"An error occurred: {e}")

    if not table.selection():
        mb.showerror('No expense selected!', 'You have not selected any expense in the table for editing. Please select one.')
        return

    view_expense_details()  # Load selected expense details into input fields

    # **🔥 Remove Add button & Show Edit button (only if add_btn exists)**
    if 'add_btn' in globals():
        add_btn.destroy()
    
    edit_btn = Button(data_entry_frame, text='Save Changes', font=btn_font, width=30,
                      bg=hlb_btn_bg, command=edit_existing_expense)
    edit_btn.place(x=10, y=395)

def show_chart_options():
    def generate_selected_chart():
        chart_type = selected_chart.get()
        if chart_type == "Bar Chart":
            generate_bar_chart()
        elif chart_type == "Pie Chart":
            generate_pie_chart()
        elif chart_type == "Line Chart":
            generate_line_chart()
        elif chart_type == "Scatter Plot":
            generate_scatter_plot()
        elif chart_type == "Histogram":
            generate_histogram()
        else:
            mb.showerror("Invalid Choice", "Please select a valid chart type")

    # New window for chart selection
    chart_window = Toplevel(root)
    chart_window.title("Select Chart Type")
    chart_window.geometry("300x250")

    Label(chart_window, text="Select a Chart Type:", font=lbl_font).pack(pady=10)

    # Dropdown list for chart types
    selected_chart = StringVar(value="Bar Chart")
    chart_types = ["Bar Chart", "Pie Chart", "Line Chart", "Scatter Plot", "Histogram"]
    OptionMenu(chart_window, selected_chart, *chart_types).pack(pady=20)

    Button(chart_window, text="Generate Chart", font=btn_font, command=generate_selected_chart).pack(pady=10)

def generate_bar_chart():
    global selected_month, selected_year

    # Check if a filter is applied
    if selected_month and selected_year:
        # Convert month name to numeric format
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }
        selected_month_num = month_map[selected_month]

        # Fetch filtered data
        query = """
            SELECT Payee, SUM(Amount) 
            FROM SPENDOMETER 
            WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
            GROUP BY Payee
        """
        cursor = connector.execute(query, (selected_month_num, selected_year))
        data = cursor.fetchall()

        chart_title = f'Expenses by Payee - {selected_month} {selected_year}'
    else:
        # Fetch all data
        query = "SELECT Payee, SUM(Amount) FROM SPENDOMETER GROUP BY Payee"
        cursor = connector.execute(query)
        data = cursor.fetchall()

        chart_title = 'Expenses by Payee - All Time'

    if not data:
        mb.showerror("No Data", "There is no data to display charts!")
        return

    # Prepare data for plotting
    payees = [row[0] for row in data]
    amounts = [row[1] for row in data]

    # Plot Bar Chart
    plt.figure(figsize=(10, 6))
    plt.bar(payees, amounts, color='skyblue')
    plt.xlabel('Payees')
    plt.ylabel('Total Amount')
    plt.title(chart_title)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def generate_pie_chart():
    global selected_month, selected_year

    if not selected_month or not selected_year:
        mb.showerror("Filter Error", "Please apply a month and year filter first!")
        return

    # Convert selected month to numeric format
    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }
    selected_month_num = month_map[selected_month]

    # Fetch filtered data
    query = """
        SELECT Payee, SUM(Amount) 
        FROM SPENDOMETER 
        WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
        GROUP BY Payee
    """
    cursor = connector.execute(query, (selected_month_num, selected_year))
    data = cursor.fetchall()

    if not data:
        mb.showerror("No Data", f"No data available for {selected_month} {selected_year}.")
        return

    payees = [row[0] for row in data]
    amounts = [row[1] for row in data]

    plt.figure(figsize=(8, 8))
    plt.pie(amounts, labels=payees, autopct='%1.1f%%', startangle=140)
    plt.title(f'Expense Distribution by Payee - {selected_month} {selected_year}')
    plt.tight_layout()
    plt.show()

def generate_line_chart():
    global selected_month, selected_year

    if not selected_month or not selected_year:
        mb.showerror("Filter Error", "Please apply a month and year filter first!")
        return

    selected_month_num = datetime.strptime(selected_month, '%b').strftime('%m')

    query = """
        SELECT Date, SUM(Amount) 
        FROM SPENDOMETER 
        WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
        GROUP BY Date
    """
    cursor = connector.execute(query, (selected_month_num, selected_year))
    data = cursor.fetchall()

    if not data:
        mb.showerror("No Data", f"No data available for {selected_month} {selected_year}.")
        return

    dates = [row[0] for row in data]
    amounts = [row[1] for row in data]

    plt.figure(figsize=(10, 6))
    plt.plot(dates, amounts, marker='o', linestyle='-', color='green')
    plt.xlabel('Date')
    plt.ylabel('Total Amount')
    plt.title(f'Expenses Over Time - {selected_month} {selected_year}')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def generate_scatter_plot():
    global selected_month, selected_year

    if not selected_month or not selected_year:
        mb.showerror("Filter Error", "Please apply a month and year filter first!")
        return

    selected_month_num = datetime.strptime(selected_month, '%b').strftime('%m')

    query = """
        SELECT Payee, Amount 
        FROM SPENDOMETER
        WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
    """
    cursor = connector.execute(query, (selected_month_num, selected_year))
    data = cursor.fetchall()

    if not data:
        mb.showerror("No Data", f"No data available for {selected_month} {selected_year}.")
        return

    payees = [row[0] for row in data]
    amounts = [row[1] for row in data]

    plt.figure(figsize=(10, 6))
    plt.scatter(payees, amounts, color='purple', alpha=0.6)
    plt.xlabel('Payees')
    plt.ylabel('Amount')
    plt.title(f'Scatter Plot of Expenses by Payee - {selected_month} {selected_year}')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def generate_histogram():
    global selected_month, selected_year

    if not selected_month or not selected_year:
        mb.showerror("Filter Error", "Please apply a month and year filter first!")
        return

    selected_month_num = datetime.strptime(selected_month, '%b').strftime('%m')

    query = """
        SELECT PAYEE 
        FROM SPENDOMETER 
        WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
    """
    cursor = connector.execute(query, (selected_month_num, selected_year))
    data = cursor.fetchall()

    if not data:
        mb.showerror("No Data", f"No data available for {selected_month} {selected_year}.")
        return

    amounts = [row[0] for row in data]

    plt.figure(figsize=(10, 6))
    plt.hist(amounts, bins=10, color='orange', edgecolor='black')
    plt.xlabel('Payee')
    plt.ylabel('Frequency')
    plt.title(f'Histogram of Expense Amounts - {selected_month} {selected_year}')
    plt.tight_layout()
    plt.show()

def selected_expense_to_words():
  global table

  if not table.selection():
     mb.showerror('No expense selected!', 'Please select an expense from the table for us to read')
     return

  current_selected_expense = table.item(table.focus())
  values = current_selected_expense['values']

  message = f'Your expense can be read like: \n"You paid {values[4]} to {values[2]} for {values[3]} on {values[1]} via {values[5]}"'

  mb.showinfo('Here\'s how to read your expense', message)

def expense_to_words_before_adding():
  global date, desc, amnt, payee, MoP

  if not date or not desc or not amnt or not payee or not MoP:
     mb.showerror('Incomplete data', 'The data is incomplete, meaning fill all the fields first!')

  message = f'Your expense can be read like: \n"You paid {amnt.get()} to {payee.get()} for {desc.get()} on {date.get_date()} via {MoP.get()}"'

  add_question = mb.askyesno('Read your record like: ', f'{message}\n\nShould I add it to the database?')

  if add_question:
     add_another_expense()
  else:
     mb.showinfo('Ok', 'Please take your time to add this record')

# Connecting to the Database

connector = sqlite3.connect(
    "SPENDOMETER.db")
cursor = connector.cursor()

connector.execute(
    'CREATE TABLE IF NOT EXISTS SPENDOMETER (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
    'iid INTEGER, Date DATETIME, Payee TEXT, Description TEXT, Amount FLOAT, ModeOfPayment TEXT)'
)
connector.commit()

# Backgrounds and Fonts
dataentery_frame_bg = 'Thistle'
buttons_frame_bg = 'Plum'
hlb_btn_bg = 'Orchid'

lbl_font = ('Georgia', 13)
entry_font = 'Times 13 bold'
btn_font = ('Gill Sans MT', 13)

# Initializing the GUI window
root = Tk()

# Set window title and size
root.title('Smart Spending! Better Living!🚀')
root.geometry('1200x550')  # Initial size of the window

# Allow the window to be resized
root.resizable(True, True)  # Enables both horizontal and vertical resizing


Label(root, text='SPENDOMETER: TRACK! SAVE! SUCCEED!🚀', font=('Noto Sans CJK TC', 15, 'bold'), bg=hlb_btn_bg).pack(side=TOP, fill=X)

# StringVar and DoubleVar variables
desc = StringVar()
amnt = DoubleVar()
payee = StringVar()
MoP = StringVar(value='Cash')

# Frames
data_entry_frame = Frame(root, bg=dataentery_frame_bg)
data_entry_frame.place(x=0, y=30, relheight=0.95, relwidth=0.25)

buttons_frame = Frame(root, bg=buttons_frame_bg)
buttons_frame.place(relx=0.25, rely=0.05, relwidth=0.75, relheight=0.21)

tree_frame = Frame(root)
tree_frame.place(relx=0.25, rely=0.26, relwidth=0.75, relheight=0.74)

# Data Entry Frame
Label(data_entry_frame, text='Date (M/DD/YY) :', font=lbl_font, bg=dataentery_frame_bg).place(x=10, y=50)
date = DateEntry(data_entry_frame, date=datetime.now().date(), font=entry_font)
date.place(x=160, y=50)

Label(data_entry_frame, text='Payee\t             :', font=lbl_font, bg=dataentery_frame_bg).place(x=10, y=230)
Entry(data_entry_frame, font=entry_font, width=31, text=payee).place(x=10, y=260)

Label(data_entry_frame, text='Description           :', font=lbl_font, bg=dataentery_frame_bg).place(x=10, y=100)
Entry(data_entry_frame, font=entry_font, width=31, text=desc).place(x=10, y=130)

Label(data_entry_frame, text='Amount\t             :', font=lbl_font, bg=dataentery_frame_bg).place(x=10, y=180)
Entry(data_entry_frame, font=entry_font, width=14, text=amnt).place(x=160, y=180)

Label(data_entry_frame, text='Mode of Payment:', font=lbl_font, bg=dataentery_frame_bg).place(x=10, y=310)
dd1 = OptionMenu(data_entry_frame, MoP, *['Cash', 'Cheque', 'Credit Card', 'Debit Card', 'Paytm', 'Google Pay', 'Razorpay'])
dd1.place(x=160, y=305)     ;     dd1.configure(width=10, font=entry_font)

Button(data_entry_frame, text='Add expense', command=add_another_expense, font=btn_font, width=30,
       bg=hlb_btn_bg).place(x=10, y=395)

Button(data_entry_frame, text="Charts", font=btn_font, width=30, bg=hlb_btn_bg, command=show_chart_options).place(x=10, y=450)

Button(data_entry_frame, text="Chat", font=btn_font, width=30, bg=hlb_btn_bg, command=open_chat_window).place(x=10, y=500)

Button(data_entry_frame, text="Total Expenses", command=calculate_total_expenses, font=btn_font, width=30, bg=hlb_btn_bg).place(x=10, y=550)

total_expenses_label = Label(data_entry_frame, text="Total Expenses: $0.00", font=lbl_font, bg=dataentery_frame_bg)
total_expenses_label.place(x=10, y=600)

# Buttons' Frame
Button(buttons_frame, text='Delete Expense', font=btn_font, width=25, bg=hlb_btn_bg, command=remove_expense).place(x=30, y=5)

Button(buttons_frame, text='Clear Fields in DataEntry Frame', font=btn_font, width=25, bg=hlb_btn_bg,
      command=clear_fields).place(x=335, y=5)

Button(buttons_frame, text='Delete All Expenses', font=btn_font, width=25, bg=hlb_btn_bg, command=remove_all_expenses).place(x=640, y=5)

Button(buttons_frame, text='View Selected Expense\'s Details', font=btn_font, width=25, bg=hlb_btn_bg,
      command=view_expense_details).place(x=30, y=65)

Button(buttons_frame, text="M/Y", font=btn_font, width=25, bg=hlb_btn_bg, command=filter_by_month_year).place(x=30, y=125)

Button(buttons_frame, text='Edit Selected Expense', command=edit_expense, font=btn_font, width=25, bg=hlb_btn_bg).place(x=335,y=65)

Button(buttons_frame, text='Convert Expense to a sentence', font=btn_font, width=25, bg=hlb_btn_bg,
      command=selected_expense_to_words).place(x=640, y=65)

Button(buttons_frame, text='Compare Expenses', font=btn_font, width=25, bg=hlb_btn_bg, 
      command=compare_expenses).place(x=335, y=125)

Button(buttons_frame, text='Refresh', font=btn_font, width=25, bg=hlb_btn_bg, 
      command=refresh_expenses).place(x=640, y=125)

# Treeview Frame
table = ttk.Treeview(tree_frame, selectmode=BROWSE, columns=('ID', 'iid', 'Date', 'Payee', 'Description', 'Amount', 'Mode of Payment'))

X_Scroller = Scrollbar(table, orient=HORIZONTAL, command=table.xview)
Y_Scroller = Scrollbar(table, orient=VERTICAL, command=table.yview)
X_Scroller.pack(side=BOTTOM, fill=X)
Y_Scroller.pack(side=RIGHT, fill=Y)

table.config(yscrollcommand=Y_Scroller.set, xscrollcommand=X_Scroller.set)

table.heading('ID', text='S No.', anchor=CENTER)
table.heading('iid', text='IID', anchor=CENTER)
table.heading('Date', text='Date', anchor=CENTER)
table.heading('Payee', text='Payee', anchor=CENTER)
table.heading('Description', text='Description', anchor=CENTER)
table.heading('Amount', text='Amount', anchor=CENTER)
table.heading('Mode of Payment', text='Mode of Payment', anchor=CENTER)

table.column('#0', width=0, stretch=NO)
table.column('#1', width=50, stretch=NO)
table.column('#2', width=95, stretch=NO)  # Date column
table.column('#3', width=150, stretch=NO)  # Payee column
table.column('#4', width=325, stretch=NO)  # Title column
table.column('#5', width=135, stretch=NO)  # Amount column
table.column('#6', width=125, stretch=NO)  # Mode of Payment column

table.place(relx=0, y=0, relheight=1, relwidth=1)
list_all_expenses()

# Finalizing the GUI window
root.update()
root.mainloop()
