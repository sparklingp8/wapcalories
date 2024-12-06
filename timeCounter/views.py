from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
import time
def getAge(request):
    theTime = time.strftime("%d/%m/%Y %H:%M:%S")

    return render(request, "timeCounter/time.html", {"theTime":theTime})
