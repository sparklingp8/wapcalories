from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
import time
from datetime import datetime, timedelta


def getAge(request):
    theTime = datetime(2030, 11, 8)
    theTime = datetime.now() + timedelta(minutes=1)
    print(theTime)
    important_dates = [
    {"date": "2070-03-07", "label": "Last"},
    {"date": "2030-03-07", "label": "Dream"},
    # Add more dates as needed
]

    return render(request, "timeCounter/time.html", {"important_dates":important_dates})
