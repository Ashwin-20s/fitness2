"""
body_analysis.py
Sends an uploaded photo to the Anthropic API for a brief, respectful,
fitness-calibration-only estimate of build (e.g. lean / moderate / solid).

This is NOT a medical or body-fat measurement tool. It only exists to
help pick a sensible starting intensity/weight recommendation. Results
are always shown as a soft qualitative note, never as a diagnosis or
a number the user could over-index on.

Requires the ANTHROPIC_API_KEY environment variable to be set.
See README.md for setup instructions.
"""

import base64
import os

import anthropic

SYSTEM_PROMPT = (
    "You are a fitness-coaching assistant calibrating a workout program. "
    "You will be shown a photo a user submitted of themselves for this sole purpose. "
    "Reply with ONLY one word from this exact set: lean, moderate, solid, unclear. "
    "Definitions: 'lean' = visibly low body fat / slight build, 'moderate' = average "
    "build, 'solid' = higher body fat or heavily muscled build, 'unclear' = the image "
    "does not clearly show a person's build (bad lighting, not a body photo, unclear angle, "
    "or any reason you cannot make a respectful estimate). "
    "Never comment on attractiveness, age, gender, identity, or anything beyond this single "
    "word. If the image is inappropriate, sexual, of a minor, or not suitable for this use, "
    "reply 'unclear'."
)

_VALID_RESULTS = {"lean", "moderate", "solid", "unclear"}


def analyze_build(image_bytes, media_type="image/jpeg"):
    """Returns one of: 'lean', 'moderate', 'solid', 'unclear', or None on error."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=10,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Estimate build for workout calibration purposes.",
                        },
                    ],
                }
            ],
        )

        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip().lower()

        return text if text in _VALID_RESULTS else "unclear"

    except Exception:
        # Fail soft — the plan still generates without the photo insight.
        return None


BUILD_NOTES = {
    "lean": "Your build reads as lean — plans below start with slightly lighter loads and higher reps to build a base before adding heavy weight.",
    "moderate": "Your build reads as average/moderate — the plan below uses standard starting loads for your experience level.",
    "solid": "Your build reads as solid/higher body fat or heavily muscled — the plan below leans on circuit-style and compound work to maximize efficiency.",
    "unclear": None,
}
