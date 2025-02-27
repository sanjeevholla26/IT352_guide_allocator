import os
import django
from tkinter import *
from tkinter import ttk, messagebox

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project_Guide_Allocator.settings')
django.setup()

# Import models
from Allocator.models import Role, MyUser

class RoleAssignerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Role Assigner")

        # Frame for user selection
        frame = Frame(self.root)
        frame.pack(pady=20, padx=20)

        Label(frame, text="Select User:").grid(row=0, column=0, padx=10, pady=10)
        
        # Dropdown for selecting users
        self.user_var = StringVar()
        self.users = self.get_users()
        self.user_dropdown = ttk.Combobox(frame, textvariable=self.user_var, values=self.users, state="readonly", width=30)
        self.user_dropdown.grid(row=0, column=1, padx=10, pady=10)

        # Dropdown for selecting role
        Label(frame, text="Select Role:").grid(row=1, column=0, padx=10, pady=10)
        
        self.role_var = StringVar()
        self.roles = ["admin", "student", "faculty"]
        self.role_dropdown = ttk.Combobox(frame, textvariable=self.role_var, values=self.roles, state="readonly", width=30)
        self.role_dropdown.grid(row=1, column=1, padx=10, pady=10)

        # Button to assign role
        assign_button = Button(frame, text="Assign Role", command=self.assign_role)
        assign_button.grid(row=2, column=0, columnspan=2, pady=20)

    def get_users(self):
        # Fetch all users from the database
        users = MyUser.objects.all()
        return [f"{user.id}: {user.edu_email}-{user.username}" for user in users]

    def assign_role(self):
        selected_user = self.user_var.get()
        selected_role = self.role_var.get()

        if not selected_user or not selected_role:
            messagebox.showwarning("Input Error", "Please select both user and role.")
            return
        
        # Extract user ID from selection
        user_id = selected_user.split(":")[0]
        try:
            user = MyUser.objects.get(id=user_id)
            role = Role.objects.get(role_name=selected_role)
            user.roles.clear()  # Clear existing roles
            user.roles.add(role)  # Assign new role
            user.save()
            messagebox.showinfo("Success", f"Assigned {selected_role} role to {user.edu_email}")
        except MyUser.DoesNotExist:
            messagebox.showerror("Error", "User not found.")
        except Role.DoesNotExist:
            messagebox.showerror("Error", "Role not found.")

if __name__ == "__main__":
    root = Tk()
    app = RoleAssignerApp(root)
    root.mainloop()
