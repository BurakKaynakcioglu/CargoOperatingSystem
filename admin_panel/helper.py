from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q
import math
import requests
from admin_panel.models import Location, Route, RouteCache

def get_osrm_route(lat1, lon1, lat2, lon2):
    """
    OSRM API kullanarak iki nokta arasındaki gerçek yol verisini çeker.
    Önce veritabanı önbelleğine bakar.
    """
    lat1 = round(float(lat1), 6)
    lon1 = round(float(lon1), 6)
    lat2 = round(float(lat2), 6)
    lon2 = round(float(lon2), 6)

    cached = RouteCache.objects.filter(
        start_lat=lat1, start_lon=lon1,
        end_lat=lat2, end_lon=lon2
    ).first()

    if cached:
        return float(cached.distance), cached.geometry

    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 'Ok' and data['routes']:
                route = data['routes'][0]
                distance_km = route['distance'] / 1000
                geometry = [[coord[1], coord[0]] for coord in route['geometry']['coordinates']]
                
                RouteCache.objects.create(
                    start_lat=lat1, start_lon=lon1,
                    end_lat=lat2, end_lon=lon2,
                    distance=distance_km,
                    geometry=geometry
                )
                
                return distance_km, geometry
    except Exception as e:
        print(f"OSRM Error: {e}")
    
    return 0, [[lat1, lon1], [lat2, lon2]]

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def get_color(index):
    colors = ['#FF0000', '#0000FF', '#008000', '#FFA500', '#800080', '#00FFFF', '#FF00FF', '#808000', '#008080', '#A52A2A']
    return colors[index % len(colors)]

def calculate_routes(selected_date, rental_capacity=500, rental_cost=200, v1_capacity=500, v2_capacity=750, v3_capacity=1000):
    try:
        depot = Location.objects.get(name="Kocaeli Üniversitesi")
    except Location.DoesNotExist:
        depot = Location.objects.first() 

    locations = Location.objects.annotate(
        total_weight=Sum('cargo__weight', filter=Q(cargo__delivery_date=selected_date)),
        cargo_count=Count('cargo', filter=Q(cargo__delivery_date=selected_date))
    ).filter(total_weight__gt=0)
    
    stops = []
    for loc in locations:
        #userid leri topla bu konumdaki ve tarihteki kargolar için
        current_cargos = loc.cargo_set.filter(delivery_date=selected_date)
        user_ids = list(current_cargos.values_list('user_id', flat=True).distinct())
        
        stops.append({
            'id': loc.id,
            'name': loc.name,
            'lat': float(loc.latitude),
            'lon': float(loc.longitude),
            'weight': loc.total_weight,
            'count': loc.cargo_count,
            'user_ids': user_ids
        })
        
    if not stops:
        return []

    fleet = [
        {'name': f'Araç 3 ({v3_capacity}kg)', 'capacity': v3_capacity, 'cost': 0, 'type': 'owned'},
        {'name': f'Araç 2 ({v2_capacity}kg)', 'capacity': v2_capacity, 'cost': 0, 'type': 'owned'},
        {'name': f'Araç 1 ({v1_capacity}kg)', 'capacity': v1_capacity, 'cost': 0, 'type': 'owned'},
    ]
    
    fleet.sort(key=lambda x: x['capacity'], reverse=True)
    
    routes = []
    unvisited = stops.copy()
    
    def find_nearest(current_node, candidates):
        nearest = None
        min_dist = float('inf')
        for node in candidates:
            #gerçek mesafe için OSRM kullanıldı
            dist, _ = get_osrm_route(current_node['lat'], current_node['lon'], node['lat'], node['lon'])
            if dist < min_dist:
                min_dist = dist
                nearest = node
        return nearest, min_dist

    def find_furthest_from_depot(candidates):
        furthest = None
        max_dist = -1
        for node in candidates:
            dist = haversine_distance(float(depot.latitude), float(depot.longitude), node['lat'], node['lon'])
            if dist > max_dist:
                max_dist = dist
                furthest = node
        return furthest

    vehicle_idx = 0
    
    #tüm noktaların depoya göre açısını hesapla ve sırala
    def get_angle(node):
        return math.atan2(node['lat'] - float(depot.latitude), node['lon'] - float(depot.longitude))
    
    unvisited.sort(key=get_angle)
    
    #noktaları sırayla araçlara dağıt
    clusters = []
    temp_unvisited = unvisited.copy()
    
    while temp_unvisited:
        if vehicle_idx < len(fleet):
            current_vehicle = fleet[vehicle_idx]
            vehicle_idx += 1
        else:
            current_vehicle = {'name': f'Kiralık Araç {vehicle_idx - 2}', 'capacity': rental_capacity, 'cost': rental_cost, 'type': 'rented'}
            vehicle_idx += 1
            
        cluster_stops = []
        remaining_cap = current_vehicle['capacity']
        
        #sıralı listeden kapasite dolana kadar al
        while temp_unvisited and remaining_cap > 0:
            candidate = temp_unvisited[0]
            
            if candidate['weight'] <= remaining_cap:
                cluster_stops.append(candidate)
                remaining_cap -= candidate['weight']
                temp_unvisited.pop(0)
            else:
                #parçalı yük durumu
                take_weight = remaining_cap
                partial_stop = candidate.copy()
                partial_stop['weight'] = take_weight
                partial_stop['note'] = '(Parçalı)'
                
                cluster_stops.append(partial_stop)
                
                #orijinal listedeki yükü güncelle
                temp_unvisited[0]['weight'] -= take_weight
                remaining_cap = 0
        
        if cluster_stops:
            clusters.append({'vehicle': current_vehicle, 'stops': cluster_stops})

    #her cluster için rota optimizasyonu yap
    for cluster in clusters:
        current_vehicle = cluster['vehicle']
        cluster_nodes = cluster['stops']
        
        route_stops = []
        route_weight = sum(n['weight'] for n in cluster_nodes)
        
        #cluster içindeki optimizasyon (Nearest Neighbor)
        local_unvisited = cluster_nodes.copy()
        
        #başlangıç için cluster içindeki depoya en uzak noktayı bul
        start_node = find_furthest_from_depot(local_unvisited)
        if start_node:
            route_stops.append(start_node)
            local_unvisited.remove(start_node)
            current_pos = start_node
            
            while local_unvisited:
                nearest, _ = find_nearest(current_pos, local_unvisited)
                if nearest:
                    route_stops.append(nearest)
                    local_unvisited.remove(nearest)
                    current_pos = nearest
                else:
                    break
        
        #rota hesaplama osrm ile
        if route_stops:
            dist = 0
            steps = []
            path_coords = []
            
            #ilk Durak
            first_stop = route_stops[0]
            
            steps.append({
                'from_name': 'Başlangıç',
                'to_name': first_stop['name'],
                'distance': 0,
                'cargo_weight': first_stop['weight'],
                'cargo_count': first_stop['count'],
                'user_ids': first_stop.get('user_ids', [])
            })
            
            prev = first_stop
            
            #ara duraklar
            for stop in route_stops[1:]:
                segment_dist, segment_path = get_osrm_route(prev['lat'], prev['lon'], stop['lat'], stop['lon'])
                dist += segment_dist
                if segment_path:
                    path_coords.extend(segment_path)
                
                steps.append({
                    'from_name': prev['name'],
                    'to_name': stop['name'],
                    'distance': round(segment_dist, 2),
                    'cargo_weight': stop['weight'],
                    'cargo_count': stop['count'],
                    'user_ids': stop.get('user_ids', [])
                })
                prev = stop
                
            #dönüş (kocaeli üniye)
            segment_dist, segment_path = get_osrm_route(prev['lat'], prev['lon'], float(depot.latitude), float(depot.longitude))
            dist += segment_dist
            if segment_path:
                path_coords.extend(segment_path)
            
            steps.append({
                'from_name': prev['name'],
                'to_name': depot.name,
                'distance': round(segment_dist, 2),
                'cargo_weight': 0,
                'cargo_count': 0
            })
            
            #bu rota içindeki tüm user id lerini topla
            route_user_ids = set()
            for stop in route_stops:
                if 'user_ids' in stop:
                    route_user_ids.update(stop['user_ids'])

            routes.append({
                'vehicle': current_vehicle['name'],
                'stops': route_stops,
                'steps': steps,
                'total_weight': route_weight,
                'capacity': current_vehicle['capacity'],
                'distance': round(dist, 2),
                'cost': round(dist * 1 + current_vehicle['cost'], 2),
                'path': path_coords,
                'color': get_color(len(routes)),
                'transported_users': list(sorted(route_user_ids))
            })

    Route.objects.filter(date=selected_date).delete()
    
    for r in routes:
        Route.objects.create(
            vehicle_name=r['vehicle'],
            date=selected_date,
            total_weight=r['total_weight'],
            capacity=r['capacity'],
            distance=r['distance'],
            cost=r['cost'],
            path_data=r['path'],
            color=r['color'],
            transported_users=r['transported_users'],
            steps=r['steps'],
            stops=r['stops']
        )

    return routes

def delete_location(delete_id):
    try:
        location = get_object_or_404(Location, id=delete_id)
        name = location.name
        location.delete()
        success_msg = f'{name} silindi.'
    except Exception as e:
        print(f"Error deleting location: {e}")
        success_msg = None
    
    return success_msg

def create_location(name, latitude, longitude):
    try:
        if name and latitude and longitude:
            Location.objects.create(
                name=name,
                latitude=latitude,
                longitude=longitude
            )
            success_msg = f'{name} başarıyla eklendi.'
    except Exception as e:
        print(f"Error adding location: {e}")
        success_msg = None
        
    return success_msg