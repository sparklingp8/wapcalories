from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
import time
from datetime import datetime, timedelta
import json

def getAge(request):
    timers = [
        {
            'event_name': 'Dreams',
            'target_time': '2025-06-06 19:43:46'
        },
        {
            'event_name': 'Life',
            'target_time': '2060-01-01 00:00:00'
        }
    ]

    context = {
        'timers': timers,
        'timers_json': json.dumps(timers)  # Pass JSON-serialized data to the template
    }

    return render(request, 'timeCounter/time.html', context)
