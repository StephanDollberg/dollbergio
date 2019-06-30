from flask import Flask, request, send_from_directory, Response, render_template
import subprocess
import hashlib
import os

app = Flask(__name__, static_url_path='')

def render(text, hash):
    if os.path.exists(os.path.join('memes', hash)):
        return

    subprocess.check_call(['convert', 'memes/raw.jpg', '-font', 'Impact',
        '-fill', 'white', '-stroke', 'black', '-strokewidth', '2',
        '-background', 'none', '-gravity', 'south', '-pointsize', '120', '-size', '788x',
        'caption:'+text, '-composite', os.path.join('memes', hash)],
        timeout=1)

@app.route('/memes/<path:path>')
def send_memes(path):
    return send_from_directory('memes', path)

@app.route("/post", methods=['POST'])
def post():

    if 'text' not in request.form:
        return "Oooh no meme"

    text = request.form['text']
    text = text[:100]

    if text == '':
        return '', 400

    hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    filename = hash + ".jpg"

    render(text, filename)

    return hash

@app.route("/robots.txt")
def robots():
    txt = '''User-agent: *
Disallow: /
'''

    return Response(txt, mimetype="text/plain")

@app.route("/")
def home():
    return root('')
    
@app.route("/v/<path:path>")
def root(path):
    img = path if path != '' else 'raw'

    return render_template('base.html', imghash=img)
