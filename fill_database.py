import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CargoOperatingSystem.settings')
django.setup()

from admin_panel.models import Location
from user_panel.models import User

locations_data = [
    {"name": "Başiskele", "latitude": 40.713049, "longitude": 29.932389, "is_default": True},
    {"name": "Cayırova", "latitude": 40.815152, "longitude": 29.371901, "is_default": True},
    {"name": "Darıca", "latitude": 40.762207, "longitude": 29.385636, "is_default": True},
    {"name": "Derince", "latitude": 40.757677, "longitude": 29.829160, "is_default": True},
    {"name": "Dilovası", "latitude": 40.786525, "longitude": 29.536233, "is_default": True},
    {"name": "Gebze", "latitude": 40.800433, "longitude": 29.432090, "is_default": True},
    {"name": "Gölcük", "latitude": 40.720164, "longitude": 29.821072, "is_default": True},
    {"name": "Kandıra", "latitude": 41.069727, "longitude": 30.152697, "is_default": True},
    {"name": "Karamürsel", "latitude": 40.693157, "longitude": 29.615707, "is_default": True},
    {"name": "Kartepe", "latitude": 40.751832, "longitude": 30.022816, "is_default": True},
    {"name": "Körfez", "latitude": 40.762696, "longitude": 29.786856, "is_default": True},
    {"name": "İzmit", "latitude": 40.764373, "longitude": 29.934470, "is_default": True},
    {"name": "Kocaeli Üniversitesi", "latitude": 40.823537, "longitude": 29.925393, "is_default": True},
]

for loc_data in locations_data:
    location, created = Location.objects.get_or_create(
        name=loc_data["name"],
        defaults={
            "latitude": loc_data["latitude"],
            "longitude": loc_data["longitude"],
            "is_default": loc_data.get("is_default", False)
        }
    )
    if created:
        print(f"✓ {location.name} eklendi - ({location.latitude}, {location.longitude})")
    else:
        print(f"- {location.name} zaten mevcut")

print(f"\nToplam {Location.objects.count()} konum veritabanında.")

users_data = [
    {"name": "Burak"},
    {"name": "Mustafa"},
    {"name": "Emre"},
    {"name": "Uğur"},
]

for user_data in users_data:
    user, created = User.objects.get_or_create(
        name=user_data["name"]
    )
    if created:
        print(f"✓ {user.name} eklendi")
    else:
        print(f"- {user.name} zaten mevcut")

print(f"\nToplam {User.objects.count()} kullanıcı veritabanında.")

