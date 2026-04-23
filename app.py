from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import re

app = Flask(__name__)

# --- THE UI ---
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SC STATION</title>
    <style>
        body { font-family: monospace; padding: 20px; background: #c0c0c0; color: #000; }
        .box { border: 2px solid #000; background: #d4d0c8; padding: 15px; width: 500px; box-shadow: 2px 2px 0px #000; }
        .title-bar { background: #000080; color: #fff; padding: 3px; font-weight: bold; margin: -15px -15px 15px -15px; }
        .result-item { margin-bottom: 15px; padding: 10px; border: 1px solid #808080; background: #fff; }
        .artist { color: #555; font-size: 11px; text-transform: uppercase; }
        #status { font-weight: bold; margin: 10px 0; color: #000080; }
        button { cursor: pointer; font-family: monospace; padding: 5px; }
    </style>
</head>
<body>
    <div class="box">
        <div class="title-bar"> SC_STATION_V2.EXE</div>
        <input type="text" id="q" placeholder="Artist or Song..." style="width:70%;">
        <button onclick="search()">SEARCH</button>
        <div id="status">Status: Ready.</div>
        <div id="results"></div>
    </div>

    <script>
        function search() {
            const q = document.getElementById('q').value;
            const status = document.getElementById('status');
            const resDiv = document.getElementById('results');
            if(!q) return;
            status.innerText = "Status: Searching...";
            resDiv.innerHTML = "";

            fetch('/api/search?q=' + encodeURIComponent(q))
                .then(res => res.json())
                .then(data => {
                    status.innerText = "Status: Results loaded.";
                    data.forEach(item => {
                        const d = document.createElement('div');
                        d.className = 'result-item';
                        // Clean title for URL passing
                        const safeName = `${item.artist} - ${item.title}`;
                        d.innerHTML = `
                            <span class="artist">${item.artist}</span><br>
                            <b>${item.title}</b><br><br>
                            <button onclick="download('${item.url}', '${encodeURIComponent(safeName)}')">DOWNLOAD MP3</button>
                        `;
                        resDiv.appendChild(d);
                    });
                });
        }

        function download(url, fileName) {
            const status = document.getElementById('status');
            const resDiv = document.getElementById('results');
            resDiv.innerHTML = "";
            status.innerText = "Status: DOWNLOADING " + decodeURIComponent(fileName) + "...";
            
            // Pass the custom filename to the backend
            window.location.href = `/api/download?url=${encodeURIComponent(url)}&name=${fileName}`;
            
            setTimeout(() => { status.innerText = "Status: Ready."; }, 12000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return INDEX_HTML

@app.route('/api/search')
def search():
    query = request.args.get('q')
    ydl_opts = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"scsearch5:{query}", download=False)
        entries = [{
            'title': e.get('title'), 
            'url': e.get('url'),
            'artist': e.get('uploader', 'Unknown')
        } for e in info['entries']]
    return jsonify(entries)

@app.route('/api/download')
def download():
    sc_url = request.args.get('url')
    # Get the "Artist - Title" name from the browser
    custom_name = request.args.get('name', 'track')
    
    # Sanitize filename (remove characters that Windows/Linux hate)
    clean_name = re.sub(r'[\\/*?:"<>|]', "", custom_name)
    
    temp_file = "sc_download"
    if os.path.exists(f"{temp_file}.mp3"):
        try: os.remove(f"{temp_file}.mp3")
        except: pass

    dl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_file,
        'quiet': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    with yt_dlp.YoutubeDL(dl_opts) as ydl:
        ydl.download([sc_url])
    
    # Send file with the nice "Artist - Title.mp3" name
    return send_file(
        f"{temp_file}.mp3", 
        as_attachment=True, 
        download_name=f"{clean_name}.mp3"
    )

if __name__ == '__main__':
    # Render tells the app which port to use via the 'PORT' variable
    port = int(os.environ.get("PORT", 10000)) 
    app.run(host='0.0.0.0', port=port)
