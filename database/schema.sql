-- ============================================================================
-- WellFit SQLite Database Schema
-- Deployment-safe, minimal schema for user-specific and generated data
-- SQLite 3.x compatible
-- ============================================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- ============================================================================
-- USERS TABLE
-- Core user authentication and identification
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    CHECK (email LIKE '%_@_%._%')
);

-- ============================================================================
-- USER PROFILES TABLE
-- One-to-one relationship with users
-- Stores user's physical attributes and fitness preferences
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    height_cm REAL NOT NULL,
    weight_kg REAL NOT NULL,
    fitness_goal TEXT NOT NULL,
    experience_level TEXT NOT NULL,
    workout_days_per_week INTEGER NOT NULL,
    workout_time_minutes INTEGER NOT NULL,
    diet_type TEXT NOT NULL,
    monthly_budget REAL NOT NULL,
    state TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    CHECK (age >= 15 AND age <= 100),
    CHECK (gender IN ('male', 'female')),
    CHECK (height_cm >= 100 AND height_cm <= 250),
    CHECK (weight_kg >= 30 AND weight_kg <= 300),
    CHECK (fitness_goal IN ('lose_weight', 'maintain', 'gain_muscle')),
    CHECK (experience_level IN ('beginner', 'intermediate')),
    CHECK (workout_days_per_week >= 0 AND workout_days_per_week <= 7),
    CHECK (workout_time_minutes >= 20 AND workout_time_minutes <= 120),
    CHECK (diet_type IN ('veg', 'non-veg')),
    CHECK (monthly_budget > 0)
);

-- ============================================================================
-- WORKOUT PLANS TABLE
-- Stores generated workout plans for users
-- ============================================================================

CREATE TABLE IF NOT EXISTS workout_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_date TEXT NOT NULL,
    workout_data TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================================
-- DIET PLANS TABLE
-- Stores generated diet plans for users
-- ============================================================================

CREATE TABLE IF NOT EXISTS diet_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_date TEXT NOT NULL,
    diet_data TEXT NOT NULL,
    total_cost REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    CHECK (total_cost >= 0)
);

-- ============================================================================
-- PAIN REPORTS TABLE
-- Stores user pain reports for workout modifications
-- ============================================================================

CREATE TABLE IF NOT EXISTS pain_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pain_text TEXT NOT NULL,
    affected_body_part TEXT,
    report_date TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES
-- For faster lookups on frequently queried columns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_plans_user_id ON workout_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_plans_date ON workout_plans(user_id, plan_date);
CREATE INDEX IF NOT EXISTS idx_diet_plans_user_id ON diet_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_diet_plans_date ON diet_plans(user_id, plan_date);
CREATE INDEX IF NOT EXISTS idx_pain_reports_user_id ON pain_reports(user_id);

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
