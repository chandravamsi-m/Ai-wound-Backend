from users.models import User

# Check admin user
admin = User.objects.filter(role='Admin').first()

if admin:
    print(f"Admin user found: {admin.email}")
    print(f"Has password: {bool(admin.password)}")
    
    # Set a known password
    admin.set_password("Admin@123")
    admin.save()
    print("Password set to: Admin@123")
    
    # Verify it works
    if admin.verify_password("Admin@123"):
        print("✅ Password verification successful!")
    else:
        print("❌ Password verification failed!")
else:
    print("No admin user found")
    print("\nCreating admin user...")
    admin = User.objects.create(
        name="System Administrator",
        email="admin@hospital.com",
        role="Admin",
        status="ACTIVE",
        isActive=True
    )
    admin.set_password("Admin@123")
    admin.save()
    print(f"✅ Admin user created: {admin.email}")
