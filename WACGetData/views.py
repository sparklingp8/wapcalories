from django.http import HttpResponse
from django.http import JsonResponse
from openai import OpenAI
import os
import json
from django.views.decorators.csrf import csrf_exempt
from .models import UserProfile, DailyEntry
import time, datetime
from django.http import JsonResponse
from django.conf import settings
from datetime import date, time
from django.utils import timezone

@csrf_exempt
def get_message_api(request):
    if request.method == "GET":
        return JsonResponse({"need data": "secret_key, unique_id, image*, caption*  ","Example":"""curl -X POST https://mynewnokiap8.pythonanywhere.com/wac/get_message_api/ -F "secret_key=my_super_secret_key" -F "unique_id=user123" -F "caption=Hello from curl" -F "image=@image.jpg"
"""}, status=400)

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    secret_key = request.POST.get("secret_key")
    unique_id = request.POST.get("unique_id")
    image = request.FILES.get("image")
    caption = request.POST.get("caption")

    # caption = "stats"
    if caption == "stats":
        individual_entries = DailyEntry.objects.filter(
        user__user_id=7,
        date=timezone.localdate()
    ).values("value1", "value2", "value3")
        data_list = [(e['value1'], e['value2'], e['value3']) for e in individual_entries]
        total_v1, total_v2, total_v3 = [sum(x) for x in zip(*data_list)] if data_list else (0, 0, 0)
        print(data_list)

        return JsonResponse({"Today you ate food you just ate":f"protien-{total_v1}, fat-{total_v2}, carbs-{total_v3}"}, status=201)

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
    print("data123",request)
    # print("------ NEW REQUEST RECEIVED ------")
    # print("Method:", request.method)
    # print("Headers:", dict(request.headers))
    # print("POST Data:", request.POST)
    # print("FILES:", request.FILES)

    x=chat_with_gpt("ate 3 chapatis with cheicken curry")
    try:
        x=eval(x)
    except:
        print("error converting gpt reply")
    user = UserProfile.objects.get(user_id=7)
    


    entry = DailyEntry.objects.create(
        date=timezone.localdate(),
        user=user,
        time=timezone.localtime().time(),
        value1=float(x[0]),   # protein
        value2=float(x[1]),   # carbs
        value3=float(x[2])      # fat
    )

    return JsonResponse({"food you just ate":f"protien-{x[0]}, fat-{x[1]}, carbs-{x[2]}"}, status=201)


def add_user(request):
    user = UserProfile.objects.create(
        user_id=9999,
        name="Test User",
        gender="M",
        dob=datetime.strptime("1999-01-01", "%Y-%m-%d")
    )

    return JsonResponse({"message": "User added"})
def get_msg(request):
    return HttpResponse("hello")


def add_daily_entry(user_id, entry_date, entry_time, v1, v2, v3):
    user = UserProfile.objects.get(user_id=user_id)

    entry = DailyEntry.objects.create(
        user=user,
        date=entry_date,
        time=entry_time,
        value1=v1,
        value2=v2,
        value3=v3
    )

    return entry


client = OpenAI(api_key=settings.CHAT_API_KEY)

def chat_with_gpt(message):
    
    try:            
        user_message = message
        print("called, gpt", user_message)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": """
                        Act as a Nutrition Assistant: Analyze the text to provide total Protein, Carbs, and Fat of all food items in grams as tuple nothing else (p,c,f)
                        If no food data is found, output "(-1,-1,-1)";                   

                    """},
                {"role": "user", "content": user_message}
            ]
        )

        reply = response.choices[0].message.content
        print("cgat gpt reply", reply)

        return reply

    except Exception as e:
        print("error, gpt", user_message,e)
        return JsonResponse({"error": str(e)}, status=500)

