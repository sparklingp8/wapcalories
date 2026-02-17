"""Functions for calculating nutrition goals based on user metrics."""

import logging
from datetime import date
from .models import UserProfile

logger = logging.getLogger(__name__)


def check_user_weight_data(user: UserProfile) -> dict:
    """Check if user has both current weight and desired weight.
    
    Args:
        user: UserProfile instance
        
    Returns:
        Dictionary with keys: {has_both: bool, missing: list, message: str}
    """
    missing = []
    
    if user.weight is None:
        missing.append("weight")
    
    if user.desired_weight is None:
        missing.append("desired_weight")
    
    if missing:
        missing_str = " and ".join(missing)
        message = f"❌ Please update your {missing_str} first.\n\nUse:\n*update {missing[0]} <value>*"
        return {
            'has_both': False,
            'missing': missing,
            'message': message
        }
    
    return {
        'has_both': True,
        'missing': [],
        'message': ''
    }


def check_all_required_data(user: UserProfile) -> dict:
    """Check if user has all required data for nutrition calculation.
    
    Required data:
    - Current weight
    - Desired weight
    - Height
    - Date of birth
    
    Args:
        user: UserProfile instance
        
    Returns:
        Dictionary with keys: {has_all: bool, missing: list, message: str}
    """
    missing = []
    
    if user.weight is None:
        missing.append("weight (current)")
    
    if user.desired_weight is None:
        missing.append("desired weight")
    
    if user.height is None:
        missing.append("height")
    
    if user.dob is None:
        missing.append("date of birth")
    
    if missing:
        missing_str = "\n• ".join(missing)
        message = f"❌ Missing required data for nutrition calculation:\n\n• {missing_str}\n\nPlease update these using:\n*update weight 75*\n*update desired_weight 70*\n*update height 180*\n*update dob 1990-05-15*"
        return {
            'has_all': False,
            'missing': missing,
            'message': message
        }
    
    return {
        'has_all': True,
        'missing': [],
        'message': ''
    }


def calculate_bmr(user: UserProfile) -> float:
    """Calculate Basal Metabolic Rate using average Mifflin-St Jeor equation.
    
    Args:
        user: UserProfile instance
        
    Returns:
        BMR in calories per day
    """
    if not user.weight or not user.height or not user.dob:
        return None
    
    # Calculate age
    today = date.today()
    age = today.year - user.dob.year - ((today.month, today.day) < (user.dob.month, user.dob.day))
    
    weight = user.weight  # in kg
    height = user.height  # in cm
    
    # Using average formula (neutral between male and female)
    bmr = (10 * weight) + (6.25 * height) - (5 * age) - 78
    
    return bmr


def calculate_tdee(user: UserProfile, activity_level: float = 1.5) -> float:
    """Calculate Total Daily Energy Expenditure.
    
    Args:
        user: UserProfile instance
        activity_level: Activity multiplier
            1.2 = Sedentary (little or no exercise)
            1.375 = Lightly active (1-3 days/week)
            1.55 = Moderately active (3-5 days/week)
            1.725 = Very active (6-7 days/week)
            1.9 = Extremely active (physical job or training twice per day)
        
    Returns:
        TDEE in calories per day
    """
    bmr = calculate_bmr(user)
    if bmr is None:
        return None
    
    return bmr * activity_level


def calculate_calories_needed(user: UserProfile, activity_level: float = 1.5) -> float:
    """Calculate daily calories needed to achieve desired weight.
    
    Args:
        user: UserProfile instance
        activity_level: Activity multiplier (see calculate_tdee)
        
    Returns:
        Calories needed per day
    """
    if user.weight is None or user.desired_weight is None:
        return None
    
    tdee = calculate_tdee(user, activity_level)
    if tdee is None:
        return None
    
    weight_diff = user.weight - user.desired_weight
    
    # Calorie adjustment: 7700 calories = 1 kg of weight
    # Assuming 3.5 kg loss/gain per month (500 cal/day deficit/surplus)
    if weight_diff > 0:
        # User wants to lose weight
        adjusted_calories = tdee - 500
    elif weight_diff < 0:
        # User wants to gain weight
        adjusted_calories = tdee + 500
    else:
        # Same weight, maintain
        adjusted_calories = tdee
    
    return adjusted_calories


def calculate_macros(calories_needed: float, protein_percentage: float = 0.30, 
                     carbs_percentage: float = 0.40, fat_percentage: float = 0.30) -> dict:
    """Calculate macro targets based on calorie needs.
    
    Args:
        calories_needed: Daily calorie target
        protein_percentage: Percentage of calories from protein (default 30%)
        carbs_percentage: Percentage of calories from carbs (default 40%)
        fat_percentage: Percentage of calories from fat (default 30%)
        
    Returns:
        Dictionary with keys: {protein: float, carbs: float, fat: float}
    """
    # Calories per gram: protein=4, carbs=4, fat=9
    protein_grams = (calories_needed * protein_percentage) / 4
    carbs_grams = (calories_needed * carbs_percentage) / 4
    fat_grams = (calories_needed * fat_percentage) / 9
    
    return {
        'protein': round(protein_grams, 1),
        'carbs': round(carbs_grams, 1),
        'fat': round(fat_grams, 1)
    }


def update_user_nutrition_goals(user: UserProfile, activity_level: float = 1.5, 
                                protein_pct: float = 0.30, carbs_pct: float = 0.40, 
                                fat_pct: float = 0.30) -> dict:
    """Calculate and update user's nutrition goals based on current and desired weight.
    
    Args:
        user: UserProfile instance
        activity_level: Activity multiplier (default 1.5 = moderately active)
        protein_pct: Protein percentage (default 30%)
        carbs_pct: Carbs percentage (default 40%)
        fat_pct: Fat percentage (default 30%)
        
    Returns:
        Dictionary with keys: {success: bool, message: str, data: dict or None}
    """
    # Check if all required data exists
    check_result = check_all_required_data(user)
    if not check_result['has_all']:
        return {
            'success': False,
            'message': check_result['message'],
            'data': None
        }
    
    try:
        # Calculate calories needed
        calories_needed = calculate_calories_needed(user, activity_level)
        if calories_needed is None or calories_needed <= 0:
            return {
                'success': False,
                'message': "❌ Unable to calculate nutrition goals. Please ensure all required data is set correctly.",
                'data': None
            }
        
        # Calculate macros
        macros = calculate_macros(calories_needed, protein_pct, carbs_pct, fat_pct)
        
        # Update user profile
        user.calories_needed = round(calories_needed, 1)
        user.target_protein = macros['protein']
        user.target_carbs = macros['carbs']
        user.target_fat = macros['fat']
        user.save()
        
        logger.info(
            "Updated nutrition goals for user %s: calories=%s, protein=%s, carbs=%s, fat=%s",
            user.user_id, user.calories_needed, user.target_protein, user.target_carbs, user.target_fat
        )
        
        return {
            'success': True,
            'message': (
                f"✅ Nutrition goals calculated and updated!\n\n"
                f"*Daily Targets:*\n"
                f"Calories: {user.calories_needed} kcal\n"
                f"Protein: {user.target_protein}g\n"
                f"Carbs: {user.target_carbs}g\n"
                f"Fat: {user.target_fat}g"
            ),
            'data': {
                'calories_needed': user.calories_needed,
                'target_protein': user.target_protein,
                'target_carbs': user.target_carbs,
                'target_fat': user.target_fat
            }
        }
    
    except Exception as e:
        logger.error("Error updating nutrition goals for user %s: %s", user.user_id, e)
        return {
            'success': False,
            'message': f"❌ Error calculating nutrition goals: {str(e)}",
            'data': None
        }
