import os

from dotenv import load_dotenv
from flask import Flask
from supabase import Client, create_client

load_dotenv()

app = Flask(__name__)

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_key)


@app.route("/")
def home():
    product_areas_response = supabase.table("product_areas").select("*").execute()
    companies_response = supabase.table("companies").select("*").execute()
    feedback_response = (
        supabase.table("feedback")
        .select("*, companies(name, arr)")
        .execute()
    )

    return {
        "message": "Customer Feedback Intelligence",
        "product_areas": product_areas_response.data,
        "companies": companies_response.data,
        "feedback": feedback_response.data,
    }


if __name__ == "__main__":
    app.run(debug=True)