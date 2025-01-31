# route_planner/models.py
from django.db import models

class FuelStation(models.Model):
    name = str
    latitude = models.FloatField()
    longitude = models.FloatField()
    price = models.FloatField()

    class Meta:
        db_table = 'fuel_stations'
