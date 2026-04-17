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
import csv
import re

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
from db import execute_query, execute_insert, execute_update

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


def _protein_target_grams(weight_kg: float, fitness_goal: str) -> float:
    """Estimate daily protein target from body weight and goal."""
    multipliers = {
        'lose_weight': 1.0,
        'maintain': 1.2,
        'gain_muscle': 1.6,
    }
    multiplier = multipliers.get(fitness_goal, 1.2)
    return max(40.0, float(weight_kg) * multiplier)


def _build_budget_guidance(profile_data: dict, daily_calories: float, daily_budget: float) -> dict:
    """
    Compute an estimated minimum daily/monthly budget for current user targets.
    This is heuristic guidance (not a strict hard rule).
    """
    diet_type = profile_data.get('diet_type', 'veg')
    if diet_type == 'veg':
        available_foods = FOOD_NUTRITION[FOOD_NUTRITION['is_vegetarian'] == True].copy()
    else:
        available_foods = FOOD_NUTRITION.copy()

    merged = available_foods.merge(
        FOOD_PRICES[['food_name', 'price_per_kg']],
        left_on='name',
        right_on='food_name',
        how='left'
    )

    merged['price_per_kg'] = merged['price_per_kg'].fillna(999999)
    merged = merged[(merged['price_per_kg'] > 0) & (merged['calories_per_100g'] > 0)]

    if len(merged) == 0:
        return {
            'target_calories': round(float(daily_calories), 1),
            'target_protein_g': round(_protein_target_grams(profile_data.get('weight_kg', 60), profile_data.get('fitness_goal', 'maintain')), 1),
            'daily_budget': round(float(daily_budget), 2),
            'estimated_min_daily_budget': round(float(daily_budget), 2),
            'estimated_min_monthly_budget': round(float(daily_budget) * 30, 2),
            'is_budget_low': False,
            'note': 'Not enough pricing data to estimate budget guidance.'
        }

    merged['calories_per_rupee'] = merged['calories_per_100g'] / (merged['price_per_kg'] / 10 + 0.0001)
    merged['protein_per_rupee'] = merged['protein_g'] / (merged['price_per_kg'] / 10 + 0.0001)

    best_calories_per_rupee = float(merged['calories_per_rupee'].max())
    best_protein_per_rupee = float(max(merged['protein_per_rupee'].max(), 0.01))

    protein_target = _protein_target_grams(
        profile_data.get('weight_kg', 60),
        profile_data.get('fitness_goal', 'maintain')
    )

    min_for_calories = float(daily_calories) / max(best_calories_per_rupee, 0.01)
    min_for_protein = float(protein_target) / max(best_protein_per_rupee, 0.01)

    # Add margin for realistic meal composition and diversity constraints.
    estimated_min_daily = max(min_for_calories, min_for_protein) * 1.15

    # Practical guardrails: avoid unrealistically tiny estimates from outlier market prices.
    min_rs_per_100_kcal = 2.5 if diet_type == 'veg' else 2.9
    calorie_floor = (float(daily_calories) / 100.0) * min_rs_per_100_kcal
    protein_floor = float(protein_target) * 0.8
    estimated_min_daily = max(estimated_min_daily, calorie_floor, protein_floor, 60.0)
    estimated_min_monthly = estimated_min_daily * 30

    return {
        'target_calories': round(float(daily_calories), 1),
        'target_protein_g': round(float(protein_target), 1),
        'daily_budget': round(float(daily_budget), 2),
        'estimated_min_daily_budget': round(float(estimated_min_daily), 2),
        'estimated_min_monthly_budget': round(float(estimated_min_monthly), 2),
        'is_budget_low': float(daily_budget) < float(estimated_min_daily),
        'note': 'Estimated from current food-price efficiency and nutrition targets.'
    }

# Build exercise name → image URL lookup
# Priority order: user CSV mapping -> free-exercise-db -> local exercises.json.
EXERCISE_GIF_LOOKUP = {}  # lowercase name → URL/path


def _normalize_gif_path(value: str) -> str:
    val = str(value or '').strip()
    if not val:
        return ''
    if val.startswith('http://') or val.startswith('https://') or val.startswith('/'):
        return val
    return f"/gifs/{val.lstrip('/')}"


def _is_unreliable_gif_url(url: str) -> bool:
    """Filter known problematic remote endpoints that frequently return non-image errors."""
    u = str(url or '').strip().lower()
    if not u:
        return True
    # ExerciseDB image endpoint often returns 5xx/JSON instead of an image in browser usage.
    if 'v2.exercisedb.io/image/' in u:
        return True
    return False


def _load_local_gif_mapping() -> int:
    """Load optional user-provided GIF mapping CSV from data/processed."""
    mapping_path = os.path.join(
        os.path.dirname(__file__),
        'data',
        'processed',
        'exercise_gif_mapping.csv'
    )
    if not os.path.exists(mapping_path):
        return 0

    loaded = 0
    try:
        with open(mapping_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_l = {str(k).strip().lower(): (v if v is not None else '') for k, v in row.items()}
                name = (
                    row_l.get('exercise')
                    or row_l.get('exercise_name')
                    or row_l.get('name')
                    or row_l.get('title')
                    or ''
                )
                gif = (
                    row_l.get('gif_url')
                    or row_l.get('image_url')
                    or row_l.get('gif')
                    or row_l.get('image')
                    or row_l.get('url')
                    or ''
                )
                key = str(name).strip().lower()
                url = _normalize_gif_path(gif)
                if key and url and not _is_unreliable_gif_url(url):
                    EXERCISE_GIF_LOOKUP[key] = url
                    loaded += 1
    except Exception as e:
        print(f"WARNING: Could not load exercise_gif_mapping.csv: {e}")
        return 0

    print(f"  - {loaded} exercise GIF mappings loaded from data/processed/exercise_gif_mapping.csv")
    return loaded


_load_local_gif_mapping()

_FREE_DB_BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"
try:
    import urllib.request as _req
    import json as _json
    _db_url = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
    with _req.urlopen(_db_url, timeout=8) as _resp:
        _free_exercises = _json.loads(_resp.read().decode())
    _added = 0
    for _ex in _free_exercises:
        _name_key = _ex.get('name', '').lower().strip()
        _images = _ex.get('images', [])
        if _name_key and _images and _name_key not in EXERCISE_GIF_LOOKUP:
            EXERCISE_GIF_LOOKUP[_name_key] = _FREE_DB_BASE + _images[0]
            _added += 1
    print(f"  - {_added} exercise images added from free-exercise-db")
except Exception as _e:
    print(f"WARNING: Could not load free-exercise-db images (offline?): {_e}")

# Final fallback: local exercises.json (old GIF lookup), only filling missing keys.
try:
    import json as _json
    _raw_exercises_path = os.path.join(os.path.dirname(__file__), 'data', 'raw', 'exercises.json')
    with open(_raw_exercises_path, 'r') as _f:
        _raw_exercises = _json.load(_f)
    _added = 0
    for _ex in _raw_exercises:
        _name_key = _ex.get('name', '').lower().strip()
        _gif = _ex.get('gifUrl', '')
        if _name_key and _gif and _name_key not in EXERCISE_GIF_LOOKUP:
            EXERCISE_GIF_LOOKUP[_name_key] = _normalize_gif_path(_gif)
            _added += 1
    if _added:
        print(f"  - {_added} exercise GIFs added from local exercises.json fallback")
except Exception as _e2:
    print(f"WARNING: Local GIF fallback unavailable: {_e2}")


_NAME_STOPWORDS = {
    'machine', 'cable', 'barbell', 'dumbbell', 'bodyweight', 'assisted',
    'male', 'female', 'with', 'and', 'the', 'a', 'an'
}


def _normalize_exercise_name(name: str) -> str:
    """Normalize exercise names to improve cross-dataset GIF matching."""
    s = str(name or '').strip().lower()
    if not s:
        return ''

    # Remove parenthetical qualifiers like "(machine)".
    s = re.sub(r'\([^)]*\)', ' ', s)

    # Canonical replacements for common variants.
    replacements = {
        'push-ups': 'push up',
        'pull-ups': 'pull up',
        'chin-ups': 'chin up',
        'sit-ups': 'sit up',
        'deadlifts': 'deadlift',
        'lunges': 'lunge',
        'squats': 'squat',
        'rows': 'row',
        'presses': 'press',
        'flyes': 'fly',
        'tricep ': 'triceps ',
        'bicep ': 'biceps ',
    }
    for old, new in replacements.items():
        s = s.replace(old, new)

    s = re.sub(r'[^a-z0-9]+', ' ', s)
    tokens = [t for t in s.split() if t and t not in _NAME_STOPWORDS]

    normalized_tokens = []
    for t in tokens:
        # Very light singularization to align plural variants.
        if t.endswith('ies') and len(t) > 4:
            t = t[:-3] + 'y'
        elif t.endswith('s') and len(t) > 3 and not t.endswith('ss'):
            t = t[:-1]
        normalized_tokens.append(t)

    return ' '.join(normalized_tokens)


EXERCISE_GIF_LOOKUP_NORM = {}
for _k, _v in EXERCISE_GIF_LOOKUP.items():
    _nk = _normalize_exercise_name(_k)
    if _nk and _nk not in EXERCISE_GIF_LOOKUP_NORM:
        EXERCISE_GIF_LOOKUP_NORM[_nk] = _v

EXERCISE_GIF_LOOKUP_NORM_TOKENS = {
    _k: set(_k.split()) for _k in EXERCISE_GIF_LOOKUP_NORM.keys()
}


def _resolve_exercise_gif(exercise_name: str) -> str | None:
    """Resolve the best available GIF URL for an exercise name."""
    raw = str(exercise_name or '').strip().lower()
    if not raw:
        return None

    # 1) Exact raw key match.
    url = EXERCISE_GIF_LOOKUP.get(raw)
    if url:
        return url

    # 2) Exact normalized key match.
    norm = _normalize_exercise_name(raw)
    if norm in EXERCISE_GIF_LOOKUP_NORM:
        return EXERCISE_GIF_LOOKUP_NORM[norm]

    # 3) Token-overlap fallback.
    norm_tokens = set(norm.split())
    if not norm_tokens:
        return None

    best_key = None
    best_score = 0.0

    for key, key_tokens in EXERCISE_GIF_LOOKUP_NORM_TOKENS.items():
        inter = len(norm_tokens & key_tokens)
        if inter == 0:
            continue

        # Recall-focused score: how much of requested exercise name is covered.
        score = inter / max(len(norm_tokens), 1)
        if score > best_score:
            best_score = score
            best_key = key

    if best_key and best_score >= 0.6:
        return EXERCISE_GIF_LOOKUP_NORM.get(best_key)

    return None


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
            "state": str (optional),
            "full_name": str (optional, display name)
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

        raw_name = data.get('full_name')
        if isinstance(raw_name, str):
            full_name = raw_name.strip() or None
        else:
            full_name = None

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
                    full_name = ?,
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
                full_name,
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
                    workout_time_minutes, diet_type, monthly_budget, workout_split_preference, state, full_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                data.get('state'),
                full_name
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
        budget_guidance = _build_budget_guidance(profile_data, daily_calories, daily_budget)

        diet_plan = generate_diet_plan(
            daily_calories=daily_calories,
            diet_type=profile_data['diet_type'],
            daily_budget=daily_budget,
            food_nutrition=FOOD_NUTRITION,
            food_prices=FOOD_PRICES,
            allow_incomplete=True,
            target_protein_g=budget_guidance['target_protein_g']
        )
        
        # Calculate totals
        total_calories = sum(item['calories'] for item in diet_plan)
        total_protein = sum(item['protein_g'] for item in diet_plan)
        total_cost = sum(item['cost'] for item in diet_plan)
        total_items = len(diet_plan)
        target_protein = budget_guidance['target_protein_g']

        achieved_calorie_pct = round((total_calories / daily_calories) * 100, 1) if daily_calories else 0
        achieved_protein_pct = round((total_protein / target_protein) * 100, 1) if target_protein else 0

        diet_warning = None
        if achieved_calorie_pct < 90 or achieved_protein_pct < 90:
            diet_warning = (
                f"Your current budget (Rs.{profile_data['monthly_budget']:.2f}/month) may be low for full targets. "
                f"Current plan achieves {achieved_calorie_pct}% calories and {achieved_protein_pct}% protein. "
                f"Recommended minimum is about Rs.{budget_guidance['estimated_min_monthly_budget']:.2f}/month."
            )
        
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
            ) VALUES (?, CURRENT_DATE, ?, ?)
        """, (
            user_id,
            json.dumps(diet_plan),
            total_cost
        ))
        
        # Step 5: Save workout plan to database
        workout_plan_id = execute_insert("""
            INSERT INTO workout_plans (
                user_id, plan_date, workout_data
            ) VALUES (?, CURRENT_DATE, ?)
        """, (
            user_id,
            json.dumps(workout_plan)
        ))
        
        return jsonify({
            'success': True,
            'message': 'Plans generated successfully',
            'daily_calories': daily_calories,
            'budget_guidance': budget_guidance,
            'diet_plan': {
                'id': diet_plan_id,
                'meals': diet_plan,
                'total_calories': round(total_calories, 1),
                'total_protein': round(total_protein, 1),
                'total_cost': round(total_cost, 2),
                'total_items': total_items,
                'target_calories': round(float(daily_calories), 1),
                'target_protein': round(float(target_protein), 1),
                'achieved_calorie_pct': achieved_calorie_pct,
                'achieved_protein_pct': achieved_protein_pct,
                'warning': diet_warning
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
        profile_data = None

        profile = execute_query(
            "SELECT * FROM user_profiles WHERE user_id = ?",
            (user_id,)
        )
        if profile:
            profile_data = dict(profile[0])
        
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
            meals = json.loads(diet_data['diet_data'])
            total_calories = round(sum(float(item.get('calories', 0)) for item in meals), 1)
            total_protein = round(sum(float(item.get('protein_g', 0)) for item in meals), 1)
            total_items = len(meals)
            target_calories = None
            target_protein = None
            achieved_calorie_pct = None
            achieved_protein_pct = None
            warning = None
            budget_guidance = None

            if profile_data:
                target_calories = calculate_daily_calories(
                    age=profile_data['age'],
                    gender=profile_data['gender'],
                    height_cm=profile_data['height_cm'],
                    weight_kg=profile_data['weight_kg'],
                    goal=profile_data['fitness_goal'],
                    workout_days_per_week=profile_data['workout_days_per_week']
                )
                daily_budget = float(profile_data['monthly_budget']) / 30.0
                budget_guidance = _build_budget_guidance(profile_data, target_calories, daily_budget)
                target_protein = budget_guidance['target_protein_g']
                achieved_calorie_pct = round((total_calories / target_calories) * 100, 1) if target_calories else 0
                achieved_protein_pct = round((total_protein / target_protein) * 100, 1) if target_protein else 0
                if achieved_calorie_pct < 90 or achieved_protein_pct < 90:
                    warning = (
                        f"Budget may be low for full targets: {achieved_calorie_pct}% calories, "
                        f"{achieved_protein_pct}% protein achieved."
                    )

            response['diet_plan'] = {
                'id': diet_data['id'],
                'meals': meals,
                'total_cost': diet_data['total_cost'],
                'total_calories': total_calories,
                'total_protein': total_protein,
                'total_items': total_items,
                'target_calories': target_calories,
                'target_protein': target_protein,
                'achieved_calorie_pct': achieved_calorie_pct,
                'achieved_protein_pct': achieved_protein_pct,
                'warning': warning,
                'budget_guidance': budget_guidance,
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
                        gif_file = _resolve_exercise_gif(ex.get('name', ''))
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
        
        import json

        # PostgreSQL: plan_date may be text or date — compare as date (not SQLite date('now'))
        workout_plan = execute_query("""
            SELECT id, workout_data
            FROM workout_plans
            WHERE user_id = ?
              AND CAST(plan_date AS DATE) = CURRENT_DATE
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))

        def _generic_mobility_suggestions(body_part_label):
            import random
            bp = (body_part_label or 'your body').lower()
            pool = [
                {
                    'name': 'Easy walking or marching in place',
                    'category': 'mobility',
                    'muscle_groups': bp,
                    'equipment': 'none',
                    'sets': 1,
                    'reps': '5–8 min',
                    'rest_seconds': 0,
                    'instructions': 'Low-impact movement increases blood flow and can ease stiffness.'
                },
                {
                    'name': 'Cat–cow or gentle spine mobility',
                    'category': 'mobility',
                    'muscle_groups': 'spine, core',
                    'equipment': 'mat optional',
                    'sets': 2,
                    'reps': '8–10 slow reps',
                    'rest_seconds': 30,
                    'instructions': 'Move slowly; stop if anything sharpens the pain.'
                },
                {
                    'name': 'Light stretching (affected area)',
                    'category': 'mobility',
                    'muscle_groups': bp,
                    'equipment': 'none',
                    'sets': 2,
                    'reps': '20–30 s hold',
                    'rest_seconds': 20,
                    'instructions': 'Gentle range of motion only — no forcing or bouncing.'
                },
                {
                    'name': 'Deep breathing focus',
                    'category': 'recovery',
                    'muscle_groups': 'core, diaphragm',
                    'equipment': 'none',
                    'sets': 1,
                    'reps': '3–5 min',
                    'rest_seconds': 0,
                    'instructions': 'Focus on deep, diaphragmatic breathing to promote parasympathetic nervous system recovery.'
                },
                {
                    'name': 'Childs Pose',
                    'category': 'mobility',
                    'muscle_groups': 'back, hips, shoulders',
                    'equipment': 'mat optional',
                    'sets': 1,
                    'reps': '45–60 s hold',
                    'rest_seconds': 0,
                    'instructions': 'Sink into the hips and stretch the arms forward to lengthen the spine. Do not force the hips.'
                },
                {
                    'name': 'Bird Dog holds',
                    'category': 'mobility',
                    'muscle_groups': 'core, spine',
                    'equipment': 'mat optional',
                    'sets': 2,
                    'reps': '5 reps per side',
                    'rest_seconds': 30,
                    'instructions': 'Move with slow control, focusing on stability rather than range of motion.'
                },
                {
                    'name': 'Glute Bridge (bodyweight)',
                    'category': 'mobility',
                    'muscle_groups': 'glutes, hips',
                    'equipment': 'none',
                    'sets': 2,
                    'reps': '10 slow reps',
                    'rest_seconds': 30,
                    'instructions': 'Squeeze glutes at the top. This is to wake up the muscles, not to exhaust them.'
                },
                {
                    'name': 'Dynamic Arm Circles',
                    'category': 'mobility',
                    'muscle_groups': 'shoulders, upper back',
                    'equipment': 'none',
                    'sets': 2,
                    'reps': '15 forward, 15 back',
                    'rest_seconds': 20,
                    'instructions': 'Keep the motion smooth and fluid to lubricate the shoulder joints.'
                }
            ]
            return random.sample(pool, 3)

        # No saved plan for today, or we could not load it: still help with mobility (never 404)
        if not workout_plan:
            modification_result = modify_workout_for_pain(
                pain_text=pain_text,
                today_workout_plan=[],
                pain_keywords=PAIN_KEYWORDS,
                exercises_df=EXERCISES,
                exercise_contraindications=EXERCISE_CONTRAINDICATIONS,
                recovery_exercises=RECOVERY_EXERCISES
            )
            mw = modification_result['modified_workout'] or []
            if not mw and modification_result.get('pain_detected'):
                if modification_result.get('severity') == 'high' or modification_result.get('medical_attention_needed'):
                    mw = []
                else:
                    mw = _generic_mobility_suggestions(modification_result.get('affected_body_part'))
            elif not mw:
                mw = _generic_mobility_suggestions(None)

            pain_report_id = execute_insert("""
                INSERT INTO pain_reports (
                    user_id, pain_text, affected_body_part
                ) VALUES (?, ?, ?)
            """, (
                user_id,
                pain_text,
                modification_result['affected_body_part']
            ))

            if not mw and (modification_result.get('severity') == 'high' or modification_result.get('medical_attention_needed')):
                friendly = (
                    'There is no workout saved for today, so nothing was changed in your plan. '
                    f"{modification_result['immediate_action']} "
                    'If symptoms are severe or worsening, seek professional care.'
                )
            else:
                friendly = (
                    'There is no workout saved for today, so we have not changed a plan. '
                    'Light mobility work can still help you move more comfortably. '
                    'If pain is sharp or getting worse, ease off and consider speaking with a professional.'
                )

            return jsonify({
                'success': True,
                'mobility_only': True,
                'no_workout_today': True,
                'message': friendly,
                'pain_report_id': pain_report_id,
                'pain_detected': modification_result['pain_detected'],
                'affected_body_part': modification_result['affected_body_part'],
                'severity': modification_result['severity'],
                'medical_attention_needed': modification_result['medical_attention_needed'],
                'immediate_action': modification_result['immediate_action'],
                'modified_workout': mw,
                'removed_exercises': [],
                'added_exercises': modification_result.get('added_exercises') or [],
                'modification_summary': modification_result['modification_summary']
            })

        workout_data = dict(workout_plan[0])
        workout_plan_id = workout_data['id']
        current_plan = json.loads(workout_data['workout_data'])

        today_workout = []
        if 'weekly_plan' in current_plan and len(current_plan['weekly_plan']) > 0:
            today_workout = current_plan['weekly_plan'][0].get('exercises', [])

        if not today_workout:
            modification_result = modify_workout_for_pain(
                pain_text=pain_text,
                today_workout_plan=[],
                pain_keywords=PAIN_KEYWORDS,
                exercises_df=EXERCISES,
                exercise_contraindications=EXERCISE_CONTRAINDICATIONS,
                recovery_exercises=RECOVERY_EXERCISES
            )
            mw = modification_result['modified_workout'] or []
            if not mw and modification_result.get('pain_detected'):
                if modification_result.get('severity') == 'high' or modification_result.get('medical_attention_needed'):
                    mw = []
                else:
                    mw = _generic_mobility_suggestions(modification_result.get('affected_body_part'))
            elif not mw:
                mw = _generic_mobility_suggestions(None)

            pain_report_id = execute_insert("""
                INSERT INTO pain_reports (
                    user_id, pain_text, affected_body_part
                ) VALUES (?, ?, ?)
            """, (
                user_id,
                pain_text,
                modification_result['affected_body_part']
            ))

            if not mw and (modification_result.get('severity') == 'high' or modification_result.get('medical_attention_needed')):
                friendly = (
                    'Today has no exercises listed in your plan. '
                    f"{modification_result['immediate_action']}"
                )
            else:
                friendly = (
                    'Today looks like a rest day or your session has no exercises listed. '
                    'Here are gentle mobility ideas you can try. Move lightly and stop if pain increases.'
                )

            return jsonify({
                'success': True,
                'mobility_only': True,
                'no_workout_today': False,
                'rest_day': True,
                'message': friendly,
                'pain_report_id': pain_report_id,
                'pain_detected': modification_result['pain_detected'],
                'affected_body_part': modification_result['affected_body_part'],
                'severity': modification_result['severity'],
                'medical_attention_needed': modification_result['medical_attention_needed'],
                'immediate_action': modification_result['immediate_action'],
                'modified_workout': mw,
                'removed_exercises': [],
                'added_exercises': modification_result.get('added_exercises') or [],
                'modification_summary': modification_result['modification_summary']
            })

        modification_result = modify_workout_for_pain(
            pain_text=pain_text,
            today_workout_plan=today_workout,
            pain_keywords=PAIN_KEYWORDS,
            exercises_df=EXERCISES,
            exercise_contraindications=EXERCISE_CONTRAINDICATIONS,
            recovery_exercises=RECOVERY_EXERCISES
        )

        response_message = 'Workout adaptation processed.'

        if modification_result.get('pain_detected'):
            bp = modification_result.get('affected_body_part')
            severity = modification_result.get('severity')
            medical_attention = bool(modification_result.get('medical_attention_needed'))
            safe_plan = modification_result.get('modified_workout') or []
            removed_count = len(modification_result.get('removed_exercises') or [])

            if severity == 'high' or medical_attention:
                modification_result['modified_workout'] = []
                modification_result['removed_exercises'] = today_workout
                modification_result['added_exercises'] = []
                modification_result['mobility_only'] = True
                modification_result['modification_summary'] = (
                    f"Pain detected in {bp} ({severity}). Rest-only recommendation for today for safety."
                )
                response_message = (
                    'High-severity pain detected. Workout paused for today; please prioritize rest.'
                )
            elif len(safe_plan) == 0:
                mobility_plan = _generic_mobility_suggestions(bp)
                modification_result['modified_workout'] = mobility_plan
                modification_result['mobility_only'] = True
                modification_result['modification_summary'] = (
                    f"Pain detected in {bp} ({severity}). All planned exercises were filtered out for safety; "
                    "replaced with gentle mobility work."
                )
                response_message = (
                    'Unsafe exercises were removed and replaced with gentle mobility for recovery today.'
                )
            else:
                modification_result['mobility_only'] = False
                if removed_count > 0:
                    response_message = (
                        'Unsafe exercises were removed and your safe exercises were kept with recovery support.'
                    )
                else:
                    response_message = (
                        'No high-risk exercise detected from your pain feedback; plan kept with recovery guidance.'
                    )
        else:
            modification_result['mobility_only'] = False
            response_message = 'No pain keyword detected. Kept today\'s workout unchanged.'

        if 'weekly_plan' in current_plan and len(current_plan['weekly_plan']) > 0:
            current_plan['weekly_plan'][0]['exercises'] = modification_result.get('modified_workout') or []
            execute_update(
                """
                UPDATE workout_plans
                SET workout_data = ?
                WHERE id = ?
                """,
                (json.dumps(current_plan), workout_plan_id)
            )

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
            'mobility_only': modification_result.get('mobility_only', False),
            'message': response_message,
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


@app.route('/api/budget-guidance', methods=['POST'])
@login_required
def budget_guidance():
    """
    Return recommended minimum budget guidance from profile-like inputs.

    Request Body:
        {
            "age": int,
            "gender": "male"|"female",
            "height_cm": float,
            "weight_kg": float,
            "fitness_goal": "lose_weight"|"maintain"|"gain_muscle",
            "workout_days_per_week": int,
            "diet_type": "veg"|"non-veg",
            "monthly_budget": float
        }
    """
    try:
        data = request.get_json()
        required = [
            'age', 'gender', 'height_cm', 'weight_kg',
            'fitness_goal', 'workout_days_per_week', 'diet_type', 'monthly_budget'
        ]
        is_valid, error = validate_required_fields(data, required)
        if not is_valid:
            return jsonify({'error': error}), 400

        daily_calories = calculate_daily_calories(
            age=int(data['age']),
            gender=data['gender'],
            height_cm=float(data['height_cm']),
            weight_kg=float(data['weight_kg']),
            goal=data['fitness_goal'],
            workout_days_per_week=int(data['workout_days_per_week'])
        )

        monthly_budget = float(data['monthly_budget'])
        daily_budget = monthly_budget / 30.0

        profile_like = {
            'diet_type': data['diet_type'],
            'weight_kg': float(data['weight_kg']),
            'fitness_goal': data['fitness_goal'],
            'monthly_budget': monthly_budget,
        }
        guidance = _build_budget_guidance(profile_like, daily_calories, daily_budget)

        return jsonify({
            'success': True,
            'daily_calories': daily_calories,
            'budget_guidance': guidance
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
            food_prices=FOOD_PRICES,
            allow_incomplete=True
        )
        
        # Calculate totals
        total_calories = sum(item['calories'] for item in meal_plan)
        total_protein = sum(item['protein_g'] for item in meal_plan)
        total_cost = sum(item['cost'] for item in meal_plan)
        total_items = len(meal_plan)
        target_calories = float(data['daily_calories'])
        achieved_calorie_pct = round((total_calories / target_calories) * 100, 1) if target_calories else 0
        warning = None
        if achieved_calorie_pct < 90:
            warning = (
                f"Budget may be low for target calories. Achieved {achieved_calorie_pct}% "
                f"of target calories."
            )
        
        return jsonify({
            'diet_plan': meal_plan,
            'total_calories': round(total_calories, 1),
            'total_protein': round(total_protein, 1),
            'total_cost': round(total_cost, 2),
            'total_items': total_items,
            'target_calories': round(target_calories, 1),
            'achieved_calorie_pct': achieved_calorie_pct,
            'warning': warning,
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