from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return {"message": "Hello World from Flask and Render!"}

if __name__ == '__main__':
    app.run(debug=True)