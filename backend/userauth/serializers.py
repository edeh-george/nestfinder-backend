from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
User = get_user_model()



class UserEmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()
    safe = serializers.CharField()

class UserSignUpSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    _password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['_password']:
            raise serializers.ValidationError({"error": "Passwords don't match"})
        # Removes the '_password' as it is not a user model attribute
        del attrs['_password']
        
        attrs['first_name'], attrs['last_name'] = attrs['name'].split(' ', maxsplit=1)
        del attrs['name']
        attrs['username'] = attrs['first_name'] + '_' + attrs['last_name']
        return attrs
    
    def create(self, validated_data):
        # Hash the password before saving the user
        validated_data['password'] = make_password(validated_data['password'])
        
        # Create and return the new user
        return User.objects.create(**validated_data)
    

class UserPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class UserLogoutSerializer(serializers.Serializer):
    pass