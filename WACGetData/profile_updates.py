"""Functions for handling UserProfile updates and retrieving user nutrition data."""

import logging
from datetime import datetime, date
from django.utils import timezone
from .models import DailyEntry, UserProfile

logger = logging.getLogger(__name__)


def validate_dob(dob_string: str) -> dict:
    """Validate date of birth string with standard conditions.
    
    Valid format: YYYY-MM-DD or YYYY/MM/DD or DD-MM-YYYY or DD/MM/YYYY
    Conditions:
    - User must be at least 13 years old
    - User cannot be born in the future
    - Year must be between 1900 and current year
    
    Args:
        dob_string: Date of birth string
        
    Returns:
        Dictionary with keys: {valid: bool, date: date or None, message: str}
    """
    if not dob_string or not dob_string.strip():
        return {
            'valid': False,
            'date': None,
            'message': "❌ DOB cannot be empty"
        }
    
    # Try different date formats
    formats = [
        "%Y-%m-%d",  # 1990-05-15
        "%Y/%m/%d",  # 1990/05/15
        "%d-%m-%Y",  # 15-05-1990
        "%d/%m/%Y",  # 15/05/1990
        "%m-%d-%Y",  # 05-15-1990
        "%m/%d/%Y",  # 05/15/1990
    ]
    
    dob_date = None
    for date_format in formats:
        try:
            dob_date = datetime.strptime(dob_string.strip(), date_format).date()
            break
        except ValueError:
            continue
    
    if dob_date is None:
        return {
            'valid': False,
            'date': None,
            'message': "❌ Invalid date format. Use YYYY-MM-DD (e.g., 1990-05-15)"
        }
    
    today = date.today()
    
    # Check if in future
    if dob_date > today:
        return {
            'valid': False,
            'date': None,
            'message': "❌ Date of birth cannot be in the future"
        }
    
    # Check year range
    if dob_date.year < 1900:
        return {
            'valid': False,
            'date': None,
            'message': "❌ Year must be 1900 or later"
        }
    
    # Calculate age
    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    
    # Check minimum age (13 years)
    if age < 13:
        return {
            'valid': False,
            'date': None,
            'message': f"❌ You must be at least 13 years old. You are currently {age} years old."
        }
    
    return {
        'valid': True,
        'date': dob_date,
        'message': ""
    }


def update_user_dob(user: UserProfile, dob_string: str) -> dict:
    """Update a user's date of birth with validation.
    
    Args:
        user: UserProfile instance
        dob_string: Date of birth string
        
    Returns:
        Dictionary with keys: {success: bool, message: str}
    """
    validation_result = validate_dob(dob_string)
    
    if not validation_result['valid']:
        return {
            'success': False,
            'message': validation_result['message']
        }
    
    dob_date = validation_result['date']
    user.dob = dob_date
    user.save()
    
    # Calculate age
    today = date.today()
    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    
    logger.info("Updated DOB for user %s: %s (age: %s)", user.user_id, dob_date, age)
    
    return {
        'success': True,
        'message': f"✅ Date of birth updated to {dob_date.strftime('%B %d, %Y')} (Age: {age})"
    }


def get_user_all_data(user: UserProfile) -> dict:
    """Get all user profile data formatted for display.
    
    Args:
        user: UserProfile instance
        
    Returns:
        Dictionary with all user data and formatted message
    """
    today = date.today()
    age = today.year - user.dob.year - ((today.month, today.day) < (user.dob.month, user.dob.day)) if user.dob else "N/A"
    
    # Format personal info
    personal_info = f"*Personal Information:*\n"
    personal_info += f"Name: {user.name}\n"
    personal_info += f"User ID: {user.user_id}\n"
    personal_info += f"Date of Birth: {user.dob.strftime('%B %d, %Y') if user.dob else 'Not set'}\n"
    personal_info += f"Age: {age}\n"
    
    # Format physical measurements
    physical_info = f"\n*Physical Measurements:*\n"
    physical_info += f"Current Weight: {user.weight} kg" if user.weight else "Current Weight: Not set"
    physical_info += f"\nDesired Weight: {user.desired_weight} kg" if user.desired_weight else "\nDesired Weight: Not set"
    physical_info += f"\nHeight: {user.height} cm" if user.height else "\nHeight: Not set"
    physical_info += f"\nLast Weight Update: {user.weight_last_updated}" if user.weight_last_updated else "\nLast Weight Update: Never"
    
    # Format nutrition goals
    nutrition_info = f"\n*Nutrition Goals:*\n"
    nutrition_info += f"Daily Calories: {user.calories_needed} kcal" if user.calories_needed else "Daily Calories: Not calculated"
    nutrition_info += f"\nTarget Protein: {user.target_protein}g" if user.target_protein else "\nTarget Protein: Not set"
    nutrition_info += f"\nTarget Carbs: {user.target_carbs}g" if user.target_carbs else "\nTarget Carbs: Not set"
    nutrition_info += f"\nTarget Fat: {user.target_fat}g" if user.target_fat else "\nTarget Fat: Not set"
    
    # Get today's nutrition
    today_entries = DailyEntry.objects.filter(
        user=user,
        date=timezone.localdate()
    )
    
    today_protein = sum(entry.value1 for entry in today_entries)
    today_carbs = sum(entry.value2 for entry in today_entries)
    today_fat = sum(entry.value3 for entry in today_entries)
    today_calories = sum(
        (entry.value1 * 4) + (entry.value2 * 4) + (entry.value3 * 9)
        for entry in today_entries
    )
    
    today_info = f"\n*Today's Nutrition (as of now):*\n"
    today_info += f"Protein: {today_protein}g\n"
    today_info += f"Carbs: {today_carbs}g\n"
    today_info += f"Fat: {today_fat}g\n"
    today_info += f"Total Calories: {today_calories} kcal"
    
    full_message = personal_info + physical_info + nutrition_info + today_info
    
    return {
        'success': True,
        'message': full_message,
        'data': {
            'name': user.name,
            'user_id': user.user_id,
            'age': age,
            'weight': user.weight,
            'desired_weight': user.desired_weight,
            'height': user.height,
            'calories_needed': user.calories_needed,
            'target_protein': user.target_protein,
            'target_carbs': user.target_carbs,
            'target_fat': user.target_fat,
            'today_protein': today_protein,
            'today_carbs': today_carbs,
            'today_fat': today_fat,
            'today_calories': today_calories
        }
    }


def get_today_nutrition_totals(user: UserProfile) -> dict:
    """Get today's total nutrition values for a user.
    
    Args:
        user: UserProfile instance
        
    Returns:
        Dictionary with today's totals: {protein, carbs, fat, calories}
    """
    today = timezone.localdate()
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
    
    return {
        'protein': today_protein,
        'carbs': today_carbs,
        'fat': today_fat,
        'calories': today_calories
    }


def build_target_status(user: UserProfile, nutrition_totals: dict) -> str:
    """Build a formatted status string showing progress towards targets.
    
    Args:
        user: UserProfile instance
        nutrition_totals: Dictionary from get_today_nutrition_totals()
        
    Returns:
        Formatted string with target achievement status
    """
    target_status = ""
    
    if user.target_protein:
        protein_achieved = "✅" if nutrition_totals['protein'] >= user.target_protein else "❌"
        target_status += f"Protein: {nutrition_totals['protein']}g / {user.target_protein}g {protein_achieved}\n"
    
    if user.target_carbs:
        carbs_achieved = "✅" if nutrition_totals['carbs'] >= user.target_carbs else "❌"
        target_status += f"Carbs: {nutrition_totals['carbs']}g / {user.target_carbs}g {carbs_achieved}\n"
    
    if user.target_fat:
        fat_achieved = "✅" if nutrition_totals['fat'] >= user.target_fat else "❌"
        target_status += f"Fat: {nutrition_totals['fat']}g / {user.target_fat}g {fat_achieved}\n"
    
    return target_status


def build_calories_status(user: UserProfile, nutrition_totals: dict) -> str:
    """Build a formatted string showing calorie progress.
    
    Args:
        user: UserProfile instance
        nutrition_totals: Dictionary from get_today_nutrition_totals()
        
    Returns:
        Formatted string with calorie achievement status (or empty string if no target)
    """
    if not user.calories_needed:
        return ""
    
    calories_achieved = "✅" if nutrition_totals['calories'] >= user.calories_needed else "❌"
    return f"Calories: {nutrition_totals['calories']}kcal / {user.calories_needed}kcal {calories_achieved}\n"


def get_user_by_phone(phone_number: str) -> UserProfile:
    """Get UserProfile by phone number mapping.
    
    Args:
        phone_number: Phone number to look up
        
    Returns:
        UserProfile instance
        
    Raises:
        PhoneNumberMapping.DoesNotExist: If phone number not found
    """
    from .models import PhoneNumberMapping
    
    phone_mapping = PhoneNumberMapping.objects.get(phone_number=phone_number)
    return phone_mapping.user


def get_daily_entries_for_today(user: UserProfile) -> list:
    """Get all daily entries for a user for today.
    
    Args:
        user: UserProfile instance
        
    Returns:
        QuerySet of DailyEntry objects for today
    """
    today = timezone.localdate()
    return DailyEntry.objects.filter(
        user=user,
        date=today
    )


def update_user_weight(user: UserProfile, weight: float) -> dict:
    """Update a user's weight and set weight_last_updated to today.
    If both current weight and desired_weight exist, calculate nutrition goals.
    
    Args:
        user: UserProfile instance
        weight: Weight value in kg
        
    Returns:
        Dictionary with keys: {success: bool, message: str}
    """
    from .nutrition_calculator import update_user_nutrition_goals, check_user_weight_data
    
    user.weight = weight
    user.weight_last_updated = timezone.localdate()
    user.save()
    
    logger.info("Updated weight for user %s: %s kg", user.user_id, weight)
    
    # Check if we have both weight and desired_weight
    check_result = check_user_weight_data(user)
    
    if check_result['has_both']:
        # Both values exist, calculate nutrition goals
        calc_result = update_user_nutrition_goals(user)
        return {
            'success': True,
            'message': (
                f"✅ Weight updated to {weight} kg\n\n"
                f"{calc_result['message']}"
            )
        }
    else:
        # Missing desired_weight, ask user to provide it
        return {
            'success': True,
            'message': (
                f"✅ Weight updated to {weight} kg\n\n"
                f"To calculate your nutrition goals, please update your desired weight:\n"
                f"*update desired_weight <value>*"
            )
        }


def update_user_height(user: UserProfile, height: float) -> UserProfile:
    """Update a user's height.
    
    Args:
        user: UserProfile instance
        height: Height value in cm
        
    Returns:
        Updated UserProfile instance
    """
    user.height = height
    user.save()
    logger.info("Updated height for user %s: %s cm", user.user_id, height)
    return user


def update_user_desired_weight(user: UserProfile, desired_weight: float) -> dict:
    """Update a user's desired weight.
    If both current weight and desired_weight exist, calculate nutrition goals.
    
    Args:
        user: UserProfile instance
        desired_weight: Desired weight value in kg
        
    Returns:
        Dictionary with keys: {success: bool, message: str}
    """
    from .nutrition_calculator import update_user_nutrition_goals, check_user_weight_data
    
    user.desired_weight = desired_weight
    user.save()
    
    logger.info("Updated desired weight for user %s: %s kg", user.user_id, desired_weight)
    
    # Check if we have both weight and desired_weight
    check_result = check_user_weight_data(user)
    
    if check_result['has_both']:
        # Both values exist, calculate nutrition goals
        calc_result = update_user_nutrition_goals(user)
        return {
            'success': True,
            'message': (
                f"✅ Desired weight updated to {desired_weight} kg\n\n"
                f"{calc_result['message']}"
            )
        }
    else:
        # Missing weight, ask user to provide it
        return {
            'success': True,
            'message': (
                f"✅ Desired weight updated to {desired_weight} kg\n\n"
                f"To calculate your nutrition goals, please update your current weight:\n"
                f"*update weight <value>*"
            )
        }


def update_user_physical_details(user: UserProfile, weight: float = None, height: float = None) -> UserProfile:
    """Update a user's weight and/or height in a single operation.
    
    Args:
        user: UserProfile instance
        weight: Weight value in kg (optional)
        height: Height value in cm (optional)
        
    Returns:
        Updated UserProfile instance
    """
    updated = False
    
    if weight is not None:
        user.weight = weight
        user.weight_last_updated = timezone.localdate()
        updated = True
    
    if height is not None:
        user.height = height
        updated = True
    
    if updated:
        user.save()
        logger.info("Updated physical details for user %s: weight=%s kg, height=%s cm", 
                    user.user_id, user.weight, user.height)
    
    return user


def get_user_physical_details(user: UserProfile) -> dict:
    """Get a user's physical details.
    
    Args:
        user: UserProfile instance
        
    Returns:
        Dictionary with user's physical details: {weight, height, weight_last_updated}
    """
    return {
        'weight': user.weight,
        'height': user.height,
        'weight_last_updated': user.weight_last_updated
    }


def update_user_name(user: UserProfile, name: str) -> UserProfile:
    """Update a user's name.
    
    Args:
        user: UserProfile instance
        name: New name for the user
        
    Returns:
        Updated UserProfile instance
    """
    user.name = name
    user.save()
    logger.info("Updated name for user %s: %s", user.user_id, name)
    return user


def create_user_from_phone(phone_number: str) -> UserProfile:
    """Create a new user and map their phone number.
    
    Args:
        phone_number: Phone number to map to new user
        
    Returns:
        Newly created UserProfile instance with default DOB
    """
    from .models import PhoneNumberMapping
    
    # Generate a new unique user_id
    max_user_id = UserProfile.objects.all().order_by('-user_id').first()
    new_user_id = (max_user_id.user_id + 13) if max_user_id else 1000
    
    # Create new user with default values (DOB will be updated by user)
    user = UserProfile.objects.create(
        user_id=new_user_id,
        name="New User",
        gender="O",
        dob=datetime.strptime("2000-01-01", "%Y-%m-%d").date()
    )
    
    # Create phone mapping
    PhoneNumberMapping.objects.create(
        phone_number=phone_number,
        user=user
    )
    
    logger.info("Created new user %s with phone number %s", new_user_id, phone_number)
    return user


def handle_update_command(user: UserProfile, caption: str) -> dict:
    """Handle update commands in format: "update <field> <value>"
    
    Supported commands:
    - "update weight <value_in_kg>"
    - "update desired_weight <value_in_kg>"
    - "update height <value_in_cm>"
    - "update dob <YYYY-MM-DD>"
    - "update name <new_name>"
    
    Args:
        user: UserProfile instance
        caption: Command string from user
        
    Returns:
        Dictionary with keys: {success: bool, message: str}
    """
    try:
        # Parse the command
        parts = caption.strip().lower().split(maxsplit=2)
        
        if len(parts) < 3 or parts[0] != "update":
            return {
                'success': False,
                'message': (
                    "❌ Invalid format. Use:\n"
                    "*update weight 75.5*\n"
                    "*update desired_weight 70*\n"
                    "*update height 180*\n"
                    "*update dob 1990-05-15*\n"
                    "*update name John*"
                )
            }
        
        field = parts[1]
        value = parts[2]
        
        # Handle weight update
        if field == "weight":
            try:
                weight = float(value)
                if weight <= 0:
                    return {
                        'success': False,
                        'message': "❌ Weight must be a positive number"
                    }
                result = update_user_weight(user, weight)
                return {
                    'success': result['success'],
                    'message': result['message']
                }
            except ValueError:
                return {
                    'success': False,
                    'message': f"❌ Invalid weight value: {value}. Please use a number like 75.5"
                }
        
        # Handle desired_weight update
        elif field == "desired_weight":
            try:
                desired_weight = float(value)
                if desired_weight <= 0:
                    return {
                        'success': False,
                        'message': "❌ Desired weight must be a positive number"
                    }
                result = update_user_desired_weight(user, desired_weight)
                return {
                    'success': result['success'],
                    'message': result['message']
                }
            except ValueError:
                return {
                    'success': False,
                    'message': f"❌ Invalid desired weight value: {value}. Please use a number like 70"
                }
        
        # Handle height update
        elif field == "height":
            try:
                height = float(value)
                if height <= 0:
                    return {
                        'success': False,
                        'message': "❌ Height must be a positive number"
                    }
                update_user_height(user, height)
                return {
                    'success': True,
                    'message': f"✅ Height updated to {height} cm"
                }
            except ValueError:
                return {
                    'success': False,
                    'message': f"❌ Invalid height value: {value}. Please use a number like 180"
                }
        
        # Handle name update
        elif field == "name":
            new_name = caption.split(maxsplit=2)[2]  # Get original case for name
            update_user_name(user, new_name)
            return {
                'success': True,
                'message': f"✅ Name updated to {new_name}"
            }
        
        # Handle DOB update
        elif field == "dob":
            result = update_user_dob(user, value)
            return {
                'success': result['success'],
                'message': result['message']
            }
        
        else:
            return {
                'success': False,
                'message': (
                    f"❌ Unknown field: {field}\n\n"
                    "I can update:\n"
                    "• weight\n"
                    "• desired_weight\n"
                    "• height\n"
                    "• dob (date of birth)\n"
                    "• name"
                )
            }
    
    except Exception as e:
        logger.error("Error handling update command: %s", e)
        return {
            'success': False,
            'message': f"❌ Error processing your request: {str(e)}"
        }
