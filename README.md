# 🏋️ WellFit – Smart Fitness & Nutrition Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**WellFit** is an AI-powered fitness and nutrition assistant that provides personalized, budget-aware, and pain-adaptive workout and diet plans. Built to help users train safely, eat affordably, and stay consistent with their fitness journey.

---

## 🎯 Project Purpose

WellFit is designed as a **real-world web application** (not an academic demo) that delivers:
- **Personalized workout plans** based on user goals, experience, and availability
- **Budget-conscious nutrition plans** using real Indian food price data
- **Pain-adaptive training** that dynamically adjusts workouts based on user-reported discomfort
- **Safe, practical fitness guidance** without medical diagnosis

---

## ✨ Key Features

### 🔐 User Authentication
- Secure registration and login system
- Session-based authentication

### 👤 Personal Fitness Profile
Users can create and edit profiles with:
- Age, height, weight
- Fitness goal (fat loss / muscle gain / endurance)
- Experience level (beginner / intermediate / advanced)
- Workout frequency (days per week)
- Session duration
- Diet preference (vegetarian / non-vegetarian)
- Monthly food budget
- Location (state) for price estimation

### 💪 Smart Workout Generation
- Personalized exercise plans based on user profile
- Goal-specific training programs
- Time-optimized sessions
- Experience-appropriate difficulty

### 🥗 Budget-Aware Nutrition Planning
- Calorie and macro targets calculated automatically
- Meal plans within user's monthly budget
- Indian food database with real pricing
- Cheaper alternatives suggested when over budget
- Cost breakdown and comparison

### 🩹 Pain-Adaptive Training
- Free-text pain reporting
- Keyword-based body part identification
- **Same-day workout redesign** when pain is reported:
  - Removes risky exercises
  - Adds safer alternatives
  - Recommends stretching and mobility work
- Prioritizes safety and recovery

### 📊 Dashboard
- Unified view of workout and nutrition plans
- Calorie and macro tracking
- Budget analysis
- Quick access to profile editing

---

## 🏗️ Architecture

### Tech Stack
- **Backend**: Python + Flask
- **Database**: SQLite
- **Data Storage**: CSV files for reference data
- **Frontend**: HTML, CSS, JavaScript
- **APIs**: Custom REST APIs

### System Design Principles
```
┌─────────────┐
│   Frontend  │  (HTML/CSS/JS)
└──────┬──────┘
       │
┌──────▼──────┐
│  REST APIs  │  (Flask routes)
└──────┬──────┘
       │
┌──────▼──────┐
│ Logic Layer │  (Business logic)
└──────┬──────┘
       │
┌──────▼──────┬──────────────┐
│  Database   │  CSV Files   │
│  (SQLite)   │  (Reference) │
└─────────────┴──────────────┘
```

### Modular Architecture
- **APIs** (`/api`): REST endpoints for frontend communication
- **Logic Layer** (`/logic`): All business logic and decision-making
- **Database** (`/database`): User data, profiles, plans, pain reports
- **CSV Data** (`/data/processed`): Static reference data (exercises, nutrition, prices)
- **Templates** (`/templates`): HTML pages
- **Static Assets** (`/static`): CSS and JavaScript

---

## 📁 Project Structure

```
WellFit/
├── api/                          # REST API endpoints
│   ├── auth.py                   # Authentication APIs
│   ├── profile.py                # Profile management
│   ├── workout.py                # Workout plan APIs
│   ├── diet.py                   # Diet plan APIs
│   └── pain.py                   # Pain reporting
├── logic/                        # Business logic layer
│   ├── workout_generator.py      # Workout plan generation
│   ├── diet_generator.py         # Diet plan generation
│   ├── calorie_calculator.py     # Calorie/macro calculations
│   ├── budget_logic.py           # Budget management
│   ├── pain_handler.py           # Pain detection & adaptation
│   └── data_loader.py            # CSV data loading
├── database/                     # Database layer
│   ├── models.py                 # SQLAlchemy models
│   └── db_utils.py               # Database utilities
├── data/
│   └── processed/                # Processed CSV datasets
│       ├── exercises_comprehensive.csv
│       ├── food_nutrition_comprehensive.csv
│       ├── food_prices_comprehensive.csv
│       ├── pain_keywords_comprehensive.csv
│       └── ...
├── templates/                    # HTML templates
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── dashboard.html
│   ├── workout.html
│   └── diet.html
├── static/                       # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── app.py                        # Flask application entry point
├── config.py                     # Configuration settings
├── init_db.py                    # Database initialization
└── requirements.txt              # Python dependencies
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/wellfit.git
   cd wellfit
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser and navigate to: `http://localhost:5000`

---

## 📊 Data Strategy

### CSV-Based Reference Data
Static reference data is stored in CSV files and loaded into memory:
- **exercises_comprehensive.csv**: Exercise database with muscle groups, difficulty, equipment
- **food_nutrition_comprehensive.csv**: Nutritional information for Indian foods
- **food_prices_comprehensive.csv**: Price estimates for food items by state
- **pain_keywords_comprehensive.csv**: Keywords for pain detection and body part mapping

### Database Storage
SQLite database stores only dynamic user data:
- User accounts and authentication
- User fitness profiles
- Generated workout plans
- Generated diet plans
- Pain reports and history

**Why this approach?**
- Reference data doesn't change frequently
- Faster reads from memory
- Simpler deployment
- Easy data updates via CSV replacement

---

## 🔄 Core User Flow

1. **Registration & Login**
   - User creates an account
   - Secure authentication

2. **Profile Creation**
   - User fills out fitness profile
   - System validates and stores data

3. **Plan Generation**
   - System analyzes profile
   - Generates personalized workout plan
   - Generates budget-aware nutrition plan
   - Calculates calorie and macro targets

4. **Dashboard View**
   - User sees complete fitness overview
   - Workout schedule
   - Meal plans with costs
   - Macro breakdown

5. **Pain Reporting** (Optional)
   - User reports pain in free text
   - System identifies affected body parts
   - **Same-day workout is redesigned**:
     - Risky exercises removed
     - Safer alternatives added
     - Recovery exercises recommended

6. **Profile Updates**
   - User can edit profile anytime
   - Plans automatically regenerate

---

## 🧠 Logic Highlights

### Budget Management
- Diet plans must fit within monthly budget
- Real Indian grocery price data
- Automatic substitution with cheaper alternatives
- Clear cost breakdown displayed

### Pain Handling
- Keyword-based pain detection (no ML required)
- Body part identification from user text
- **No medical diagnosis** – safety-first approach
- Dynamic workout modification
- Stretching and mobility recommendations

### Workout Personalization
- Goal-based exercise selection (fat loss / muscle gain / endurance)
- Experience-level appropriate difficulty
- Time-constrained session planning
- Progressive overload principles

### Nutrition Personalization
- Calorie targets based on TDEE calculations
- Macro split aligned with fitness goals
- Diet preference respected (veg/non-veg)
- Budget constraints honored

---

## 🛡️ What WellFit Does NOT Do

- ❌ Provide medical advice or diagnosis
- ❌ Replace professional healthcare
- ❌ Use paid external APIs for core logic
- ❌ Overcomplicate with unnecessary ML
- ❌ Mix data, logic, and UI responsibilities

---

## 🔧 API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/logout` - User logout

### Profile Management
- `GET /api/profile` - Get user profile
- `POST /api/profile` - Create/update profile

### Workout Plans
- `GET /api/workout` - Get current workout plan
- `POST /api/workout/generate` - Generate new workout plan

### Diet Plans
- `GET /api/diet` - Get current diet plan
- `POST /api/diet/generate` - Generate new diet plan

### Pain Reporting
- `POST /api/pain/report` - Report pain/discomfort
- `GET /api/pain/history` - Get pain report history

---

## 🎨 Frontend

### Pages
- **Landing Page** (`index.html`): Introduction and features
- **Login** (`login.html`): User authentication
- **Register** (`register.html`): New user signup
- **Profile** (`profile.html`): Fitness profile creation/editing
- **Dashboard** (`dashboard.html`): Main user interface
- **Workout** (`workout.html`): Detailed workout view
- **Diet** (`diet.html`): Detailed nutrition view

### Design Principles
- Clean, minimal UI
- Mobile-responsive
- Accessibility-focused
- Fast loading times

---

## 🧪 Testing

### Manual Testing Checklist
- [ ] User registration and login
- [ ] Profile creation with various goals
- [ ] Workout plan generation
- [ ] Diet plan generation within budget
- [ ] Pain reporting and workout adaptation
- [ ] Profile editing and plan regeneration

### Future Enhancements
- Unit tests for logic layer
- Integration tests for APIs
- End-to-end testing

---

## 📝 Development Roadmap

### ✅ Completed
- User authentication system
- Profile management
- Workout plan generation
- Diet plan generation
- Budget-aware meal planning
- Pain-adaptive training
- Dashboard interface

### 🔄 In Progress
- Enhanced UI/UX improvements
- Additional exercise variations
- More food options

### 📋 Planned
- Progress tracking and analytics
- Workout history logging
- Meal prep suggestions
- Export plans to PDF
- Mobile app version

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- Exercise data sourced from public fitness datasets
- Nutrition data from Indian food databases
- Price data from Kaggle datasets
- Inspired by the need for accessible, budget-friendly fitness guidance

---

## 📞 Support

If you have any questions or need help, please:
- Open an issue on GitHub
- Contact via email

---

<div align="center">
  <strong>Built with ❤️ for a healthier, fitter India</strong>
</div>
