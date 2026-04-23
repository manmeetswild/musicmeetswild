from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import re

app = Flask(__name__)

# --- THE FRONTEND (Dark Theme, Mobile Scaled, IE Compatible) ---
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SC DOWNLOADER</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: "Courier New", monospace; 
            padding: 10px; 
            background: #121212; 
            color: #e0e0e0; 
        }
        .box { 
            border: 2px solid #333; 
            background: #1e1e1e; 
            padding: 15px; 
            max-width: 480px; 
            margin: auto; 
            box-shadow: 4px 4px 0px #000; 
        }
        .title-bar { 
            background: #ff5500; 
            color: #fff; 
            padding: 5px; 
            font-weight: bold; 
            margin: -15px -15px 15px -15px; 
            text-align: center;
        }
        .result-item { 
            margin-bottom: 15px; 
            padding: 10px; 
            border: 1px solid #444; 
            background: #252525; 
        }
        #status { 
            font-weight: bold; 
            margin: 10px 0; 
            color: #ff5500; 
            min-height: 20px; 
        }
        input[type="text"] { 
            width: 95%; 
            padding: 8px; 
            background: #333; 
            border: 1px solid #555; 
            color: #fff; 
            margin-bottom: 10px;
        }
        button { 
            cursor: pointer; 
            padding: 10px; 
            font-family: "Courier New", monospace; 
            background: #444; 
            color: #fff; 
            border: 1px solid #666; 
            width: 100%;
        }
        button:active { background: #ff5500; }
        small { color: #aaa; }
    </style>
</head>
<body>
    <div class="box">
        <div class="title-bar">SC DOWNLOADER</div>
        
        <input type="text" id="q" placeholder="Search SoundCloud...">
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
                if (xhr.readyState == 4 && xhr.status == 200) {
                    var data = JSON.parse(xhr.responseText);
                    status.innerHTML = "Status: " + data.length + " tracks.";
                    for (var i = 0; i < data.length; i++) {
                        renderTrack(data[i], resDiv);
                    }
                }
            };
            xhr.send();
        }

        function renderTrack(item, container) {
            var itemDiv = document.createElement('div');
            itemDiv.className = 'result-item';
            
            var artist = document.createElement('small');
            artist.appendChild(document.createTextNode(item.artist));
            itemDiv.appendChild(artist);
            itemDiv.appendChild(document.createElement('br'));
            
            var title = document.createElement('b');
            title.appendChild(document.createTextNode(item.title));
            itemDiv.appendChild(title);
            itemDiv.appendChild(document.createElement('br'));
            itemDiv.appendChild(document.createElement('br'));
            
            var btn = document.createElement('button');
            btn.innerHTML = "DOWNLOAD MP3";
            
            (function(u, a, t) {
                btn.onclick = function() {
                    document.getElementById('status').innerHTML = "Status: Processing...";
                    var name = encodeURIComponent(a + " - " + t);
                    window.location.href = '/api/download?url=' + encodeURIComponent(u) + '&name=' + name;
                };
            })(item.url, item.artist, item.title);
            
            itemDiv.appendChild(btn);
            container.appendChild(itemDiv);
        }
    </script>
</body>
</html>
"""

# --- THE BACKEND ---

@app.route('/')
def index():
    return INDEX_HTML

@app.route('/api/search')
def search_api():
    query = request.args.get('q')
    ydl_opts = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"scsearch5:{query}", download=False)
            entries = [{
                'title': e.get('title'), 
                'url': e.get('url'), 
                'artist': e.get('uploader', 'Unknown')
            } for e in info['entries']]
            return jsonify(entries)
        except:
            return jsonify([])

@app.route('/api/download')
def download_api():
    url = request.args.get('url')
    raw_name = request.args.get('name', 'track')
    clean_name = re.sub(r'[^a-zA-Z0-9 \-]', '', raw_name).strip()
    
    temp_file = "sc_temp"
    
    # Precise cleanup
    if os.path.exists(temp_file + ".mp3"):
        try: os.remove(temp_file + ".mp3")
        except: pass

    opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_file,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        
        return send_file(
            temp_file + ".mp3", 
            as_attachment=True, 
            download_name=f"{clean_name}.mp3", 
            mimetype="audio/mpeg"
        )
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
