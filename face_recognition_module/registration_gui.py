import tkinter as tk
from tkinter import ttk, messagebox
import re
import threading
from register import register_customer
import firebase_admin
from firebase_admin import credentials, firestore
import os
import shutil
from datetime import datetime
from send_message import send_whatsapp_message
from tkcalendar import DateEntry
from dotenv import load_dotenv

cred_path = os.environ.get("FIREBASE_CREDENTIAL_PATH")
if not cred_path:
    raise ValueError("FIREBASE_CRED_PATH not set in environment variables")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

db = firestore.client()


def normalize_phone(phone):
    phone = re.sub(r"[^\d+]", "", phone)  # Remove all except digits and +

    if phone.startswith("+961"):
        number = phone[4:]
    elif phone.startswith("961"):
        number = phone[3:]
    elif phone.startswith("0"):
        number = phone[1:]
    else:
        number = phone

    # Allowed prefixes
    valid_prefixes = ("70", "71", "76", "78", "81", "03")

    # Check prefix and length
    if len(number) == 8 and number.startswith(valid_prefixes):
        return "+961" + number

    return None


def is_valid_name(name):
    name = name.strip()
    if len(name) < 2 or len(name) > 30:
        return False
    if not all(c.isalpha() or c in " -'" for c in name):
        return False
    return True


def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")  # must be YYYY-MM-DD
        return True
    except ValueError:
        return False


class RegistrationApp:
    def __init__(self, root):
        self.root = root

        tk.Label(root, text="Customer Name: ").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(root, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.name_error = tk.Label(root, text="", fg="red")
        self.name_error.grid(row=1, column=1, sticky="w")

        tk.Label(root, text="Phone Number: ").grid(
            row=2, column=0, sticky="w", padx=5, pady=5)
        self.phone_var = tk.StringVar()
        phone_entry = ttk.Entry(root, textvariable=self.phone_var)
        phone_entry.grid(row=2, column=1, padx=5, pady=5)
        self.phone_error = tk.Label(root, text="", fg="red")
        self.phone_error.grid(row=3, column=1, sticky="w")

        tk.Label(root, text="Date of Birth: ").grid(
            row=4, column=0, sticky="w", padx=5, pady=5)

        self.dob_entry = DateEntry(
            root,
            date_pattern="yyyy-mm-dd",  # Ensures format YYYY-MM-DD
            width=12,
            background="darkblue",
            foreground="white",
            borderwidth=2,
            year=2000  # Default year shown in calendar
        )
        self.dob_entry.grid(row=4, column=1, padx=5, pady=5)

        self.dob_error = tk.Label(root, text="", fg="red")
        self.dob_error.grid(row=5, column=1, sticky="w")

        tk.Label(root, text="Gender: ").grid(
            row=6, column=0, sticky="w", padx=5, pady=5)
        self.gender_var = tk.StringVar()
        gender_combo = ttk.Combobox(root, textvariable=self.gender_var,
                                    values=["Male", "Female"], state="readonly")
        gender_combo.grid(row=6, column=1, padx=5, pady=5)
        self.gender_error = tk.Label(root, text="", fg="red")
        self.gender_error.grid(row=7, column=1, sticky="w")

        self.start_btn = ttk.Button(root, text="Start Camera",
                                    state="disabled", command=self.start_camera)
        self.start_btn.grid(row=8, column=1, pady=10)

        self.cancel_btn = ttk.Button(
            root, text="Cancel", state="normal", command=self.cancel_registration)
        self.cancel_btn.grid(row=10, column=1, pady=10)

        self.status_label = tk.Label(
            root, text="Enter valid name and Lebanese phone", fg="blue")
        self.status_label.grid(row=11, column=0, columnspan=2)

        self.name_var.trace_add("write", self.validate)
        self.phone_var.trace_add("write", self.validate)
        self.gender_var.trace_add("write", self.validate)
        self.dob_entry.bind("<<DateEntrySelected>>", lambda e: self.validate())

        self.samples = 0
        self.max_samples = 10
        self.registration_done = False

    def validate(self, *args):
        name = self.name_var.get()
        phone = self.phone_var.get()
        dob = self.dob_entry.get()
        gender = self.gender_var.get().strip()

        valid_name = is_valid_name(name)
        normalized_phone = normalize_phone(phone)
        valid_dob = is_valid_date(dob)
        valid_gender = gender in ["Male", "Female"]

        if valid_name:
            self.name_error.config(text="")
        else:
            self.name_error.config(text="Invalid name")

        if phone == "":
            self.phone_error.config(text="Phone required")
        elif normalized_phone is None:
            self.phone_error.config(text="Invalid phone")
        else:
            self.phone_error.config(text="")

        if dob == "" or not valid_dob:
            self.dob_error.config(text="Invalid date format (YYYY-MM-DD)")
        else:
            self.dob_error.config(text="")

        if not valid_gender:
            self.gender_error.config(text="Select a gender")
        else:
            self.gender_error.config(text="")

        if valid_name and normalized_phone and valid_dob and valid_gender:
            self.start_btn.config(state="normal")
            self.status_label.config(
                text="Ready to start camera", foreground="green")
        else:
            self.start_btn.config(state="disabled")
            self.status_label.config(
                text="Enter valid name and lebanese number", foreground="blue")

    def start_camera(self):
        name = self.name_var.get().strip()
        phone = normalize_phone(self.phone_var.get())

        try:
            docs = db.collection('customers').where(
                'name', '==', name).stream()
            for doc in docs:
                messagebox.showerror("Error", f"Name '{name}' already exists!")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")
            return

        try:
            docs = db.collection('customers').where(
                'phone_number', '==', phone).stream()
            for doc in docs:
                messagebox.showerror("Error", "Phone number is already exist")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")
            return

        self.start_btn.config(state="disabled")
        self.samples = 0
        self.status_label.config(text="Starting Registration", fg="orange")

        threading.Thread(target=self.run_registration, daemon=True).start()

    def run_registration(self):

        dob_str = self.dob_entry.get()
        dob_datetime = datetime.strptime(dob_str, "%Y-%m-%d")
        success, result = register_customer(
            self.name_var.get(), normalize_phone(self.phone_var.get()),
            dob=dob_datetime, gender=self.gender_var.get().strip(),
            progress_callback=self.update_progress)

        def ui():
            if success:
                self.registration_data = result
                self.status_label.config(text=result['message'], fg="green")
                confirmation = messagebox.askyesno(
                    "Confirm Submission", "Customer registered successfully.\nDo you want to submit now?")
                if confirmation:
                    self.save_registration_data()
                    messagebox.showinfo(
                        "Success", "Registration saved to database!")
                    self.root.destroy()
                else:
                    self.cleanup_registration_data()
                    messagebox.showinfo(
                        "Cancelled", "Registration cancelled and cleaned up!")
                    self.root.destroy()

            else:
                self.status_label.config(text=result, fg="red")
                self.start_btn.config(state='normal')

        self.root.after(0, ui)

    def update_progress(self, sample_number, sample_max):
        def update():
            self.status_label.config(
                text=f"Captured sample {sample_number}/{sample_max}", fg="green")
        self.root.after(0, update)

    def save_registration_data(self):
        try:
            if not hasattr(self, 'registration_data'):
                messagebox.showerror("Error", "No registration data found")
                return
            data = self.registration_data
            doc_ref = db.collection('customers').document(data['customer_id'])
            doc_ref.set({
                'name': self.name_var.get(),
                'phone_number': normalize_phone(self.phone_var.get()),
                'date_of_birth': data['dob'].strftime("%Y-%m-%d"),
                'gender': data['gender'],
                'encodings': data['flattened_encodings'],
                'created_at': datetime.utcnow().isoformat(),
                'last_visit': None,
                'purchase_history': data['purchase_history'],
                'last_emotion': None
            })
            self.registration_done = True
            self.status_label.config(
                text="Registration saved succesfully!", fg="green")
            welcome_message = f'Hello {self.name_var.get()}, Welcome to our supermarket! Enjoy your first visit.'
            send_whatsapp_message(normalize_phone(
                self.phone_var.get()), welcome_message)
            self.root.destroy()

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to save registration: {str(e)}")
            self.cleanup_registration_data()

    def cleanup_registration_data(self):
        try:
            if not hasattr(self, 'registration_data'):
                return
            data = self.registration_data

            if os.path.exists(data['file_path']):
                os.remove(data['file_path'])

            if os.path.exists(data['person_image_dir']):
                shutil.rmtree(data['person_image_dir'])

            self.registration_done = False
            self.status_label.config(text='Registration cancelled', fg='blue')
            self.root.destroy()

        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            self.root.destroy()

    def submit_registration(self):
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        normalized = normalize_phone(phone)
        messagebox.showinfo(
            "Registration Complete", f"Customer {name}\nPhone: {normalized}")
        self.samples = 0
        self.start_btn.config(state="disabled")
        self.status_label.config(
            text="Enter valid name and lebanese phone number", fg="blue")
        self.name_var.set("")
        self.phone_var.set("")
        self.registration_done = False

    def cancel_registration(self):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Customer registration")
    app = RegistrationApp(root)
    root.mainloop()
