# Design Document

## Overview

WellFit is designed as a modular Flask web application with a clean separation between data, logic, and presentation layers. The system uses CSV files for static reference data and SQLite for user-specific data, with a REST API architecture that enables future scalability and potential mobile app integration.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask APIs    │    │   Logic Layer   │
│  (HTML/CSS/JS)  │◄──►│   (Routes)      │◄──►│  (Business)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   SQLite DB     │    │   CSV Files     │
                       │  (User Data)    │    │ (Reference)     │
                       └─────────────────┘    └─────────────────┘
```

### Directory Structure

```
wellfit/
├── app.py                 # Flask application entry point
├── config.py             # Configuration settings
├── api/                  # REST API endpoints
│   ├── auth.py          # Authentication routes
│   ├── profile.py       # Profile management routes
│   ├── plans.py         # Workout/nutrition plan routes
│   └── pain.py          # Pain reporting routes
├── logic/               # Business logic layer
│   ├── auth_logic.py    # Authentication logic
│   ├── profile_logic.py # Profile processing
│   ├── plan_generator.py # Plan generation algorithms
│   ├── pain_analyzer.py # Pain analysis and adaptation
│   └── data_loader.py   # CSV data loading utilities
├── database/            # Database models and utilities
│   ├── models.py        # SQLAlchemy models
│   └── db_utils.py      # Database utilities
├── data/                # CSV reference data
│   ├── exercises.csv
│   ├── food_nutrition.csv
│   ├── food_prices.csv
│   └── pain_keywords.csv
├── static/              # CSS, JS, images
└── templates/           # HTML templates
```

## Components and Interfaces

### 1. Authentication System

**Components:**
- `auth_logic.py`: Handles user registration, login validation, session management
- `api/auth.py`: Authentication API endpoints
- `templates/auth/`: Login and registration templates

**Key Functions:**
```python
# auth_logic.py
def register_user(username, email, password) -> dict
def authenticate_user(email, password) -> dict
def validate_session(session_token) -> bool
```

### 2. Profile Management System

**Components:**
- `profile_logic.py`: Profile validation, CRUD operations, change detection
- `api/profile.py`: Profile management endpoints
- `templates/profile/`: Profile creation and editing forms

**Key Functions:**
```python
# profile_logic.py
def create_profile(user_id, profile_data) -> dict
def update_profile(user_id, profile_data) -> dict
def get_profile(user_id) -> dict
def calculate_calorie_needs(profile) -> int
```

### 3. Plan Generation System

**Components:**
- `plan_generator.py`: Core plan generation algorithms
- `data_loader.py`: CSV data loading and caching
- `api/plans.py`: Plan retrieval and regeneration endpoints

**Key Functions:**
```python
# plan_generator.py
def generate_workout_plan(profile, exercises_data) -> dict
def generate_nutrition_plan(profile, food_data, price_data) -> dict
def optimize_for_budget(nutrition_plan, budget_limit) -> dict
def calculate_macros(profile) -> dict
```

### 4. Pain Analysis and Adaptation System

**Components:**
- `pain_analyzer.py`: Text analysis, body part detection, workout modification
- `api/pain.py`: Pain reporting endpoints

**Key Functions:**
```python
# pain_analyzer.py
def analyze_pain_text(pain_description, keywords_data) -> list
def identify_affected_bodyparts(pain_keywords) -> list
def adapt_workout_for_pain(workout_plan, affected_parts) -> dict
def suggest_recovery_exercises(affected_parts) -> list
```

## Data Models

### Database Schema (SQLite)

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User profiles table
CREATE TABLE user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    age INTEGER NOT NULL,
    height FLOAT NOT NULL,
    weight FLOAT NOT NULL,
    fitness_goal VARCHAR(20) NOT NULL, -- 'fat_loss', 'muscle_gain', 'endurance'
    experience_level VARCHAR(20) NOT NULL, -- 'beginner', 'intermediate', 'advanced'
    workout_days_per_week INTEGER NOT NULL,
    workout_time_per_session INTEGER NOT NULL, -- minutes
    diet_preference VARCHAR(20) NOT NULL, -- 'vegetarian', 'non_vegetarian'
    monthly_food_budget FLOAT NOT NULL,
    location VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Generated workout plans
CREATE TABLE workout_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_data TEXT NOT NULL, -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Generated diet plans
CREATE TABLE diet_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_data TEXT NOT NULL, -- JSON string
    estimated_cost FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Pain reports
CREATE TABLE pain_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pain_description TEXT NOT NULL,
    detected_bodyparts TEXT, -- JSON array
    workout_modified BOOLEAN DEFAULT FALSE,
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### CSV Data Structures

**exercises.csv:**
```csv
id,name,category,muscle_groups,equipment,difficulty,instructions,safety_notes
1,Push-ups,strength,"chest,triceps,shoulders",bodyweight,beginner,"...",""
2,Squats,strength,"quadriceps,glutes",bodyweight,beginner,"...",""
```

**food_nutrition.csv:**
```csv
id,name,category,calories_per_100g,protein_g,carbs_g,fat_g,fiber_g
1,Rice,grains,130,2.7,28,0.3,0.4
2,Chicken Breast,protein,165,31,0,3.6,0
```

**food_prices.csv:**
```csv
food_id,region,price_per_kg,currency,last_updated
1,maharashtra,45,INR,2024-01-01
2,maharashtra,280,INR,2024-01-01
```

**pain_keywords.csv:**
```csv
keyword,body_part,severity_weight
"knee pain",knee,0.8
"back ache",lower_back,0.7
"shoulder hurt",shoulder,0.6
```

## Error Handling

### API Error Responses

```python
# Standard error response format
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid profile data provided",
        "details": ["Age must be between 13 and 100"]
    }
}
```

### Error Categories

1. **Validation Errors**: Invalid input data, missing required fields
2. **Authentication Errors**: Invalid credentials, expired sessions
3. **Data Errors**: Missing CSV files, database connection issues
4. **Business Logic Errors**: Budget constraints, plan generation failures

### Error Handling Strategy

- API layer validates input and returns structured error responses
- Logic layer raises custom exceptions with specific error codes
- Frontend displays user-friendly error messages
- Critical errors are logged for debugging

## Testing Strategy

### Unit Testing

**Logic Layer Tests:**
```python
# test_plan_generator.py
def test_generate_workout_plan_beginner()
def test_generate_nutrition_plan_within_budget()
def test_optimize_for_budget_replaces_expensive_items()

# test_pain_analyzer.py
def test_analyze_pain_text_detects_keywords()
def test_adapt_workout_removes_risky_exercises()
```

**API Tests:**
```python
# test_api_endpoints.py
def test_register_user_success()
def test_create_profile_validates_required_fields()
def test_report_pain_modifies_current_workout()
```

### Integration Testing

- Test complete user flows (registration → profile → plan generation)
- Test pain reporting and workout adaptation end-to-end
- Test budget optimization with real CSV data
- Test profile updates trigger plan regeneration

### Data Testing

- Validate CSV file formats and required columns
- Test data loading and caching mechanisms
- Test database schema migrations
- Test data consistency between CSV and database

## Performance Considerations

### Data Loading Strategy

- Load CSV data once at application startup
- Cache reference data in memory for fast access
- Implement lazy loading for large datasets
- Use database indexes for user data queries

### Plan Generation Optimization

- Cache generated plans to avoid regeneration
- Use efficient algorithms for budget optimization
- Implement pagination for large plan displays
- Optimize database queries with proper indexing

### Scalability Considerations

- Stateless API design enables horizontal scaling
- Separate read/write operations for better performance
- Consider Redis for session management in production
- Database connection pooling for concurrent users