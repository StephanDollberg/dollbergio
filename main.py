from flask import Flask, request, send_from_directory, Response
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

    render(text, hash)

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
    img = path if path != '' else 'raw.jpg'

    # webscale inline Vanilla-JS

    return '''<html style="display: table;margin: auto;">
<body style="display: table-cell;vertical-align: middle;">

<img id="thememe" src="/memes/XXXXX" height="788px" width="788px">

<form action="#" >
    <br>
        <input id="text" type="text" name="text" value="" onkeypress="keypress(event)" />
        <button type="button" onclick="return submitform();">Meme it!</button> 
    </br>
</form> 

<script type="text/javascript">

function keypress(event)
{
    if(event.keyCode === 13){
        event.preventDefault();
        submitform();
    }

    return false;
}

function submitform()
{
    var text = document.getElementById('text').value;
    var r = new XMLHttpRequest();
    r.open("POST", "/post", true);
    r.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    r.onreadystatechange = function () {
        if (r.readyState != 4 || r.status != 200) {
            console.log("fail");
            return;
        }

        document.getElementById("thememe").src="/memes/"+r.responseText;
        window.history.pushState(null, null, "/v/" + r.responseText);
    };
    r.send("text="+text);

    return false;
}
</script>


</body>
</html>'''.replace('XXXXX', img)
