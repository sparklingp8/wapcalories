from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse
from .models import PersonData  # Replace 'myapp' with your actual app name

import time

def get_data_mobile(pid, cal=0, mode=""):
    pid=int(pid)
    cal=int(cal)
    if mode == "" or mode == "see_data":
        person_id = pid
        s = "what"
        data = PersonData.objects.filter(person_id=pid).first()
        if data:
            if cal != 0:
                today_date = time.strftime('%d/%m/%Y')
                data.add_data(int(cal))  # Make sure this method exists in your model
                print(f"calorie data is {cal} {data.cal_data} of person_id {data.person_id}.")
                s = f"calorie data is {cal} {data.cal_data} of person_id {data.person_id}."
            else:
                print(f"data is {data.cal_data} of person_id {data.person_id}.")
                s = f"data is {data.cal_data} of person_id {data.person_id}."
        else:
            # Handle the case where the person_id does not exist
            data = PersonData(
                person_id=pid,
                cal_data={}
            )
            data.save()
            print(f"Person with ID {person_id} added to dataBase.")
            s = f"Person with ID {pid} added to dataBase."

    return s
def get_data(request, pid, cal=0):
    person_id = pid
    s = "what"
    data = PersonData.objects.filter(person_id=pid).first()

    if data:
        if cal != 0:
            today_date = time.strftime('%d/%m/%Y')
            data.add_data(int(cal))  # Make sure this method exists in your model
            print(f"calorie data is {cal} {data.cal_data} of person_id {data.person_id}.")
            s = f"calorie data is {cal} {data.cal_data} of person_id {data.person_id}."
        else:
            print(f"data is {data.cal_data} of person_id {data.person_id}.")
            s = f"data is {data.cal_data} of person_id {data.person_id}."
    else:
        # Handle the case where the person_id does not exist
        data = PersonData(
            person_id=pid,
            cal_data={}
        )
        data.save()
        print(f"Person with ID {person_id} added to dataBase.")
        s = f"Person with ID {pid} added to dataBase."

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
        if len(u_data) >1:
          rsp=get_data_mobile(u_data[0], u_data[1], mode="")
        else:
            rsp=get_data_mobile(u_data[0], 0, mode="")

        # For demonstration, we'll just echo the user's message
        # Note: Using eval() is dangerous and not recommended in production
        response.message(f"{str(rsp)}")

        print(str(response))
        return HttpResponse(str(response), content_type='text/xml')
# Create your views here.
def get_msg(request):
    return HttpResponse("hello")