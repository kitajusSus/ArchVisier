from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/ping")
def ping():
    return jsonify(message="pong")


if __name__ == "__main__":
    app.run(debug=True)
