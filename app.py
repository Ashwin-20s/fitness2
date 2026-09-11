import os

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from plan_engine import build_workout_plan, build_diet_plan, get_missed_workout_tasks
from body_analysis import analyze_build, BUILD_NOTES

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def get_fitness_plan(goal, experience, equipment, days, job_type,
                      weight_kg=None, height_cm=None, age=None, sex=None,
                      build_estimate=None):
    """
    Full expert-system inference: builds the weekly workout split,
    the diet plan, and the job-based missed-workout compensation list.
    """
    workout_days = build_workout_plan(goal, experience, days, equipment)
    diet = build_diet_plan(goal, weight_kg, height_cm, age, sex, days=len(workout_days))
    missed_workout_tasks = get_missed_workout_tasks(job_type)

    plan_names = {
        ("muscle_gain", "beginner"): "Full-Body Strength Training",
        ("muscle_gain", "intermediate"): "Push / Pull / Legs (PPL) Split",
        ("muscle_gain", "advanced"): "Push / Pull / Legs (PPL) Split",
    }
    plan_name = plan_names.get((goal, experience))
    if not plan_name:
        plan_name = {
            "weight_loss": "Circuit Training + Cardio",
            "endurance": "Cardio-Focused Program",
            "flexibility": "Mobility & Yoga Routine",
        }.get(goal, "General Fitness Plan")

    return {
        "plan": plan_name,
        "workout_days": workout_days,
        "diet": diet,
        "missed_workout_tasks": missed_workout_tasks,
        "build_note": BUILD_NOTES.get(build_estimate) if build_estimate else None,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    form_data = {
        "goal": "", "experience": "beginner", "days": "4", "equipment": "yes",
        "job_type": "desk_job", "weight_kg": "", "height_cm": "", "age": "", "sex": "male",
    }

    if request.method == "POST":
        for field in ("goal", "experience", "days", "job_type", "weight_kg", "height_cm", "age", "sex"):
            form_data[field] = request.form.get(field, form_data.get(field, ""))
        form_data["equipment"] = request.form.get("equipment", "no")

        build_estimate = None
        photo = request.files.get("body_photo")
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            content_type = photo.mimetype
            if content_type in ALLOWED_IMAGE_TYPES:
                image_bytes = photo.read()
                # Processed in-memory only — never written to disk.
                build_estimate = analyze_build(image_bytes, media_type=content_type)

        result = get_fitness_plan(
            form_data["goal"], form_data["experience"], form_data["equipment"],
            form_data["days"], form_data["job_type"],
            weight_kg=form_data["weight_kg"] or None,
            height_cm=form_data["height_cm"] or None,
            age=form_data["age"] or None,
            sex=form_data["sex"],
            build_estimate=build_estimate,
        )

    return render_template("index.html", result=result, form_data=form_data)


if __name__ == "__main__":
    app.run(debug=True)
