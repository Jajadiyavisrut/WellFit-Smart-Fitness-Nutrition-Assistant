# 🏋️ WellFit – Smart Fitness & Nutrition Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E.svg)](https://supabase.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**WellFit** is an intelligent, AI-driven fitness and nutrition application that provides personalized, budget-aware, and pain-adaptive workout and diet plans. Featuring a premium, responsive glassmorphism aesthetic, WellFit is built to help users train safely, eat affordably, and stay consistent with their fitness journey.

---

## 🎯 Project Purpose

WellFit is designed as a **real-world web application** that delivers:
- **Personalized workout plans** based on user goals, experience, and availability.
- **Budget-conscious nutrition plans** tailored to real Indian food price data.
- **Pain-adaptive training** that intelligently restructures workouts based on user-reported discomfort to prioritize mobility and recovery.
- **A premium user experience** driven by a modern dark neon and glassmorphism interface.

---

## ✨ Key Features

### 🔐 Supabase User Authentication
- Secure registration and login system powered by **Supabase**.
- Cross-session persistence and robust data security.

### 👤 Personal Fitness Profile
Users can create and edit profiles with:
- Age, height, weight
- Fitness goal (fat loss / muscle gain / endurance)
- Experience level (beginner / intermediate / advanced)
- Workout frequency (days per week) and session duration
- Diet preference (vegetarian / non-vegetarian)
- Monthly food budget
- Preferred Workout Split Style (Bro Split, PPL, etc.)

### 💪 Smart Workout Generation
- Personalized exercise plans based on user profiles.
- Automatic distribution of muscle groups across the week.
- Time-optimized sessions and progressive difficulty.

### 🥗 Budget-Aware Nutrition Planning
- Meal plans heavily optimized to fit within the user's defined monthly budget.
- Automatic substitution with highly cost-efficient protein alternatives when budgets are tight.
- Intelligent handling for Vegetarian and Non-Vegetarian choices.

### 🩹 Dynamic Pain & Injury Adaptation
- Intelligent keyword-based pain detection.
- **Instant Workout Redesign**: If a user reports an injury (e.g., "my knee hurts" or "I feel sick"), WellFit immediately scrubs heavy load-bearing exercises from the day's routine.
- Instantly generates an alternative **Mobility and Recovery Flow** designed completely around the injured body part to ensure healing.

### 📊 Dashboard
- Luxurious glassmorphism UI offering a unified view of your entire week's routines.
- Calorie and macro tracking alongside budget analysis.

---

## 🏗️ Architecture

### Tech Stack
- **Backend & APIs**: Python + Flask
- **Database & Auth**: Supabase (PostgreSQL)
- **Data Storage**: CSV files for massive static reference datasets (foods, exercises).
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism), JavaScript

### Modular Structure
- **APIs** (`/api`): RESTful endpoints for seamless frontend communication.
- **Logic Layer** (`/logic`): Contains the core `diet_generator.py` and `workout_generator.py` engines.
- **Database Layer** (`/database`): PostgreSQL connection strings and schema initializers.
- **Data Layer** (`/data/processed`): Static datasets to minimize database calls.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- A Supabase Project (for PostgreSQL and Authentication)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Jajadiyavisrut/WellFit-Smart-Fitness-Nutrition-Assistant.git
   cd "WellFit-Smart-Fitness-Nutrition-Assistant"
   ```

2. **Environment Configuration**
   Create a `.env` file in the root directory containing your Supabase credentials:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   DATABASE_URL=your_postgresql_connection_string
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the Database Schema**
   *Note: This will execute the required schema migrations on your Supabase Postgres instance.*
   ```bash
   python init_db.py
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

6. **Access the Web App**
   Open your browser and navigate to: `http://localhost:5001`

---

## 🛡️ What WellFit Does NOT Do

- ❌ Provide medical advice or medical diagnosis.
- ❌ Replace professional healthcare.
- ❌ Rely on paid external generative AI APIs for core logic (completely free and programmatic).

---

## 👨‍💻 Author

**Visrut Jajadiya**
- GitHub: [@Jajadiyavisrut](https://github.com/Jajadiyavisrut)

<div align="center">
  <strong>Built with ❤️ for a healthier, fitter India</strong>
</div>
