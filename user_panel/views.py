from django.shortcuts import render, redirect
from admin_panel.models import Location, Route
from .models import Cargo, User
from .helper import create_cargos
import json

def login_view(request):
    error_msg = None
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            return redirect('user_panel:locations_map', user_id=user_id)
        else:
            error_msg = 'Lütfen bir kullanıcı seçiniz'
    
    users = User.objects.all()
    
    return render(request, 'user_panel/login.html', {
        'users': users,
        'error_msg': error_msg
    })

def locations_map(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('user_panel:login')
    
    success_msg = None
    error_msg = None
    
    if request.method == 'POST':
        if 'delete_id' in request.POST:
            try:
                delete_id = request.POST.get('delete_id')
                cargo = Cargo.objects.get(id=delete_id, user=user)
                cargo.delete()
                success_msg = 'Kargo başarıyla silindi.'
            except Cargo.DoesNotExist:
                error_msg = 'Kargo bulunamadı veya silme yetkiniz yok.'
            except Exception as e:
                error_msg = f'Hata oluştu: {str(e)}'
        else:
            try:
                delivery_date = request.POST.get('deliveryDate')
                cargos_json = request.POST.get('cargos')
                cargos = json.loads(cargos_json)
                
                success_msg = create_cargos(cargos, delivery_date, user)
            except Exception as e:
                error_msg = f'Hata oluştu: {str(e)}'
    
    locations = Location.objects.all()
    my_cargos = Cargo.objects.filter(user=user).order_by('-delivery_date')
    
    my_cargos_json = []
    for cargo in my_cargos:
        my_cargos_json.append({
            'id': cargo.id,
            'date': cargo.delivery_date.strftime('%Y-%m-%d'),
            'destination_name': cargo.destination.name,
            'lat': float(cargo.destination.latitude),
            'lon': float(cargo.destination.longitude),
            'weight': cargo.weight
        })
    
    #userin bulundugu rotaları filtrele
    all_routes = Route.objects.all()
    my_routes_objs = [r for r in all_routes if user.id in r.transported_users]
    
    my_routes = []
    for route in my_routes_objs:
        #userın ilgili tarih için kargo duraklarını bul
        user_destinations = set()
        for cargo in my_cargos:
            if cargo.delivery_date == route.date:
                user_destinations.add(cargo.destination.name)

        #userın kargo duraklarını işaretle
        processed_steps = []
        for step in route.steps:
            step_copy = step.copy()
            if step['to_name'] in user_destinations:
                step_copy['is_my_stop'] = True
            processed_steps.append(step_copy)

        my_routes.append({
            'id': route.id,
            'vehicle_name': route.vehicle_name,
            'path_data': route.path_data,
            'color': route.color,
            'distance': float(route.distance),
            'cost': float(route.cost),
            'steps': processed_steps,
            'date': route.date.strftime('%Y-%m-%d')
        })
    
    return render(request, 'user_panel/locations_map.html', {
        'locations': locations,
        'user': user,
        'my_cargos': my_cargos,
        'my_cargos_json': my_cargos_json,
        'my_routes': my_routes,
        'success_msg': success_msg,
        'error_msg': error_msg
    })
