# Fitness Expert System

## What's new in this version
- **Full structured weekly workout split** — real exercises with sets x reps per day, not just a one-line summary.
- **Diet plan with macros** — if weight/height/age/sex are provided, it calculates calories + protein/carbs/fat targets (Mifflin-St Jeor formula). Without them, it still gives general food-group guidance.
- **Job-based "missed workout" backup plan** — pick a job/activity type and get substitute active tasks for days you can't train.
- **Optional body photo upload** — an AI vision call gives a soft "lean / moderate / solid" build read, used only to nudge starting workout intensity. Never stored on disk, never shown as a number, and it fails silently (plan still generates) if unset or unclear.

## Setup

```bash
pip install -r requirements.txt
```

### Required for the photo feature: Anthropic API key
The body-photo analysis calls the Anthropic API, so you need your own key:

1. Get a key from https://console.anthropic.com/ (Settings → API Keys).
2. Set it as an environment variable before running the app — **do not hardcode it in app.py or commit it**:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python app.py
```

If `ANTHROPIC_API_KEY` isn't set, the app still works fine — it just skips the photo analysis and generates the plan without a build note.

### Privacy note
Since this app accepts a photo of a real person, if you deploy this for other users:
- Get their explicit consent before they upload (the form already has a hint about this — consider a required checkbox for a public deployment).
- The current code never writes the photo to disk (processed in memory, discarded after the API call), but double-check your hosting platform isn't logging request bodies.
- Consider adding a max-upload-size message in the UI (currently capped server-side at 5 MB).

## Files
- `app.py` — Flask routes, form handling, photo upload
- `plan_engine.py` — exercise database, workout split generator, diet/macro calculator, job-based task list
- `body_analysis.py` — Anthropic vision call for the build estimate
- `templates/index.html`, `static/style.css` — UI
