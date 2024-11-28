from rest_framework import serializers
from .models import Review
from userprofile.serializers import UserProfileSerializer
from django.contrib.auth import get_user_model
from datetime import datetime

class ReviewSerializer(serializers.ModelSerializer):

    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ['comment', 'rating', 'user', 'apartment',
                  'is_active', 'is_liked', 'created', 'profile']
    
    def get_profile(self, obj):
        request = self.context.get('request')
        data = UserProfileSerializer(obj.user.user_profile).data
        data['profile_picture'] = request.build_absolute_uri(
            data['profile_picture']
        )
        user =  get_user_model().objects.get(id=data['user'])
        data['user'] = ' '.join([user.first_name, user.last_name]) if user.first_name else user.username
        return data
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['created'] = datetime.fromisoformat(ret['created'].rstrip("Z")).date()
        return ret
        