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
            'target_time': '2027-03-07 11:46:46'
        },
        {
            'event_name': 'Mid',
            'target_time': '2040-02-07 23:56:00'
        },
        {
            'event_name': 'Life',
            'target_time': '2067-02-07 23:56:00'
        },
        {
            'event_name': 'Python Master',
            'target_time': '2025-02-26 23:58:02'
        },
        # {
        #     'event_name': 'USA',
        #     'target_time': '2025-02-26 23:58:00'
        # },
    ]

    # Sort the timers list by 'target_time' after converting the string to a datetime object
    timers_sorted = sorted(timers, key=lambda x: datetime.strptime(x['target_time'], '%Y-%m-%d %H:%M:%S'))

    # Prepare the context
    context = {
        'timers': timers_sorted,
        'timers_json': json.dumps(timers_sorted)  # Pass JSON-serialized data to the template
    }

    return render(request, 'timeCounter/time.html', context)
