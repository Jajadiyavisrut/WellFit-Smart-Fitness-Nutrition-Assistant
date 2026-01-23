# Requirements Document

## Introduction

WellFit is an AI-powered fitness and nutrition assistant that provides personalized, budget-aware, and pain-adaptive workout and diet plans. The application helps users train safely, eat affordably, and maintain consistency in their fitness journey through intelligent plan generation and real-time adaptation based on user feedback and pain reports.

## Requirements

### Requirement 1: User Authentication and Registration

**User Story:** As a new user, I want to register and log into the WellFit application, so that I can access personalized fitness and nutrition plans.

#### Acceptance Criteria

1. WHEN a user visits the registration page THEN the system SHALL display fields for username, email, and password
2. WHEN a user submits valid registration data THEN the system SHALL create a new user account and redirect to profile creation
3. WHEN a user attempts to register with an existing email THEN the system SHALL display an error message
4. WHEN a registered user enters valid login credentials THEN the system SHALL authenticate and redirect to the dashboard
5. WHEN a user enters invalid login credentials THEN the system SHALL display an appropriate error message

### Requirement 2: User Profile Management

**User Story:** As a user, I want to create and manage my fitness profile with personal details and preferences, so that the system can generate personalized plans.

#### Acceptance Criteria

1. WHEN a new user completes registration THEN the system SHALL redirect to profile creation form
2. WHEN a user fills the profile form THEN the system SHALL collect age, height, weight, fitness goal, experience level, workout frequency, session duration, diet preference, monthly budget, and optional location
3. WHEN a user submits a complete profile THEN the system SHALL validate all required fields and save the profile
4. WHEN a user clicks the profile icon THEN the system SHALL display the profile editing interface
5. WHEN a user updates their profile THEN the system SHALL automatically regenerate workout and nutrition plans
6. IF any required profile field is missing THEN the system SHALL display validation errors

### Requirement 3: Workout Plan Generation

**User Story:** As a user, I want the system to generate personalized workout plans based on my profile, so that I can follow a structured fitness routine.

#### Acceptance Criteria

1. WHEN a user completes their profile THEN the system SHALL generate a workout plan based on fitness goal, experience level, and available time
2. WHEN generating workout plans THEN the system SHALL use exercise data from exercises.csv
3. WHEN a workout plan is created THEN the system SHALL store it in the database linked to the user
4. WHEN displaying workout plans THEN the system SHALL show exercises, sets, reps, and rest periods
5. IF a user has beginner experience level THEN the system SHALL prioritize basic, low-risk exercises

### Requirement 4: Nutrition Plan Generation

**User Story:** As a user, I want the system to create budget-aware nutrition plans that fit my dietary preferences and financial constraints, so that I can eat healthily within my means.

#### Acceptance Criteria

1. WHEN a user profile includes dietary preferences and budget THEN the system SHALL generate a nutrition plan within the specified budget
2. WHEN creating nutrition plans THEN the system SHALL use food data from food_nutrition.csv and food_prices.csv
3. WHEN a nutrition plan exceeds the user's budget THEN the system SHALL replace expensive foods with cheaper alternatives
4. WHEN displaying nutrition plans THEN the system SHALL show estimated costs and budget comparison
5. IF a user is vegetarian THEN the system SHALL exclude non-vegetarian food items from the plan
6. WHEN calculating nutrition plans THEN the system SHALL determine appropriate calorie and macro targets based on user goals

### Requirement 5: Dashboard Display

**User Story:** As a user, I want to view my workout plans, nutrition plans, and progress on a central dashboard, so that I can easily access all my fitness information.

#### Acceptance Criteria

1. WHEN a user logs in THEN the system SHALL display the main dashboard
2. WHEN displaying the dashboard THEN the system SHALL show current workout plan, nutrition plan, calorie targets, and macro breakdown
3. WHEN on the dashboard THEN the system SHALL display budget comparison for the nutrition plan
4. WHEN a user has active plans THEN the system SHALL highlight the current day's workout and meals
5. WHEN displaying plans THEN the system SHALL provide clear navigation to detailed views

### Requirement 6: Pain Reporting and Workout Adaptation

**User Story:** As a user, I want to report pain or discomfort in free text, so that the system can adapt my current day's workout to be safer and more appropriate.

#### Acceptance Criteria

1. WHEN a user wants to report pain THEN the system SHALL provide a text input field for pain description
2. WHEN a user submits a pain report THEN the system SHALL analyze the text using keywords from pain_keywords.csv
3. WHEN pain is detected THEN the system SHALL identify affected body parts and modify ONLY the current day's workout
4. WHEN adapting workouts for pain THEN the system SHALL remove exercises that target affected body parts
5. WHEN removing risky exercises THEN the system SHALL replace them with safer alternatives or stretching exercises
6. WHEN pain affects a body part THEN the system SHALL recommend appropriate mobility and stretching exercises
7. IF no pain keywords are detected THEN the system SHALL store the report but not modify the workout

### Requirement 7: Data Management and Storage

**User Story:** As a system administrator, I want the application to efficiently manage static reference data and user-specific data, so that the system performs well and maintains data integrity.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL load static data from CSV files (exercises.csv, food_nutrition.csv, food_prices.csv, pain_keywords.csv)
2. WHEN storing user data THEN the system SHALL use SQLite database for users, profiles, workout plans, diet plans, and pain reports
3. WHEN accessing reference data THEN the system SHALL read directly from CSV files without database storage
4. WHEN generating plans THEN the system SHALL combine CSV reference data with user profile data
5. IF CSV files are missing or corrupted THEN the system SHALL display appropriate error messages

### Requirement 8: API Architecture

**User Story:** As a developer, I want the system to follow a clean API architecture with separated concerns, so that the application is maintainable and scalable.

#### Acceptance Criteria

1. WHEN implementing business logic THEN the system SHALL separate logic into dedicated logic layer modules
2. WHEN creating API endpoints THEN the system SHALL only call logic layer functions and not contain business logic
3. WHEN building the frontend THEN the system SHALL communicate with backend only through REST APIs
4. WHEN processing requests THEN the system SHALL validate input data at the API layer
5. IF external APIs are needed THEN the system SHALL use them only for data import, never for core application logic

### Requirement 9: Profile Updates and Plan Regeneration

**User Story:** As a user, I want my workout and nutrition plans to automatically update when I change my profile, so that my plans always reflect my current goals and constraints.

#### Acceptance Criteria

1. WHEN a user saves profile changes THEN the system SHALL automatically trigger plan regeneration
2. WHEN regenerating plans THEN the system SHALL use the updated profile data
3. WHEN plans are regenerated THEN the system SHALL replace existing plans with new ones
4. WHEN profile updates affect budget THEN the system SHALL recalculate nutrition plan costs
5. IF profile changes affect fitness goals THEN the system SHALL adjust workout intensity and focus accordingly