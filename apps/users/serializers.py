from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, SystemLog
import re

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    activity = serializers.SerializerMethodField()  # Computed field for dynamic activity
    

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'status', 'role', 'activity', 'last_activity', 'isActive']
        extra_kwargs = {
            'password': {'write_only': True},
            'last_activity': {'read_only': True}
        }
    
    def get_activity(self, obj):
        """Return dynamic activity status"""
        return obj.get_activity_status()
    

    def validate_password(self, value):
        """
        Validate password requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one number
        - At least one special character
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        
        return value
    
    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({"password": "Password is required when creating a user."})
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user, hash password if provided"""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance

class SystemLogSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.name', default='System')

    class Meta:
        model = SystemLog
        fields = ['id', 'timestamp', 'user', 'user_name', 'ip_address', 'action', 'severity']


class CustomTokenObtainPairSerializer(serializers.Serializer):
    """
    Custom JWT serializer to include user role and additional information in the token.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        # Get email and password from attrs
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError('Email and password are required')
        
        try:
            # Get user from our custom User model
            user = User.objects.get(email=email)
            
            # Check if user is active
            if not user.isActive:
                raise serializers.ValidationError('Account is disabled')
            
            # Verify password using our custom method
            if not user.verify_password(password):
                raise serializers.ValidationError('Invalid credentials')
            
            # Generate tokens using simplejwt
            from rest_framework_simplejwt.tokens import RefreshToken
            
            refresh = RefreshToken()
            refresh['email'] = user.email
            refresh['role'] = user.role
            refresh['name'] = user.name
            refresh['user_id'] = user.id
            
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'role': user.role,
                    'status': user.status,
                    'isActive': user.isActive,
                }
            }
            
            return data
            
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid credentials')


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate_new_password(self, value):
        """
        Validate new password requirements.
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs
