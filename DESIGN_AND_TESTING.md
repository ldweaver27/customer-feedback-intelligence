# Customer Feedback Intelligence

## Detailed Design and Testing Document

**Status:** MVP complete and deployed\
**Live application:**
https://customer-feedback-intelligence-31uz.onrender.com\
**Repository:**
https://github.com/ldweaver27/customer-feedback-intelligence\
**Agile board:**
https://ldweaver27.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog

------------------------------------------------------------------------

# 1. Executive Summary

Customer Feedback Intelligence is an AI-enabled web application that
transforms fragmented qualitative customer feedback into structured,
transparent product-demand intelligence.

The system separates original customer feedback, the underlying customer
pain point, and an explicitly requested solution. AI performs semantic
interpretation: Product Area classification, pain-point extraction,
requested-solution extraction, semantic theme matching, and
proposed-theme generation. Product Managers retain control of the
taxonomy by reviewing, editing, approving, or rejecting AI-proposed
themes.

Approved themes are converted into deterministic demand signals using
the rule **one company = one demand vote per theme**. The application
also calculates feedback volume, demand rate, Low/Medium/High
classification, and represented ARR. ARR is commercial context only and
does not affect demand classification.

# 2. Requirements and Scope

The MVP supports Product Area configuration; company and ARR management;
manual and CSV feedback ingestion; AI classification; pain-point and
requested-solution extraction; semantic theme matching; AI-proposed
themes; PM edit/approve/reject governance; unique-company demand;
feedback volume; demand rate and classification; represented ARR; a
Product Insights Dashboard; evidence drill-down; automated testing; CI;
and cloud deployment.

Deferred backlog items include requested-solution aggregation, trends
over time, advanced dashboard filtering, direct CRM/product-feedback
integrations, authentication, multi-tenancy, vector retrieval for large
taxonomies, and advanced observability. These were deliberately deferred
to protect MVP quality, testing, deployment, and final delivery.

# 3. System Architecture

``` text
                         +----------------------+
                         | Browser / PM         |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Render Web Service   |
                         | Flask + Jinja2       |
                         | Gunicorn             |
                         +----+-------------+---+
                              |             |
                              v             v
                 +-------------------+   +-------------------+
                 | Supabase          |   | OpenAI API        |
                 | PostgreSQL        |   | AI Interpretation |
                 | PostgREST         |   | and Matching      |
                 +-------------------+   +-------------------+

 Local Development -> GitHub -> GitHub Actions
                         |
                         +-------> Render deployment
```

A request enters Flask, which performs validation and workflow
orchestration. Relational data is persisted in Supabase. OpenAI is
invoked only for semantic interpretation. Quantitative demand metrics
are calculated with deterministic Python logic. Jinja2 renders the
result.

This separation is intentional: probabilistic AI interprets language;
deterministic code calculates business metrics.

# 4. Technology and Architecture Decisions

## Python and Flask

Python supports web development, data processing, testing, and AI
integration in one language. Flask was chosen because the MVP is a
focused server-rendered application. Its minimal framework overhead,
straightforward routing, Jinja2 integration, test client, and Gunicorn
deployment fit the project well. A heavier framework could provide
built-in authentication or ORM features, but those were outside MVP
scope.

## Jinja2

Server-rendered Jinja2 templates avoid unnecessary frontend complexity.
A shared `base.html` uses template inheritance to centralize navigation
and styling, reducing duplicated markup.

## Supabase / PostgreSQL

A relational database fits the domain because companies, feedback,
Product Areas, themes, and feedback-theme associations have explicit
relationships. Supabase provides managed PostgreSQL and PostgREST access
while reducing infrastructure administration.

## OpenAI API

OpenAI provides semantic interpretation for classification, pain-point
extraction, requested-solution extraction, theme matching, and
proposed-theme generation. AI-specific logic is isolated in
`ai_service.py`.

## pandas

pandas supports reliable CSV parsing and row-level ingestion validation.

## pytest and GitHub Actions

pytest provides automated verification, including Flask route tests and
deterministic business-rule tests. GitHub Actions runs the suite in a
clean environment, supplementing local testing.

## Render and Gunicorn

Render hosts the Flask application and integrates with GitHub. Gunicorn
is used as the production web server rather than Flask's development
server.

# 5. Software Patterns

The project uses a lightweight layered architecture:

-   `app.py`: routing, validation, orchestration, persistence,
    rendering.
-   `ai_service.py`: semantic AI operations.
-   `demand_service.py`: deterministic demand calculations.
-   `templates/`: presentation.
-   `tests/`: automated verification.

`ai_service.py` and `demand_service.py` act as service modules. The
`feedback_themes` junction table separates feedback and themes and
supports future many-to-many behavior.

The AI workflow follows a **human-in-the-loop pattern**. AI-proposed
themes begin as `Proposed`; PMs may edit, approve, or reject them. Only
`Approved` themes become future matching targets.

External AI failures follow a fail-safe pattern: controlled 503
responses are returned rather than exposing Flask tracebacks or
fabricating output.

# 6. Data Architecture

``` text
product_areas 1 ---- * feedback * ---- 1 companies
      |                    |
      |                    *
      |              feedback_themes
      |                    *
      |                    |
      +------ 1 ---- * themes
```

## `companies`

Stores company identity and optional ARR. Company ID is the
deduplication key for demand.

## `product_areas`

Stores PM-defined name, description, and core functionality. These
definitions are provided to AI during classification.

## `feedback`

Preserves original feedback, source, date, contact, company, Product
Area, AI pain point, and requested solution. Original feedback is never
overwritten.

## `themes`

Stores recurring pain-point themes and their Product Area. Governance
status is `Proposed`, `Approved`, or `Rejected`.

## `feedback_themes`

Associates evidence with themes and supports feedback-volume,
unique-company, and ARR calculations.

# 7. AI Architecture

``` text
Raw Feedback
     |
     v
analyze_feedback()
     |
     +--> Product Area
     +--> Pain Point
     +--> Requested Solution / null
     |
     v
Approved themes in Product Area
     |
     v
match_theme()
     |
  +--+----------------+
  |                   |
Match               No Match
  |                   |
  v                   v
Associate       propose_theme()
existing              |
theme                 v
                 Proposed Theme
                       |
                       v
                 PM Review
              Edit / Approve / Reject
```

`analyze_feedback()` is constrained to the PM-defined Product Areas and
instructed to use solution-neutral pain-point language. Requested
solutions are separated from underlying problems and may be null.

`match_theme()` compares a pain point only against Approved themes
within the assigned Product Area. It is instructed not to force a match
merely because two problems share a broad Product Area.

`propose_theme()` creates a concise solution-neutral proposal when no
Approved theme fits. AI cannot independently approve taxonomy changes.

The MVP uses constrained LLM matching rather than embeddings because the
theme taxonomy is small. This avoids vector infrastructure and embedding
persistence. At larger scale, embedding/vector retrieval would be a
reasonable candidate-retrieval layer before final semantic evaluation.

# 8. Demand Intelligence

The central rule is:

> **One company = one demand vote per theme.**

``` text
Demand Rate =
Unique companies associated with theme
--------------------------------------- x 100
Unique companies represented in feedback
```

Classification thresholds are:

  Demand Rate          Classification
  -------------------- ----------------
  \< 10%               Low
  \>= 10% and \< 25%   Medium
  \>= 25%              High

ARR is summed once per unique company per theme. ARR does not influence
classification; it is displayed separately as commercial context.

Demand logic lives in `demand_service.py`, not in the LLM. AI is
appropriate for semantic interpretation; counting, deduplication,
percentages, threshold classification, and ARR aggregation must be
repeatable and testable.

# 9. Security and Reliability

Local secrets are stored in `.env`, which is excluded from source
control. Production secrets are stored as Render environment variables.
Sensitive configuration includes `SUPABASE_URL`, `SUPABASE_KEY`, and
`OPENAI_API_KEY`.

The OpenAI client is initialized only when an AI operation is invoked.
This prevents module import from requiring an AI credential and improves
CI testability.

GitHub Push Protection also blocked a workflow change it identified as a
possible OpenAI secret exposure. The design was changed rather than
bypassing protection.

OpenAI failures are caught and returned as controlled
service-unavailable responses.

The current MVP does not include authentication or authorization. A
production multi-user implementation should add identity, role-based
authorization, stronger database access controls, audit logging, and
least-privilege credentials.

# 10. Deployment Options and Cost Implications

## Current Managed Cloud Deployment

The MVP uses Render for Flask/Gunicorn, Supabase for managed PostgreSQL,
OpenAI for inference, GitHub for source control, and GitHub Actions for
CI.

**Relative cost: Low for a small pilot, increasing with usage.**

This option minimizes operational overhead. Costs scale with application
capacity, database storage/usage, and AI request volume.

## Larger Managed Cloud Deployment

A larger implementation could use managed containers/application hosting
and managed PostgreSQL on a major cloud provider.

**Relative cost: Medium to High**, depending on availability,
autoscaling, private networking, backups, observability, compliance, and
support.

The benefit is stronger enterprise control and scalability; the tradeoff
is higher recurring cost and infrastructure complexity.

## On-Premises / Self-Hosted

Flask and PostgreSQL could run on organization-managed infrastructure.
OpenAI could remain external, or the organization could host a model
separately.

**Total operational cost can be High** even if direct cloud-service
spending is reduced, because the organization assumes responsibility for
servers, patching, backups, availability, security, monitoring,
staffing, and potentially AI compute.

## Recommendation

Managed cloud deployment is recommended for the MVP and an early pilot
because it minimizes operational burden. Enterprise deployment should be
reevaluated against security, compliance, data residency, availability,
and volume requirements.

# 11. Testing Strategy

Testing combined automated tests, Flask route tests, mocked
dependencies, manual AI evaluation, manual functional QA, CI testing,
and production smoke testing.

The focus was on high-risk behavior: validation, AI-output handling,
taxonomy governance, unique-company deduplication, demand thresholds,
ARR behavior, and core workflows.

# 12. Automated Testing

At MVP completion, the project had **19 passing automated tests**.

Automated coverage includes:

-   root-to-Dashboard routing;
-   Product Areas, Companies, Feedback, Themes, and Dashboard routes;
-   required-field validation;
-   duplicate-company rejection;
-   structured AI-result handling;
-   null requested-solution behavior;
-   theme approval;
-   theme rejection;
-   theme edit-page behavior;
-   demand-classification boundaries;
-   one-company-one-vote deduplication;
-   ARR deduplication;
-   missing-ARR behavior;
-   empty-theme behavior; and
-   dashboard demand content.

AI calls are mocked where appropriate so CI remains deterministic, fast,
cost-controlled, and independent of third-party availability.

## Demand Boundary Tests

The automated suite explicitly verifies:

-   0% -\> Low
-   9.9% -\> Low
-   10% -\> Medium
-   24.9% -\> Medium
-   25% -\> High
-   100% -\> High

A representative demand test uses three feedback records from two
companies and verifies that feedback volume is 3 while unique-company
demand is 2. It also verifies that ARR is counted once per company.

A missing-ARR company still contributes a demand vote; missing
commercial data does not remove the customer from demand calculations.

An empty theme returns zero feedback, zero companies, 0% demand, Low
classification, and zero represented ARR.

# 13. Manual AI Evaluation

Automated tests do not claim to measure semantic model quality.
Representative live AI cases were manually evaluated.

## Positive Extraction Case

Feedback requesting an API because analysts manually downloaded and
combined reports produced:

-   the correct Reporting & Data Access Product Area;
-   a solution-neutral pain point describing manual
    retrieval/consolidation effort; and
-   an API as the requested solution.

## Null-Solution Case

Feedback describing difficulty understanding changes between reporting
periods correctly returned no requested solution rather than inventing a
feature.

## Positive Theme Match

A pain point about manual retrieval and consolidation matched the
Approved theme **Difficulty accessing data for downstream workflows**.

## Negative Theme Match

A pain point about identifying differences across reporting periods
correctly did not match the data-access theme despite sharing the same
Product Area.

The system then proposed a new solution-neutral theme, which was
reviewed and approved through the PM governance workflow.

These checks demonstrated representative behavior; they are not
presented as a statistically comprehensive model benchmark.

# 14. Manual Functional QA

Manual QA covered:

-   Product Area create/edit/delete;
-   Company create/edit and duplicate handling;
-   manual feedback entry;
-   CSV upload with successful and failed rows;
-   AI analysis from the Feedback page;
-   persistence of AI results in PostgreSQL;
-   semantic theme association;
-   proposed-theme creation;
-   PM theme edit, approval, and rejection;
-   dashboard calculations;
-   theme evidence drill-down;
-   persistent navigation; and
-   Gunicorn execution.

A live database test associated three feedback records with one theme:
two from Acme and one from Cyberdyne. The UI correctly displayed:

-   Feedback Volume: 3
-   Unique Companies: 2
-   Demand Rate: 33.3%
-   Classification: High
-   ARR Represented: \$925,000

This directly validated the one-company-one-vote rule in persisted
application data.

# 15. Continuous Integration and Defects Found

GitHub Actions runs pytest in a clean Linux/Python environment.

CI identified an environment-specific defect after the AI service was
introduced. The OpenAI client was originally created at module import
time, causing CI test collection to fail when no OpenAI credential was
present. The client initialization was moved inside AI functions. This
allowed mocked tests to run without production AI credentials and
improved separation of concerns.

Other defects found during development and QA included:

-   an incorrect Supabase API URL path;
-   malformed Python indentation detected by `py_compile` and pytest;
-   duplicated HTML controls and malformed template structure;
-   incomplete Flask routes returning `None`;
-   missing Flask endpoints referenced by templates;
-   API-credit exhaustion producing an unhandled traceback;
-   and navigation gaps discovered during production smoke testing.

Each issue was corrected and regression-tested before the associated
work was considered complete.

# 16. Production Testing

After deployment to Render, production smoke testing verified:

-   the public Dashboard loads;
-   Supabase data is readable;
-   production database writes succeed;
-   Dashboard, Themes, Feedback, Companies, Product Areas, and detail
    pages render;
-   shared navigation works across major workflows;
-   demand metrics render from production data; and
-   Render successfully redeploys from the GitHub `main` branch.

The OpenAI workflow had already been validated through live API calls
during development. Production hardening added controlled OpenAI error
handling so external service failures do not expose application
tracebacks.

# 17. Testing Limitations

Current testing limitations include:

-   no browser automation/end-to-end framework;
-   no load or stress testing;
-   no formal penetration testing;
-   no statistical AI-quality benchmark;
-   no automated live OpenAI tests in CI;
-   no multi-user concurrency testing; and
-   no authentication/authorization tests because authentication is
    outside MVP scope.

These are appropriate future additions before enterprise production use.

# 18. Agile Delivery

Development was managed in Jira using Scrum with three primary
development sprints.

**Sprint 1 --- Foundation & Feedback Ingestion** - Flask/Supabase
foundation - Product Areas - Companies - manual feedback - CSV
ingestion - initial tests and CI

**Sprint 2 --- AI Feedback Intelligence** - OpenAI integration - Product
Area classification - pain-point and requested-solution extraction -
semantic theme matching - proposed themes - PM governance - expanded
testing

**Sprint 3 --- Demand Intelligence & Dashboard** - unique-company
demand - demand rate/classification - ARR context - Product Area
summary - Dashboard - theme evidence detail - expanded testing

Post-MVP work covered deployment, shared navigation, UI polish,
production smoke testing, and graceful AI-service failure handling.

Lower-priority enhancements remain in the backlog rather than being
marked complete.

# 19. Conclusion

Customer Feedback Intelligence demonstrates an end-to-end AI-assisted
product-feedback workflow while keeping quantitative prioritization
explainable and Product Manager governance explicit.

The architecture deliberately assigns different responsibilities to
different mechanisms:

-   AI interprets language.
-   Product Managers govern taxonomy.
-   PostgreSQL preserves structured evidence and relationships.
-   Deterministic Python calculates demand.
-   Automated and manual testing validate behavior.
-   GitHub Actions provides repeatable CI.
-   Managed cloud services provide a low-operations deployment path.

The resulting MVP is deployed, testable, traceable to original customer
evidence, and structured for future extension without requiring AI to
make opaque prioritization decisions.
