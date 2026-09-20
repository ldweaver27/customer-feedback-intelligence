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