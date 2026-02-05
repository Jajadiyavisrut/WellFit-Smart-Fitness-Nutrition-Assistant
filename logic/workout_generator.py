"""
WellFit Workout Generator Module

This module provides rule-based workout generation logic.
Generates weekly workout plans based on fitness goals, experience level, and schedule.

Architecture Rules:
- Rule-based logic only (no ML)
- No pain handling
- No database
- Logic only
"""

import pandas as pd
import sys
from typing import List, Dict


def generate_workout_plan(
    fitness_goal: str,
    experience_level: str,
    workout_days_per_week: int,
    workout_time_minutes: int,
    exercises: pd.DataFrame
) -> Dict:
    """
    Generate a weekly workout plan based on user parameters.
    
    Args:
        fitness_goal: "fat_loss", "muscle_gain", or "endurance"
        experience_level: "beginner" or "intermediate"
        workout_days_per_week: Number of workout days per week (3-6)
        workout_time_minutes: Available workout time per session
        exercises: DataFrame with exercise data
        
    Returns:
        Dictionary containing:
            - goal: Fitness goal
            - level: Experience level
            - days_per_week: Number of workout days
            - split_type: Type of workout split used
            - weekly_plan: List of daily workout sessions
            
    Raises:
        ValueError: If parameters are invalid
    """
    # Validate inputs
    if fitness_goal not in ["fat_loss", "muscle_gain", "endurance"]:
        raise ValueError("fitness_goal must be 'fat_loss', 'muscle_gain', or 'endurance'")
    
    if experience_level not in ["beginner", "intermediate"]:
        raise ValueError("experience_level must be 'beginner' or 'intermediate'")
    
    if workout_days_per_week < 3 or workout_days_per_week > 6:
        raise ValueError("workout_days_per_week must be between 3 and 6")
    
    if workout_time_minutes < 20 or workout_time_minutes > 120:
        raise ValueError("workout_time_minutes must be between 20 and 120")
    
    # Filter exercises by experience level
    if experience_level == "beginner":
        available_exercises = exercises[
            (exercises['is_beginner_safe'] == True) | 
            (exercises['difficulty'] == 'beginner')
        ].copy()
    else:
        # Intermediate can use beginner and intermediate exercises
        available_exercises = exercises[
            exercises['difficulty'].isin(['beginner', 'intermediate'])
        ].copy()
    
    # Determine workout split based on days per week
    split_type, workout_split = _get_workout_split(workout_days_per_week, fitness_goal)
    
    # Generate daily workouts
    weekly_plan = []
    
    for day_num, day_info in enumerate(workout_split, 1):
        day_name = day_info['name']
        focus_areas = day_info['focus']
        
        # Generate workout for this day
        daily_workout = _generate_daily_workout(
            day_name=day_name,
            focus_areas=focus_areas,
            fitness_goal=fitness_goal,
            experience_level=experience_level,
            workout_time_minutes=workout_time_minutes,
            available_exercises=available_exercises
        )
        
        weekly_plan.append(daily_workout)
    
    return {
        'goal': fitness_goal,
        'level': experience_level,
        'days_per_week': workout_days_per_week,
        'split_type': split_type,
        'weekly_plan': weekly_plan
    }


def _get_workout_split(days_per_week: int, fitness_goal: str) -> tuple:
    """
    Determine the workout split based on days per week and fitness goal.
    
    Returns:
        Tuple of (split_type, workout_split_list)
    """
    if days_per_week == 3:
        split_type = "Full Body (3x/week)"
        workout_split = [
            {'name': 'Day 1 - Full Body', 'focus': ['upper', 'lower', 'core']},
            {'name': 'Day 2 - Full Body', 'focus': ['upper', 'lower', 'core']},
            {'name': 'Day 3 - Full Body', 'focus': ['upper', 'lower', 'core']}
        ]
    elif days_per_week == 4:
        split_type = "Upper/Lower Split"
        workout_split = [
            {'name': 'Day 1 - Upper Body', 'focus': ['upper', 'core']},
            {'name': 'Day 2 - Lower Body', 'focus': ['lower', 'core']},
            {'name': 'Day 3 - Upper Body', 'focus': ['upper', 'core']},
            {'name': 'Day 4 - Lower Body', 'focus': ['lower', 'core']}
        ]
    elif days_per_week == 5:
        split_type = "Push/Pull/Legs"
        workout_split = [
            {'name': 'Day 1 - Push', 'focus': ['chest', 'shoulders', 'triceps']},
            {'name': 'Day 2 - Pull', 'focus': ['back', 'biceps']},
            {'name': 'Day 3 - Legs', 'focus': ['legs', 'core']},
            {'name': 'Day 4 - Push', 'focus': ['chest', 'shoulders', 'triceps']},
            {'name': 'Day 5 - Pull', 'focus': ['back', 'biceps', 'core']}
        ]
    else:  # 6 days
        split_type = "Push/Pull/Legs (2x/week)"
        workout_split = [
            {'name': 'Day 1 - Push', 'focus': ['chest', 'shoulders', 'triceps']},
            {'name': 'Day 2 - Pull', 'focus': ['back', 'biceps']},
            {'name': 'Day 3 - Legs', 'focus': ['legs', 'core']},
            {'name': 'Day 4 - Push', 'focus': ['chest', 'shoulders', 'triceps']},
            {'name': 'Day 5 - Pull', 'focus': ['back', 'biceps']},
            {'name': 'Day 6 - Legs', 'focus': ['legs', 'core']}
        ]
    
    return split_type, workout_split


def _generate_daily_workout(
    day_name: str,
    focus_areas: List[str],
    fitness_goal: str,
    experience_level: str,
    workout_time_minutes: int,
    available_exercises: pd.DataFrame
) -> Dict:
    """
    Generate a single day's workout.
    
    Returns:
        Dictionary with day_name and exercises list
    """
    # Filter exercises by focus areas
    focused_exercises = available_exercises[
        available_exercises['muscle_groups'].str.contains('|'.join(focus_areas), case=False, na=False) |
        available_exercises['body_part'].str.contains('|'.join(focus_areas), case=False, na=False)
    ].copy()
    
    # If no exercises found, use broader category filter
    if len(focused_exercises) == 0:
        focused_exercises = available_exercises[
            available_exercises['category'] == 'strength'
        ].copy()
    
    # Determine number of exercises based on time
    if workout_time_minutes <= 30:
        num_exercises = 4
    elif workout_time_minutes <= 45:
        num_exercises = 5
    elif workout_time_minutes <= 60:
        num_exercises = 6
    else:
        num_exercises = 7
    
    # Select exercises
    selected_exercises = []
    
    # Prioritize compound movements for first exercises
    compound_exercises = focused_exercises[
        focused_exercises['name'].str.contains('squat|deadlift|press|pull|row|lunge', case=False, na=False)
    ]
    
    # Get strength exercises
    strength_exercises = focused_exercises[focused_exercises['category'] == 'strength']
    
    # Mix of compound and isolation
    exercises_to_select = pd.concat([compound_exercises, strength_exercises]).drop_duplicates()
    
    if len(exercises_to_select) < num_exercises:
        exercises_to_select = focused_exercises
    
    # Sample exercises
    if len(exercises_to_select) >= num_exercises:
        selected = exercises_to_select.sample(n=min(num_exercises, len(exercises_to_select)))
    else:
        selected = exercises_to_select
    
    # Assign sets and reps based on goal and experience
    for _, exercise in selected.iterrows():
        sets, reps = _get_sets_and_reps(fitness_goal, experience_level, exercise)
        
        selected_exercises.append({
            'name': exercise['name'],
            'category': exercise['category'],
            'muscle_groups': exercise['muscle_groups'],
            'equipment': exercise['equipment'],
            'sets': sets,
            'reps': reps,
            'rest_seconds': int(exercise['rest_time_seconds']) if pd.notna(exercise['rest_time_seconds']) else 60,
            'instructions': exercise['instructions'][:100] + '...' if pd.notna(exercise['instructions']) and len(str(exercise['instructions'])) > 100 else exercise['instructions']
        })
    
    # Add core exercise if not in focus
    if 'core' not in focus_areas and len(selected_exercises) < num_exercises:
        core_exercises = available_exercises[
            available_exercises['category'] == 'core'
        ]
        if len(core_exercises) > 0:
            core_ex = core_exercises.sample(n=1).iloc[0]
            sets, reps = _get_sets_and_reps(fitness_goal, experience_level, core_ex)
            selected_exercises.append({
                'name': core_ex['name'],
                'category': core_ex['category'],
                'muscle_groups': core_ex['muscle_groups'],
                'equipment': core_ex['equipment'],
                'sets': sets,
                'reps': reps,
                'rest_seconds': 45,
                'instructions': core_ex['instructions'][:100] + '...' if pd.notna(core_ex['instructions']) and len(str(core_ex['instructions'])) > 100 else core_ex['instructions']
            })
    
    return {
        'day_name': day_name,
        'exercises': selected_exercises
    }


def _get_sets_and_reps(fitness_goal: str, experience_level: str, exercise: pd.Series) -> tuple:
    """
    Determine sets and reps based on fitness goal and experience level.
    
    Returns:
        Tuple of (sets, reps)
    """
    # Use exercise's target if available
    if pd.notna(exercise.get('target_sets')) and pd.notna(exercise.get('target_reps')):
        base_sets = int(exercise['target_sets'])
        base_reps = exercise['target_reps']
    else:
        base_sets = 3
        base_reps = "10-12"
    
    # Adjust based on goal
    if fitness_goal == "muscle_gain":
        if experience_level == "beginner":
            sets = 3
            reps = "8-12"
        else:
            sets = 4
            reps = "8-12"
    elif fitness_goal == "fat_loss":
        if experience_level == "beginner":
            sets = 3
            reps = "12-15"
        else:
            sets = 3
            reps = "12-15"
    else:  # endurance
        if experience_level == "beginner":
            sets = 2
            reps = "15-20"
        else:
            sets = 3
            reps = "15-20"
    
    # For cardio exercises, adjust
    if exercise['category'] == 'cardio':
        sets = 1
        reps = "10-15 min"
    elif exercise['category'] == 'core':
        sets = 3
        reps = "15-20"
    
    return sets, reps


def print_workout_plan(plan: Dict) -> None:
    """
    Print a formatted workout plan.
    
    Args:
        plan: Workout plan dictionary from generate_workout_plan()
    """
    print("\n" + "=" * 80)
    print("WEEKLY WORKOUT PLAN")
    print("=" * 80)
    print(f"\nGoal: {plan['goal'].replace('_', ' ').title()}")
    print(f"Experience Level: {plan['level'].title()}")
    print(f"Workout Days: {plan['days_per_week']} days/week")
    print(f"Split Type: {plan['split_type']}")
    print("=" * 80)
    
    for day in plan['weekly_plan']:
        print(f"\n{day['day_name'].upper()}")
        print("-" * 80)
        
        for i, exercise in enumerate(day['exercises'], 1):
            print(f"\n{i}. {exercise['name']}")
            print(f"   Muscle Groups: {exercise['muscle_groups']}")
            print(f"   Equipment: {exercise['equipment']}")
            print(f"   Sets x Reps: {exercise['sets']} x {exercise['reps']}")
            print(f"   Rest: {exercise['rest_seconds']}s")
    
    print("\n" + "=" * 80)
    print("WORKOUT PLAN COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    """
    Test block to generate and print a sample workout plan.
    """
    print("Loading exercise data...")
    
    try:
        # Import data loader
        from data_loader import load_exercises
        
        # Load data
        exercises = load_exercises()
        
        print(f"Loaded {len(exercises)} exercises")
        
        # Test parameters
        fitness_goal = "muscle_gain"
        experience_level = "beginner"
        workout_days_per_week = 4
        workout_time_minutes = 60
        
        print(f"\nGenerating workout plan:")
        print(f"  Fitness Goal: {fitness_goal}")
        print(f"  Experience Level: {experience_level}")
        print(f"  Workout Days: {workout_days_per_week} days/week")
        print(f"  Workout Time: {workout_time_minutes} minutes/session")
        
        # Generate workout plan
        plan = generate_workout_plan(
            fitness_goal=fitness_goal,
            experience_level=experience_level,
            workout_days_per_week=workout_days_per_week,
            workout_time_minutes=workout_time_minutes,
            exercises=exercises
        )
        
        # Print the plan
        print_workout_plan(plan)
        
        print("\nSUCCESS: Workout plan generated successfully!")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
