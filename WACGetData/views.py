import logging
from typing import Tuple
from datetime import datetime

from django.conf import settings
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI

from .models import DailyEntry, UserProfile, PhoneNumberMapping
from .profile_updates import (
    get_today_nutrition_totals,
    build_target_status,
    build_calories_status,
    get_user_by_phone,
    get_daily_entries_for_today,
    update_user_weight,
    update_user_height,
    update_user_desired_weight,
    update_user_physical_details,
    get_user_physical_details,
    update_user_name,
    update_user_dob,
    validate_dob,
    get_user_all_data,
    create_user_from_phone,
    handle_update_command
)

logger = logging.getLogger(__name__)

# Constants
DEFAULT_USER_ID = 7
OPENAI_MODEL = "gpt-4.1-mini"
GPT_TEMPERATURE = 0

SYSTEM_PROMPT = """You are a Nutrition Assistant.
From the input text, calculate total Protein, Carbs, and Fat (in grams) for all food/drink items.
Output ONLY a tuple in this format:
(protein_g, carbs_g, fat_g)
If no food/drink items are found, output:
(-1, -1, -1)
Do not include any explanation or extra text."""

# Initialize OpenAI client
client = OpenAI(api_key=settings.CHAT_API_KEY)


@csrf_exempt
def get_message_api(request):
    """Handle nutrition tracking API requests from WhatsApp."""
    if request.method == "GET":
        return JsonResponse({
            "need data": "secret_key, unique_id, image*, caption*",
            "Example": "curl -X POST https://mynewnokiap8.pythonanywhere.com/wac/get_message_api/ -F \"secret_key=my_super_secret_key\" -F \"unique_id=user123\" -F \"caption=Hello from curl\" -F \"image=@image.jpg\""
        }, status=400)

    # if request.method != "POST":
    #     return JsonResponse({"error": "Method not allowed"}, status=405)

    secret_key = request.POST.get("secret_key")
    phone_number = request.POST.get("unique_id")
    caption = request.POST.get("caption")
    print(request.POST, request.POST.get("unique_id"),"log123")
    # Validate authentication and required fields
    if secret_key != settings.UPLOAD_SECRET_KEY:
        return JsonResponse({"error": "Invalid secret key"}, status=403)

    if not phone_number:
        return JsonResponse({"error": "unique_id (phone_number) is required"}, status=400)

    # Resolve phone number to user
    try:
        user = get_user_by_phone(phone_number)
    except Exception as e:
        # Phone number not found, create new user
        user = create_user_from_phone(phone_number)
        return JsonResponse({
            "message": (
                f"👋 Welcome! I've created your account.\n\n"
                f"To get started, please provide:\n\n"
                f"1️⃣ Your name:\n"
                f"*my name is John*\n\n"
                f"2️⃣ Your date of birth:\n"
                f"*update dob 1990-05-15*\n\n"
                f"(Use format: YYYY-MM-DD)"
            )
        }, status=201)

    user_id = user.user_id

    # Check if user hasn't set their name yet
    if user.name == "New User":
        # Allow setting name, block everything else
        if not (caption and caption.lower().startswith("my name is ")):
            return JsonResponse({
                "message": (
                    f"👋 Welcome! Before we proceed, please set your name:\n\n"
                    f"*my name is Your Name*\n\n"
                    f"Replace 'Your Name' with your actual name."
                )
            }, status=201)

    # Check if user is setting their name
    if caption and caption.lower().startswith("my name is "):
        name = caption[11:].strip()  # Extract name after "my name is "
        if name:
            update_user_name(user, name)
            return JsonResponse({
                "message": (
                    f"✅ Hi {name}! I've updated your name.\n\n"
                    f"Now please update your physical details one by one:\n\n"
                    f"1️⃣ *Current Weight (in kg):*\n"
                    f"update weight 75.5\n\n"
                    f"2️⃣ *Desired Weight (in kg):*\n"
                    f"update desired_weight 70\n\n"
                    f"3️⃣ *Height (in cm):*\n"
                    f"update height 180\n\n"
                    f"Once you provide all three, I'll calculate your nutrition goals! 🎯"
                )
            }, status=201)

    # Handle info command
    if caption and caption.lower().strip() == "my info":
        result = get_user_all_data(user)
        return JsonResponse({
            "message": result['message']
        }, status=201)

    # Handle update command
    if caption and caption.lower().startswith("update "):
        result = handle_update_command(user, caption)
        return JsonResponse({
            "message": result['message']
        }, status=201)

    # Handle delete command
    if caption and "delete" in caption.lower():
        return _handle_delete_request(user_id)

    # Handle stats command
    if caption and "stat" in caption.lower():
        return _handle_stats_request(user_id)

    if not caption:
        return JsonResponse({
            "error": "Either image or caption is required"
        }, status=400)

    # Process food entry through GPT
    gpt_response = chat_with_gpt(caption)
    gpt_response_str = str(gpt_response)

    try:
        nutrition_data = eval(gpt_response_str)
    except Exception as e:
        return JsonResponse({
            "message": (
                f"❌ Couldn't process data from AI.\n\n"
                f"Exception: {e}\n"
                f"AI Reply: {gpt_response_str}"
            )
        }, status=201)

    user = UserProfile.objects.get(user_id=user_id)

    # Check if GPT returned valid data
    if nutrition_data[0] == -1 or nutrition_data[1] == -1:
        return JsonResponse({
            "message": (
                f"Hi {user.name}! ❌\n\n"
                f"Couldn't process this food entry:\n\n"
                f"{caption}\n\n"
                f"Please try again with clear food details."
            )
        }, status=201)

    # Calculate calories: protein*4 + carbs*4 + fat*9
    protein = round(float(nutrition_data[0]), 2)
    carbs = round(float(nutrition_data[1]), 2)
    fat = round(float(nutrition_data[2]), 2)
    calories = round((protein * 4) + (carbs * 4) + (fat * 9), 2)

    # Get current day's total calories before this entry
    today = timezone.localdate()
    current_calories = round(sum(
        (entry.value1 * 4) + (entry.value2 * 4) + (entry.value3 * 9)
        for entry in get_daily_entries_for_today(user)
    ), 2)

    # Create daily entry
    DailyEntry.objects.create(
        date=today,
        user=user,
        time=timezone.localtime().time(),
        value1=protein,  # protein
        value2=carbs,    # carbs
        value3=fat,      # fat
        current_calories=current_calories
    )

    # Get today's totals including the newly created entry
    nutrition_totals = get_today_nutrition_totals(user)
    target_status = build_target_status(user, nutrition_totals)
    calories_status = build_calories_status(user, nutrition_totals)
    today_entries = DailyEntry.objects.filter(
        user=user,
        date=today
    )

    today_protein = round(sum(entry.value1 for entry in today_entries), 2)
    today_carbs = round(sum(entry.value2 for entry in today_entries), 2)
    today_fat = round(sum(entry.value3 for entry in today_entries), 2)
    today_calories = round(sum(
        (entry.value1 * 4) + (entry.value2 * 4) + (entry.value3 * 9)
        for entry in today_entries
    ), 2)

    # Build target achievement status
    target_status = ""
    if user.target_protein:
        protein_achieved = "✅" if today_protein >= user.target_protein else "❌"
        target_status += f"Protein: {round(today_protein, 2)}g / {round(user.target_protein, 2)}g {protein_achieved}\n"
    if user.target_carbs:
        carbs_achieved = "✅" if today_carbs >= user.target_carbs else "❌"
        target_status += f"Carbs: {round(today_carbs, 2)}g / {round(user.target_carbs, 2)}g {carbs_achieved}\n"
    if user.target_fat:
        fat_achieved = "✅" if today_fat >= user.target_fat else "❌"
        target_status += f"Fat: {round(today_fat, 2)}g / {round(user.target_fat, 2)}g {fat_achieved}\n"

    calories_status = ""
    if user.calories_needed:
        calories_achieved = "✅" if today_calories >= user.calories_needed else "❌"
        calories_status = f"Calories: {round(today_calories, 2)}kcal / {round(user.calories_needed, 2)}kcal {calories_achieved}\n"

    return JsonResponse({
        "message": (
            f"Hi {user.name}! 🍽️\n\n"
            f"Your food entry: {caption}\n\n"
            f"*Nutritional Info:*\n"
            f"Protein: {round(nutrition_data[0], 2)} g\n"
            f"Carbs: {round(nutrition_data[1], 2)} g\n"
            f"Fat: {round(nutrition_data[2], 2)} g\n"
            f"Calories: {round(calories, 2)} kcal\n\n"

            f"*======================*\n"
            f"*Today's Goals Status*\n"
            f"*======================*\n\n"
            f"{target_status}"
            f"{calories_status}"
            f"New food recorded successfully ✅"\n
        )
    }, status=201)


def _handle_delete_request(user_id: int) -> JsonResponse:
    """Handle deletion of the last food entry."""
    user = UserProfile.objects.get(user_id=user_id)
    deleted = delete_last_record(user_id=user_id)

    if deleted:
        protein, carbs, fat = deleted
        deleted_calories = round((protein * 4) + (carbs * 4) + (fat * 9), 2)

        return JsonResponse({
            "message": (
                f"Hi {user.name}! 🗑️\n\n"
                f"Last food entry deleted successfully.\n\n"
                f"Protein Removed: {round(protein, 2)} g\n"
                f"Carbs Removed: {round(carbs, 2)} g\n"
                f"Fat Removed: {round(fat, 2)} g\n"
                f"Calories Removed: {round(deleted_calories, 2)} kcal\n\n"
                f"Your latest record has been removed."
            )
        }, status=200)

    return JsonResponse({
        "message": f"Hey {user.name}! ⚠️ No recent food entry found to delete."
    }, status=200)


def _handle_stats_request(user_id: int) -> JsonResponse:
    """Handle stats request for today's nutrient summary."""
    user = UserProfile.objects.get(user_id=user_id)

    # Get today's nutrition totals
    nutrition_totals = get_today_nutrition_totals(user)

    # Get today's entries
    today_entries = DailyEntry.objects.filter(
        user=user,
        date=timezone.localdate()
    )

    # Calculate totals
    today_protein = round(sum(entry.value1 for entry in today_entries), 2)
    today_carbs = round(sum(entry.value2 for entry in today_entries), 2)
    today_fat = round(sum(entry.value3 for entry in today_entries), 2)
    today_calories = round(sum(
        (entry.value1 * 4) + (entry.value2 * 4) + (entry.value3 * 9)
        for entry in today_entries
    ), 2)

    # Build target achievement status
    target_status = ""
    if user.target_protein:
        protein_achieved = "✅" if today_protein >= user.target_protein else "❌"
        target_status += f"*Protein:* {round(today_protein, 2)}g / {round(user.target_protein, 2)}g {protein_achieved}\n"
    if user.target_carbs:
        carbs_achieved = "✅" if today_carbs >= user.target_carbs else "❌"
        target_status += f"*Carbs:* {round(today_carbs, 2)}g / {round(user.target_carbs, 2)}g {carbs_achieved}\n"
    if user.target_fat:
        fat_achieved = "✅" if today_fat >= user.target_fat else "❌"
        target_status += f"*Fat:* {round(today_fat, 2)}g / {round(user.target_fat, 2)}g {fat_achieved}\n"

    calories_status = ""
    if user.calories_needed:
        calories_achieved = "✅" if today_calories >= user.calories_needed else "❌"
        calories_status = f"*Calories:* {round(today_calories, 2)}kcal / {round(user.calories_needed, 2)}kcal {calories_achieved}\n"

    return JsonResponse({
        "message": (
            f"Hi {user.name}! 📊\n\n"
            f"*Today's Nutrient Summary*\n\n"
            f"*Calories Consumed:* {round(today_calories, 2)} kcal\n"
            f"*Protein:* {round(today_protein, 2)} g\n"
            f"*Carbs:* {round(today_carbs, 2)} g\n"
            f"*Fat:* {round(today_fat, 2)} g\n\n"
            f"*======================*\n"
            f"*Today's Goals Status*\n"
            f"*======================*\n"
            f"{target_status}"
            f"{calories_status}"
        )
    }, status=201)


def add_user(request):
    """Create a test user in the database."""
    user = UserProfile.objects.create(
        user_id=9999,
        name="Test User",
        gender="M",
        dob=datetime.strptime("1999-01-01", "%Y-%m-%d")
    )
    return JsonResponse({"message": "User added"})


def get_msg(request):
    """Simple test endpoint."""
    return HttpResponse("hello")


def add_daily_entry(user_id: int, entry_date, entry_time, v1: float, v2: float, v3: float) -> DailyEntry:
    """Create a daily nutrition entry for a user.

    Args:
        user_id: The user's ID
        entry_date: The date of the entry
        entry_time: The time of the entry
        v1: Protein value in grams
        v2: Carbs value in grams
        v3: Fat value in grams

    Returns:
        The created DailyEntry object
    """
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


def chat_with_gpt(message: str) -> Tuple[int, int, int]:
    """Send message to GPT and return nutrition values.

    Args:
        message: Food description to analyze

    Returns:
        Tuple of (protein_g, carbs_g, fat_g) or (-1, -1, -1) on error
    """
    if not message or not message.strip():
        logger.warning("Empty message passed to chat_with_gpt")
        return (-1, -1, -1)

    try:
        logger.info("Calling GPT with message: %s", message)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            temperature=GPT_TEMPERATURE
        )

        reply = response.choices[0].message.content.strip()
        logger.info("GPT reply for '%s': %s", message, reply)
        return reply

    except Exception as e:
        logger.error("Error calling GPT: %s", e)
        return (-1, -1, -1)


def delete_last_record(user_id: int):
    """Delete the most recent food entry for a user.

    Args:
        user_id: The user's ID

    Returns:
        Tuple of deleted macro values (protein, carbs, fat) or None if not found
    """
    try:
        latest_entry = (
            DailyEntry.objects
            .filter(user__user_id=user_id)
            .order_by('-created_at')
            .first()
        )

        if latest_entry:
            deleted_values = (
                latest_entry.value1,
                latest_entry.value2,
                latest_entry.value3
            )
            latest_entry.delete()
            logger.info("Deleted entry for user %s: %s", user_id, deleted_values)
            return deleted_values

    except Exception as e:
        logger.error("Error deleting record for user %s: %s", user_id, e)

    return None




