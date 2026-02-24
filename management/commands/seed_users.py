import os
import sys
import django

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wound_analysis_backend.settings')
django.setup()

from users.models import User

def seed_data():
    # Sample user data with password "Vamsi123@" for all users
    users_data = [
        {"name": "Dr. Virat Kohli", "email": "viratkohli@gmail.com", "status": "ACTIVE", "role": "Doctor", "activity": "2 mins ago", "isActive": True},
        {"name": "Dr. Rohit Sharma", "email": "rohitsharma@gmail.com", "status": "ACTIVE", "role": "Doctor", "activity": "1 hour ago", "isActive": True},
        {"name": "Dr. Jasprit Bumrah", "email": "jaspritbumrah@gmail.com", "status": "DISABLED", "role": "Doctor", "activity": "Just now", "isActive": False},
        {"name": "Nurse Mithali Raj", "email": "mithaliraj@gmail.com", "status": "ACTIVE", "role": "Nurse", "activity": "10 mins ago", "isActive": True},
        {"name": "Admin Hardik Pandya", "email": "hardikpandya@gmail.com", "status": "ACTIVE", "role": "Admin", "activity": "3 days ago", "isActive": True},
        {"name": "Nurse Smriti Mandhana", "email": "smritimandhana@gmail.com", "status": "ACTIVE", "role": "Nurse", "activity": "5 mins ago", "isActive": True},
        {"name": "Dr. KL Rahul", "email": "klrahul@gmail.com", "status": "ACTIVE", "role": "Doctor", "activity": "30 mins ago", "isActive": True},
        {"name": "Nurse Harmanpreet Kaur", "email": "harmanpreetkaur@gmail.com", "status": "DISABLED", "role": "Nurse", "activity": "2 weeks ago", "isActive": False},
        {"name": "Admin Ravindra Jadeja", "email": "ravindrajadeja@gmail.com", "status": "ACTIVE", "role": "Admin", "activity": "1 day ago", "isActive": True},
        {"name": "Nurse Jhulan Goswami", "email": "jhulangoswami@gmail.com", "status": "ACTIVE", "role": "Nurse", "activity": "4 hours ago", "isActive": True},
        {"name": "Dr. Suryakumar Yadav", "email": "suryakumaryadav@gmail.com", "status": "ACTIVE", "role": "Doctor", "activity": "15 mins ago", "isActive": True},
        {"name": "Nurse Richa Ghosh", "email": "richaghosh@gmail.com", "status": "DISABLED", "role": "Nurse", "activity": "1 month ago", "isActive": False},
    ]
    
    password = "Vamsi123@"  # Same password for all users
    
    for item in users_data:
        user = User(
            name=item['name'],
            email=item['email'],
            status=item['status'],
            role=item['role'],
            activity=item['activity'],
            isActive=item['isActive'],
        )
        user.set_password(password)  # Hash the password
        user.save()
        
    print(f"Successfully seeded {len(users_data)} users with password: {password}")

if __name__ == '__main__':
    seed_data()
