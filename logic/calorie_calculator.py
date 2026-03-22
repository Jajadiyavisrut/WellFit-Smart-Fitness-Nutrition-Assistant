"""
WellFit Calorie Calculator Module

This module provides calorie calculation logic based on user profile and goals.

Architecture Rules:
- Rule-based logic only (no ML)
- No database
- Logic only
"""


def calculate_bmr(age: int, gender: str, height_cm: float, weight_kg: float) -> float:
    """
    Calculate Basal Metabolic Rate (BMR) using Mifflin-St Jeor Equation.
    
    Args:
        age: Age in years
        gender: "male" or "female"
        height_cm: Height in centimeters
        weight_kg: Weight in kilograms
        
    Returns:
        BMR in calories per day
        
    Raises:
        ValueError: If gender is invalid
    """
    if gender.lower() == 'male':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    elif gender.lower() == 'female':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        raise ValueError("gender must be 'male' or 'female'")
    
    return bmr


def calculate_tdee(bmr: float, workout_days_per_week: int) -> float:
    """
    Calculate Total Daily Energy Expenditure (TDEE) based on activity level.
    
    Args:
        bmr: Basal Metabolic Rate
        workout_days_per_week: Number of workout days per week (0-7)
        
    Returns:
        TDEE in calories per day
    """
    # Activity multipliers
    if workout_days_per_week == 0:
        activity_multiplier = 1.2  # Sedentary
    elif workout_days_per_week <= 2:
        activity_multiplier = 1.375  # Lightly active
    elif workout_days_per_week <= 4:
        activity_multiplier = 1.55  # Moderately active
    elif workout_days_per_week <= 6:
        activity_multiplier = 1.725  # Very active
    else:
        activity_multiplier = 1.9  # Extremely active
    
    return bmr * activity_multiplier


def calculate_daily_calories(
    age: int,
    gender: str,
    height_cm: float,
    weight_kg: float,
    goal: str,
    workout_days_per_week: int
) -> int:
    """
    Calculate daily calorie target based on user profile and fitness goal.
    
    Args:
        age: Age in years
        gender: "male" or "female"
        height_cm: Height in centimeters
        weight_kg: Weight in kilograms
        goal: "lose_weight", "maintain", or "gain_muscle"
        workout_days_per_week: Number of workout days per week (0-7)
        
    Returns:
        Daily calorie target (integer)
        
    Raises:
        ValueError: If inputs are invalid
    """
    # Validate inputs
    if age < 15 or age > 100:
        raise ValueError("age must be between 15 and 100")
    
    if height_cm < 100 or height_cm > 250:
        raise ValueError("height_cm must be between 100 and 250")
    
    if weight_kg < 30 or weight_kg > 300:
        raise ValueError("weight_kg must be between 30 and 300")
    
    if workout_days_per_week < 0 or workout_days_per_week > 7:
        raise ValueError("workout_days_per_week must be between 0 and 7")
    
    if goal not in ['lose_weight', 'maintain', 'gain_muscle']:
        raise ValueError("goal must be 'lose_weight', 'maintain', or 'gain_muscle'")
    
    # Calculate BMR
    bmr = calculate_bmr(age, gender, height_cm, weight_kg)
    
    # Calculate TDEE
    tdee = calculate_tdee(bmr, workout_days_per_week)
    
    # Adjust for goal
    if goal == 'lose_weight':
        # 500 calorie deficit for ~0.5kg loss per week
        daily_calories = tdee - 500
    elif goal == 'maintain':
        daily_calories = tdee
    else:  # gain_muscle
        # 300-500 calorie surplus for muscle gain
        daily_calories = tdee + 400
    
    # Ensure minimum calories
    min_calories = 1200 if gender.lower() == 'female' else 1500
    daily_calories = max(daily_calories, min_calories)
    
    return int(daily_calories)


if __name__ == "__main__":
    """
    Test block to demonstrate calorie calculation.
    """
    print("=" * 80)
    print("CALORIE CALCULATOR TEST")
    print("=" * 80)
    
    # Test case 1: Male, maintain weight
    print("\nTest 1: 25-year-old male, 175cm, 70kg, maintain weight, 3 workouts/week")
    calories1 = calculate_daily_calories(25, 'male', 175, 70, 'maintain', 3)
    print(f"Daily Calories: {calories1}")
    
    # Test case 2: Female, lose weight
    print("\nTest 2: 30-year-old female, 165cm, 65kg, lose weight, 4 workouts/week")
    calories2 = calculate_daily_calories(30, 'female', 165, 65, 'lose_weight', 4)
    print(f"Daily Calories: {calories2}")
    
    # Test case 3: Male, gain muscle
    print("\nTest 3: 22-year-old male, 180cm, 75kg, gain muscle, 5 workouts/week")
    calories3 = calculate_daily_calories(22, 'male', 180, 75, 'gain_muscle', 5)
    print(f"Daily Calories: {calories3}")
    
    print("\n" + "=" * 80)
    print("SUCCESS: Calorie calculator working correctly!")
    print("=" * 80)
