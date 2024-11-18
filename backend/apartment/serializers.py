from rest_framework import serializers
from . models import Apartment, ApartmentImage

#To reduce load media files are added in the gitignore, you should consider storing links to the images instead
LOCATION = [
    ('ODI', 'Odim'),
    ('ODE', 'Odenigwe'),
    ('BF', 'Behind Flat'),
    ('GH', 'Green House'),
    ('HT', 'Hilltop'),
    ('SQ', 'Staff Quarters')
]
location_dict =  dict(LOCATION)

class ApartmentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Apartment
        fields = '__all__'
    

class ApartmentDetailSerializer(serializers.ModelSerializer):
    image_url_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Apartment  
        fields = '__all__'
        
    def get_apartment_id(self, obj):
        return obj.id 
    
    def get_image_url_list(self, obj):
        request = self.context.get('request')
        image_urls = [
            request.build_absolute_uri(image.images.url)
            for image in obj.image_list if image.images
            ]
        
        return image_urls
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['location'] = location_dict.get(ret['location'])
        return ret