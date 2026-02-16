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

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    secret_key = request.POST.get("secret_key")
    phone_number = request.POST.get("unique_id")
    caption = request.POST.get("caption")

    # Validate authentication and required fields
    if secret_key != settings.UPLOAD_SECRET_KEY:
        return JsonResponse({"error": "Invalid secret key"}, status=403)

    if not phone_number:
        return JsonResponse({"error": "unique_id (phone_number) is required"}, status=400)

    # Resolve phone number to user_id
    try:
        phone_mapping = PhoneNumberMapping.objects.get(phone_number=phone_number)
        user_id = phone_mapping.user.user_id
    except PhoneNumberMapping.DoesNotExist:
        return JsonResponse({
            "error": f"Phone number {phone_number} not found in system"
        }, status=404)

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
    gpt_response = "(10,20,30)"#chat_with_gpt(caption)
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
                f"❌ Couldn't process this food entry:\n\n"
                f"{caption}\n\n"
                f"Please try again with clear food details."
            )
        }, status=201)

    # Calculate calories: protein*4 + carbs*4 + fat*9
    protein = float(nutrition_data[0])
    carbs = float(nutrition_data[1])
    fat = float(nutrition_data[2])
    calories = (protein * 4) + (carbs * 4) + (fat * 9)

    # Get current day's total calories before this entry
    today = timezone.localdate()
    today_entries = DailyEntry.objects.filter(
        user=user,
        date=today
    )
    current_calories = sum(
        (entry.value1 * 4) + (entry.value2 * 4) + (entry.value3 * 9)
        for entry in today_entries
    )

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
    today_entries = DailyEntry.objects.filter(
        user=user,
        date=today
    )
    
    today_protein = sum(entry.value1 for entry in today_entries)
    today_carbs = sum(entry.value2 for entry in today_entries)
    today_fat = sum(entry.value3 for entry in today_entries)
    today_calories = sum(
        (entry.value1 * 4) + (entry.value2 * 4) + (entry.value3 * 9)
        for entry in today_entries
    )

    # Build target achievement status
    target_status = ""
    if user.target_protein:
        protein_achieved = "✅" if today_protein >= user.target_protein else "❌"
        target_status += f"Protein: {today_protein}g / {user.target_protein}g {protein_achieved}\n"
    if user.target_carbs:
        carbs_achieved = "✅" if today_carbs >= user.target_carbs else "❌"
        target_status += f"Carbs: {today_carbs}g / {user.target_carbs}g {carbs_achieved}\n"
    if user.target_fat:
        fat_achieved = "✅" if today_fat >= user.target_fat else "❌"
        target_status += f"Fat: {today_fat}g / {user.target_fat}g {fat_achieved}\n"

    calories_status = ""
    if user.calories_needed:
        calories_achieved = "✅" if today_calories >= user.calories_needed else "❌"
        calories_status = f"Calories: {today_calories}kcal / {user.calories_needed}kcal {calories_achieved}\n"

    return JsonResponse({
        "message": (
            f"Hi {user.name} your food/drinks nutrients : {caption}\n\n"
            f"Protein: {nutrition_data[0]} g\n"
            f"Carbs: {nutrition_data[1]} g\n"
            f"Fat: {nutrition_data[2]} g\n"
            f"Calories Consumed Now: {calories} kcal\n\n"            
            f"Today's Total Calories: {today_calories} kcal\n"
            f"{calories_status}"
            f"{target_status}\n"
            f"New food recorded successfully ✅"
        )
    }, status=201)


def _handle_delete_request(user_id: int) -> JsonResponse:
    """Handle deletion of the last food entry."""
    deleted = delete_last_record(user_id=user_id)

    if deleted:
        protein, carbs, fat = deleted
        deleted_calories = (protein * 4) + (carbs * 4) + (fat * 9)
        
        return JsonResponse({
            "message": (
                "🗑️ Last food entry deleted successfully.\n\n"
                f"Protein Removed: {protein} g\n"
                f"Carbs Removed: {carbs} g\n"
                f"Fat Removed: {fat} g\n"
                f"Calories Removed: {deleted_calories} kcal\n\n"
                "Your latest record has been removed."
            )
        }, status=200)

    return JsonResponse({
        "message": "⚠️ No recent food entry found to delete."
    }, status=200)


def _handle_stats_request(user_id: int) -> JsonResponse:
    """Handle stats request for today's nutrient summary."""
    user = UserProfile.objects.get(user_id=user_id)
    
    # Get today's entries
    today_entries = DailyEntry.objects.filter(
        user=user,
        date=timezone.localdate()
    )
    
    # Calculate totals
    today_protein = sum(entry.value1 for entry in today_entries)
    today_carbs = sum(entry.value2 for entry in today_entries)
    today_fat = sum(entry.value3 for entry in today_entries)
    today_calories = sum(
        (entry.value1 * 4) + (entry.value2 * 4) + (entry.value3 * 9)
        for entry in today_entries
    )

    # Build target achievement status
    target_status = ""
    if user.target_protein:
        protein_achieved = "✅" if today_protein >= user.target_protein else "❌"
        target_status += f"*Protein:* {today_protein}g / {user.target_protein}g {protein_achieved}\n"
    if user.target_carbs:
        carbs_achieved = "✅" if today_carbs >= user.target_carbs else "❌"
        target_status += f"*Carbs:* {today_carbs}g / {user.target_carbs}g {carbs_achieved}\n"
    if user.target_fat:
        fat_achieved = "✅" if today_fat >= user.target_fat else "❌"
        target_status += f"*Fat:* {today_fat}g / {user.target_fat}g {fat_achieved}\n"

    calories_status = ""
    if user.calories_needed:
        calories_achieved = "✅" if today_calories >= user.calories_needed else "❌"
        calories_status = f"*Calories:* {today_calories}kcal / {user.calories_needed}kcal {calories_achieved}\n"

    return JsonResponse({
        "message": (
            f"*📊 Today's Nutrient Summary*\n\n"
            f"*Total Calories:* {today_calories} kcal\n"
            f"{calories_status}"
            f"*Protein:* {today_protein} g\n"
            f"*Carbs:* {today_carbs} g\n"
            f"*Fat:* {today_fat} g\n\n"
            f"*Daily Targets*\n"
            f"{target_status}"
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




