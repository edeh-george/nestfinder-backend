import json
from backend.userauth.models import UserModel 
from backend.apartment.models import Apartment

import os


apartment_data = json.load('apartments_data_new.json')
apartmentCreate =  []
try:
    for apartment in range(len(apartment_data)):
        
        apartment = Apartment(
            id=apartment.id,
            name="Chukwuebuka Lodge",
            apartment_type=apartment.apartment_type,
            description=apartment.description,
            price=apartment.price,
            location=apartment.location,
            is_leased=apartment.is_leased,
            created=apartment.created,  # Current time
            modified=apartment.modified,
            uploaded_by = apartment.uploaded_by 
        )
        
        apartmentCreate.append(apartment)

    Apartment.objects.bulk_create(apartmentCreate)
except Exception as e:
    print(e)

print(f'{len(apartment_data)} apartments created successfully!')

