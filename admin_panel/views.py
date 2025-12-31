from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.utils import timezone
from .models import Location
from admin_panel.helper import *


def admin_map_view(request):
    active_panel = request.GET.get('panel', 'locations')
    data = {}
    
    match active_panel:
        case 'locations':
            if request.method == 'POST':
                delete_id = request.POST.get('delete_id')

                if delete_id:
                    msg = delete_location(delete_id)
                    data['success_msg'] = msg
                else:
                    name = request.POST.get('name')
                    latitude = request.POST.get('latitude')
                    longitude = request.POST.get('longitude')
                    
                    msg = create_location(name, latitude, longitude)
                    data['success_msg'] = msg
            
            data['active_panel'] = active_panel
            data['locations'] = Location.objects.all()
        case 'cargos':
            selected_date = request.GET.get('date')
            
            if not selected_date:
                selected_date = timezone.now().date().strftime('%Y-%m-%d')
                
            locations = Location.objects.annotate(
                cargo_count=Count('cargo', filter=Q(cargo__delivery_date=selected_date)),
                total_weight=Sum('cargo__weight', filter=Q(cargo__delivery_date=selected_date))
            )

            data['locations'] = locations
            data['active_panel'] = active_panel
            data['selected_date'] = selected_date
        case 'create_route':
            selected_date = request.GET.get('date')

            if not selected_date:
                selected_date = timezone.now().date().strftime('%Y-%m-%d')

            if request.method == 'POST':
                rental_capacity = int(request.POST.get('rental_capacity') or 500)
                rental_cost = int(request.POST.get('rental_cost') or 200)
                v1_capacity = int(request.POST.get('v1_capacity') or 500)
                v2_capacity = int(request.POST.get('v2_capacity') or 750)
                v3_capacity = int(request.POST.get('v3_capacity') or 1000)
                
                routes = calculate_routes(selected_date, rental_capacity, rental_cost, v1_capacity, v2_capacity, v3_capacity)
                data['routes'] = routes

            locations = Location.objects.annotate(
                cargo_count=Count('cargo', filter=Q(cargo__delivery_date=selected_date)),
                total_weight=Sum('cargo__weight', filter=Q(cargo__delivery_date=selected_date))
            )
            
            data['active_panel'] = active_panel
            data['locations'] = locations
            data['selected_date'] = selected_date
         
    return render(request, 'admin_panel/admin_map.html', data)
