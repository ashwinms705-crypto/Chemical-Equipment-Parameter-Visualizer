from rest_framework import serializers
from .models import EquipmentData

class EquipmentDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentData
        fields = '__all__'
