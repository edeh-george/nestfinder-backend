from rest_framework import serializers


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


        return attrs
    

class UserPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()