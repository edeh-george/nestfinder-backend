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
        related_apartment = getattr(obj, 'related_apartments', [])
        print({'message': related_apartment})
        # return[ 
        #        { "id": apartment.id,
        #           "name": apartment.name,
        #           "price": apartment.price,
        #           "location": apartment.location,
        #           "image": apartment.image,
        #     }
        #         for apartment in related_apartment.all()
               
        # ]
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['location'] = location_dict.get(ret['location'])
        del ret['apartments']
        # return ret