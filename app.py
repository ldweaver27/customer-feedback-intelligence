import os
import pandas as pd

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from supabase import Client, create_client

from ai_service import analyze_feedback, match_theme, propose_theme

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
@app.route("/companies", methods=["GET", "POST"])
def companies():
    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        arr_raw = request.form.get("arr", "").strip()

        if not name:
            error = "Company name is required."

        else:
            existing_company = (
                supabase.table("companies")
                .select("id")
                .eq("name", name)
                .execute()
            )

            if existing_company.data:
                error = "A company with this name already exists."

            else:
                arr = float(arr_raw) if arr_raw else None

                supabase.table("companies").insert(
                    {
                        "name": name,
                        "arr": arr,
                    }
                ).execute()

                return redirect(url_for("companies"))

    response = (
        supabase.table("companies")
        .select("*")
        .order("name")
        .execute()
    )

    return render_template(
        "companies.html",
        companies=response.data,
        error=error,
    )
@app.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
def edit_company(company_id):
    error = None

    company_response = (
        supabase.table("companies")
        .select("*")
        .eq("id", company_id)
        .single()
        .execute()
    )

    company = company_response.data

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        arr_raw = request.form.get("arr", "").strip()

        if not name:
            error = "Company name is required."

        else:
            duplicate = (
                supabase.table("companies")
                .select("id")
                .eq("name", name)
                .neq("id", company_id)
                .execute()
            )

            if duplicate.data:
                error = "A company with this name already exists."

            else:
                arr = float(arr_raw) if arr_raw else None

                (
                    supabase.table("companies")
                    .update(
                        {
                            "name": name,
                            "arr": arr,
                        }
                    )
                    .eq("id", company_id)
                    .execute()
                )

                return redirect(url_for("companies"))

    return render_template(
        "edit_company.html",
        company=company,
        error=error,
    )
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    error = None

    companies_response = (
        supabase.table("companies")
        .select("*")
        .order("name")
        .execute()
    )
    companies = companies_response.data

    if request.method == "POST":
        company_id = request.form.get("company_id", "").strip()
        feedback_text = request.form.get("feedback_text", "").strip()
        source = request.form.get("source", "").strip()
        feedback_date = request.form.get("feedback_date", "").strip()
        contact = request.form.get("contact", "").strip()

        if not company_id or not feedback_text or not source or not feedback_date:
            error = "Company, feedback, source, and date are required."

        else:
            supabase.table("feedback").insert(
                {
                    "company_id": int(company_id),
                    "feedback_text": feedback_text,
                    "source": source,
                    "feedback_date": feedback_date,
                    "contact": contact if contact else None,
                }
            ).execute()

            return redirect(url_for("feedback"))

    feedback_response = (
        supabase.table("feedback")
        .select("*, companies(name, arr), product_areas(name)")
        .order("feedback_date", desc=True)
        .execute()
    )

    return render_template(
        "feedback.html",
        companies=companies,
        feedback_records=feedback_response.data,
        error=error,
    )
@app.route("/feedback/upload", methods=["GET", "POST"])
def upload_feedback():
    error = None
    result = None

    if request.method == "POST":
        uploaded_file = request.files.get("file")

        if not uploaded_file or uploaded_file.filename == "":
            error = "Please select a CSV file."

        elif not uploaded_file.filename.lower().endswith(".csv"):
            error = "Only CSV files are supported."

        else:
            try:
                dataframe = pd.read_csv(uploaded_file)

                required_columns = {
                    "company",
                    "feedback",
                    "source",
                    "date",
                }

                missing_columns = (
                    required_columns - set(dataframe.columns)
                )

                if missing_columns:
                    error = (
                        "CSV is missing required columns: "
                        + ", ".join(sorted(missing_columns))
                    )

                else:
                    success_count = 0
                    errors = []

                    for index, row in dataframe.iterrows():
                        row_number = index + 2

                        company_name = (
                            str(row.get("company", "")).strip()
                            if pd.notna(row.get("company"))
                            else ""
                        )

                        feedback_text = (
                            str(row.get("feedback", "")).strip()
                            if pd.notna(row.get("feedback"))
                            else ""
                        )

                        source = (
                            str(row.get("source", "")).strip()
                            if pd.notna(row.get("source"))
                            else ""
                        )

                        feedback_date = (
                            str(row.get("date", "")).strip()
                            if pd.notna(row.get("date"))
                            else ""
                        )

                        contact = (
                            str(row.get("contact", "")).strip()
                            if pd.notna(row.get("contact"))
                            else None
                        )

                        arr_value = (
                            row.get("arr")
                            if "arr" in dataframe.columns
                            and pd.notna(row.get("arr"))
                            else None
                        )

                        if (
                            not company_name
                            or not feedback_text
                            or not source
                            or not feedback_date
                        ):
                            errors.append(
                                {
                                    "row": row_number,
                                    "reason": (
                                        "Company, feedback, source, "
                                        "and date are required."
                                    ),
                                }
                            )
                            continue

                        try:
                            parsed_date = pd.to_datetime(
                                feedback_date,
                                errors="raise",
                            ).date().isoformat()

                        except (ValueError, TypeError):
                            errors.append(
                                {
                                    "row": row_number,
                                    "reason": "Invalid feedback date.",
                                }
                            )
                            continue

                        company_response = (
                            supabase.table("companies")
                            .select("*")
                            .eq("name", company_name)
                            .execute()
                        )

                        if company_response.data:
                            company = company_response.data[0]

                        else:
                            company_data = {
                                "name": company_name,
                                "arr": (
                                    float(arr_value)
                                    if arr_value is not None
                                    else None
                                ),
                            }

                            new_company_response = (
                                supabase.table("companies")
                                .insert(company_data)
                                .execute()
                            )

                            company = new_company_response.data[0]

                        supabase.table("feedback").insert(
                            {
                                "company_id": company["id"],
                                "feedback_text": feedback_text,
                                "source": source,
                                "feedback_date": parsed_date,
                                "contact": contact,
                            }
                        ).execute()

                        success_count += 1

                    result = {
                        "success_count": success_count,
                        "failure_count": len(errors),
                        "errors": errors,
                    }

            except Exception as exc:
                error = f"Unable to process CSV: {exc}"

    return render_template(
        "upload_feedback.html",
        error=error,
        result=result,
    )
@app.route("/feedback/<int:feedback_id>/analyze", methods=["POST"])
def analyze_feedback_route(feedback_id):
    feedback_response = (
        supabase.table("feedback")
        .select("*")
        .eq("id", feedback_id)
        .single()
        .execute()
    )

    feedback_record = feedback_response.data

    product_areas_response = (
        supabase.table("product_areas")
        .select("*")
        .execute()
    )

    product_areas = product_areas_response.data

    analysis = analyze_feedback(
        feedback_record["feedback_text"],
        product_areas,
    )

    matching_product_area = next(
        (
            area
            for area in product_areas
            if area["name"] == analysis["product_area"]
        ),
        None,
    )

    product_area_id = (
        matching_product_area["id"]
        if matching_product_area
        else None
    )

    (
        supabase.table("feedback")
        .update(
            {
                "product_area_id": product_area_id,
                "ai_pain_point": analysis["pain_point"],
                "requested_solution": analysis["requested_solution"],
            }
        )
        .eq("id", feedback_id)
        .execute()
    )
    if product_area_id:
        themes_response = (
            supabase.table("themes")
            .select("*")
            .eq("product_area_id", product_area_id)
            .eq("status", "Approved")
            .execute()
        )

        approved_themes = themes_response.data

        theme_match = match_theme(
            analysis["pain_point"],
            approved_themes,
        )

        if theme_match["matched"] and theme_match["theme_id"]:
            existing_association = (
                supabase.table("feedback_themes")
                .select("id")
                .eq("feedback_id", feedback_id)
                .eq("theme_id", theme_match["theme_id"])
                .execute()
            )

            if not existing_association.data:
                supabase.table("feedback_themes").insert(
                    {
                        "feedback_id": feedback_id,
                        "theme_id": theme_match["theme_id"],
                    }
                ).execute()

        else:
            proposed_theme = propose_theme(
                analysis["pain_point"]
            )

            new_theme_response = (
                supabase.table("themes")
                .insert(
                    {
                        "product_area_id": product_area_id,
                        "name": proposed_theme["name"],
                        "description": proposed_theme["description"],
                        "status": "Proposed",
                    }
                )
                .execute()
            )

            new_theme = new_theme_response.data[0]

            supabase.table("feedback_themes").insert(
                {
                    "feedback_id": feedback_id,
                    "theme_id": new_theme["id"],
                }
            ).execute()

    return redirect(url_for("feedback"))

@app.route("/themes")
def themes():
    proposed_response = (
        supabase.table("themes")
        .select(
            "*, "
            "product_areas(name), "
            "feedback_themes("
            "feedback("
            "feedback_text, "
            "companies(name)"
            ")"
            ")"
        )
        .eq("status", "Proposed")
        .order("created_at")
        .execute()
    )

    approved_response = (
        supabase.table("themes")
        .select("*, product_areas(name)")
        .eq("status", "Approved")
        .order("name")
        .execute()
    )

    return render_template(
        "themes.html",
        proposed_themes=proposed_response.data,
        approved_themes=approved_response.data,
    )
@app.route("/themes/<int:theme_id>/edit", methods=["GET", "POST"])
def edit_theme(theme_id):
    theme_response = (
        supabase.table("themes")
        .select("*")
        .eq("id", theme_id)
        .single()
        .execute()
    )

    theme = theme_response.data

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if name and description:
            (
                supabase.table("themes")
                .update(
                    {
                        "name": name,
                        "description": description,
                    }
                )
                .eq("id", theme_id)
                .execute()
            )

            return redirect(url_for("themes"))

    return render_template(
        "edit_theme.html",
        theme=theme,
    )


@app.route("/themes/<int:theme_id>/approve", methods=["POST"])
def approve_theme(theme_id):
    (
        supabase.table("themes")
        .update({"status": "Approved"})
        .eq("id", theme_id)
        .execute()
    )

    return redirect(url_for("themes"))


@app.route("/themes/<int:theme_id>/reject", methods=["POST"])
def reject_theme(theme_id):
    (
        supabase.table("themes")
        .update({"status": "Rejected"})
        .eq("id", theme_id)
        .execute()
    )

    return redirect(url_for("themes"))


if __name__ == "__main__":
    app.run(debug=True)