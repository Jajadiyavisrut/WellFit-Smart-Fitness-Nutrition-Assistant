"""
Input validation utilities for WellFit API
Provides reusable validators for all API endpoints
"""

from typing import Dict, Any, List, Tuple


# Valid enum values
VALID_GENDERS = ['male', 'female']
VALID_DIET_TYPES = ['veg', 'non-veg']
VALID_FITNESS_GOALS = ['lose_weight', 'maintain', 'gain_muscle']
VALID_EXPERIENCE_LEVELS = ['beginner', 'intermediate']


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, str]:
    """
    Validate that all required fields are present in the data.
    
    Args:
        data: Input data dictionary
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not data:
        return False, "Request body is required"
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.
    
    Args:
        email: Email string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string"
    
    email = email.strip()
    
    if '@' not in email or '.' not in email:
        return False, "Invalid email format"
    
    if len(email) < 5:
        return False, "Email is too short"
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    
    Args:
        password: Password string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password must be a non-empty string"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    return True, ""


def validate_age(age: Any) -> Tuple[bool, str]:
    """
    Validate age is within acceptable range.
    
    Args:
        age: Age value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        age = int(age)
    except (ValueError, TypeError):
        return False, "Age must be a number"
    
    if age < 15 or age > 100:
        return False, "Age must be between 15 and 100"
    
    return True, ""


def validate_gender(gender: str) -> Tuple[bool, str]:
    """
    Validate gender is a valid value.
    
    Args:
        gender: Gender string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not gender or not isinstance(gender, str):
        return False, "Gender must be a string"
    
    if gender not in VALID_GENDERS:
        return False, f"Gender must be one of: {', '.join(VALID_GENDERS)}"
    
    return True, ""


def validate_height(height_cm: Any) -> Tuple[bool, str]:
    """
    Validate height is within acceptable range.
    
    Args:
        height_cm: Height in centimeters
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        height_cm = float(height_cm)
    except (ValueError, TypeError):
        return False, "Height must be a number"
    
    if height_cm < 100 or height_cm > 250:
        return False, "Height must be between 100 and 250 cm"
    
    return True, ""


def validate_weight(weight_kg: Any) -> Tuple[bool, str]:
    """
    Validate weight is within acceptable range.
    
    Args:
        weight_kg: Weight in kilograms
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        weight_kg = float(weight_kg)
    except (ValueError, TypeError):
        return False, "Weight must be a number"
    
    if weight_kg < 30 or weight_kg > 300:
        return False, "Weight must be between 30 and 300 kg"
    
    return True, ""


def validate_fitness_goal(goal: str) -> Tuple[bool, str]:
    """
    Validate fitness goal is a valid value.
    
    Args:
        goal: Fitness goal string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not goal or not isinstance(goal, str):
        return False, "Fitness goal must be a string"
    
    if goal not in VALID_FITNESS_GOALS:
        return False, f"Fitness goal must be one of: {', '.join(VALID_FITNESS_GOALS)}"
    
    return True, ""


def validate_experience_level(level: str) -> Tuple[bool, str]:
    """
    Validate experience level is a valid value.
    
    Args:
        level: Experience level string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not level or not isinstance(level, str):
        return False, "Experience level must be a string"
    
    if level not in VALID_EXPERIENCE_LEVELS:
        return False, f"Experience level must be one of: {', '.join(VALID_EXPERIENCE_LEVELS)}"
    
    return True, ""


def validate_workout_days(days: Any) -> Tuple[bool, str]:
    """
    Validate workout days per week.
    
    Args:
        days: Number of workout days
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        days = int(days)
    except (ValueError, TypeError):
        return False, "Workout days must be a number"
    
    if days < 0 or days > 7:
        return False, "Workout days must be between 0 and 7"
    
    return True, ""


def validate_workout_time(minutes: Any) -> Tuple[bool, str]:
    """
    Validate workout time in minutes.
    
    Args:
        minutes: Workout time in minutes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        minutes = int(minutes)
    except (ValueError, TypeError):
        return False, "Workout time must be a number"
    
    if minutes < 20 or minutes > 120:
        return False, "Workout time must be between 20 and 120 minutes"
    
    return True, ""


def validate_diet_type(diet_type: str) -> Tuple[bool, str]:
    """
    Validate diet type is a valid value.
    
    Args:
        diet_type: Diet type string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not diet_type or not isinstance(diet_type, str):
        return False, "Diet type must be a string"
    
    if diet_type not in VALID_DIET_TYPES:
        return False, f"Diet type must be one of: {', '.join(VALID_DIET_TYPES)}"
    
    return True, ""


def validate_budget(budget: Any) -> Tuple[bool, str]:
    """
    Validate monthly budget.
    
    Args:
        budget: Monthly budget amount
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        budget = float(budget)
    except (ValueError, TypeError):
        return False, "Budget must be a number"
    
    if budget <= 0:
        return False, "Budget must be greater than 0"
    
    if budget > 1000000:
        return False, "Budget must be less than 1,000,000"
    
    return True, ""


def validate_profile_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate complete profile data.
    
    Args:
        data: Profile data dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    required_fields = [
        'user_id', 'age', 'gender', 'height_cm', 'weight_kg',
        'fitness_goal', 'experience_level', 'workout_days_per_week',
        'workout_time_minutes', 'diet_type', 'monthly_budget'
    ]
    
    is_valid, error = validate_required_fields(data, required_fields)
    if not is_valid:
        return False, error
    
    # Validate each field
    validators = [
        (validate_age, data['age']),
        (validate_gender, data['gender']),
        (validate_height, data['height_cm']),
        (validate_weight, data['weight_kg']),
        (validate_fitness_goal, data['fitness_goal']),
        (validate_experience_level, data['experience_level']),
        (validate_workout_days, data['workout_days_per_week']),
        (validate_workout_time, data['workout_time_minutes']),
        (validate_diet_type, data['diet_type']),
        (validate_budget, data['monthly_budget'])
    ]
    
    for validator_func, value in validators:
        is_valid, error = validator_func(value)
        if not is_valid:
            return False, error
    
    return True, ""
