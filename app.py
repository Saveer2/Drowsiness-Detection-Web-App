from flask import Flask, render_template, Response, jsonify
from drowsiness import generate_frames, get_status

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video")
def video():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/status")
def status():
    return jsonify(get_status())

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/detect")
def detect():
    return render_template("detect.html")

if __name__ == "__main__":
    app.run(debug=True)