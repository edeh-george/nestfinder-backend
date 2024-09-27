from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError


User = get_user_model()

class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        # Set write_only to True by default
        kwargs['write_only'] = True
        super().__init__(**kwargs)


class UserEmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()
    safe = serializers.CharField()

class UserSignUpSerializer(serializers.Serializer):

    name = serializers.CharField()
    email = serializers.EmailField()
    password = PasswordField()
    _password = PasswordField()


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

class UserPasswordResetLoggedinSerializer(serializers.Serializer):
    old_password = PasswordField()
    new_password = PasswordField()
    _new_password = PasswordField()

    def __init__(self, instance=None, data=..., **kwargs):
        super().__init__(instance, data, **kwargs)
        self.request = self.context.get('request')

        


    def validate(self, attrs):
        if attrs['new_password'] != attrs['_new_password']:
            raise ValidationError(detail="Passwords don't match")
        del attrs['_new_password']
        #Checks if the old password matches the user old password
        if not self.instance.check_password(attrs['old_password']):
            raise ValidationError(detail="Old passsword is incorrect")
        del attrs['old_password']
        return attrs


class UserLogoutSerializer(serializers.Serializer):
    pass