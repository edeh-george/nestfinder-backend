from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from django.core.validators import RegexValidator
from userprofile.serializers import UserProfileSerializer



User = get_user_model()

class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        # Set write_only to True by default
        kwargs['write_only'] = True
        super().__init__(**kwargs)

PasswordValidator = RegexValidator(
                        regex=r'^[\\w+/\-]*$',  # Only letters and numbers allowed
                        message="Username must contain only letters and numbers or special characters (\, /, -, _)",
                        code='invalid_password'
                    )


class UserEmailVerificationSerializer(serializers.Serializer):
    # token = serializers.CharField()
    # safe = serializers.CharField()
    pass

class UserSignUpSerializer(serializers.Serializer):

    name = serializers.CharField()
    email = serializers.EmailField()
    password = PasswordField(validators=[PasswordValidator])
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

class UserNewPasswordResetSerializer(serializers.Serializer):
    password = PasswordField(validators=[PasswordValidator])
    password_confirm = PasswordField(validators=[PasswordValidator])
        


    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise ValidationError(detail="Passwords don't match")
        del attrs['password_confirm']
        return attrs
    
    def update(self, instance, validated_data):

        field = list(validated_data.keys())[0]
        setattr(instance, field, make_password(validated_data[field]))
        instance.save(force_update=True, update_fields=validated_data.keys())

        return instance

    


class UserLogoutSerializer(serializers.Serializer):
    pass


class UserDetailSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile']

    def get_profile(self,obj):
        request = self.context.get('request')
        data = UserProfileSerializer(obj.user_profile).data
        if data['profile_picture']:
            data['profile_picture'] = request.build_absolute_uri(
                data['profile_picture']
            )
        del data['user']

        return data