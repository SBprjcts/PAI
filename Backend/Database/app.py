from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Flask!"

@app.route("/about")
def about():
    return "This is a simple Flask app."

if __name__ == "__main__":
    app.run(port=5000, debug=True)