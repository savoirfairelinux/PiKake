#!flask/bin/python
from flask import Flask
from flask import render_template
from flask import request
import json

app = Flask(__name__)

with open('config.json', 'rb') as fp:
    config = json.load(fp)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', config=config)

@app.route('/', methods=['POST'])
def post():
    config['tabs'] = request.form.getlist('option[]')
    save_config()
    return str(request.form)

def save_config():
    # Save the new config to file
    with open('config.json', 'wb') as fp:
        json.dump(config, fp)


if __name__ == '__main__':
    app.run(debug=True)
