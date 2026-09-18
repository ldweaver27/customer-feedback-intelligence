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
    response = supabase.table("product_areas").select("*").execute()
    product_areas = response.data

    return {
        "message": "Customer Feedback Intelligence",
        "product_areas": product_areas,
    }


if __name__ == "__main__":
    app.run(debug=True)