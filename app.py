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
        button { cursor: pointer; padding: 5px; font-family: "Courier New", monospace; }
    </style>
</head>
<body>
    <div class="box">
        <div class="title-bar"> SC_STATION_V5_FINAL.EXE</div>
        <input type="text" id="q" style="width:70%;">
        <button type="button" onclick="search()">SEARCH</button>
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
            var url = '/api/search?q=' + encodeURIComponent(q) + '&t=' + new Date().getTime();
            
            xhr.open('GET', url, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState == 4) {
                    if (xhr.status == 200) {
                        var data = JSON.parse(xhr.responseText);
                        status.innerHTML = "Status: " + data.length + " results.";
                        
                        for (var i = 0; i < data.length; i++) {
                            var item = data[i];
                            
                            // Create the container
                            var itemDiv = document.createElement('div');
                            itemDiv.className = 'result-item';
                            
                            // Create Artist Text
                            var artistSpan = document.createElement('small');
                            artistSpan.appendChild(document.createTextNode(item.artist));
                            itemDiv.appendChild(artistSpan);
                            itemDiv.appendChild(document.createElement('br'));
                            
                            // Create Title Text
                            var titleBold = document.createElement('b');
                            titleBold.appendChild(document.createTextNode(item.title));
                            itemDiv.appendChild(titleBold);
                            itemDiv.appendChild(document.createElement('br'));
                            itemDiv.appendChild(document.createElement('br'));
                            
                            // Create Button
                            var btn = document.createElement('button');
                            btn.innerHTML = "DOWNLOAD";
                            
                            // Attach event without strings
                            setupDownload(btn, item.url, item.artist, item.title);
                            
                            itemDiv.appendChild(btn);
                            resDiv.appendChild(itemDiv);
                        }
                    } else {
                        status.innerHTML = "Status: Error " + xhr.status;
                    }
                }
            };
            xhr.send();
        }

        // Separate function to avoid loop variable closure issues in IE
        function setupDownload(btn, url, artist, title) {
            btn.onclick = function() {
                var status = document.getElementById('status');
                status.innerHTML = "Status: DOWNLOADING...";
                var fileName = encodeURIComponent(artist + " - " + title);
                window.location.href = '/api/download?url=' + encodeURIComponent(url) + '&name=' + fileName;
            };
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
