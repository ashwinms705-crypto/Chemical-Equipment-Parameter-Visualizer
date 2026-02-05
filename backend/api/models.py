from django.db import models

class EquipmentData(models.Model):
    upload_date = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    total_count = models.IntegerField()
    avg_flowrate = models.FloatField()
    avg_pressure = models.FloatField()
    avg_temperature = models.FloatField()
    equipment_distribution = models.JSONField()

    def __str__(self):
        return f"{self.filename} - {self.upload_date}"
