import os
import django
import random
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CargoOperatingSystem.settings')
django.setup()

from admin_panel.models import Location
from user_panel.models import User, Cargo

SCENARIOS = [
    {
        "date": date(2025, 12, 20),
        "data": [
            ("Başiskele", 10, 120),
            ("Çayırova", 8, 80),
            ("Darıca", 15, 200),
            ("Derince", 10, 150),
            ("Dilovası", 12, 180),
            ("Gebze", 5, 70),
            ("Gölcük", 7, 90),
            ("Kandıra", 6, 60),
            ("Karamürsel", 9, 110),
            ("Kartepe", 11, 130),
            ("Körfez", 6, 75),
            ("İzmit", 14, 160),
        ]
    },
    {
        "date": date(2025, 12, 21),
        "data": [
            ("Başiskele", 40, 200),
            ("Çayırova", 35, 175),
            ("Darıca", 10, 150),
            ("Derince", 5, 100),
            ("Dilovası", 0, 0),
            ("Gebze", 8, 120),
            ("Gölcük", 0, 0),
            ("Kandıra", 0, 0),
            ("Karamürsel", 0, 0),
            ("Kartepe", 0, 0),
            ("Körfez", 0, 0),
            ("İzmit", 20, 160),
        ]
    },
    {
        "date": date(2025, 12, 22),
        "data": [
            ("Başiskele", 0, 0),
            ("Çayırova", 4, 700),
            ("Darıca", 0, 0),
            ("Derince", 0, 0),
            ("Dilovası", 4, 800),
            ("Gebze", 5, 900),
            ("Gölcük", 0, 0),
            ("Kandıra", 0, 0),
            ("Karamürsel", 0, 0),
            ("Kartepe", 0, 0),
            ("Körfez", 0, 0),
            ("İzmit", 5, 300),
        ]
    },
    {
        "date": date(2025, 12, 23),
        "data": [
            ("Başiskele", 30, 300),
            ("Çayırova", 0, 0),
            ("Darıca", 0, 0),
            ("Derince", 0, 0),
            ("Dilovası", 0, 0),
            ("Gebze", 0, 0),
            ("Gölcük", 15, 210),
            ("Kandıra", 5, 250),
            ("Karamürsel", 20, 180),
            ("Kartepe", 10, 200),
            ("Körfez", 8, 400),
            ("İzmit", 0, 0),
        ]
    },
]

def add_all_scenarios():
    user, created = User.objects.get_or_create(name="Burak")
    
    print(f"Kullanıcı: {user.name}")
    print("=" * 50)
    
    grand_total = 0
    
    for scenario_idx, scenario in enumerate(SCENARIOS, 1):
        target_date = scenario["date"]
        scenario_data = scenario["data"]
        
        print(f"\n📦 Senaryo {scenario_idx} - {target_date}")
        print("-" * 40)
        
        deleted_count, _ = Cargo.objects.filter(delivery_date=target_date, user=user).delete()
        if deleted_count > 0:
            print(f"  {deleted_count} adet eski kargo kaydı silindi.")
        
        total_cargos = 0
        
        for loc_name, count, total_weight in scenario_data:
            if count == 0:
                continue
                
            try:
                try:
                    location = Location.objects.get(name=loc_name)
                except Location.DoesNotExist:
                    if loc_name == "Cayırova":
                        location = Location.objects.get(name="Çayırova")
                    elif loc_name == "Çayırova":
                        location = Location.objects.get(name="Cayırova")
                    else:
                        raise
                
                avg_weight = total_weight // count
                remainder = total_weight % count
                
                for i in range(count):
                    weight = avg_weight
                    if i < remainder:
                        weight += 1
                    
                    Cargo.objects.create(
                        user=user,
                        destination=location,
                        weight=weight,
                        delivery_date=target_date
                    )
                
                print(f"  ✓ {loc_name}: {count} kargo, {total_weight}kg")
                total_cargos += count
                
            except Location.DoesNotExist:
                print(f"  !!! HATA: {loc_name} veritabanında bulunamadı!")
            except Exception as e:
                print(f"  !!! HATA ({loc_name}): {e}")
        
        print(f"  → Senaryo {scenario_idx}: {total_cargos} kargo eklendi.")
        grand_total += total_cargos
    
    print("\n" + "=" * 50)
    print(f"🎉 Toplam {grand_total} kargo başarıyla eklendi!")

if __name__ == "__main__":
    add_all_scenarios()

