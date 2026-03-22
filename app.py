"""
WellFit Flask Backend API

This module provides REST APIs for WellFit logic modules.
Includes authentication and session management.
"""

from flask import Flask, request, jsonify, session, render_template, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sys
import os
import time
import smtplib

# Load .env variables into os.environ BEFORE anything else reads them
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on real environment variables

# Add logic directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logic'))

# Import logic modules
from data_loader import (
    load_exercises,
    load_food_nutrition,
    load_food_prices,
    load_pain_keywords,
    load_exercise_contraindications,
    load_recovery_exercises
)
from calorie_calculator import calculate_daily_calories
from diet_generator import generate_diet_plan
from workout_generator import generate_workout_plan
from pain_handler import modify_workout_for_pain

# Add database directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'database'))
from db import get_db, execute_query, execute_insert

# Add utils directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
from validators import (
    validate_required_fields,
    validate_email,
    validate_password,
    validate_profile_data
)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv not installed; use system env vars

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize Supabase client
from supabase import create_client, Client
SUPABASE_URL = app.config.get('SUPABASE_URL')
SUPABASE_KEY = app.config.get('SUPABASE_KEY')

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("WARNING: SUPABASE_URL or SUPABASE_KEY missing in config.")
    supabase = None

# Configure secret key for sessions
# In production, use environment variable
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


# ============================================================================
# AUTHENTICATION HELPERS
# ============================================================================

def login_required(f):
    """
    Decorator to protect routes that require authentication.
    Checks if user_id exists in session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please login to access this resource'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


# Load CSV data once at startup
print("Loading CSV data...")
try:
    EXERCISES = load_exercises()
    FOOD_NUTRITION = load_food_nutrition()
    FOOD_PRICES = load_food_prices()
    PAIN_KEYWORDS = load_pain_keywords()
    EXERCISE_CONTRAINDICATIONS = load_exercise_contraindications()
    RECOVERY_EXERCISES = load_recovery_exercises()
    print(f"Data loaded successfully!")
    print(f"  - {len(EXERCISES)} exercises")
    print(f"  - {len(FOOD_NUTRITION)} food items (nutrition)")
    print(f"  - {len(FOOD_PRICES)} food items (prices)")
    print(f"  - {len(PAIN_KEYWORDS)} pain keywords")
    print(f"  - {len(EXERCISE_CONTRAINDICATIONS)} contraindications")
    print(f"  - {len(RECOVERY_EXERCISES)} recovery exercises")
except Exception as e:
    print(f"ERROR loading data: {e}")
    sys.exit(1)

# Build exercise name → image URL lookup from free-exercise-db (GitHub)
# Images served directly from GitHub raw CDN – no local storage needed.
EXERCISE_GIF_LOOKUP = {}  # lowercase name → full https image URL
_FREE_DB_BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"
try:
    import urllib.request as _req
    import json as _json
    _db_url = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
    with _req.urlopen(_db_url, timeout=8) as _resp:
        _free_exercises = _json.loads(_resp.read().decode())
    for _ex in _free_exercises:
        _name_key = _ex.get('name', '').lower().strip()
        _images = _ex.get('images', [])
        if _name_key and _images:
            # Use the first image (frame 0) served from GitHub raw CDN
            EXERCISE_GIF_LOOKUP[_name_key] = _FREE_DB_BASE + _images[0]
    print(f"  - {len(EXERCISE_GIF_LOOKUP)} exercise images loaded from free-exercise-db")
except Exception as _e:
    print(f"WARNING: Could not load free-exercise-db images (offline?): {_e}")
    # Fallback: try local exercises.json (old GIF lookup)
    try:
        import json as _json
        _raw_exercises_path = os.path.join(os.path.dirname(__file__), 'data', 'raw', 'exercises.json')
        with open(_raw_exercises_path, 'r') as _f:
            _raw_exercises = _json.load(_f)
        for _ex in _raw_exercises:
            _name_key = _ex.get('name', '').lower().strip()
            _gif = _ex.get('gifUrl', '')
            if _name_key and _gif:
                EXERCISE_GIF_LOOKUP[_name_key] = f'/gifs/{_gif}'
        print(f"  - {len(EXERCISE_GIF_LOOKUP)} exercise GIFs loaded from local fallback")
    except Exception as _e2:
        print(f"WARNING: Local fallback also failed: {_e2}")
        EXERCISE_GIF_LOOKUP = {}


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def index():
    """Redirect to login page"""
    return redirect('/login.html')


@app.route('/login.html')
def login_page():
    """Serve login page"""
    return render_template('login.html')


@app.route('/register.html')
def register_page():
    """Serve register page"""
    return render_template('register.html')


@app.route('/profile.html')
def profile_page():
    """Serve profile page"""
    return render_template('profile.html')


@app.route('/dashboard.html')
def dashboard_page():
    """Serve dashboard page"""
    return render_template('dashboard.html')


@app.route('/gifs/<path:filename>')
def serve_gif(filename):
    """Serve exercise GIF files from data/raw/gifs_180x180/"""
    from flask import send_from_directory
    gif_dir = os.path.join(os.path.dirname(__file__), 'data', 'raw', 'gifs_180x180')
    return send_from_directory(gif_dir, filename)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON: { "status": "ok" }
    """
    return jsonify({
        'status': 'ok',
        'message': 'WellFit API is running',
        'version': '1.0.0'
    })


@app.route('/db-test', methods=['GET'])
def database_test():
    """
    Database connection test endpoint.
    Tests basic read/write operations.
    
    Returns:
        JSON: Database test results
    """
    try:
        # Test 1: Insert dummy user if not exists
        existing_users = execute_query(
            "SELECT * FROM users WHERE email = ?",
            ('test@wellfit.com',)
        )
        
        if not existing_users:
            user_id = execute_insert(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                ('test@wellfit.com', 'dummy_hash_for_testing')
            )
            message = f"Created test user (ID: {user_id})"
        else:
            user_id = existing_users[0]['id']
            message = f"Test user already exists (ID: {user_id})"
        
        # Test 2: Fetch all users
        all_users = execute_query("SELECT id, email, created_at FROM users")
        
        # Convert Row objects to dicts
        users_list = [dict(row) for row in all_users]
        
        return jsonify({
            'success': True,
            'message': message,
            'database_status': 'connected',
            'total_users': len(users_list),
            'users': users_list
        })
        
    except FileNotFoundError as e:
        return jsonify({
            'success': False,
            'error': 'Database file not found',
            'details': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Database operation failed',
            'details': str(e)
        }), 500


# ============================================================================
# AUTHENTICATION APIS
# ============================================================================

@app.route('/api/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Request Body:
        {
            "email": str,
            "password": str
        }
    
    Returns:
        JSON: Success message with user_id
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        is_valid, error = validate_required_fields(data, ['email', 'password'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate email
        is_valid, error = validate_email(email)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Validate password
        is_valid, error = validate_password(password)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Check if user already exists
        existing_user = execute_query(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        )
        
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Supabase Auth Sign Up
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            if not res.user:
                return jsonify({'error': 'Registration failed with Supabase.'}), 500
        except Exception as e:
            # Handle Supabase errors cleanly without crashing
            error_msg = str(e)
            if "already registered" in error_msg.lower():
                return jsonify({'error': 'Email already registered'}), 409
            return jsonify({'error': f'Supabase Registration Error: {error_msg}'}), 400
        
        # Insert new user into our mapping table
        user_id = execute_insert(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, 'SUPABASE_AUTH')
        )
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully with Supabase',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """
    Login user and create session.
    
    Request Body:
        {
            "email": str,
            "password": str
        }
    
    Returns:
        JSON: Success message with user info
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        is_valid, error = validate_required_fields(data, ['email', 'password'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Fetch user from local mapping
        user = execute_query(
            "SELECT id, email, password_hash FROM users WHERE email = ?",
            (email,)
        )
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        user_data = dict(user[0])
        
        # If it's a legacy user (has a hash), verify locally, otherwise use Supabase
        if user_data['password_hash'] != 'SUPABASE_AUTH':
            if not check_password_hash(user_data['password_hash'], password):
                return jsonify({'error': 'Invalid email or password'}), 401
        else:
            # Supabase Auth Sign In
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if not res.session:
                    return jsonify({'error': 'Invalid email or password'}), 401
            except Exception as e:
                return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create session
        session['user_id'] = user_data['id']
        session['email'] = user_data['email']
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user_data['id'],
                'email': user_data['email']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    """
    Logout user and clear session.
    
    Returns:
        JSON: Success message
    """
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    })


# ============================================================================
# PROFILE CRUD APIS
# ============================================================================

@app.route('/api/profile', methods=['POST'])
@login_required
def create_or_update_profile():
    """
    Create or update user profile.
    If profile exists for user_id, it will be updated.
    Otherwise, a new profile will be created.
    
    Request Body:
        {
            "user_id": int,
            "age": int,
            "gender": "male" or "female",
            "height_cm": float,
            "weight_kg": float,
            "fitness_goal": "lose_weight", "maintain", or "gain_muscle",
            "experience_level": "beginner" or "intermediate",
            "workout_days_per_week": int (0-7),
            "workout_time_minutes": int (20-120),
            "diet_type": "veg" or "non-veg",
            "monthly_budget": float,
            "state": str (optional)
        }
    
    Returns:
        JSON: Success message with profile data
    """
    try:
        data = request.get_json()
        
        # Validate complete profile data
        is_valid, error = validate_profile_data(data)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Check if user exists
        user_exists = execute_query(
            "SELECT id FROM users WHERE id = ?",
            (data['user_id'],)
        )
        
        if not user_exists:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if profile already exists
        existing_profile = execute_query(
            "SELECT id FROM user_profiles WHERE user_id = ?",
            (data['user_id'],)
        )
        
        if existing_profile:
            # UPDATE existing profile
            execute_query("""
                UPDATE user_profiles SET
                    age = ?,
                    gender = ?,
                    height_cm = ?,
                    weight_kg = ?,
                    fitness_goal = ?,
                    experience_level = ?,
                    workout_days_per_week = ?,
                    workout_time_minutes = ?,
                    diet_type = ?,
                    monthly_budget = ?,
                    workout_split_preference = ?,
                    state = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                RETURNING id
            """, (
                data['age'],
                data['gender'],
                data['height_cm'],
                data['weight_kg'],
                data['fitness_goal'],
                data['experience_level'],
                data['workout_days_per_week'],
                data['workout_time_minutes'],
                data['diet_type'],
                data['monthly_budget'],
                data.get('workout_split_preference', 'default'),
                data.get('state'),
                data['user_id']
            ))
            message = "Profile updated successfully"
            profile_id = existing_profile[0]['id']
        else:
            # INSERT new profile
            profile_id = execute_insert("""
                INSERT INTO user_profiles (
                    user_id, age, gender, height_cm, weight_kg,
                    fitness_goal, experience_level, workout_days_per_week,
                    workout_time_minutes, diet_type, monthly_budget, workout_split_preference, state
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['user_id'],
                data['age'],
                data['gender'],
                data['height_cm'],
                data['weight_kg'],
                data['fitness_goal'],
                data['experience_level'],
                data['workout_days_per_week'],
                data['workout_time_minutes'],
                data['diet_type'],
                data['monthly_budget'],
                data.get('workout_split_preference', 'default'),
                data.get('state')
            ))
            
            message = "Profile created successfully"
        
        # Fetch the profile to return
        profile = execute_query(
            "SELECT * FROM user_profiles WHERE id = ?",
            (profile_id,)
        )
        
        return jsonify({
            'success': True,
            'message': message,
            'profile': dict(profile[0]) if profile else None
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@app.route('/api/profile/<int:user_id>', methods=['GET'])
@login_required
def get_profile(user_id):
    """
    Get user profile by user_id.
    
    Args:
        user_id: User ID from URL path
        
    Returns:
        JSON: User profile data
    """
    try:
        # Fetch profile
        profile = execute_query(
            "SELECT * FROM user_profiles WHERE user_id = ?",
            (user_id,)
        )
        
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Profile not found'
            }), 404
        
        return jsonify({
            'success': True,
            'profile': dict(profile[0])
        })
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


# ============================================================================
# PLAN GENERATION AND RETRIEVAL APIS
# ============================================================================

@app.route('/api/generate-plan', methods=['POST'])
@login_required
def generate_plan():
    """
    Generate diet and workout plans for logged-in user.
    Fetches user profile, generates plans using logic modules, and saves to database.
    
    Returns:
        JSON: Generated diet and workout plans
    """
    try:
        user_id = session['user_id']
        
        # Fetch user profile
        profile = execute_query(
            "SELECT * FROM user_profiles WHERE user_id = ?",
            (user_id,)
        )
        
        if not profile:
            return jsonify({
                'error': 'Profile not found',
                'message': 'Please create your profile first'
            }), 404
        
        profile_data = dict(profile[0])
        
        # Step 1: Calculate daily calories
        daily_calories = calculate_daily_calories(
            age=profile_data['age'],
            gender=profile_data['gender'],
            height_cm=profile_data['height_cm'],
            weight_kg=profile_data['weight_kg'],
            goal=profile_data['fitness_goal'],
            workout_days_per_week=profile_data['workout_days_per_week']
        )
        
        # Step 2: Generate diet plan
        # Convert monthly budget to daily budget
        daily_budget = profile_data['monthly_budget'] / 30
        
        diet_plan = generate_diet_plan(
            daily_calories=daily_calories,
            diet_type=profile_data['diet_type'],
            daily_budget=daily_budget,
            food_nutrition=FOOD_NUTRITION,
            food_prices=FOOD_PRICES
        )
        
        # Calculate totals
        total_calories = sum(item['calories'] for item in diet_plan)
        total_protein = sum(item['protein_g'] for item in diet_plan)
        total_cost = sum(item['cost'] for item in diet_plan)
        
        # Step 3: Generate workout plan
        # Map profile fitness_goal to workout generator format
        goal_mapping = {
            'lose_weight': 'fat_loss',
            'maintain': 'endurance',
            'gain_muscle': 'muscle_gain'
        }
        workout_goal = goal_mapping.get(profile_data['fitness_goal'], 'endurance')
        
        workout_plan = generate_workout_plan(
            fitness_goal=workout_goal,
            experience_level=profile_data['experience_level'],
            workout_days_per_week=int(profile_data['workout_days_per_week']),
            workout_time_minutes=int(profile_data['workout_time_minutes']),
            exercises=EXERCISES,
            split_preference=profile_data.get('workout_split_preference', 'default')
        )
        
        # Step 4: Save diet plan to database
        import json
        diet_plan_id = execute_insert("""
            INSERT INTO diet_plans (
                user_id, plan_date, diet_data, total_cost
            ) VALUES (?, date('now'), ?, ?)
        """, (
            user_id,
            json.dumps(diet_plan),
            total_cost
        ))
        
        # Step 5: Save workout plan to database
        workout_plan_id = execute_insert("""
            INSERT INTO workout_plans (
                user_id, plan_date, workout_data
            ) VALUES (?, date('now'), ?)
        """, (
            user_id,
            json.dumps(workout_plan)
        ))
        
        return jsonify({
            'success': True,
            'message': 'Plans generated successfully',
            'daily_calories': daily_calories,
            'diet_plan': {
                'id': diet_plan_id,
                'meals': diet_plan,
                'total_calories': round(total_calories, 1),
                'total_protein': round(total_protein, 1),
                'total_cost': round(total_cost, 2)
            },
            'workout_plan': {
                'id': workout_plan_id,
                'split_type': workout_plan['split_type'],
                'weekly_plan': workout_plan['weekly_plan']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Plan generation failed: {str(e)}'}), 500


@app.route('/api/today-plan', methods=['GET'])
@login_required
def get_today_plan():
    """
    Get today's diet and workout plans for logged-in user.
    
    Returns:
        JSON: Today's diet and workout plans
    """
    try:
        user_id = session['user_id']
        
        # Fetch most recent diet plan (not just today's)
        diet_plan = execute_query("""
            SELECT id, diet_data, total_cost, created_at, plan_date
            FROM diet_plans
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        
        # Fetch most recent workout plan (not just today's)
        workout_plan = execute_query("""
            SELECT id, workout_data, created_at, plan_date
            FROM workout_plans
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        
        if not diet_plan and not workout_plan:
            return jsonify({
                'success': False,
                'message': 'No plans found',
                'suggestion': 'Generate a new plan using /api/generate-plan'
            }), 404
        
        import json
        response = {
            'success': True
        }
        
        if diet_plan:
            diet_data = dict(diet_plan[0])
            response['diet_plan'] = {
                'id': diet_data['id'],
                'meals': json.loads(diet_data['diet_data']),
                'total_cost': diet_data['total_cost'],
                'created_at': diet_data['created_at'],
                'plan_date': diet_data['plan_date']
            }
        
        if workout_plan:
            workout_data = dict(workout_plan[0])
            plan_json = json.loads(workout_data['workout_data'])
            # Inject gif_url into every exercise using fuzzy name matching
            if 'weekly_plan' in plan_json:
                for day in plan_json['weekly_plan']:
                    for ex in day.get('exercises', []):
                        ex_name_lower = ex.get('name', '').lower().strip()
                        # Direct match
                        gif_file = EXERCISE_GIF_LOOKUP.get(ex_name_lower)
                        # Fuzzy: match first word(s) of exercise name against lookup keys
                        if not gif_file:
                            for key, val in EXERCISE_GIF_LOOKUP.items():
                                if ex_name_lower in key or key in ex_name_lower:
                                    gif_file = val
                                    break
                        ex['gif_url'] = gif_file if gif_file else None
            response['workout_plan'] = {
                'id': workout_data['id'],
                'plan': plan_json,
                'created_at': workout_data['created_at'],
                'plan_date': workout_data['plan_date']
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch plans: {str(e)}'}), 500


@app.route('/api/adapt-workout', methods=['POST'])
@login_required
def adaptive_workout():
    """
    Adapt today's workout based on pain feedback.
    Fetches today's workout, applies pain modifications, updates database, and logs pain report.
    
    Request Body:
        {
            "pain_text": str
        }
    
    Returns:
        JSON: Modified workout plan with pain details
    """
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        # Validate input
        is_valid, error = validate_required_fields(data, ['pain_text'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        pain_text = data['pain_text']
        
        if not isinstance(pain_text, str):
            return jsonify({'error': 'pain_text must be a string'}), 400
        
        pain_text = pain_text.strip()
        
        if not pain_text:
            return jsonify({'error': 'pain_text cannot be empty'}), 400
        
        # Fetch today's workout plan
        workout_plan = execute_query("""
            SELECT id, workout_data
            FROM workout_plans
            WHERE user_id = ? AND plan_date = date('now')
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        
        if not workout_plan:
            return jsonify({
                'error': 'No workout plan found for today',
                'message': 'Please generate a workout plan first using /api/generate-plan'
            }), 404
        
        import json
        workout_data = dict(workout_plan[0])
        workout_plan_id = workout_data['id']
        current_plan = json.loads(workout_data['workout_data'])
        
        # Extract today's workout from weekly plan
        # For simplicity, we'll use the first day's workout
        today_workout = []
        if 'weekly_plan' in current_plan and len(current_plan['weekly_plan']) > 0:
            today_workout = current_plan['weekly_plan'][0].get('exercises', [])
        
        if not today_workout:
            return jsonify({
                'error': 'No exercises found in today\'s workout',
                'message': 'Workout plan may be empty'
            }), 404
        
        # Apply pain modifications using pain_handler
        modification_result = modify_workout_for_pain(
            pain_text=pain_text,
            today_workout_plan=today_workout,
            pain_keywords=PAIN_KEYWORDS,
            exercises_df=EXERCISES,
            exercise_contraindications=EXERCISE_CONTRAINDICATIONS,
            recovery_exercises=RECOVERY_EXERCISES
        )
        
        # Update the workout plan with modified exercises
        current_plan['weekly_plan'][0]['exercises'] = modification_result['modified_workout']
        
        # Save updated workout plan to database
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workout_plans
                SET workout_data = ?
                WHERE id = ?
            """, (json.dumps(current_plan), workout_plan_id))
        
        # Log pain report to database
        pain_report_id = execute_insert("""
            INSERT INTO pain_reports (
                user_id, pain_text, affected_body_part
            ) VALUES (?, ?, ?)
        """, (
            user_id,
            pain_text,
            modification_result['affected_body_part']
        ))
        
        return jsonify({
            'success': True,
            'message': 'Workout adapted based on pain feedback',
            'pain_report_id': pain_report_id,
            'pain_detected': modification_result['pain_detected'],
            'affected_body_part': modification_result['affected_body_part'],
            'severity': modification_result['severity'],
            'medical_attention_needed': modification_result['medical_attention_needed'],
            'immediate_action': modification_result['immediate_action'],
            'modified_workout': modification_result['modified_workout'],
            'removed_exercises': modification_result['removed_exercises'],
            'added_exercises': modification_result['added_exercises'],
            'modification_summary': modification_result['modification_summary']
        })
        
    except Exception as e:
        return jsonify({'error': f'Workout adaptation failed: {str(e)}'}), 500


# @app.route('/api/chat-workout', methods=['POST'])
# @login_required
# def chat_workout():
#     """
#     Chatbot for workout modifications.
#     Processes natural language requests to modify workouts.
#     """
#     try:
#         user_id = session['user_id']
#         data = request.get_json()
#         message = data.get('message', '').lower().strip()
        
#         if not message:
#             return jsonify({'error': 'Message cannot be empty'}), 400
        
#         # Get current workout plan
#         workout_plan = execute_query("""
#             SELECT id, workout_data
#             FROM workout_plans
#             WHERE user_id = ?
#             ORDER BY created_at DESC
#             LIMIT 1
#         """, (user_id,))
        
#         if not workout_plan:
#             return jsonify({
#                 'response': "You don't have a workout plan yet. Please generate one first!",
#                 'workout_modified': False
#             })
        
#         workout_plan_id = workout_plan[0]['id']
#         current_plan = json.loads(workout_plan[0]['workout_data'])
        
#         # Simple keyword-based responses
#         response = ""
#         workout_modified = False
        
#         # Check for pain-related keywords
#         if any(word in message for word in ['pain', 'hurt', 'sore', 'injury', 'ache']):
#             # Extract today's workout from weekly plan
#             today_workout = []
#             if 'weekly_plan' in current_plan and len(current_plan['weekly_plan']) > 0:
#                 today_workout = current_plan['weekly_plan'][0].get('exercises', [])
            
#             # Use pain handler
#             modification_result = modify_workout_for_pain(
#                 pain_text=message,
#                 today_workout_plan=today_workout,
#                 pain_keywords=PAIN_KEYWORDS,
#                 exercises_df=EXERCISES,
#                 exercise_contraindications=EXERCISE_CONTRAINDICATIONS,
#                 recovery_exercises=RECOVERY_EXERCISES
#             )
            
#             if modification_result['pain_detected']:
#                 # Update the first day's exercises with modified workout
#                 current_plan['weekly_plan'][0]['exercises'] = modification_result['modified_workout']
                
#                 # Update workout in database
#                 with get_db() as conn:
#                     cursor = conn.cursor()
#                     cursor.execute("""
#                         UPDATE workout_plans
#                         SET workout_data = ?
#                         WHERE id = ?
#                     """, (json.dumps(current_plan), workout_plan_id))
                
#                 response = f"I've modified your workout to avoid exercises that might aggravate your {modification_result['affected_body_part']} pain. {modification_result['modification_summary']}"
#                 workout_modified = True
#             else:
#                 response = "I understand you're experiencing discomfort. Could you describe which body part hurts?"
        
#         # Check for difficulty adjustments
#         elif any(word in message for word in ['easier', 'reduce', 'lighter', 'beginner']):
#             response = "I can help make your workout easier! To properly adjust it, please update your experience level in your profile to 'Beginner', then generate a new plan."
            
#         elif any(word in message for word in ['harder', 'increase', 'advanced', 'challenging']):
#             response = "Ready for a challenge! To increase difficulty, update your experience level to 'Intermediate' in your profile and generate a new plan."
        
#         # Check for focus area requests
#         elif any(word in message for word in ['arms', 'biceps', 'triceps']):
#             response = "To focus more on arms, I recommend generating a new plan with a Push/Pull/Legs split. This will give you dedicated arm days!"
            
#         elif any(word in message for word in ['legs', 'squat', 'glutes']):
#             response = "For more leg focus, try increasing your workout days to 4-5 per week in your profile. This allows for dedicated leg days!"
            
#         elif any(word in message for word in ['cardio', 'running', 'endurance']):
#             response = "To add more cardio, update your fitness goal to 'Maintain Weight' or 'Lose Weight' in your profile. The system will include more cardio exercises!"
            
#         elif any(word in message for word in ['chest', 'bench']):
#             response = "For chest development, a Push/Pull/Legs or Upper/Lower split works best. Update your workout days to 4+ per week for optimal results!"
        
#         # General help
#         else:
#             response = "I can help you with:\n- Reporting pain or injuries\n- Adjusting workout difficulty\n- Focusing on specific muscle groups\n- Adding cardio\n\nWhat would you like to change?"
        
#         return jsonify({
#             'response': response,
#             'workout_modified': workout_modified
#         })
        
#     except Exception as e:
#         return jsonify({'error': f'Chat failed: {str(e)}'}), 500


@app.route('/api/calories', methods=['POST'])
def calculate_calories():
    """
    Calculate daily calorie needs.
    
    Request Body:
        {
            "age": int,
            "gender": "male" or "female",
            "height_cm": float,
            "weight_kg": float,
            "goal": "lose_weight", "maintain", or "gain_muscle",
            "workout_days": int (0-7)
        }
    
    Returns:
        JSON: {
            "daily_calories": int,
            "bmr": float,
            "tdee": float,
            "goal": str
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['age', 'gender', 'height_cm', 'weight_kg', 'goal', 'workout_days']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Calculate calories
        daily_calories = calculate_daily_calories(
            age=int(data['age']),
            gender=data['gender'],
            height_cm=float(data['height_cm']),
            weight_kg=float(data['weight_kg']),
            goal=data['goal'],
            workout_days_per_week=int(data['workout_days'])
        )
        
        return jsonify({
            'daily_calories': daily_calories,
            'goal': data['goal'],
            'success': True
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@app.route('/api/diet', methods=['POST'])
def generate_diet():
    """
    Generate a daily diet plan.
    
    Request Body:
        {
            "daily_calories": int,
            "diet_type": "veg" or "non-veg",
            "daily_budget": float
        }
    
    Returns:
        JSON: {
            "diet_plan": [...],
            "total_calories": float,
            "total_protein": float,
            "total_cost": float
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['daily_calories', 'diet_type', 'daily_budget']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate diet plan
        meal_plan = generate_diet_plan(
            daily_calories=int(data['daily_calories']),
            diet_type=data['diet_type'],
            daily_budget=float(data['daily_budget']),
            food_nutrition=FOOD_NUTRITION,
            food_prices=FOOD_PRICES
        )
        
        # Calculate totals
        total_calories = sum(item['calories'] for item in meal_plan)
        total_protein = sum(item['protein_g'] for item in meal_plan)
        total_cost = sum(item['cost'] for item in meal_plan)
        
        return jsonify({
            'diet_plan': meal_plan,
            'total_calories': round(total_calories, 1),
            'total_protein': round(total_protein, 1),
            'total_cost': round(total_cost, 2),
            'success': True
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@app.route('/api/workout', methods=['POST'])
def generate_workout():
    """
    Generate a weekly workout plan.
    
    Request Body:
        {
            "goal": "fat_loss", "muscle_gain", or "endurance",
            "experience": "beginner" or "intermediate",
            "workout_days": int (3-6),
            "workout_time": int (20-120 minutes)
        }
    
    Returns:
        JSON: {
            "weekly_plan": [...],
            "split_type": str,
            "goal": str,
            "level": str
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['goal', 'experience', 'workout_days', 'workout_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate workout plan
        plan = generate_workout_plan(
            fitness_goal=data['goal'],
            experience_level=data['experience'],
            workout_days_per_week=int(data['workout_days']),
            workout_time_minutes=int(data['workout_time']),
            exercises=EXERCISES
        )
        
        return jsonify({
            'weekly_plan': plan['weekly_plan'],
            'split_type': plan['split_type'],
            'goal': plan['goal'],
            'level': plan['level'],
            'days_per_week': plan['days_per_week'],
            'success': True
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@app.route('/api/pain', methods=['POST'])
def handle_pain():
    """
    Modify workout based on reported pain.
    
    Request Body:
        {
            "pain_text": str,
            "today_workout_plan": [
                {
                    "name": str,
                    "category": str,
                    "muscle_groups": str,
                    "equipment": str,
                    "sets": int,
                    "reps": str,
                    "rest_seconds": int
                },
                ...
            ]
        }
    
    Returns:
        JSON: {
            "pain_detected": bool,
            "affected_body_part": str or null,
            "severity": str,
            "modified_workout": [...],
            "removed_exercises": [...],
            "added_exercises": [...],
            "modification_summary": str
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['pain_text', 'today_workout_plan']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Modify workout based on pain
        result = modify_workout_for_pain(
            pain_text=data['pain_text'],
            today_workout_plan=data['today_workout_plan'],
            pain_keywords=PAIN_KEYWORDS,
            exercises_df=EXERCISES,
            exercise_contraindications=EXERCISE_CONTRAINDICATIONS,
            recovery_exercises=RECOVERY_EXERCISES
        )
        
        return jsonify({
            'pain_detected': result['pain_detected'],
            'affected_body_part': result['affected_body_part'],
            'severity': result['severity'],
            'medical_attention_needed': result['medical_attention_needed'],
            'immediate_action': result['immediate_action'],
            'modified_workout': result['modified_workout'],
            'removed_exercises': result['removed_exercises'],
            'added_exercises': result['added_exercises'],
            'modification_summary': result['modification_summary'],
            'success': True
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({'error': 'Method not allowed'}), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("WellFit Flask API Server")
    print("=" * 80)
    print("\nAvailable Endpoints:")
    print("  GET  /health              - Health check")
    print("  GET  /db-test             - Database connection test")
    print("  POST /api/register        - Register new user")
    print("  POST /api/login           - Login user")
    print("  POST /api/logout          - Logout user")
    print("  POST /api/profile         - Create/update user profile (protected)")
    print("  GET  /api/profile/<id>    - Get user profile (protected)")
    print("  POST /api/generate-plan   - Generate diet & workout plans (protected)")
    print("  GET  /api/today-plan      - Get today's plans (protected)")
    print("  POST /api/adaptive-workout - Adapt workout based on pain (protected)")
    print("  POST /api/calories        - Calculate daily calories")
    print("  POST /api/diet            - Generate diet plan")
    print("  POST /api/workout         - Generate workout plan")
    print("  POST /api/pain            - Modify workout for pain")
    print("\n" + "=" * 80)
    print("Starting server on http://localhost:5001")
    print("=" * 80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)