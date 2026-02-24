from users.models import User

# Get admin user
admin = User.objects.filter(email='hardiksharma@gmail.com').first()

if admin:
    print(f"User: {admin.email}")
    print(f"Role: {admin.role}")
    print(f"Active: {admin.isActive}")
    print(f"Password hash (first 30 chars): {admin.password[:30] if admin.password else 'None'}...")
    
    # Test password verification
    test_password = "Admin@123"
    result = admin.verify_password(test_password)
    print(f"\nPassword verification for '{test_password}': {result}")
    
    # Try setting password again and testing
    print("\nSetting password again...")
    admin.set_password(test_password)
    admin.save()
    
    # Test again
    result = admin.verify_password(test_password)
    print(f"Password verification after reset: {result}")
    
    if result:
        print("\n✅ Password is working correctly!")
    else:
        print("\n❌ Password verification still failing!")
        print("Checking password hash...")
        from django.contrib.auth.hashers import check_password
        print(f"Django check_password result: {check_password(test_password, admin.password)}")
else:
    print("User not found!")
