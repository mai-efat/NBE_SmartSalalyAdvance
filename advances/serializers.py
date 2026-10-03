from datetime import date
from decimal import Decimal
from urllib import request



from rest_framework import serializers
from .models import AdvancePolicy, AdvanceRequest



class AdvanceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvanceRequest
        fields = [
            'advance_id',
            'request_date',
            'requested_amount',
            'reason',
            'status',
        ]
        read_only_fields = ['advance_id', 'request_date', 'status']

class AdvanceRequestHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvanceRequest
        fields = [
            'advance_id',
            'requested_amount',
            'approved_amount',
            'reason',
            'status',
            'request_date',
      
        ]
        read_only_fields = fields