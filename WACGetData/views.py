from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse
from .models import PersonData

import time


def get_data_mobile(request, pid, cal=0, mode=""):
    cal = 0
    mode = ""
    pid = int(pid)
    cal = int(cal)
    s = "whatt..?"
    person_id = pid
    data = PersonData.objects.filter(person_id=pid).first()
    if data:
        if cal != 0:
            msg = data.add_data(int(cal))
            print(f"calorie data is {cal} {data.cal_data} of person_id {data.person_id}.")
            s = f"{msg}\ncalorie data is {cal} {data.cal_data} of person_id {data.person_id}."
        else:
            print(f"data is {data.cal_data} of person_id {data.person_id}.")
            s = f"data is {data.cal_data} of person_id {data.person_id}."
    else:
        print(f"Person with ID {person_id} does not Exist.")
        s = f"Person with ID {person_id} does not Exist."
    if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return s
    else:
        return s


def add_get_cal_data(request, pid, cal=0):
    person_id = pid
    s = "what"
    data = PersonData.objects.filter(person_id=pid).first()

    if data:
        if cal != 0:
            msg = data.add_data(int(cal))
            print(f"calorie data is {cal} {data.cal_data} of person_id {data.person_id}.")
            s = f"{msg}\ncalorie data is {cal} {data.cal_data} of person_id {data.person_id}."
        else:
            print(f"data is {data.cal_data} of person_id {data.person_id}.")
            s = f"data is {data.cal_data} of person_id {data.person_id}."
    else:
        print(f"Person with ID {person_id} does not Exist.")
        s = f"Person with ID {person_id} does not Exist."
    return HttpResponse(s)


@csrf_exempt
def bot(request):
    if request.method in ["POST"]:
        # User input
        user_msg = request.POST.get('Body', '').lower()

        # Creating object of MessagingResponse
        response = MessagingResponse()

        u_data = str(user_msg).split(",")
        #response.message(f"{u_data[0]},len(u_data)")
        if len(u_data) > 1:
            rsp = get_data_mobile(request, u_data[0], u_data[1], mode="")
        else:
            rsp = get_data_mobile(request, u_data[0], 0, mode="")

        # For demonstration, we'll just echo the user's message
        # Note: Using eval() is dangerous and not recommended in production
        response.message(f"{str(rsp)}")

        print(str(rsp),"rsppp")
        return HttpResponse(str(rsp), content_type='text/xml')


# Create your views here.
def get_msg(request):
    return HttpResponse("hello")


def add_user(request, uid):
    data = PersonData.objects.filter(person_id=uid).first()

    if data:
        print(f"Person with ID {uid} Already Exists.")
        s = f"Person with ID {uid} Already Exists."
    else:
        data = PersonData(
            person_id=uid,
            cal_data={}
        )
        data.save()
        print(f"Person with ID {uid} added to dataBase.")
        s = f"Person with ID {uid} added to dataBase."
    return HttpResponse(s)
