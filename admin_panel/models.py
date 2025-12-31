from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_default = models.BooleanField(default=False)

class Route(models.Model):
    vehicle_name = models.CharField(max_length=100)
    date = models.DateField()
    total_weight = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.DecimalField(max_digits=10, decimal_places=2)
    distance = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    path_data = models.JSONField(default=list)
    color = models.CharField(max_length=20)
    transported_users = models.JSONField(default=list)
    steps = models.JSONField(default=list)
    stops = models.JSONField(default=list)

class RouteCache(models.Model):
    start_lat = models.DecimalField(max_digits=9, decimal_places=6)
    start_lon = models.DecimalField(max_digits=9, decimal_places=6)
    end_lat = models.DecimalField(max_digits=9, decimal_places=6)
    end_lon = models.DecimalField(max_digits=9, decimal_places=6)
    distance = models.DecimalField(max_digits=10, decimal_places=2)
    geometry = models.JSONField(default=list)

    class Meta:
        unique_together = ('start_lat', 'start_lon', 'end_lat', 'end_lon')
        indexes = [
            models.Index(fields=['start_lat', 'start_lon', 'end_lat', 'end_lon']),
        ]


