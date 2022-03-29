import pyotp
import pyqrcode
import os
import tkinter as tk
import sqlite3

'''To install dependencies:
pip install pyotp pyqrcode pypng'''

class Login(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.pack()

        self.configure(border=10)

        # Username Label
        self.username_label = tk.Label(self, text="Username: ")
        self.username_label.grid(row=0, column=0)

        # Stores the data for the username Entry
        self.username_var = tk.StringVar()

        # Username Entry
        self.username_entry = tk.Entry(self, textvariable=self.username_var)
        self.username_entry.grid(row=0, column=1)

        # Passcode Label
        self.passcode_label = tk.Label(self, text="Passcode: ")
        self.passcode_label.grid(row=1, column=0)

        # Stores the data for the passcode Entry
        self.passcode_var = tk.StringVar()

        # Passcode Entry
        self.passcode_entry = tk.Entry(self, textvariable=self.passcode_var)
        self.passcode_entry.grid(row=1, column=1)

        # Submit Button
        self.submit_button = tk.Button(self, text="Submit", command=self.submit)
        self.submit_button.grid(row = 2, column=0)

        # Cancel Button
        self.cancel_button = tk.Button(self, text="Cancel", command=self.cancel)
        self.cancel_button.grid(row=2, column=1)

        # Add User Button
        self.add_user_button = tk.Button(self, text="Add User", command=self.add_user)
        self.add_user_button.grid(row=3, column=0)
    
    def submit(self):
        # Authenticate with the Backend
        username = self.username_var.get()
        passcode = self.passcode_var.get()
        self.app.authenticate(username, passcode)
    
    def cancel(self):
        # This should be something else
        exit()

    def add_user(self):
        # This should not be here
        username = self.username_var.get()
        self.app.add_user(username)

class QRPopup(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.wm_title("QR Code")

        # Instructions Label
        instructions_label = tk.Label(self, text="Scan this QR code with your authenticator app.")
        instructions_label.pack()

        # Load the PNG with Tk
        self.qr_image = tk.PhotoImage(file="qr_temp.png")
        # Create a Label with the Image
        qr_label = tk.Label(self, image=self.qr_image)
        qr_label.pack()

        # Done Button
        done_button = tk.Button(self, text="Done", command=self.destroy)
        done_button.pack()
    
    def __del__(self):
        # Delete the Temporary PNG if it Exists
        try:
            os.remove("qr_temp.png")
        except FileNotFoundError:
            pass

class App():
    def __init__(self):
        # This will be a proper database
        self.users = {"alice@google.com": "JBSWY3DPEHPK3PXP"}
        # Init Tk
        root = tk.Tk()
        app = Login(root, self)
        app.mainloop()
    
    def authenticate(self, username, passcode):
        # Check that the User Exists
        if username not in self.users:
            print("User not found")
            return
        #  Check that the Passcode Matches the Current TOTP
        totp = pyotp.TOTP(self.users[username])
        if totp.now() == passcode:
            print(username, "authenticated successfully!")
    
    def add_user(self, username):
        # Check that the User Does Not Exist
        if username in self.users:
            print("User already exists")
            return
        # Generate the Secret Key
        secret_key = pyotp.random_base32()
        self.users[username] = secret_key
        # Generate a URI that the authenticator can understand
        auth_uri = pyotp.totp.TOTP(secret_key).provisioning_uri(name=username, issuer_name="Student Viewer")
        # Generate QR Code Data
        qrcode = pyqrcode.create(auth_uri)
        # Save a PNG of the QR Code
        qrcode.png("qr_temp.png", scale=8)
        # Display it in a Window
        QRPopup()

if __name__ == '__main__':
    App()
