import mysql.connector
import random
import os

# DB Connection
db = mysql.connector.connect(
    host="localhost", 
    user="root",
    password=os.getenv("MySQL_Password"),
    database="bank_db_v2"
)
cursor = db.cursor()

# Check account exists
def account_exists(acc_no):
    cursor.execute("SELECT * FROM accounts WHERE acc_no=%s", (acc_no,))
    return cursor.fetchone() is not None

# Check account status
def is_active(acc_no):
    cursor.execute("SELECT status FROM accounts WHERE acc_no=%s", (acc_no,))
    result = cursor.fetchone()
    return result and result[0] == 'active'

# Generate Account Number 
def generate_acc_no():
    while True:
        acc_no = "955301" + f"{random.randint(0, 9999):04}"
        cursor.execute("SELECT * FROM accounts WHERE acc_no=%s", (acc_no,))
        if not cursor.fetchone():
            return acc_no

# Create Account
def create_account():
    name = input("Enter name: ")
    if not all(ch.isalpha() or ch.isspace() for ch in name):
        print("Name should contain only letters and spaces!")
        return
    pin = int(input("Set PIN: "))
    acc_no = generate_acc_no()
    ifsc = "SBIN0001234"
    
    cursor.execute(
        "INSERT INTO accounts (acc_no, ifsc, name, pin, balance, status) VALUES (%s, %s, %s, %s, 0, 'active')",
        (acc_no, ifsc, name, pin)
    )
    
    db.commit()
    
    print("\nAccount created successfully!")
    print("Account Number:", acc_no)
    print("IFSC Code:", ifsc)

# Login
def login():
    acc_no = input("Enter account number: ")

    if not account_exists(acc_no):
        print("Account not found!")
        return None

    if not is_active(acc_no):
        print("Account is closed!")
        return None

    pin = int(input("Enter PIN: "))

    cursor.execute(
        "SELECT * FROM accounts WHERE acc_no=%s AND pin=%s",
        (acc_no, pin)
    )
    user = cursor.fetchone()

    if user:
        print(f"Login successful! Welcome {user[2]}")
        return acc_no
    else:
        print("Invalid PIN!")
        return None

# Check Balance
def check_balance(acc_no):
    cursor.execute("SELECT balance FROM accounts WHERE acc_no=%s", (acc_no,))
    print("Balance:", cursor.fetchone()[0]) 

# Deposit
def deposit(acc_no):

    amt = float(input("Enter amount: "))
    
    cursor.execute("UPDATE accounts SET balance = balance + %s WHERE acc_no=%s", (amt, acc_no))
    cursor.execute(
        "INSERT INTO transactions (acc_no, type, amount) VALUES (%s, 'deposit', %s)",
        (acc_no, amt)
    )
    
    db.commit()
    print("Deposit successful")

# Withdraw
def withdraw(acc_no):

    amt = float(input("Enter amount: "))
    
    cursor.execute("SELECT balance FROM accounts WHERE acc_no=%s", (acc_no,))
    balance = cursor.fetchone()[0]
    
    if balance >= amt:
        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE acc_no=%s", (amt, acc_no))
        cursor.execute(
            "INSERT INTO transactions (acc_no, type, amount) VALUES (%s, 'withdraw', %s)",
            (acc_no, amt)
        )
        db.commit()
        print("Withdraw successful")
    else:
        print("Insufficient balance")

# Transfer
def transfer(from_acc):

    to_acc = input("Enter receiver acc no: ")
    
    #  SAME ACCOUNT CHECK
    if from_acc == to_acc:
        print("You cannot transfer money to your own account!")
        return
    # Check Receiver acc EXISTS 
    if not account_exists(to_acc):
        print("Receiver account not found!")
        return
    # Check Receiver acc status
    if not is_active(to_acc):
        print("Receiver account is closed!")
        return

    amt = float(input("Enter amount: "))
    
    try:
        cursor.execute("SELECT balance FROM accounts WHERE acc_no=%s", (from_acc,))
        balance = cursor.fetchone()[0]
        
        if balance < amt:
            raise Exception("Insufficient funds")
        
        # debit
        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE acc_no=%s", (amt, from_acc))
        
        # credit
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE acc_no=%s", (amt, to_acc))
        
        # record transactions
        cursor.execute(
            "INSERT INTO transactions (acc_no, to_acc, type, amount) VALUES (%s, %s, 'transfer_out', %s)",
            (from_acc, to_acc, amt)
        )
        
        cursor.execute(
            "INSERT INTO transactions (acc_no, to_acc, type, amount) VALUES (%s, %s, 'transfer_in', %s)",
            (to_acc, from_acc, amt)
        )
        
        db.commit()
        print("Transfer successful")

    except Exception as e:
        db.rollback()
        print("Transaction failed:", e)

# Transaction History
def history(acc_no):
    cursor.execute("SELECT name FROM accounts WHERE acc_no=%s", (acc_no,))
    name = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM transactions WHERE acc_no=%s ORDER BY date DESC", (acc_no,))
    result = cursor.fetchall()
    
    cursor.execute("SELECT balance FROM accounts WHERE acc_no=%s", (acc_no,))
    balance = cursor.fetchone()[0]
    
    print("\n====== MINI STATEMENT ======")
    print("Account Holder:", name)
    print("Account No:", acc_no)
    print("Current Balance:", balance)
    print("-" * 70)
    print(f"{'TxnID':<8} {'TYPE':<15} {'AMOUNT':<10} {'TO/FROM':<15} {'DATE'}")
    print("-" * 70)
    
    for row in result:
        txn_id = row[0]
        acc = row[1]
        to_acc = row[2]
        txn_type = row[3]
        amount = row[4]
        date = row[5]
        
        if txn_type == "transfer_out":
            tf = f"To {to_acc}"
        elif txn_type == "transfer_in":
            tf = f"From {to_acc}"
        else:
            tf = "-"
        
        print("{:<8} {:<15} {:<10} {:<15} {}".format(
            txn_id, txn_type, amount, tf, date
        ))
    
    print("-" * 70)

# Close Account
def close_account(acc_no):
    pin=int(input("Enter pin for account close:"))
    cursor.execute("select pin from accounts WHERE acc_no=%s",(acc_no,))
    result=cursor.fetchone()
    if result and result[0]==pin:
        cursor.execute("UPDATE accounts SET status='closed' WHERE acc_no=%s", (acc_no,))
        db.commit()
        print("Account closed successfully!")
    else:
        print("Pin is incorrect !")    

# Main Menu
while True:
    print("\n1. Create Account\n2. Login\n3. Exit")
    ch = int(input("Enter choice: "))
    
    if ch == 1:
        create_account()
        
    elif ch == 2:
        account_No = login()
        if account_No:
            while True:
                print("\n1. Balance\n2. Deposit\n3. Withdraw\n4. Transfer\n5. History\n6. Close Account\n7. Logout")
                opt = int(input("Enter option: "))
                
                if opt == 1:
                    check_balance(account_No)
                elif opt == 2:
                    deposit(account_No)
                elif opt == 3:
                    withdraw(account_No)
                elif opt == 4:
                    transfer(account_No)
                elif opt == 5:
                    history(account_No)
                elif opt == 6:
                    close_account(account_No)
                    break
                elif opt == 7:
                    break
                    
    elif ch == 3:
        break
    