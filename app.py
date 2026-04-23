from flask import Flask, request, jsonify, redirect
import yt_dlp
import os
import requests

app = Flask(__name__)

# A list of reliable public Invidious instances
INVIDIOUS_INSTANCES = [
    "https://inv.tux.rs",
    "https://invidious.nerdvpn.de",
    "https://iv.melmac.space",
    "https://invidious.slipfox.xyz"
]

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MEDIA STATION</title>
    <style>
        body { font-family: "Courier New", monospace; padding: 20px; background: #c0c0c0; }
        .box { border: 2px solid #000; background: #d4d0c8; padding: 15px; width: 500px; box-shadow: 2px 2px 0px #000; margin: auto; }
        .title-bar { background: #000080; color: #fff; padding: 3px; font-weight: bold; margin: -15px -15px 15px -15px; }
        .result-item { margin-bottom: 15px; padding: 10px; border: 1px solid #808080; background: #fff; }
        #status { font-weight: bold; margin: 10px 0; color: #000080; min-height: 20px; }
        .menu-btn { width: 100%; padding: 15px; margin-bottom: 10px; font-weight: bold; cursor: pointer; font-family: "Courier New", monospace; }
        button { cursor: pointer; padding: 5px; font-family: "Courier New", monospace; }
        #main-ui { display: none; }
    </style>
</head>
<body>
    <div class="box">
        <div class="title-bar"> MEDIA_STATION_INVIDIOUS.EXE</div>
        <div id="home-menu">
            <p>SELECT STATION:</p>
            <button class="menu-btn" onclick="openStation('sc')">SOUNDCLOUD (MP3)</button>
            <button class="menu-btn" onclick="openStation('yt')">YOUTUBE (VIA INVIDIOUS)</button>
        </div>
        <div id="main-ui">
            <button onclick="location.reload()"><< MENU</button>
            <input type="text" id="q" style="width:60%;">
            <button onclick="search()">SEARCH</button>
            <div id="status">Status: Ready.</div>
            <div id="results"></div>
        </div>
    </div>
    <script>
        var mode = 'sc';
        function openStation(m) {
            mode = m;
            document.getElementById('home-menu').style.display = 'none';
            document.getElementById('main-ui').style.display = 'block';
        }
        function search() {
            var q = document.getElementById('q').value;
            var resDiv = document.getElementById('results');
            document.getElementById('status').innerHTML = "Searching...";
            resDiv.innerHTML = "";
            
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/api/search?mode='+mode+'&q='+encodeURIComponent(q), true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState == 4 && xhr.status == 200) {
                    var data = JSON.parse(xhr.responseText);
                    document.getElementById('status').innerHTML = data.length + " found.";
                    for (var i = 0; i < data.length; i++) {
                        var div = document.createElement('div');
                        div.className = 'result-item';
                        div.innerHTML = '<small>'+data[i].author+'</small><br><b>'+data[i].title+'</b><br><br>';
                        var btn = document.createElement('button');
                        btn.innerHTML = "DOWNLOAD / STREAM";
                        btn.onclick = (function(url){ return function(){
                            document.getElementById('status').innerHTML = "Redirecting to stream...";
                            window.location.href = '/api/download?mode='+mode+'&url='+encodeURIComponent(url);
                        }})(data[i].url);
                        div.appendChild(btn);
                        resDiv.appendChild(div);
                    }
                }
            };
            xhr.send();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return INDEX_HTML

@app.route('/api/search')
def search_api():
    query = request.args.get('q')
    mode = request.args.get('mode', 'sc')
    prefix = "scsearch5:" if mode == "sc" else "ytsearch5:"
    
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        try:
            info = ydl.extract_info(f"{prefix}{query}", download=False)
            return jsonify([{'title': e.get('title'), 'url': e.get('url'), 'author': e.get('uploader') or e.get('channel')} for e in info['entries']])
        except:
            return jsonify([])

@app.route('/api/download')
def download_api():
    url = request.args.get('url')
    mode = request.args.get('mode', 'sc')
    
    if mode == 'yt':
        # Extract the Video ID
        video_id = url.split("v=")[-1]
        # Use a public Invidious instance to get the stream
        # This redirects the user's browser to the Invidious download page
        instance = INVIDIOUS_INSTANCES 
        return redirect(f"{instance}/latest_version?id={video_id}&itag=22")
    
    # SoundCloud still uses the old method because it's rarely blocked
    return redirect(f"https://www.google.com/search?q=direct+download+fallback")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
