import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
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

@app.route("/product-areas", methods=["GET", "POST"])
def product_areas():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        core_functionality = request.form.get("core_functionality", "").strip()

        if name and description and core_functionality:
            supabase.table("product_areas").insert(
                {
                    "name": name,
                    "description": description,
                    "core_functionality": core_functionality,
                }
            ).execute()

            return redirect(url_for("product_areas"))

    response = (
        supabase.table("product_areas")
        .select("*")
        .order("created_at")
        .execute()
    )

    return render_template(
        "product_areas.html",
        product_areas=response.data,
    )
@app.route("/product-areas/<int:area_id>/edit", methods=["GET", "POST"])
def edit_product_area(area_id):
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        core_functionality = request.form.get("core_functionality", "").strip()

        if name and description and core_functionality:
            (
                supabase.table("product_areas")
                .update(
                    {
                        "name": name,
                        "description": description,
                        "core_functionality": core_functionality,
                    }
                )
                .eq("id", area_id)
                .execute()
            )

            return redirect(url_for("product_areas"))

    response = (
        supabase.table("product_areas")
        .select("*")
        .eq("id", area_id)
        .single()
        .execute()
    )

    return render_template(
        "edit_product_area.html",
        area=response.data,
    )
@app.route("/product-areas/<int:area_id>/delete", methods=["POST"])
def delete_product_area(area_id):
    (
        supabase.table("product_areas")
        .delete()
        .eq("id", area_id)
        .execute()
    )

    return redirect(url_for("product_areas"))
if __name__ == "__main__":
    app.run(debug=True)