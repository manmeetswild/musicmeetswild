from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import re

app = Flask(__name__)

# --- THE FRONTEND (Internet Explorer Compatible) ---
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MEDIA STATION</title>
    <style>
        body { font-family: "Courier New", monospace; padding: 20px; background: #c0c0c0; color: #000; }
        .box { border: 2px solid #000; background: #d4d0c8; padding: 15px; width: 500px; box-shadow: 2px 2px 0px #000; margin: auto; }
        .title-bar { background: #000080; color: #fff; padding: 3px; font-weight: bold; margin: -15px -15px 15px -15px; }
        .result-item { margin-bottom: 15px; padding: 10px; border: 1px solid #808080; background: #fff; }
        #status { font-weight: bold; margin: 10px 0; color: #000080; height: 20px; }
        .menu-btn { width: 100%; padding: 15px; margin-bottom: 10px; font-weight: bold; cursor: pointer; font-family: "Courier New", monospace; }
        .nav-bar { margin-bottom: 15px; border-bottom: 1px solid #808080; padding-bottom: 5px; }
        button { cursor: pointer; padding: 5px; font-family: "Courier New", monospace; }
        #main-ui { display: none; }
    </style>
</head>
<body>
    <div class="box">
        <div class="title-bar"> MEDIA_STATION_V6_FINAL.EXE</div>
        
        <div id="home-menu">
            <p>SELECT STATION:</p>
            <button class="menu-btn" onclick="openStation('sc')">SOUNDCLOUD (MP3)</button>
            <button class="menu-btn" onclick="openStation('yt')">YOUTUBE (MP4 VIDEO)</button>
        </div>

        <div id="main-ui">
            <div class="nav-bar">
                <button onclick="goHome()"><< MENU</button>
                <span id="station-name" style="margin-left:20px; font-weight:bold;"></span>
            </div>
            <input type="text" id="q" style="width:70%;">
            <button type="button" onclick="search()">SEARCH</button>
            <div id="status">Status: Ready.</div>
            <div id="results"></div>
        </div>
    </div>

    <script type="text/javascript">
        var currentMode = 'sc';

        function openStation(mode) {
            currentMode = mode;
            document.getElementById('home-menu').style.display = 'none';
            document.getElementById('main-ui').style.display = 'block';
            document.getElementById('station-name').innerHTML = (mode == 'sc' ? 'SOUNDCLOUD' : 'YOUTUBE');
            document.getElementById('results').innerHTML = '';
            document.getElementById('status').innerHTML = 'Status: Ready.';
        }

        function goHome() {
            document.getElementById('home-menu').style.display = 'block';
            document.getElementById('main-ui').style.display = 'none';
        }

        function search() {
            var q = document.getElementById('q').value;
            var status = document.getElementById('status');
            var resDiv = document.getElementById('results');
            if(!q) return;

            status.innerHTML = "Status: Searching " + currentMode.toUpperCase() + "...";
            resDiv.innerHTML = "";

            var xhr = new XMLHttpRequest();
            var url = '/api/search?mode=' + currentMode + '&q=' + encodeURIComponent(q) + '&t=' + new Date().getTime();
            
            xhr.open('GET', url, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState == 4 && xhr.status == 200) {
                    var data = JSON.parse(xhr.responseText);
                    status.innerHTML = "Status: " + data.length + " results.";
                    for (var i = 0; i < data.length; i++) {
                        renderItem(data[i], resDiv);
                    }
                }
            };
            xhr.send();
        }

        function renderItem(item, container) {
            var itemDiv = document.createElement('div');
            itemDiv.className = 'result-item';
            
            var author = document.createElement('small');
            author.appendChild(document.createTextNode(item.author));
            itemDiv.appendChild(author);
            itemDiv.appendChild(document.createElement('br'));
            
            var title = document.createElement('b');
            title.appendChild(document.createTextNode(item.title));
            itemDiv.appendChild(title);
            itemDiv.appendChild(document.createElement('br'));
            itemDiv.appendChild(document.createElement('br'));
            
            var btn = document.createElement('button');
            btn.innerHTML = (currentMode == 'sc' ? "DOWNLOAD MP3" : "DOWNLOAD MP4");
            
            setupDownload(btn, item.url, item.author, item.title);
            
            itemDiv.appendChild(btn);
            container.appendChild(itemDiv);
        }

        function setupDownload(btn, url, author, title) {
            btn.onclick = function() {
                document.getElementById('status').innerHTML = "Status: DOWNLOADING...";
                var name = encodeURIComponent(author + " - " + title);
                window.location.href = '/api/download?mode=' + currentMode + '&url=' + encodeURIComponent(url) + '&name=' + name;
            };
        }
    </script>
</body>
</html>
"""

# --- THE BACKEND (Server Logic) ---

@app.route('/')
def index():
    return INDEX_HTML

@app.route('/api/search')
def search_api():
    query = request.args.get('q')
    mode = request.args.get('mode', 'sc')
    search_prefix = "scsearch5:" if mode == "sc" else "ytsearch5:"
    
    ydl_opts = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"{search_prefix}{query}", download=False)
            entries = [{
                'title': e.get('title'), 
                'url': e.get('url'), 
                'author': e.get('uploader') or e.get('channel') or 'Unknown'
            } for e in info['entries']]
            return jsonify(entries)
        except Exception as e:
            return jsonify([])

@app.route('/api/download')
def download_api():
    url = request.args.get('url')
    mode = request.args.get('mode', 'sc')
    
    # Aggressive filename cleaning for IE/Windows stability
    raw_name = request.args.get('name', 'file')
    clean_name = re.sub(r'[^a-zA-Z0-9 \-]', '', raw_name).strip()
    
    temp_base = "dl_workfile"
    
    if mode == 'sc':
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_base,
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        }
        ext = "mp3"
        mimetype = "audio/mpeg"
    else:
        # 'best[ext=mp4]' avoids complex merges on small servers
        opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': temp_base + ".mp4",
            'noplaylist': True,
        }
        ext = "mp4"
        mimetype = "video/mp4"

    # Precise cleanup
    for f_ext in ["mp3", "mp4"]:
        path = f"{temp_base}.{f_ext}"
        if os.path.exists(path):
            try: os.remove(path)
            except: pass

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        
        actual_file = f"{temp_base}.{ext}"
        
        if not os.path.exists(actual_file):
            return "Server failed to produce file", 500
            
        return send_file(
            actual_file, 
            as_attachment=True, 
            download_name=f"{clean_name}.{ext}", 
            mimetype=mimetype
        )
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    # Required for Render/Cloud deployment
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
