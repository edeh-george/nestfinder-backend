from rest_framework import serializers
from . models import Apartment, ApartmentImage

#To reduce load media files are added in the gitignore, you should consider storing links to the images instead



class ApartmentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Apartment
        # fields = '__all__'
        exclude = ['image']
    

class ApartmentDetailSerializer(serializers.ModelSerializer):
    apartment_id = serializers.SerializerMethodField()
    image_url_list = serializers.SerializerMethodField()
    
    class Meta:
        model = ApartmentImage  
        fields = ['apartment_id', 'image_url_list']
        
    def get_apartment_id(self, obj):
        return obj.id 
    
    def get_image_url_list(self, obj):
        request = self.context.get('request')
        image_urls = [
            request.build_absolute_uri(image.images.url)
            for image in obj.image_list if image.images
            ]
        
        return image_urls
        
        
class ApartmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apartment
        fields = '__all__'