# Customer Feedback Intelligence

An AI-powered product management application that transforms fragmented customer feedback into structured, transparent demand intelligence.

**Live Application:** https://customer-feedback-intelligence-31uz.onrender.com

**Agile Project Board:** https://ldweaver27.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog

**Detailed Design & Testing Documentation:**  
[DESIGN_AND_TESTING.md](DESIGN_AND_TESTING.md)

---

## Overview

Product teams receive customer feedback through many different channels, including CRM systems, customer success teams, product analytics tools, interviews, email, and in-application feedback.

The challenge is not simply collecting that feedback. Product Managers must determine:

- What underlying problems customers are experiencing
- Which areas of the product are affected
- Whether differently worded feedback represents the same customer problem
- How broadly a problem is experienced across the customer base
- Which requested features are solutions versus the underlying customer pain point
- What customer and commercial context is associated with each problem

Customer Feedback Intelligence was developed to transform fragmented feedback into structured product intelligence while preserving Product Manager oversight of the resulting taxonomy.

---

## Core Product Philosophy

Customer requests are not always the same thing as customer problems.

For example, one customer may request an API while another requests an Excel export. Although the requested solutions differ, both customers may be experiencing the same underlying problem: significant manual effort accessing and preparing application data for downstream analysis.

Customer Feedback Intelligence therefore separates:

**Original Customer Feedback**

from

**Underlying Customer Pain Point**

from

**Requested Solution**

This allows Product Managers to evaluate demand for the customer problem rather than simply counting feature requests.

---

## Key Features

### Product Area Configuration

Product Managers can create, edit, and delete Product Areas that represent the functional taxonomy of their application.

Each Product Area contains:

- Name
- Description
- Core functionality

These PM-defined Product Areas are provided to the AI analysis process as context. The AI must classify feedback using the existing taxonomy rather than inventing new Product Areas.

### Customer Company Management

Customer companies can be created and maintained with optional Annual Recurring Revenue (ARR).

Company identity is preserved throughout the feedback-analysis workflow and is later used to calculate unique-company demand.

### Feedback Ingestion

Feedback can be captured through:

- Manual feedback entry
- CSV bulk upload

Supported metadata includes:

- Company
- Feedback text
- Source
- Feedback date
- Contact
- ARR context

CSV ingestion validates required fields and reports row-level failures without preventing valid records from being imported.

### AI Feedback Analysis

Customer feedback is analyzed using the OpenAI API.

For each feedback record, the system identifies:

1. The most appropriate PM-defined Product Area
2. The underlying customer pain point
3. The requested solution, when one is explicitly present

The AI is instructed to use solution-neutral language for pain points and to return no requested solution when the customer has not actually proposed one.

Original customer feedback is preserved unchanged.

### Semantic Theme Matching

AI-generated pain points are compared against existing approved themes within the assigned Product Area.

The system attempts to determine whether differently worded customer feedback represents substantially the same underlying problem.

For the MVP, constrained LLM-based semantic matching is used because the expected theme taxonomy is relatively small. A production implementation with a substantially larger taxonomy could introduce embedding-based retrieval or vector search as a scalability enhancement.

### AI-Proposed Themes

When a pain point does not appropriately match an existing approved theme, the AI proposes a new solution-neutral pain-point theme.

New AI-generated themes begin with a **Proposed** status.

The AI cannot autonomously add a proposed theme to the approved product taxonomy.

### Human-in-the-Loop Theme Governance

Product Managers review AI-proposed themes and can:

- Review supporting customer feedback
- Edit the proposed theme name
- Edit the theme description
- Approve the theme
- Reject the theme

Only **Approved** themes are eligible for future semantic matching.

This design preserves human oversight of the product taxonomy while using AI to reduce the manual effort required to organize large volumes of customer feedback.

---

## Demand Intelligence

Customer Feedback Intelligence intentionally separates **feedback volume** from **customer demand**.

A highly vocal customer may submit many feedback records about the same problem. Counting every record as a separate demand signal would allow one customer to disproportionately influence prioritization.

The system therefore uses the rule:

> **One company = one demand vote per theme**

### Demand Rate

Demand Rate is calculated as:

```text
Unique companies associated with theme
--------------------------------------- × 100
Unique companies represented in feedback
```

### Demand Classification

| Demand Rate | Classification |
|---|---|
| Less than 10% | Low |
| 10% to less than 25% | Medium |
| 25% or greater | High |

### ARR Context

The application also calculates the total ARR represented by the unique companies associated with a theme.

ARR is counted only once per company per theme.

**ARR does not influence the demand classification.**

It is provided as additional commercial context for the Product Manager.

---

## Product Insights Dashboard

The Product Insights Dashboard provides an overview of customer-feedback intelligence.

It includes:

### Feedback Overview

- Total feedback records
- Total companies represented

### Feedback by Product Area

For each Product Area:

- Feedback volume
- Unique companies represented

Feedback that has not yet been AI-classified is displayed as **Unclassified**.

### Customer Pain-Point Demand

Approved themes are displayed with:

- Product Area
- Unique-company demand
- Feedback volume
- Demand rate
- Demand classification
- ARR represented

Themes are ranked by unique-company demand.

### Theme Detail

Product Managers can drill into a theme to review the customer evidence supporting the calculated demand signal.

The detail view includes:

- Original customer feedback
- Company
- Source
- Date
- Contact
- AI-identified pain point
- Requested solution
- Theme-level demand metrics

This allows Product Managers to understand why a demand signal exists rather than relying on an opaque AI-generated score.

---

## Technology Stack

### Application

- Python 3.11
- Flask
- Jinja2
- Gunicorn

### Data

- Supabase
- PostgreSQL
- PostgREST

### AI

- OpenAI API
- Structured feedback analysis
- Constrained semantic theme matching
- AI-assisted theme generation

### Data Processing

- pandas

### Testing

- pytest
- Flask test client
- Mocked external dependencies where appropriate

### CI/CD and Hosting

- GitHub
- GitHub Actions
- Render

### Agile Project Management

- Jira
- Scrum
- Three development sprints

---

## System Architecture

At a high level:

```text
                        ┌──────────────────────┐
                        │      Web Browser     │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │    Flask / Render    │
                        │   Web Application    │
                        └───────┬──────┬───────┘
                                │      │
                    ┌───────────┘      └───────────┐
                    ▼                              ▼
        ┌──────────────────────┐       ┌──────────────────────┐
        │ Supabase/PostgreSQL  │       │      OpenAI API      │
        │                      │       │                      │
        │ Companies            │       │ Product Area        │
        │ Product Areas        │       │ Classification      │
        │ Feedback             │       │                      │
        │ Themes               │       │ Pain-Point          │
        │ Feedback-Themes      │       │ Extraction          │
        └──────────────────────┘       │                      │
                                       │ Theme Matching       │
                                       │ & Proposal           │
                                       └──────────────────────┘
```

The application layer coordinates persistence, AI analysis, Product Manager workflows, and deterministic demand calculations.

---

## Data Model

The primary relational entities are:

### `companies`

Stores customer identity and optional ARR.

### `product_areas`

Stores the Product Manager-defined application taxonomy used by the AI classification process.

### `feedback`

Stores original customer feedback and AI-generated analysis.

Key fields include:

- Company relationship
- Original feedback text
- Source
- Feedback date
- Contact
- Product Area relationship
- AI pain point
- Requested solution

### `themes`

Stores pain-point themes.

Themes are associated with a Product Area and have one of three governance states:

- Proposed
- Approved
- Rejected

### `feedback_themes`

Junction table connecting feedback records to pain-point themes.

This relationship supports theme-level demand calculations while preserving individual customer evidence.

---

## AI Design

The AI layer is separated from the Flask application through `ai_service.py`.

The service supports three primary operations:

### `analyze_feedback()`

Transforms raw feedback into:

- Product Area
- Underlying pain point
- Requested solution

### `match_theme()`

Determines whether an AI-generated pain point represents substantially the same underlying problem as an existing approved theme.

### `propose_theme()`

Generates a solution-neutral proposed theme when no appropriate approved theme exists.

External AI calls are not used directly in automated CI tests. AI behavior is mocked where appropriate so the test suite remains:

- Deterministic
- Fast
- Cost-controlled
- Independent of third-party API availability

---

## Demand Calculation Design

Demand calculations are implemented separately from the AI layer in `demand_service.py`.

This separation is intentional.

AI is used for semantic interpretation.

Deterministic Python logic is used for quantitative demand calculations.

The demand service is responsible for:

- Deduplicating companies
- Counting feedback volume
- Calculating unique-company demand
- Calculating demand rate
- Assigning demand classifications
- Calculating represented ARR

This prevents probabilistic AI behavior from influencing deterministic product-demand metrics.

---

## Testing

The project currently includes **19 automated tests**.

Coverage includes:

- Core Flask routes
- Product Area pages
- Company pages
- Feedback pages
- Required-field validation
- Duplicate-company protection
- AI structured-response handling
- Null requested-solution behavior
- Theme review pages
- Theme approval
- Theme rejection
- Theme editing
- Demand-classification thresholds
- One-company-one-vote deduplication
- ARR deduplication
- Missing ARR behavior
- Empty-theme behavior
- Dashboard routing and content

The test suite can be run with:

```bash
pytest
```

External dependencies are mocked where appropriate.

---

## Continuous Integration

GitHub Actions runs the automated test suite on pushes and pull requests to the `main` branch.

The CI workflow:

1. Checks out the repository
2. Configures Python
3. Installs dependencies
4. Loads required non-AI test environment configuration securely
5. Runs the pytest suite

The application is deployed from the `main` branch to Render.

---

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/ldweaver27/customer-feedback-intelligence.git
cd customer-feedback-intelligence
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file:

```text
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_api_key
```

API credentials must never be committed to source control.

### 5. Run the application

```bash
python app.py
```

The development application is available at:

```text
http://127.0.0.1:5000
```

### 6. Run automated tests

```bash
pytest
```

---

## Production Deployment

The application is deployed as a Python web service on Render using Gunicorn.

Production start command:

```bash
gunicorn app:app
```

Production credentials are configured through secure environment variables rather than committed configuration files.

**Live Application:**  
https://customer-feedback-intelligence-31uz.onrender.com

---

## Agile Development Process

The application was developed using Scrum practices with Jira used to manage:

- Epics
- User stories
- Acceptance criteria
- Technical tasks
- Sprint planning
- Completion status
- Product backlog

**Jira Board:**  
https://ldweaver27.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog

### Sprint 1 — Foundation & Feedback Ingestion

Established the application and data foundation.

Major outcomes:

- Flask application
- Supabase/PostgreSQL integration
- Product Area configuration
- Company management
- Manual feedback entry
- CSV feedback ingestion
- Validation and partial-failure handling
- Automated testing
- GitHub Actions CI

### Sprint 2 — AI Feedback Intelligence

Introduced AI-powered feedback interpretation and human-governed theme management.

Major outcomes:

- OpenAI integration
- Product Area classification
- Underlying pain-point extraction
- Requested-solution extraction
- Semantic theme matching
- AI-proposed themes
- PM theme editing
- Theme approval and rejection
- Expanded automated testing

### Sprint 3 — Demand Intelligence & Dashboard

Converted structured feedback into transparent product-demand signals.

Major outcomes:

- One-company-one-vote demand model
- Feedback-volume measurement
- Demand-rate calculation
- Low / Medium / High classification
- ARR context
- Product Area summary
- Product Insights Dashboard
- Theme-level evidence drill-down
- Expanded automated testing

### Post-MVP Production Hardening

After completion of the three planned development sprints:

- Deployed the application to Render
- Added production Gunicorn configuration
- Added shared navigation
- Improved application styling
- Performed production smoke testing
- Added graceful AI-service failure handling

---

## MVP Scope Decisions

The capstone intentionally prioritizes the core customer-feedback intelligence workflow.

The MVP demonstrates:

```text
Feedback
    ↓
AI Analysis
    ↓
Underlying Customer Problems
    ↓
Pain-Point Themes
    ↓
PM Governance
    ↓
Unique-Company Demand
    ↓
Product Insights
```

Several lower-priority enhancements remain in the product backlog rather than being added late in development.

Examples include:

- Common requested-solution aggregation by theme
- Trend analysis over time
- Additional dashboard filtering
- Direct integrations with external CRM/product-feedback systems
- Embedding/vector-based theme retrieval at larger scale
- Authentication and role-based access
- Advanced visualizations

These were deliberately deferred to protect MVP quality, testing, deployment, and final delivery.

---

## Security Considerations

Sensitive credentials are stored through environment variables.

The repository does not contain:

- OpenAI API keys
- Supabase credentials
- Production secrets

Local secrets are stored in `.env`, which is excluded from Git.

Production secrets are managed through Render environment configuration.

External AI-service errors are handled gracefully rather than exposing application tracebacks to end users.

---

## Project Status

**MVP: Complete**

- Three development sprints completed
- Production application deployed
- Automated test suite passing
- Continuous integration configured
- Core AI workflow operational
- Demand-intelligence workflow operational
- Product Manager dashboard operational

Current work is focused on final capstone documentation, testing evidence, and presentation preparation.
