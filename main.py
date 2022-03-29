import pyotp
import pyqrcode
import os
import tkinter as tk
import sqlite3

'''To install dependencies:
pip install pyotp pyqrcode pypng'''

class Username(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)

        self.configure(border=10)
        self.pack()

        self.app = app

        # Username Label
        self.username_label = tk.Label(self, text="Username: ")
        self.username_label.grid(row=0, column=0)

        # Stores the data for the username Entry
        self.username_var = tk.StringVar()

        # Username Entry
        self.username_entry = tk.Entry(self, textvariable=self.username_var)
        self.username_entry.grid(row=0, column=1)

        # Submit Button
        self.submit_button = tk.Button(self, text="Submit", command=self.submit)
        self.submit_button.grid(row = 1, column=0)

        # Cancel Button
        self.cancel_button = tk.Button(self, text="Cancel", command=self.cancel)
        self.cancel_button.grid(row=1, column=1)

    def submit(self):
        # Get the Username
        username = self.username_var.get()
        # Pass the Username to the App
        self.app.set_username(username)
        # Close the Window
        self.destroy()

    def cancel(self):
        # Close the Window
        self.destroy()

class Passcode(tk.Frame):
    def __init__(self, master, app, username):
        super().__init__(master)

        self.configure(border=10)
        self.pack()

        self.app = app
        self.username = username

        # Passcode Label
        self.passcode_label = tk.Label(self, text="Passcode: ")
        self.passcode_label.grid(row=0, column=0)

        # Stores the data for the passcode Entry
        self.passcode_var = tk.StringVar()

        # Passcode Entry
        self.passcode_entry = tk.Entry(self, textvariable=self.passcode_var)
        self.passcode_entry.grid(row=0, column=1)

        # Submit Button
        self.submit_button = tk.Button(self, text="Submit", command=self.submit)
        self.submit_button.grid(row = 1, column=0)

        # Cancel Button
        self.cancel_button = tk.Button(self, text="Cancel", command=self.cancel)
        self.cancel_button.grid(row=1, column=1)

    def submit(self):
        # Get the Passcode
        passcode = self.passcode_var.get()
        # Pass the Username and Passcode to the App
        self.app.authenticate(self.username, passcode)
        # Close the Window
        self.destroy()

    def cancel(self):
        # Close the Window
        self.destroy()

class QRPopup(tk.Toplevel):
    def __init__(self, master, app, username):
        super().__init__(master)
        self.wm_title("QR Code")

        self.app = app
        self.username = username

        # Instructions Label
        instructions_label = tk.Label(self, text="Scan this QR code with your authenticator app.")
        instructions_label.pack()

        # Load the PNG with Tk
        self.qr_image = tk.PhotoImage(file="qr_temp.png")
        # Create a Label with the Image
        qr_label = tk.Label(self, image=self.qr_image)
        qr_label.pack()

        # Done Button
        done_button = tk.Button(self, text="Done", command=self.done)
        done_button.pack()
    
    def __del__(self):
        # Delete the Temporary PNG if it Exists
        try:
            os.remove("qr_temp.png")
        except FileNotFoundError:
            pass

    def done(self):
        # Ask the User to Authenticate
        self.app.set_username(self.username)
        # Close the Window
        self.destroy()

class Database():
    def __init__(self):
        # Connect to the Database and Create a Cursor
        self.connection = None
        self.cursor = None
        try:
            self.connection = sqlite3.connect(r"auth.db")
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            print("Failed to connect to database:", e)
        # Create a Table in the Database
        self.create_table()

    def __del__(self):
        self.connection.close()

    def create_table(self):
        # Create a Table called students with a UUID, Student Number and Secret Key for OTP
        sql_create_table = """ CREATE TABLE IF NOT EXISTS students (
                                   id integer PRIMARY KEY,
                                   student_num text NOT NULL UNIQUE,
                                   secret_key text NOT NULL
                               ); """
        try:
            self.cursor.execute(sql_create_table)
        except sqlite3.Error as e:
            print("Failed to create database table:", e)
    
    def user_exists(self, student_num):
        # Attempt to Select the Corresponding Student Record
        # If it fails, we assume the student is not registered
        sql_user_exists = """ SELECT * FROM students WHERE student_num=? """
        try:
            self.cursor.execute(sql_user_exists, (student_num,))
            record = self.cursor.fetchone()
        except sqlite3.Error as e:
            print("Failed to retrieve record from database:", e)
        if record:
            return True
        return False

    def add_student(self, student_num, secret_key):
        # Add a Student to the students Table
        sql_add_student = """ INSERT INTO students(student_num,secret_key)
                              VALUES(?,?) """
        record = (student_num, secret_key)
        try:
            self.cursor.execute(sql_add_student, record)
            self.connection.commit()
        except sqlite3.Error as e:
            print("Failed to add record to database:", e)

    def get_secret_key(self, student_num):
        # Get the Secret Key by Student Number
        secret_key = None
        sql_get_secret_key = """ SELECT * FROM students WHERE student_num=? """
        try:
            self.cursor.execute(sql_get_secret_key, (student_num,))
            record = self.cursor.fetchone()
        except sqlite3.Error as e:
            print("Failed to retrieve record from database:", e)
        secret_key = record[2]
        return secret_key

class App():
    def __init__(self):
        # Init Database
        self.database = Database()
        # Init Tk
        self.root = tk.Tk()
        app = Username(self.root, self)
        app.mainloop()
    
    def set_username(self, username):
        if self.database.user_exists(username):
            # Ask the user for a passcode
            Passcode(self.root, self, username)
        else:
            # Register the user
            self.add_user(username)

    def add_user(self, username):
        # Generate the Secret Key
        secret_key = pyotp.random_base32()
        # Add the Student to the Database
        self.database.add_student(username, secret_key)
        # Generate and Show the QR Code
        self.show_qrcode(username, secret_key)

    def authenticate(self, username, passcode):
        #  Check that the Passcode Matches the Current TOTP
        secret_key = self.database.get_secret_key(username)
        if not secret_key:
            print("User could not be found")
            return
        totp = pyotp.TOTP(secret_key)
        if totp.now() == passcode:
            print(username, "authenticated successfully!")
        else:
            print(username, "could not authenticate.")
            Username(self.root, self)
    
    def show_qrcode(self, username, secret_key):
        # Generate a URI that the authenticator can understand
        auth_uri = pyotp.totp.TOTP(secret_key).provisioning_uri(name=username, issuer_name="Student Record Viewer")
        # Generate QR Code Data
        qrcode = pyqrcode.create(auth_uri)
        # Save a PNG of the QR Code
        qrcode.png("qr_temp.png", scale=8)
        # Display it in a Window
        QRPopup(self.root, self, username)

if __name__ == '__main__':
    App()
