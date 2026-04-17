"""
WellFit Pain Handler Module

This module provides pain-based workout modification logic.
Detects affected body parts and adapts workout plans for safety.

Safety Rules:
- No medical diagnosis
- Always prioritize safety
- Severe/unclear pain -> suggest rest
- Modifications limited to current day only

Architecture Rules:
- Rule-based logic only (no ML)
- No database
- Logic only
"""

import pandas as pd
import sys
import re
import difflib
from typing import List, Dict, Tuple, Optional


PAIN_INTENT_WORDS = {
    'pain', 'hurting', 'hurt', 'hurts', 'ache', 'aching', 'sore', 'soreness',
    'stiff', 'stiffness', 'strain', 'swelling', 'tender', 'injured', 'injury',
    'spasm', 'numb', 'numbness', 'tingling', 'burning'
}

SEVERE_INTENT_WORDS = {
    'severe', 'unbearable', 'sharp', 'shooting', 'cannot move', 'can\'t move',
    'spasm', 'numb', 'numbness', 'tingling', 'burning'
}


BODY_PART_ALIASES = {
    'knee': ['knee', 'knees', 'kneecap', 'patella'],
    'lower_back': ['lower back', 'back', 'lumbar', 'spine'],
    'shoulder': ['shoulder', 'shoulders', 'deltoid', 'rotator cuff'],
    'neck': ['neck', 'cervical'],
    'arm': ['arm', 'arms', 'bicep', 'biceps', 'tricep', 'triceps', 'forearm', 'forearms'],
    'foot': ['foot', 'feet', 'heel', 'heels', 'arch'],
    'leg': ['leg', 'legs', 'thigh', 'thighs', 'calf', 'calves', 'hamstring', 'hamstrings', 'quad', 'quads'],
    'general': ['sick', 'ill', 'unwell', 'fever', 'fatigue', 'tired', 'exhausted']
}


def _has_intent_term(text: str, terms: set[str], fuzzy_threshold: float = 0.88) -> bool:
    """Return True when text contains any term exactly or with a small typo."""
    text_l = str(text or '').lower()
    if not text_l:
        return False

    # Exact whole-word/phrase match.
    for term in terms:
        if re.search(r'\b' + re.escape(term) + r'\b', text_l):
            return True

    # Fuzzy single-token typo matching.
    tokens = re.findall(r'[a-z0-9]+', text_l)
    for token in tokens:
        for term in terms:
            if ' ' in term:
                continue
            if difflib.SequenceMatcher(None, token, term).ratio() >= fuzzy_threshold:
                return True

    return False


def detect_pain_location(
    pain_text: str,
    pain_keywords: pd.DataFrame
) -> Optional[Dict]:
    """
    Detect affected body part from user's pain description.
    
    Args:
        pain_text: User's description of pain
        pain_keywords: DataFrame with pain keywords and body parts
        
    Returns:
        Dictionary with:
            - body_part: Detected body part
            - severity_weight: Severity score
            - requires_medical_attention: Boolean flag
            - immediate_action: Recommended immediate action
        Returns None if no pain detected
    """
    if not isinstance(pain_text, str) or not pain_text.strip():
        return None

    pain_text_lower = pain_text.lower()
    has_pain_intent = _has_intent_term(pain_text_lower, PAIN_INTENT_WORDS)

    def _build_result_from_body_part(body_part: str) -> Optional[Dict]:
        subset = pain_keywords[
            pain_keywords['body_part'].astype(str).str.lower() == str(body_part).lower()
        ]
        if subset.empty:
            return None

        has_severe_cue = _has_intent_term(pain_text_lower, SEVERE_INTENT_WORDS, fuzzy_threshold=0.9)

        # Prefer non-medical variants by default unless severe danger cues are present.
        if not has_severe_cue:
            non_medical_subset = subset[
                subset['requires_medical_attention'].astype(str).str.lower() != 'true'
            ]
            if not non_medical_subset.empty:
                subset = non_medical_subset

            # Map user wording to closest keyword style to avoid over-escalation.
            symptom_term_map = [
                ('stiff', 'stiff'),
                ('ache', 'ache'),
                ('aching', 'ache'),
                ('sore', 'ache'),
                ('swelling', 'swelling'),
                ('strain', 'strain'),
                ('spasm', 'spasm'),
                ('hurt', 'pain'),
                ('hurting', 'pain'),
                ('hurts', 'pain'),
                ('pain', 'pain'),
            ]
            for text_term, keyword_term in symptom_term_map:
                if text_term in pain_text_lower:
                    preferred = subset[
                        subset['keyword'].astype(str).str.lower().str.contains(keyword_term, na=False)
                    ]
                    if not preferred.empty:
                        subset = preferred
                    break

        # If any row keyword is partially represented in message tokens, prefer it.
        text_tokens = set(re.findall(r'[a-z0-9]+', pain_text_lower))
        scored_rows = []
        for _, r in subset.iterrows():
            kw_tokens = set(re.findall(r'[a-z0-9]+', str(r['keyword']).lower()))
            overlap = len(text_tokens & kw_tokens)
            scored_rows.append((overlap, float(r['severity_weight']), r))

        scored_rows.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best = scored_rows[0][2]
        return {
            'body_part': best['body_part'],
            'severity_weight': best['severity_weight'],
            'requires_medical_attention': best['requires_medical_attention'],
            'immediate_action': best['immediate_action'],
            'contraindicated_exercises': best['contraindicated_exercises'],
            'recommended_alternatives': best['recommended_alternatives']
        }
    
    # Check each keyword
    matches = []
    matched_body_parts = set()
    for _, row in pain_keywords.iterrows():
        keyword = str(row['keyword']).strip().lower()
        if not keyword:
            continue

        # Match whole words/phrases to avoid false positives like "hip" inside "ship".
        keyword_pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(keyword_pattern, pain_text_lower):
            body_part = str(row['body_part']).lower().strip()
            matches.append({
                'body_part': row['body_part'],
                'severity_weight': row['severity_weight'],
                'requires_medical_attention': row['requires_medical_attention'],
                'immediate_action': row['immediate_action'],
                'contraindicated_exercises': row['contraindicated_exercises'],
                'recommended_alternatives': row['recommended_alternatives'],
                'keyword_len': len(keyword)
            })
            matched_body_parts.add(body_part)

    # Add alias-derived candidates for natural language messages so phrases like
    # "my shoulder and arm are hurting" can prefer specific body regions.
    if has_pain_intent:
        for body_part, aliases in BODY_PART_ALIASES.items():
            for alias in aliases:
                if re.search(r'\b' + re.escape(alias) + r'\b', pain_text_lower):
                    result = _build_result_from_body_part(body_part)
                    if result is None:
                        continue

                    # If body part is already matched by specific keyword, avoid duplicates.
                    if str(result['body_part']).lower().strip() in matched_body_parts:
                        continue

                    result['keyword_len'] = len(alias)
                    matches.append(result)
                    matched_body_parts.add(str(result['body_part']).lower().strip())
                    break
    
    if not matches:
        # Fallback: detect body-part mentions + pain-intent words in natural phrasing,
        # e.g., "my shoulder and arm are hurting".
        if not has_pain_intent:
            return None

        for body_part, aliases in BODY_PART_ALIASES.items():
            for alias in aliases:
                if re.search(r'\b' + re.escape(alias) + r'\b', pain_text_lower):
                    result = _build_result_from_body_part(body_part)
                    if result is not None:
                        return result

        return None
    
    # Prefer highest severity; for ties, prefer the most specific (longest) keyword.
    matches.sort(key=lambda x: (x['severity_weight'], x['keyword_len']), reverse=True)
    matches[0].pop('keyword_len', None)
    return matches[0]


def check_exercise_safety(
    exercise_name: str,
    affected_body_part: str,
    exercise_contraindications: pd.DataFrame
) -> Tuple[bool, str]:
    """
    Check if an exercise is safe for the affected body part.
    
    Args:
        exercise_name: Name of the exercise
        affected_body_part: Body part experiencing pain
        exercise_contraindications: DataFrame with contraindications
        
    Returns:
        Tuple of (is_safe, risk_level)
        - is_safe: True if exercise is safe, False otherwise
        - risk_level: 'none', 'low', 'medium', 'high'
    """
    # Check exact matches in contraindications
    contraindicated = exercise_contraindications[
        (exercise_contraindications['body_part'].str.lower() == affected_body_part.lower()) &
        (exercise_contraindications['exercise_name'].str.lower().str.contains(exercise_name.lower(), na=False))
    ]
    
    if len(contraindicated) > 0:
        risk_level = contraindicated.iloc[0]['risk_level']
        return False, risk_level
    
    # Check if exercise name contains body part keywords
    exercise_lower = exercise_name.lower()
    body_part_lower = affected_body_part.lower()
    
    # Map body parts to related keywords
    body_part_keywords = {
        'knee': ['squat', 'lunge', 'jump', 'leg press', 'leg extension'],
        'lower_back': ['deadlift', 'squat', 'row', 'good morning'],
        'shoulder': ['press', 'raise', 'pull', 'row', 'fly'],
        'elbow': ['curl', 'extension', 'press', 'pull'],
        'wrist': ['curl', 'extension', 'press'],
        'ankle': ['jump', 'run', 'calf'],
        'hip': ['squat', 'lunge', 'deadlift', 'leg press']
    }
    
    if body_part_lower in body_part_keywords:
        for keyword in body_part_keywords[body_part_lower]:
            if keyword in exercise_lower:
                return False, 'medium'
    
    return True, 'none'


def get_recovery_exercises(
    affected_body_part: str,
    recovery_exercises: pd.DataFrame
) -> List[Dict]:
    """
    Get suitable recovery exercises for the affected body part.
    
    Args:
        affected_body_part: Body part experiencing pain
        recovery_exercises: DataFrame with recovery exercises
        
    Returns:
        List of recovery exercise dictionaries
    """
    suitable_exercises = recovery_exercises[
        recovery_exercises['body_part'].str.lower() == affected_body_part.lower()
    ]
    
    recovery_list = []
    for _, exercise in suitable_exercises.iterrows():
        recovery_list.append({
            'name': exercise['exercise'],
            'category': exercise['type'],
            'muscle_groups': affected_body_part,
            'equipment': 'bodyweight',
            'sets': 2,
            'reps': exercise['duration'],
            'rest_seconds': 30,
            'instructions': f"Gentle {exercise['type']} exercise for {affected_body_part} recovery"
        })
    
    return recovery_list


def modify_workout_for_pain(
    pain_text: str,
    today_workout_plan: List[Dict],
    pain_keywords: pd.DataFrame,
    exercises_df: pd.DataFrame,
    exercise_contraindications: pd.DataFrame,
    recovery_exercises: pd.DataFrame
) -> Dict:
    """
    Modify a workout plan based on reported pain.
    
    Args:
        pain_text: User's description of pain
        today_workout_plan: List of exercises planned for today
        pain_keywords: DataFrame with pain keywords
        exercises_df: DataFrame with all exercises
        exercise_contraindications: DataFrame with contraindications
        recovery_exercises: DataFrame with recovery exercises
        
    Returns:
        Dictionary containing:
            - pain_detected: Boolean
            - affected_body_part: String or None
            - severity: String ('low', 'medium', 'high')
            - medical_attention_needed: Boolean
            - immediate_action: String with recommendations
            - original_workout: Original workout plan
            - modified_workout: Modified workout plan
            - removed_exercises: List of removed exercises
            - added_exercises: List of added recovery exercises
            - modification_summary: String summary
    """
    # WORKFLOW STEP 1: Pain Detection (NLP & Keyword Mapping)
    # Scans user's text against dataset, isolates exact body part, and checks severity / medical flags.
    # Detect pain location
    pain_info = detect_pain_location(pain_text, pain_keywords)
    
    if pain_info is None:
        return {
            'pain_detected': False,
            'affected_body_part': None,
            'severity': 'none',
            'medical_attention_needed': False,
            'immediate_action': 'No pain detected. Proceed with planned workout.',
            'original_workout': today_workout_plan,
            'modified_workout': today_workout_plan,
            'removed_exercises': [],
            'added_exercises': [],
            'modification_summary': 'No modifications needed.'
        }
    
    affected_body_part = pain_info['body_part']
    severity_weight = pain_info['severity_weight']
    
    # Determine severity level.
    # Supports both 0-10 and 0-1 scales in source datasets.
    if severity_weight <= 1.0:
        high_threshold = 0.7
        medium_threshold = 0.4
    else:
        high_threshold = 7
        medium_threshold = 4

    if severity_weight >= high_threshold:
        severity = 'high'
    elif severity_weight >= medium_threshold:
        severity = 'medium'
    else:
        severity = 'low'
    
    # WORKFLOW STEP 2: Safety Gateway / Hard Stops
    # If the pain severity is >7 or requires medical attention, abort workout, force rest day.
    # If severity is high or medical attention needed, recommend rest
    if severity == 'high' or pain_info['requires_medical_attention']:
        return {
            'pain_detected': True,
            'affected_body_part': affected_body_part,
            'severity': severity,
            'medical_attention_needed': pain_info['requires_medical_attention'],
            'immediate_action': pain_info['immediate_action'],
            'original_workout': today_workout_plan,
            'modified_workout': [],
            'removed_exercises': today_workout_plan,
            'added_exercises': [],
            'modification_summary': f"HIGH SEVERITY: Complete rest recommended for {affected_body_part}. " +
                                   ("Seek medical attention. " if pain_info['requires_medical_attention'] else "") +
                                   "All exercises removed for safety."
        }
    
    # WORKFLOW STEP 3: Exercise Contraindication Filtration
    # Loops through created workout, checking every exercise against contraindications for the injured body part.
    # Modify workout - remove unsafe exercises
    modified_workout = []
    removed_exercises = []
    
    for exercise in today_workout_plan:
        exercise_name = exercise.get('name', '')
        is_safe, risk_level = check_exercise_safety(
            exercise_name,
            affected_body_part,
            exercise_contraindications
        )
        
        if is_safe:
            modified_workout.append(exercise)
        else:
            removed_exercises.append({
                'name': exercise_name,
                'risk_level': risk_level
            })
    
    # WORKFLOW STEP 4: Active Recovery Injection
    # Injects gentle, bodyweight rehabilitation movements mapped to the specific hurting body part.
    # Add recovery exercises
    recovery_list = get_recovery_exercises(affected_body_part, recovery_exercises)
    added_exercises = recovery_list
    
    # Add recovery exercises to modified workout
    modified_workout.extend(recovery_list)
    
    # WORKFLOW STEP 5: Final Output & Modification Report
    # Generates a summary explaining what was removed for safety and what was added for recovery.
    # Create summary
    summary_parts = []
    summary_parts.append(f"Pain detected in {affected_body_part} (severity: {severity}).")
    summary_parts.append(f"Removed {len(removed_exercises)} unsafe exercise(s).")
    summary_parts.append(f"Added {len(added_exercises)} recovery exercise(s).")
    summary_parts.append(f"Immediate action: {pain_info['immediate_action']}")
    
    modification_summary = " ".join(summary_parts)
    
    return {
        'pain_detected': True,
        'affected_body_part': affected_body_part,
        'severity': severity,
        'medical_attention_needed': pain_info['requires_medical_attention'],
        'immediate_action': pain_info['immediate_action'],
        'original_workout': today_workout_plan,
        'modified_workout': modified_workout,
        'removed_exercises': removed_exercises,
        'added_exercises': added_exercises,
        'modification_summary': modification_summary
    }


def print_modification_report(result: Dict) -> None:
    """
    Print a formatted report of workout modifications.
    
    Args:
        result: Result dictionary from modify_workout_for_pain()
    """
    print("\n" + "=" * 80)
    print("PAIN-BASED WORKOUT MODIFICATION REPORT")
    print("=" * 80)
    
    if not result['pain_detected']:
        print("\nNo pain detected. Proceed with planned workout.")
        print("=" * 80)
        return
    
    print(f"\nAffected Body Part: {result['affected_body_part'].upper()}")
    print(f"Severity Level: {result['severity'].upper()}")
    print(f"Medical Attention Needed: {'YES' if result['medical_attention_needed'] else 'NO'}")
    print(f"\nImmediate Action:")
    print(f"  {result['immediate_action']}")
    
    print("\n" + "-" * 80)
    print("MODIFICATION SUMMARY")
    print("-" * 80)
    print(result['modification_summary'])
    
    if result['removed_exercises']:
        print("\n" + "-" * 80)
        print("REMOVED EXERCISES (Unsafe for current condition)")
        print("-" * 80)
        for i, ex in enumerate(result['removed_exercises'], 1):
            print(f"{i}. {ex['name']} (Risk: {ex['risk_level']})")
    
    if result['added_exercises']:
        print("\n" + "-" * 80)
        print("ADDED RECOVERY EXERCISES")
        print("-" * 80)
        for i, ex in enumerate(result['added_exercises'], 1):
            print(f"{i}. {ex['name']}")
            print(f"   Type: {ex['category']}")
            print(f"   Sets x Duration: {ex['sets']} x {ex['reps']}")
    
    print("\n" + "-" * 80)
    print("MODIFIED WORKOUT PLAN")
    print("-" * 80)
    
    if not result['modified_workout']:
        print("COMPLETE REST RECOMMENDED - No exercises")
    else:
        for i, ex in enumerate(result['modified_workout'], 1):
            print(f"\n{i}. {ex['name']}")
            print(f"   Category: {ex.get('category', 'N/A')}")
            print(f"   Sets x Reps: {ex.get('sets', 'N/A')} x {ex.get('reps', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("SAFETY REMINDER: This is not medical advice. Consult a healthcare")
    print("professional if pain persists or worsens.")
    print("=" * 80)


if __name__ == "__main__":
    """
    Test block to demonstrate pain-based workout modification.
    """
    print("Loading CSV data...")
    
    try:
        # Import data loader
        from data_loader import (
            load_pain_keywords,
            load_exercises,
            load_exercise_contraindications,
            load_recovery_exercises
        )
        
        # Load data
        pain_keywords = load_pain_keywords()
        exercises = load_exercises()
        contraindications = load_exercise_contraindications()
        recovery_exercises = load_recovery_exercises()
        
        print(f"Loaded {len(pain_keywords)} pain keywords")
        print(f"Loaded {len(exercises)} exercises")
        print(f"Loaded {len(contraindications)} contraindications")
        print(f"Loaded {len(recovery_exercises)} recovery exercises")
        
        # Create a sample workout plan
        sample_workout = [
            {
                'name': 'Squats',
                'category': 'strength',
                'muscle_groups': 'quadriceps,hamstrings,glutes',
                'equipment': 'barbell',
                'sets': 4,
                'reps': '8-12',
                'rest_seconds': 90,
                'instructions': 'Compound leg exercise'
            },
            {
                'name': 'Lunges',
                'category': 'strength',
                'muscle_groups': 'quadriceps,hamstrings,glutes',
                'equipment': 'bodyweight',
                'sets': 3,
                'reps': '10-12',
                'rest_seconds': 60,
                'instructions': 'Single leg exercise'
            },
            {
                'name': 'Bench Press',
                'category': 'strength',
                'muscle_groups': 'chest,triceps,shoulders',
                'equipment': 'barbell',
                'sets': 4,
                'reps': '8-12',
                'rest_seconds': 90,
                'instructions': 'Compound chest exercise'
            },
            {
                'name': 'Pull-ups',
                'category': 'strength',
                'muscle_groups': 'back,biceps',
                'equipment': 'bodyweight',
                'sets': 3,
                'reps': '8-12',
                'rest_seconds': 90,
                'instructions': 'Compound back exercise'
            }
        ]
        
        # Simulate pain input
        pain_input = "I have some knee pain today"
        
        print(f"\n{'=' * 80}")
        print("SCENARIO: User reports knee pain")
        print(f"{'=' * 80}")
        print(f"Pain Input: '{pain_input}'")
        print(f"\nOriginal Workout ({len(sample_workout)} exercises):")
        for i, ex in enumerate(sample_workout, 1):
            print(f"  {i}. {ex['name']}")
        
        # Modify workout based on pain
        result = modify_workout_for_pain(
            pain_text=pain_input,
            today_workout_plan=sample_workout,
            pain_keywords=pain_keywords,
            exercises_df=exercises,
            exercise_contraindications=contraindications,
            recovery_exercises=recovery_exercises
        )
        
        # Print modification report
        print_modification_report(result)
        
        print("\nSUCCESS: Pain handler demonstration complete!")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
