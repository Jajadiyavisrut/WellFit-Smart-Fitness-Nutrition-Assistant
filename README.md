# WellFit - Smart Fitness & Nutrition Assistant

A comprehensive web application that provides personalized fitness and nutrition plans with pain-adaptive workout modifications.

## Features

### 🔐 Authentication & User Management
- User registration and login with secure password hashing
- Session-based authentication
- Profile management with comprehensive user data

### 🍽️ Personalized Diet Plans
- Calorie calculation based on user profile (BMR & TDEE)
- Budget-optimized meal planning
- Vegetarian and non-vegetarian options
- Daily meal breakdown with nutritional information

### 💪 Adaptive Workout Plans
- Experience-level based workout generation (Beginner/Intermediate)
- Multiple workout splits (Upper/Lower, Push/Pull/Legs, Full Body)
- Customizable workout frequency and duration
- Exercise selection based on fitness goals

### 🏥 Pain-Adaptive System
- Real-time workout modification based on pain reports
- Exercise contraindication checking
- Recovery exercise recommendations
- Pain severity assessment and medical attention alerts

### ✅ Input Validation
- Comprehensive validation for all user inputs
- Age, height, weight, and budget range validation
- Enum validation for gender, diet type, fitness goals, and experience levels
- Meaningful error messages with proper HTTP status codes

### 🎨 Modern Web Interface
- Clean, responsive UI with gradient design
- Profile icon with dropdown menu
- Real-time plan display
- Pain reporting interface

## Tech Stack

**Backend:**
- Flask (Python web framework)
- SQLite (Database)
- Pandas (Data processing)

**Frontend:**
- HTML5
- CSS3 (Vanilla CSS with modern gradients)
- JavaScript (Fetch API for AJAX calls)

**Security:**
- Werkzeug password hashing
- Session-based authentication
- CSRF protection

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Jajadiyavisrut/WellFit-Smart-Fitness-Nutrition-Assistant.git
cd WellFit-Smart-Fitness-Nutrition-Assistant
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Initialize the database:**
```bash
python init_db.py
```

4. **Run the application:**
```bash
python app.py
```

5. **Access the application:**
Open your browser and navigate to `http://localhost:5000`

## Usage

1. **Register/Login:** Create an account or login
2. **Create Profile:** Fill in your personal information, fitness goals, and preferences
3. **Generate Plan:** Click "Generate New Plan" to create personalized diet and workout plans
4. **View Plans:** See your daily meal plan and workout routine
5. **Report Pain:** If experiencing discomfort, use the pain reporting feature to get modified workouts

## Authors

- Visrut Jajadiya
