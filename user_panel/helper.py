from admin_panel.models import Location
from .models import Cargo

def create_cargos(cargos_data, delivery_date, user):
    saved_count = 0
    for cargo_data in cargos_data:
        weight = cargo_data.get('weight')
        destination_id = cargo_data.get('destination_id')
        
        try:
            location = Location.objects.get(id=destination_id)
            Cargo.objects.create(
                delivery_date=delivery_date,
                destination=location,
                weight=weight,
                user=user
            )
            saved_count += 1
        except Location.DoesNotExist:
            continue
            
    return f'{saved_count} kargo başarıyla kaydedildi!'
