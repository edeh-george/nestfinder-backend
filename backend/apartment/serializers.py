from rest_framework import serializers
from . models import Apartment
from taggit.serializers import TagListSerializerField
from django.contrib.auth import get_user_model
from django.conf import settings
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
    
    apartments = TagListSerializerField()
    class Meta:
        model = Apartment
        fields = '__all__'

    #This method is used for development purposes only
    if settings.DEBUG:
        def to_representation(self, instance):
            ret = super().to_representation(instance)
            ret['image'] = ret['image'].replace('http://', 'https://')
            return ret

class ApartmentDetailSerializer(serializers.ModelSerializer):
    image_url_list = serializers.SerializerMethodField()
    related_apartments = serializers.SerializerMethodField()
    
    class Meta:
        model = Apartment  
        fields = '__all__'
        
    def get_image_url_list(self, obj):
        request = self.context.get('request')
        if request:
            image_urls = [
                request.build_absolute_uri(image.images.url)
                for image in obj.image_list if image.images
                ]
            
            return image_urls
        
        image_urls = [
            image.images.url for image in obj.image_list if image.image
        ]
    
    def get_related_apartments(self, obj):
        apartment_ids = [str(tag.id) for tag in obj.related_apartment] 
        related_apartment = [ApartmentSerializer(
            Apartment.objects.get(pk=int(id))
            ).data for id in apartment_ids]
        return related_apartment

    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['location'] = location_dict.get(ret['location'])
        user = get_user_model().objects.get(id=ret['uploaded_by'])
        ret['uploaded_by'] = user.username
        ret['uploader_id'] = user.id

        return ret
