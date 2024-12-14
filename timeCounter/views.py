from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from .models import Event
# Create your views here.
import time
from datetime import datetime, timedelta
import json

def addUser(userID):
    return "hi"



def user_countdown(request, userID):
    user_id = userID#"ptk"
    user_data = Event.objects.filter(creator_id = user_id).first()
    #print(creator_data, "dataaaa")
    eve_name = 'Mid'
    eve_time = '2040-02-07 23:56:00'
    if user_data:
        eves = set()
        if len(user_data.data['events']) > 10:
            return HttpResponse("many Events")
        for e in user_data.data['events']:
            eves.add(e['event_name'])
        print(eves, "evesssssss")
        if eve_name not in eves:
            user_data.data["events"].append({
                 'event_name': eve_name,
                 'target_time': eve_time
            })
            user_data.save()
            print(eve_name, "added to database")
        else:
            print(eve_name, "already exists")
    else:
        return HttpResponse(f"{userID}: doesn't exisits in Database, New user adding page coming soon .....")
        user_data = addUser(userID)
        
    print(Event.objects.all(), all)
    timers = user_data.data["events"]
    # Sort the timers list by 'target_time' after converting the string to a datetime object
    timers_sorted = sorted(timers, key=lambda x: datetime.strptime(x['target_time'], '%Y-%m-%d %H:%M:%S'))

    # Prepare the context
    context = {
        'timers': timers_sorted,
        'timers_json': json.dumps(timers_sorted)  # Pass JSON-serialized data to the template
    }
    return render(request, 'timeCounter/time.html', context)


def tryy(request):
    return HttpResponse("hi")

def getAge(request):
    # event.save()
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
        {
            'event_name': 'USA',
            'target_time': '2026-07-04 00:04:08'
        },
    ]
    
    # Sort the timers list by 'target_time' after converting the string to a datetime object
    timers_sorted = sorted(timers, key=lambda x: datetime.strptime(x['target_time'], '%Y-%m-%d %H:%M:%S'))

    # Prepare the context
    context = {
        'timers': timers_sorted,
        'timers_json': json.dumps(timers_sorted)  # Pass JSON-serialized data to the template
    }

    if request.method == 'POST':
        print(request.body)
        return JsonResponse({
            'status': 'success', 
            'message': 'Event created successfully',
            'event_id': 1
        })

    return render(request, 'timeCounter/time.html', context)
