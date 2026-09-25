import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def analyze_feedback(feedback_text, product_areas):
    client = OpenAI()

    product_area_context = "\n".join(
        [   
            (
                f"- {area['name']}: {area['description']} "
                f"Core functionality: {area['core_functionality']}"
            )
            for area in product_areas
        ]
    )

    prompt = f"""
You are analyzing customer feedback for a Product Manager.

The Product Manager has defined the following product areas:

{product_area_context}

Customer feedback:
"{feedback_text}"

Analyze the feedback and return:

1. The most appropriate product area from the provided list.
2. The underlying customer pain point.
3. The specific solution or feature requested by the customer, if one exists.

Important rules:
- You must select a product area only from the provided list.
- Do not create new product areas.
- Describe the pain point in solution-neutral language.
- Do not simply repeat the requested feature as the pain point.
- If the customer does not request a specific solution, requested_solution must be null.

Return only valid JSON in this exact structure:

{{
    "product_area": "product area name",
    "pain_point": "solution-neutral description of the underlying problem",
    "requested_solution": "requested feature or solution, or null"
}}
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    return json.loads(response.output_text)


def match_theme(pain_point, themes):
    client = OpenAI()

    if not themes:
        return {
            "matched": False,
            "theme_id": None,
            "confidence": 0.0,
        }

    theme_context = "\n".join(
        [
            (
                f"- Theme ID {theme['id']}: {theme['name']}\n"
                f"  Description: {theme['description']}"
            )
            for theme in themes
        ]
    )

    prompt = f"""
You are helping a Product Manager organize customer pain points
into an existing taxonomy of approved themes.

Customer pain point:
"{pain_point}"

Approved themes:

{theme_context}

Determine whether the customer pain point represents substantially
the same underlying customer problem as one of the approved themes.

Important rules:
- Match based on the underlying problem, not exact wording.
- Different requested solutions can represent the same pain point.
- Do not force a match simply because two items relate to the same
  broad product area.
- Only match when the underlying customer problem is meaningfully
  the same.
- If no theme appropriately represents the pain point, return no match.

Return only valid JSON in this exact structure:

{{
    "matched": true or false,
    "theme_id": theme ID or null,
    "confidence": number between 0 and 1
}}
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    return json.loads(response.output_text)

def propose_theme(pain_point):
    client = OpenAI()

    prompt = f"""
You are helping a Product Manager organize customer feedback.

The following customer pain point does not appropriately match
an existing approved pain-point theme:

"{pain_point}"

Create a proposed pain-point theme that represents the underlying
customer problem.

Important rules:
- The theme must describe the customer problem, not a requested feature.
- Keep the theme broad enough that semantically similar customer
  problems could be grouped into it later.
- Do not make the theme so broad that unrelated problems would
  reasonably belong to it.
- Use solution-neutral language.
- Keep the theme name concise.
- The description should clearly explain the underlying problem.

Return only valid JSON in this exact structure:

{{
    "name": "concise pain-point theme name",
    "description": "clear solution-neutral description"
}}
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    return json.loads(response.output_text)