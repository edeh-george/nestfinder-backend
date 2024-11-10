from rest_framework import serializers
from . models import Apartment, ApartmentImage


class ApartmentSerializer(serializers.ModelSerializer):
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Apartment
        fields = ['name', 'apartment_type', 'description', \
            'image', 'price', 'location', 'is_leased',\
                'created', 'modified', 'image_url']
        
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
    

class ApartmentDetailSerializer(serializers.ModelField):
    apartment_id = serializers.SerializerMethodField()
    image_url_list = serializers.SerializerMethodField()
    
    class Meta:
        model = ApartmentImage
        fields = ['apartment_id', 'image_url_list']
        
    def get_apartment_id(self, obj):
        return obj.apartment.id 
    
    def get_image_url_list(self, obj):
        image_urls = [image.images.url for image in obj.image_list if image.images]
        
        return image_urls
        