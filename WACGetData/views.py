from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse
from .models import PersonData

import time

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings


@csrf_exempt
def get_message_api(request):
    if request.method == "GET":
        return JsonResponse({"need data": "secret_key, unique_id, image*, caption*  ","Example":"""curl -X POST https://mynewnokiap8.pythonanywhere.com/wac/get_message_api/ -F "secret_key=my_super_secret_key" -F "unique_id=user123" -F "caption=Hello from curl" -F "image=@image.jpg"
"""}, status=405)

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    secret_key = request.POST.get("secret_key")
    unique_id = request.POST.get("unique_id")
    image = request.FILES.get("image")
    caption = request.POST.get("caption")

    # 🔐 Validate secret key
    if secret_key != settings.UPLOAD_SECRET_KEY:
        return JsonResponse({"error": "Invalid secret key"}, status=403)

    # 🔎 Validate unique_id
    if not unique_id:
        return JsonResponse({"error": "unique_id is required"}, status=400)

    # 🧠 Require at least image or caption
    if not image and not caption:
        return JsonResponse(
            {"error": "Either image or caption is required"},
            status=400
        )

    #ToDo
    #process messgae
    # print(request)
    # print("------ NEW REQUEST RECEIVED ------")
    # print("Method:", request.method)
    # print("Headers:", dict(request.headers))
    # print("POST Data:", request.POST)
    # print("FILES:", request.FILES)


    return JsonResponse({"still in progress":"please wait 13/02/2026"}, status=201)












































def get_data_mobile(request, pid, cal=0, mode=""):



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
        rsp="okk"
        #response.message(f"{u_data[0]},len(u_data)")
        if len(u_data) > 1:
            rsp = get_data_mobile(request, u_data[0], int(u_data[1]), mode="")
        else:
            rsp = get_data_mobile(request, u_data[0], 0, mode="")

        # For demonstration, we'll just echo the user's message
        # Note: Using eval() is dangerous and not recommended in production
        response.message(f"{str(rsp)}")

        print(str(response),f"--->{str(rsp)}<---")
        return HttpResponse(str(response), content_type='text/xml')



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
