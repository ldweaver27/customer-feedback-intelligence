from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <h1>Customer Feedback Intelligence</h1>
    <p>AI-powered customer feedback intelligence for Product Managers.</p>
    """


if __name__ == "__main__":
    app.run(debug=True)