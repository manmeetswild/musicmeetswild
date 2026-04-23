from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import re

app = Flask(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SC STATION</title>
    <style>
        body { font-family: "Courier New", monospace; padding: 20px; background: #c0c0c0; }
        .box { border: 2px solid #000; background: #d4d0c8; padding: 15px; width: 480px; box-shadow: 2px 2px 0px #000; }
        .title-bar { background: #000080; color: #fff; padding: 3px; font-weight: bold; margin: -15px -15px 15px -15px; }
        .result-item { margin-bottom: 15px; padding: 10px; border: 1px solid #808080; background: #fff; }
        #status { font-weight: bold; margin: 10px 0; color: #000080; }
        button { cursor: pointer; }
    </style>
</head>
<body>
    <div class="box">
        <div class="title-bar"> SC_STATION_V3_IE.EXE</div>
        <input type="text" id="q" style="width:70%;">
        <button onclick="search()">SEARCH</button>
        <div id="status">Status: Ready.</div>
        <div id="results"></div>
    </div>
    <script type="text/javascript">
        function search() {
            var q = document.getElementById('q').value;
            var status = document.getElementById('status');
            var resDiv = document.getElementById('results');
            if(!q) return;
            status.innerHTML = "Status: Searching...";
            resDiv.innerHTML = "";
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/api/search?q=' + encodeURIComponent(q), true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState == 4 && xhr.status == 200) {
                    var data = JSON.parse(xhr.responseText);
                    status.innerHTML = "Status: " + data.length + " found.";
                    var html = "";
                    for (var i = 0; i < data.length; i++) {
                        var item = data[i];
                        var safeName = encodeURIComponent(item.artist + " - " + item.title);
                        html += '<div class="result-item"><small>'+item.artist+'</small><br><b>'+item.title+'</b><br><br>' +
                                '<button onclick="download(\''+item.url+'\', \''+safeName+'\')">DOWNLOAD</button></div>';
                    }
                    resDiv.innerHTML = html;
                }
            };
            xhr.send();
        }
        function download(url, n) {
            document.getElementById('status').innerHTML = "Status: DOWNLOADING...";
            window.location.href = '/api/download?url=' + encodeURIComponent(url) + '&name=' + n;
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
    ydl_opts = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"scsearch5:{query}", download=False)
        entries = [{'title': e.get('title'), 'url': e.get('url'), 'artist': e.get('uploader', 'Unknown')} for e in info['entries']]
    return jsonify(entries)

@app.route('/api/download')
def download_api():
    sc_url = request.args.get('url')
    name = re.sub(r'[\\/*?:"<>|]', "", request.args.get('name', 'track'))
    tmp = "sc_download"
    if os.path.exists(tmp+".mp3"): 
        try: os.remove(tmp+".mp3")
        except: pass
    opts = {
        'format': 'bestaudio/best', 'outtmpl': tmp,
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([sc_url])
    return send_file(tmp+".mp3", as_attachment=True, download_name=name+".mp3")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
