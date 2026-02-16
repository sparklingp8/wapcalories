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


    if "delete" in caption.lower():
        deleted = delete_last_record(user_id=7)

        if deleted:
            return JsonResponse({
                "message": (
                    "🗑️ Last food entry deleted successfully.\n\n"
                    "Your latest record has been removed."
                )
            }, status=200)

        else:
            return JsonResponse({
                "message": (
                    "⚠️ No recent food entry found to delete."
                )
            }, status=200)



    # caption = "stats"
    if "stat" in caption.lower():
        individual_entries = DailyEntry.objects.filter(
                                                        user__user_id=7,
                                                        date=timezone.localdate()
                                                        ).values("value1", "value2", "value3")

        data_list = [(e['value1'], e['value2'], e['value3']) for e in individual_entries]
        total_v1, total_v2, total_v3 = [sum(x) for x in zip(*data_list)] if data_list else (0, 0, 0)

        return JsonResponse({
                            "message": (
                                f"*📊 Today's Nutrient Summary*\n\n"
                                f"*Protein:* {total_v1} g\n"
                                f"*Carbs:* {total_v2} g\n"
                                f"*Fat:* {total_v3} g"
                            )
                        }, status=201)


    if secret_key != settings.UPLOAD_SECRET_KEY:
        return JsonResponse({"error": "Invalid secret key"}, status=403)


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

    x=chat_with_gpt(caption)
    x=str(x)
    try:
        x=eval(x)
    except Exception as e:
        return JsonResponse({
                                "message": (
                                        f"❌ Couldn't process data from AI.\n\n"
                                        f"Exception: {e}\n"
                                        f"AI Reply: {x}"
                                    )
                                }, status=201)
    user = UserProfile.objects.get(user_id=7)

    if x[0] == -1 or x[0] == -1:
        return JsonResponse({
                                "message": (
                                    f"❌ Couldn't process this food entry:\n\n"
                                    f"{caption}\n\n"
                                    f"Please try again with clear food details."
                                )
                            }, status=201)

    entry = DailyEntry.objects.create(
        date=timezone.localdate(),
        user=user,
        time=timezone.localtime().time(),
        value1=float(x[0]),   # protein
        value2=float(x[1]),   # carbs
        value3=float(x[2])      # fat
    )


    return JsonResponse({
    "message": (
        f"Food you just ate: {caption}\n\n"
        f"Protein: {x[0]} g\n"
        f"Carbs: {x[1]} g\n"
        f"Fat: {x[2]} g\n\n"
        f"Your food recorded successfully ✅"
    )
}, status=201)



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

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are a Nutrition Assistant.
From the input text, calculate total Protein, Carbs, and Fat (in grams) for all food/drink items.
Output ONLY a tuple in this format:
(protein_g, carbs_g, fat_g)
If no food/drink items are found, output:
(-1, -1, -1)
Do not include any explanation or extra text.
"""


def chat_with_gpt(message: str) -> Tuple[int, int, int]:
    """
    Sends message to GPT and returns (protein, carbs, fat)
    """

    if not message or not message.strip():
        print("Empty message passed to chat_with_gpt")
        return (-1, -1, -1)

    try:
        logger.info("Calling GPT with message: %s", message)

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            temperature=0
        )

        reply = response.choices[0].message.content.strip()

        print(f"GPT reply: {reply} for {message}")



        return reply

    except Exception as e:
        print("Error calling GPT",e)
        return (-1, -1, -1)

from django.utils import timezone

def delete_last_record(user_id):
    try:
        latest_entry = (
            DailyEntry.objects
            .filter(user__user_id=user_id)
            .order_by('-created_at')
            .first()
        )
        print("delete",latest_entry)
        if latest_entry:
            deleted_values = (
                latest_entry.value1,
                latest_entry.value2,
                latest_entry.value3
            )
            latest_entry.delete()
            return deleted_values  # return deleted macros
    except Exception as e:
        print("Error delete",e)


    return None



