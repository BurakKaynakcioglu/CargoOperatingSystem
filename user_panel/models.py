from django.db import models
from admin_panel.models import Location

class User(models.Model):
    name = models.CharField(max_length=100)
    
class Cargo(models.Model):
    delivery_date = models.DateField()
    destination = models.ForeignKey(Location, on_delete=models.CASCADE)
    weight = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)



