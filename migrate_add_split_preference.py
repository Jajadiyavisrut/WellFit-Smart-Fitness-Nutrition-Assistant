import sqlite3

db_path = r"v:\AIML(sub)\sem 4\SGP\WellFit – Smart Fitness & Nutrition Assistant\database\wellfit.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE user_profiles 
        ADD COLUMN workout_split_preference TEXT DEFAULT 'default' 
        CHECK(workout_split_preference IN ('default', 'one_muscle_per_day'))
    """)
    conn.commit()
    print("SUCCESS: Added workout_split_preference column to user_profiles table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("INFO: Column already exists, skipping migration")
    else:
        print(f"ERROR: {e}")
        raise
finally:
    conn.close()
