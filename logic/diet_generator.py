"""
WellFit Diet Generator Module

This module provides rule-based diet generation logic.
Generates budget-aware meal plans based on calorie targets and dietary preferences.

Architecture Rules:
- Rule-based logic only (no ML)
- No database
- No UI formatting
- Logic only
"""

import pandas as pd
import sys
from typing import List, Dict


def generate_diet_plan(
    daily_calories: int,
    diet_type: str,
    daily_budget: float,
    food_nutrition: pd.DataFrame,
    food_prices: pd.DataFrame
) -> List[Dict]:
    """
    Generate a 1-day diet plan based on calorie target, diet type, and budget.
    
    Args:
        daily_calories: Target daily calorie intake
        diet_type: "veg" or "non-veg"
        daily_budget: Maximum daily budget for food
        food_nutrition: DataFrame with nutritional information
        food_prices: DataFrame with food prices
        
    Returns:
        List of dictionaries containing:
            - food_name: Name of the food
            - quantity_g: Quantity in grams
            - calories: Total calories for this food item
            - protein_g: Total protein in grams
            - cost: Estimated cost
            
    Raises:
        ValueError: If diet_type is invalid or budget is too low
    """
    # Validate inputs
    if diet_type not in ["veg", "non-veg"]:
        raise ValueError("diet_type must be 'veg' or 'non-veg'")
    
    if daily_budget <= 0:
        raise ValueError("daily_budget must be positive")
    
    if daily_calories <= 0:
        raise ValueError("daily_calories must be positive")
    
    # Filter foods based on diet type
    if diet_type == "veg":
        available_foods = food_nutrition[food_nutrition['is_vegetarian'] == True].copy()
    else:
        # Non-veg can include both veg and non-veg foods
        available_foods = food_nutrition.copy()
    
    # Merge with price data
    merged_data = available_foods.merge(
        food_prices[['food_name', 'price_per_kg']],
        left_on='name',
        right_on='food_name',
        how='left'
    )
    
    # Handle missing prices by setting a default high price (to deprioritize)
    merged_data['price_per_kg'] = merged_data['price_per_kg'].fillna(999999)
    
    # Calculate protein-to-calorie ratio (higher is better)
    merged_data['protein_ratio'] = merged_data['protein_g'] / (merged_data['calories_per_100g'] + 1)
    
    # Calculate cost efficiency (calories per rupee)
    merged_data['cost_efficiency'] = merged_data['calories_per_100g'] / (merged_data['price_per_kg'] / 10 + 0.01)
    
    # Create a composite score
    if daily_budget < 100:
        # Low budget: Survival Mode. Prioritize Calories per Rupee above all else.
        # Super-heavy weight on cost efficiency (90%)
        merged_data['score'] = (merged_data['protein_ratio'] * 10) + (merged_data['cost_efficiency'] * 90)
    elif daily_budget < 300:
        # Medium budget (100-300 Rs): Balance protein quality and cost efficiency
        # Equal weight to both factors
        merged_data['score'] = (merged_data['protein_ratio'] * 50) + (merged_data['cost_efficiency'] * 50)
    else:
        # High budget (300+ Rs): Prioritize protein quality
        # Heavy weight on protein, light weight on cost
        merged_data['score'] = (merged_data['protein_ratio'] * 80) + (merged_data['cost_efficiency'] * 20)
    
    # Ensure non-veg users actually get non-veg foods by boosting their score
    if diet_type == "non-veg":
        merged_data.loc[merged_data['is_vegetarian'] == False, 'score'] *= 2.0

    # Sort by score (descending)
    merged_data = merged_data.sort_values('score', ascending=False)
    
    # Generate meal plan
    meal_plan = []
    total_calories = 0
    total_cost = 0
    
    # Meal distribution (approximate percentages)
    # Breakfast: 25%, Lunch: 35%, Snack: 10%, Dinner: 30%
    meal_targets = [
        ("Breakfast", 0.25),
        ("Lunch", 0.35),
        ("Snack", 0.10),
        ("Dinner", 0.30)
    ]
    
    used_foods = set()
    
    for meal_name, meal_percentage in meal_targets:
        # For low budget, allow repeating foods across meals (e.g. eating Rice/Dal twice)
        if daily_budget < 100:
            used_foods = set()
            
        meal_calories_target = daily_calories * meal_percentage
        meal_budget = daily_budget * meal_percentage
        meal_calories = 0
        meal_cost = 0
        
        # Select 2-4 foods per meal (more for low budget to Combine items)
        foods_in_meal = 0
        max_foods_per_meal = 5 if daily_budget < 100 else 3
        
        for _, food in merged_data.iterrows():
            if foods_in_meal >= max_foods_per_meal:
                break
            
            # Skip if already used (for variety)
            if food['name'] in used_foods:
                continue
            
            # Calculate how much we need
            remaining_calories = meal_calories_target - meal_calories
            if remaining_calories <= 0:
                break
            
            # Start with a reasonable portion
            if foods_in_meal == 0:
                # Main item gets more calories
                portion_calories = min(remaining_calories * 0.6, remaining_calories)
            else:
                # Side items get less
                portion_calories = min(remaining_calories * 0.4, remaining_calories)
            
            # Calculate quantity needed (in grams)
            quantity_g = (portion_calories / food['calories_per_100g']) * 100
            quantity_g = round(quantity_g)
            
            if quantity_g < 10:  # Skip very small portions
                continue
            
            # Calculate cost
            cost = (quantity_g / 1000) * food['price_per_kg']
            
            # Check if we're within budget
            if total_cost + meal_cost + cost > daily_budget:
                # Try a smaller portion
                affordable_quantity = ((daily_budget - total_cost - meal_cost) / food['price_per_kg']) * 1000
                if affordable_quantity < 10:
                    continue
                quantity_g = round(affordable_quantity)
                cost = (quantity_g / 1000) * food['price_per_kg']
                portion_calories = (quantity_g / 100) * food['calories_per_100g']
            
            # Add to meal plan
            meal_plan.append({
                'meal': meal_name,
                'food_name': food['name'],
                'quantity_g': int(quantity_g),
                'calories': round(portion_calories, 1),
                'protein_g': round((quantity_g / 100) * food['protein_g'], 1),
                'cost': round(cost, 2)
            })
            
            meal_calories += portion_calories
            meal_cost += cost
            total_calories += portion_calories
            total_cost += cost
            used_foods.add(food['name'])
            foods_in_meal += 1
    
    # Check if we met minimum requirements
    if total_calories < daily_calories * 0.7:
        raise ValueError(f"Unable to generate adequate meal plan. Only {int(total_calories)} calories achieved. Budget may be too low.")
    
    if total_cost > daily_budget:
        raise ValueError(f"Unable to stay within budget. Total cost: Rs.{total_cost:.2f}")
    
    return meal_plan


def print_diet_plan(meal_plan: List[Dict]) -> None:
    """
    Print a formatted diet plan.
    
    Args:
        meal_plan: List of meal items from generate_diet_plan()
    """
    print("\n" + "=" * 80)
    print("DAILY DIET PLAN")
    print("=" * 80)
    
    current_meal = None
    meal_totals = {}
    
    for item in meal_plan:
        meal = item['meal']
        
        # Print meal header
        if meal != current_meal:
            if current_meal is not None:
                print()
            print(f"\n{meal.upper()}")
            print("-" * 80)
            current_meal = meal
            meal_totals[meal] = {'calories': 0, 'protein': 0, 'cost': 0}
        
        # Print food item
        print(f"  {item['food_name']:30s} {item['quantity_g']:4d}g  "
              f"Calories: {item['calories']:6.1f}  "
              f"Protein: {item['protein_g']:5.1f}g  "
              f"Cost: Rs.{item['cost']:6.2f}")
        
        # Update meal totals
        meal_totals[meal]['calories'] += item['calories']
        meal_totals[meal]['protein'] += item['protein_g']
        meal_totals[meal]['cost'] += item['cost']
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_calories = sum(item['calories'] for item in meal_plan)
    total_protein = sum(item['protein_g'] for item in meal_plan)
    total_cost = sum(item['cost'] for item in meal_plan)
    
    print(f"\nTotal Calories: {total_calories:.1f} kcal")
    print(f"Total Protein:  {total_protein:.1f} g")
    print(f"Total Cost:     Rs.{total_cost:.2f}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    """
    Test block to generate and print a sample diet plan.
    """
    print("Loading CSV data...")
    
    try:
        # Import data loader
        from data_loader import load_food_nutrition, load_food_prices
        
        # Load data
        food_nutrition = load_food_nutrition()
        food_prices = load_food_prices()
        
        print(f"Loaded {len(food_nutrition)} food items with nutrition data")
        print(f"Loaded {len(food_prices)} food items with price data")
        
        # Test parameters
        daily_calories = 2000
        diet_type = "veg"
        daily_budget = 200.0
        
        print(f"\nGenerating diet plan:")
        print(f"  Target Calories: {daily_calories} kcal")
        print(f"  Diet Type: {diet_type}")
        print(f"  Daily Budget: Rs.{daily_budget}")
        
        # Generate diet plan
        meal_plan = generate_diet_plan(
            daily_calories=daily_calories,
            diet_type=diet_type,
            daily_budget=daily_budget,
            food_nutrition=food_nutrition,
            food_prices=food_prices
        )
        
        # Print the plan
        print_diet_plan(meal_plan)
        
        print("\nSUCCESS: Diet plan generated successfully!")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
