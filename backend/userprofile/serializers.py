from rest_framework import serializers
from .models import Profile



class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = '__all__'

    
    def to_internal_value(self, data):
        """
        It handles the conversion of the json data to a form that is python processible.
        It auguments its default behaviour by converting the nationality code from the request into the format
        that can be handled internally by python as well includes extra fields.
        """
        # Call the parent class's method to validate the standard fields
        ret = super().to_internal_value(data)
        
        # Add the extra fields from the request data
        ret = {key: value for key, value in data.items() if key not in self.fields}

        return ret

    def create(self, validated_data):
        # You can now handle extra fields as needed
        extra_fields = {key: value for key, value in validated_data.items() if key not in self.Meta.fields}
        # Create the instance without extra fields
        instance = Profile.objects.create(**validated_data)
        return instance
    
    def update(self, instance, validated_data):
        """
        Augments the update function to handle updates to both Profile and related UserModel.
        It extracts fields related to UserModel (like email) and updates them.
        """
        extra_info = {k:v for k, v in validated_data.items() if k not in self.Meta.fields}

        # Update the Profile instance
        instance = super().update(instance, validated_data)
        #Retrieve the user from the profile
        user_instance = instance.user

        # Update the related UserModel fields if provided
        if extra_info:
            for key, value in extra_info.items():
                field_list = [field.name for field in user_instance._meta.get_fields()]
                if key in field_list:
                    setattr(user_instance, key, value)  
            user_instance.save()

        return instance