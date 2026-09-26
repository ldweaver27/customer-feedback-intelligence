def classify_demand(demand_rate):
    if demand_rate >= 25:
        return "High"

    if demand_rate >= 10:
        return "Medium"

    return "Low"


def calculate_theme_demand(theme_feedback, total_feedback_companies):
    unique_companies = {}

    for association in theme_feedback:
        feedback = association["feedback"]
        company = feedback["companies"]

        company_id = company["id"]

        if company_id not in unique_companies:
            unique_companies[company_id] = company

    unique_company_count = len(unique_companies)
    feedback_volume = len(theme_feedback)

    if total_feedback_companies > 0:
        demand_rate = (
            unique_company_count
            / total_feedback_companies
        ) * 100
    else:
        demand_rate = 0

    represented_arr = sum(
        company["arr"]
        for company in unique_companies.values()
        if company["arr"] is not None
    )

    return {
        "unique_companies": unique_company_count,
        "feedback_volume": feedback_volume,
        "demand_rate": round(demand_rate, 1),
        "demand_classification": classify_demand(demand_rate),
        "represented_arr": represented_arr,
    }