"""
plan_engine.py
Knowledge base + inference logic for the fitness expert system.
Builds a full structured weekly workout split (exercises/sets/reps) and
a diet plan, and generates job-based "missed workout" compensation tasks.
"""

import math

# ---------------------------------------------------------------------------
# EXERCISE KNOWLEDGE BASE
# Each entry: gym version + a no-equipment (bodyweight) alternative.
# ---------------------------------------------------------------------------

EXERCISES = {
    "push": [
        {"gym": "Barbell Bench Press", "home": "Push-Ups"},
        {"gym": "Overhead Barbell Press", "home": "Pike Push-Ups"},
        {"gym": "Incline Dumbbell Press", "home": "Decline Push-Ups"},
        {"gym": "Cable Tricep Pushdown", "home": "Bench/Chair Dips"},
        {"gym": "Lateral Raises", "home": "Lateral Raises (water bottles/bags)"},
    ],
    "pull": [
        {"gym": "Deadlift", "home": "Superman Hold"},
        {"gym": "Lat Pulldown", "home": "Pull-Ups (or Doorway Rows)"},
        {"gym": "Barbell Row", "home": "Backpack Rows (loaded bag)"},
        {"gym": "Seated Cable Row", "home": "Towel Rows (under a table edge)"},
        {"gym": "Barbell Curl", "home": "Bodyweight Curls (resistance band/bag)"},
    ],
    "legs": [
        {"gym": "Barbell Back Squat", "home": "Bodyweight Squats"},
        {"gym": "Romanian Deadlift", "home": "Single-Leg Glute Bridge"},
        {"gym": "Leg Press", "home": "Bulgarian Split Squats"},
        {"gym": "Walking Lunges (dumbbells)", "home": "Walking Lunges (bodyweight)"},
        {"gym": "Standing Calf Raise", "home": "Single-Leg Calf Raise"},
    ],
    "core": [
        {"gym": "Cable Crunch", "home": "Crunches"},
        {"gym": "Hanging Leg Raise", "home": "Lying Leg Raise"},
        {"gym": "Weighted Plank", "home": "Plank"},
        {"gym": "Russian Twist (plate)", "home": "Russian Twist (bodyweight)"},
    ],
    "full_body": [
        {"gym": "Kettlebell Swing", "home": "Jump Squats"},
        {"gym": "Dumbbell Thruster", "home": "Burpees"},
        {"gym": "Battle Ropes", "home": "Mountain Climbers"},
        {"gym": "Rowing Machine Sprint", "home": "High Knees"},
    ],
    "mobility": [
        {"gym": "Cat-Cow Stretch", "home": "Cat-Cow Stretch"},
        {"gym": "World's Greatest Stretch", "home": "World's Greatest Stretch"},
        {"gym": "Downward Dog to Cobra Flow", "home": "Downward Dog to Cobra Flow"},
        {"gym": "Hip Flexor Lunge Stretch", "home": "Hip Flexor Lunge Stretch"},
        {"gym": "Seated Forward Fold", "home": "Seated Forward Fold"},
        {"gym": "Thread the Needle", "home": "Thread the Needle"},
    ],
}


def pick(category, n, equipment):
    """Pick n exercises from a category, rotating through the list so
    consecutive calls don't repeat the same items, respecting equipment."""
    items = EXERCISES[category]
    key = "gym" if equipment != "no" else "home"
    names = [it[key] for it in items]
    # simple rotation based on a module-level counter per category
    start = pick.counters.get(category, 0)
    picked = [names[(start + i) % len(names)] for i in range(n)]
    pick.counters[category] = (start + n) % len(names)
    return picked


pick.counters = {}


def sets_reps_line(exercise, sets, reps, note=None):
    line = f"{exercise} — {sets} sets x {reps} reps"
    if note:
        line += f" ({note})"
    return line


# ---------------------------------------------------------------------------
# WORKOUT SPLIT GENERATION
# ---------------------------------------------------------------------------

def build_workout_plan(goal, experience, days, equipment):
    """Returns a list of day dicts: {label, focus, items: [str, ...], is_rest}"""
    days = max(1, min(int(days or 3), 7))
    pick.counters = {}  # reset rotation so plans are deterministic per request
    plan = []

    if goal == "muscle_gain" and experience == "beginner":
        # Full-body, same structure each day, exercises rotate for variety
        for d in range(days):
            items = []
            items.append(sets_reps_line(pick("legs", 1, equipment)[0], 3, "10-12"))
            items.append(sets_reps_line(pick("push", 1, equipment)[0], 3, "8-12"))
            items.append(sets_reps_line(pick("pull", 1, equipment)[0], 3, "8-12"))
            items.append(sets_reps_line(pick("push", 1, equipment)[0], 3, "10-12"))
            items.append(sets_reps_line(pick("core", 1, equipment)[0], 3, "12-15"))
            plan.append({"label": f"Day {d+1}", "focus": "Full-Body Strength", "exercises": items, "is_rest": False})

    elif goal == "muscle_gain" and experience in ("intermediate", "advanced"):
        cycle = ["push", "pull", "legs"]
        for d in range(days):
            cat = cycle[d % 3]
            focus_name = {"push": "Push (Chest/Shoulders/Triceps)",
                          "pull": "Pull (Back/Biceps)",
                          "legs": "Legs"}[cat]
            names = pick(cat, 4, equipment)
            reps = "6-8" if experience == "advanced" else "8-10"
            items = [sets_reps_line(n, 4, reps if i < 2 else "10-12") for i, n in enumerate(names)]
            items.append(sets_reps_line(pick("core", 1, equipment)[0], 3, "12-15"))
            plan.append({"label": f"Day {d+1}", "focus": focus_name, "exercises": items, "is_rest": False})

    elif goal == "weight_loss":
        for d in range(days):
            names = pick("full_body", 3, equipment) + pick("legs", 1, equipment) + pick("core", 1, equipment)
            items = [sets_reps_line(n, 3, "15-20", note="minimal rest, circuit style") for n in names]
            items.append("Finish with 15-20 min moderate-pace cardio (brisk walk / cycling / jump rope)")
            plan.append({"label": f"Day {d+1}", "focus": "Circuit + Cardio", "exercises": items, "is_rest": False})

    elif goal == "endurance":
        for d in range(days):
            if d % 5 in (0, 1, 2):
                cardio_type = ["Running", "Cycling", "Swimming"][d % 3]
                items = [f"{cardio_type} — steady state, 30-40 min, conversational pace",
                         "Increase weekly distance/duration by no more than 10%"]
                plan.append({"label": f"Day {d+1}", "focus": f"Cardio ({cardio_type})", "exercises": items, "is_rest": False})
            else:
                names = pick("legs", 1, equipment) + pick("push", 1, equipment) + pick("pull", 1, equipment) + pick("core", 1, equipment)
                items = [sets_reps_line(n, 2, "12-15") for n in names]
                items.append("Light strength work to protect joints — do not train to failure")
                plan.append({"label": f"Day {d+1}", "focus": "Support Strength", "exercises": items, "is_rest": False})

    elif goal == "flexibility":
        for d in range(days):
            names = pick("mobility", 5, equipment)
            items = [f"{n} — hold 30-45 sec / 2 rounds" for n in names]
            plan.append({"label": f"Day {d+1}", "focus": "Mobility & Yoga", "exercises": items, "is_rest": False})

    else:
        for d in range(days):
            names = pick("full_body", 2, equipment) + pick("legs", 1, equipment) + pick("core", 1, equipment)
            items = [sets_reps_line(n, 3, "10-12") for n in names]
            items.append("10-15 min light cardio to finish")
            plan.append({"label": f"Day {d+1}", "focus": "General Fitness", "exercises": items, "is_rest": False})

    return plan


# ---------------------------------------------------------------------------
# DIET PLAN GENERATION
# ---------------------------------------------------------------------------

def build_diet_plan(goal, weight_kg=None, height_cm=None, age=None, sex=None, days=4):
    """Returns dict with calories/macros (if biometrics given) plus general guidance."""
    tips = {
        "muscle_gain": "Eat in a calorie surplus with high protein intake to support muscle repair and growth.",
        "weight_loss": "Eat in a moderate calorie deficit while keeping protein high to preserve lean muscle mass.",
        "endurance": "Prioritize carbohydrates for glycogen stores, with adequate protein for recovery.",
        "flexibility": "Maintain a balanced diet — flexibility work has low energy demand, so focus on hydration and joint-supportive nutrients (omega-3s, vitamin C).",
    }
    diet_tip = tips.get(goal, "Maintain a balanced diet with adequate protein, carbohydrates, and healthy fats.")

    result = {
        "diet_tip": diet_tip,
        "calories": None,
        "protein_g": None,
        "carbs_g": None,
        "fat_g": None,
        "meal_structure": [
            "Meal 1 (Breakfast): protein + complex carbs + fruit",
            "Meal 2 (Lunch): protein + carbs + vegetables",
            "Snack: nuts / yogurt / fruit",
            "Meal 3 (Dinner): protein + vegetables + moderate carbs",
        ],
        "food_groups": {
            "Protein sources": "eggs, chicken, fish, paneer/tofu, legumes, dal, curd",
            "Carb sources": "rice, roti/chapati, oats, sweet potato, fruit",
            "Fats": "nuts, seeds, olive/mustard oil, ghee in moderation",
            "Vegetables": "leafy greens, mixed seasonal vegetables — aim for variety and color",
        },
    }

    if weight_kg and height_cm and age and sex:
        try:
            weight_kg = float(weight_kg)
            height_cm = float(height_cm)
            age = float(age)
            # Mifflin-St Jeor BMR
            if sex == "male":
                bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
            else:
                bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

            activity_multiplier = 1.35 + (min(days, 6) * 0.05)  # rough scale w/ training frequency
            tdee = bmr * activity_multiplier

            if goal == "muscle_gain":
                calories = tdee * 1.12
                protein_per_kg = 2.0
            elif goal == "weight_loss":
                calories = tdee * 0.80
                protein_per_kg = 2.0
            else:
                calories = tdee
                protein_per_kg = 1.4

            protein_g = protein_per_kg * weight_kg
            fat_g = (calories * 0.25) / 9
            carb_g = (calories - (protein_g * 4) - (fat_g * 9)) / 4

            result["calories"] = round(calories)
            result["protein_g"] = round(protein_g)
            result["carbs_g"] = round(max(carb_g, 0))
            result["fat_g"] = round(fat_g)
        except (ValueError, ZeroDivisionError):
            pass

    return result


# ---------------------------------------------------------------------------
# JOB / LIFESTYLE-BASED "MISSED WORKOUT" COMPENSATION TASKS
# ---------------------------------------------------------------------------

JOB_ACTIVITY_MAP = {
    "desk_job": [
        "Take a brisk 10-minute walk every 2 hours during work",
        "Do a 5-minute desk stretch routine (neck, shoulders, wrists, hips)",
        "Use stairs instead of elevators/escalators all day",
        "Stand and do 15 bodyweight squats every time you take a call",
    ],
    "light_active": [
        "Add a brisk 20-minute walk at the start or end of your shift",
        "Do 10 minutes of mobility/stretching before bed",
        "Take the longer route on foot for any short errands today",
        "Do 3 sets of 15 bodyweight squats during a break",
    ],
    "physical_labor": [
        "Your job already provides significant activity — prioritize a 10-minute mobility/stretch session to aid recovery",
        "Do light static stretching for major muscle groups before sleeping",
        "Hydrate well and prioritize protein intake today to support recovery",
        "Take a short easy-pace walk to actively recover rather than training hard",
    ],
    "other": [
        "Take a brisk 20-30 minute walk sometime today",
        "Do a 10-minute full-body mobility/stretch routine",
        "Find 10 minutes for bodyweight movement: squats, push-ups, or a plank hold",
    ],
}


def get_missed_workout_tasks(job_type):
    return JOB_ACTIVITY_MAP.get(job_type, JOB_ACTIVITY_MAP["other"])
