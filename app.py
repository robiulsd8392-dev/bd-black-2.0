
import os
import secrets
import subprocess
from pathlib import Path
from flask import Flask, request, session, redirect, url_for, send_from_directory, render_template_string, jsonify
from werkzeug.utils import secure_filename

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / "uploads"
OUTPUTS = BASE / "outputs"
UPLOADS.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("BD_BLACK_SECRET", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

ALLOWED = {".mp4", ".mov", ".mkv", ".webm", ".avi"}

PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#050505">
<meta name="description" content="BD BLACK 2.0 video optimization studio">
<link rel="manifest" href="/manifest.json">
<title>BD BLACK 2.0</title>
<style>
:root{--green:#00ff88;--red:#ff304f;--bg:#050505;--panel:#101010}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:white;font-family:Arial,sans-serif}
header{text-align:center;padding:30px 16px;border-bottom:1px solid #242424}
.logo{font-size:clamp(30px,7vw,48px);font-weight:900;letter-spacing:2px}
.green{color:var(--green);text-shadow:0 0 12px #00ff8844}
.red{color:var(--red);text-shadow:0 0 12px #ff304f44}
.line{display:block;margin:9px auto;font-size:12px;font-weight:bold;letter-spacing:2px}
.subtitle{color:#aaa;margin-top:12px}
main{width:min(760px,94%);margin:24px auto}
.card{background:var(--panel);border:1px solid #292929;border-radius:20px;padding:22px;margin-bottom:20px;box-shadow:0 0 24px #00ff8808}
h2{margin-top:0;font-size:22px}
label{display:block;color:#ddd;margin:18px 0 8px}
input,select{width:100%;padding:14px;border-radius:11px;border:1px solid #393939;background:#191919;color:white;font-size:15px}
button,.btn{display:block;width:100%;padding:15px;border:0;border-radius:12px;font-size:15px;font-weight:800;cursor:pointer;text-align:center;text-decoration:none;margin-top:14px}
.primary{background:var(--green);color:#001b0e}
.danger{background:var(--red);color:white}
.secondary{background:#202020;color:var(--green);border:1px solid #00ff8855}
.status{padding:13px;border-radius:10px;background:#181818;line-height:1.6;overflow-wrap:anywhere}
.small{color:#aaa;font-size:13px;line-height:1.7}
nav{display:flex;gap:10px;position:sticky;bottom:0;background:#080808ed;padding:12px;border-top:1px solid #333}
nav a{flex:1;text-align:center;text-decoration:none;padding:10px 3px;font-size:12px;font-weight:bold}
footer{text-align:center;padding:22px;color:#777;font-size:12px}
.hidden{display:none}
a{color:var(--green)}
hr{border:0;border-top:1px solid #292929;margin:20px 0}
</style>
</head>
<body>
<header>
 <div class="logo"><span class="green">BD</span> <span class="red">BLACK</span> <span class="green">2.0</span></div>
 <span class="line green">VIDEO OPTIMIZATION STUDIO</span>
 <span class="line red">CREATE • OPTIMIZE • DOWNLOAD</span>
 <p class="subtitle">Your video. Your creativity. Your studio.</p>
</header>

<main>
{% if not user %}
<section class="card" id="login">
 <h2 class="green">WELCOME TO BD BLACK</h2>
 <span class="line red">SECURE ACCOUNT ACCESS</span>
 <p class="small">Sign in to access your video studio. Google sign-in becomes active after the owner configures Google OAuth credentials.</p>
 <a class="btn secondary" href="/login/google">CONTINUE WITH GOOGLE</a>
 <p class="small">Google sign-in is not configured yet. Do not enter your Google password into this website.</p>
</section>
{% else %}
<section class="card">
 <span class="line green">ACCOUNT CONNECTED</span>
 <p>{{ user }}</p>
 <a class="btn secondary" href="/logout">SIGN OUT</a>
</section>
{% endif %}

<section class="card" id="studio">
 <h2 class="green">VIDEO STUDIO</h2>
 <span class="line red">UPLOAD → OPTIMIZE → DOWNLOAD</span>
 {% if not user %}
 <p class="small">The studio preview is visible. Sign-in must be configured before restricting uploads to verified accounts.</p>
 {% endif %}
 <form action="/optimize" method="post" enctype="multipart/form-data">
  <label class="green">01 / UPLOAD VIDEO</label>
  <input type="file" name="video" accept="video/*" required>
  <label class="red">02 / OUTPUT RESOLUTION</label>
  <select name="resolution">
   <option value="original">Original resolution</option>
   <option value="720">720p HD</option>
   <option value="1080">1080p Full HD</option>
   <option value="1440">1440p / 2K</option>
   <option value="2160">2160p / 4K</option>
  </select>
  <label class="green">03 / FRAME RATE</label>
  <select name="fps">
   <option value="original">Keep original FPS</option>
   <option value="30">30 FPS</option>
   <option value="60">60 FPS</option>
  </select>
  <label class="red">04 / BRIGHTNESS</label>
  <select name="brightness">
   <option value="0">Normal</option>
   <option value="0.05">Slightly brighter</option>
   <option value="0.10">Bright</option>
   <option value="-0.05">Slightly darker</option>
  </select>
  <button class="primary" type="submit">UPLOAD &amp; OPTIMIZE VIDEO</button>
 </form>
 <p class="small">Output depends on the original video. Increasing resolution or FPS does not guarantee better quality or smoother motion.</p>
</section>

{% if message %}
<section class="card">
 <h2 class="red">PROCESSING STATUS</h2>
 <div class="status">{{ message }}</div>
 {% if download %}
 <a class="btn primary" href="{{ url_for('download_file', filename=download) }}">DOWNLOAD OPTIMIZED VIDEO</a>
 {% endif %}
</section>
{% endif %}

<section class="card" id="install">
 <h2 class="red">INSTALL THE APP</h2>
 <p class="small">When this site is published over HTTPS, supported browsers can install it on Android as an app.</p>
 <button class="secondary" id="installBtn" type="button">INSTALL BD BLACK 2.0</button>
 <p class="small" id="installMsg">Installation may not be available when using a local address.</p>
</section>

<section class="card">
 <span class="line green">BD BLACK 2.0</span>
 <span class="line red">BUILT FOR CREATORS</span>
 <p class="small">Keep your original files safe. Only upload videos you have permission to process.</p>
</section>
</main>

<nav>
<a class="green" href="#studio">STUDIO</a>
<a class="red" href="#studio">OPTIMIZE</a>
<a class="green" href="#install">INSTALL APP</a>
</nav>
<footer>BD BLACK 2.0 · VIDEO STUDIO</footer>

<script>
let installPrompt;
const installBtn=document.getElementById('installBtn');
const installMsg=document.getElementById('installMsg');
window.addEventListener('beforeinstallprompt',e=>{
 e.preventDefault();installPrompt=e;installBtn.disabled=false;
});
installBtn.addEventListener('click',async()=>{
 if(installPrompt){
  installPrompt.prompt();
  await installPrompt.userChoice;
  installPrompt=null;
 }else{
  installMsg.textContent='Open your browser menu and choose Add to Home screen, if available.';
 }
});
if('serviceWorker' in navigator && location.protocol==='https:'){
 navigator.serviceWorker.register('/sw.js').catch(()=>{});
}
</script>
</body>
</html>
"""

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.route("/")
def home():
    return render_template_string(PAGE, user=session.get("user"),
                                 message=request.args.get("message"),
                                 download=request.args.get("download"))

@app.route("/login/google")
def google_login():
    return ("Google Login is not configured. The site owner must set up "
            "Google OAuth credentials and a verified callback URL first.", 501)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/optimize", methods=["POST"])
def optimize():
    uploaded = request.files.get("video")
    if not uploaded or not uploaded.filename:
        return redirect(url_for("home", message="Please choose a video first."))

    original = secure_filename(uploaded.filename)
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED:
        return redirect(url_for("home", message="Unsupported file type. Use MP4, MOV, MKV, WEBM or AVI."))

    token = secrets.token_hex(8)
    source = UPLOADS / f"{token}{ext}"
    output = OUTPUTS / f"BD_BLACK_{token}.mp4"
    uploaded.save(source)

    resolution = request.form.get("resolution", "original")
    fps = request.form.get("fps", "original")
    brightness = request.form.get("brightness", "0")

    filters = []
    if resolution in {"720", "1080", "1440", "2160"}:
        height = int(resolution)
        filters.append(f"scale=-2:'min({height},ih)':flags=lanczos")
    if fps in {"30", "60"}:
        filters.append(f"fps={int(fps)}")
    try:
        b = float(brightness)
    except ValueError:
        b = 0.0
    b = max(-0.2, min(0.2, b))
    if b:
        filters.append(f"eq=brightness={b}")

    cmd = ["ffmpeg", "-y", "-i", str(source), "-map", "0:v:0",
           "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac",
           "-movflags", "+faststart"]
    if filters:
        cmd += ["-vf", ",".join(filters)]
    cmd.append(str(output))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        source.unlink(missing_ok=True)
        if result.returncode != 0 or not output.exists():
            output.unlink(missing_ok=True)
            return redirect(url_for("home", message="FFmpeg could not process this video. Check that FFmpeg is installed and the file is valid."))
        return redirect(url_for("home", message="Video optimized successfully!", download=output.name))
    except FileNotFoundError:
        source.unlink(missing_ok=True)
        return redirect(url_for("home", message="FFmpeg is not installed. Install it in Termux with: pkg install ffmpeg"))
    except subprocess.TimeoutExpired:
        source.unlink(missing_ok=True)
        output.unlink(missing_ok=True)
        return redirect(url_for("home", message="Processing took too long. Try a shorter or smaller video."))

@app.route("/download/<path:filename>")
def download_file(filename):
    safe = secure_filename(filename)
    if not safe or not (OUTPUTS / safe).is_file():
        return "File not found", 404
    return send_from_directory(OUTPUTS, safe, as_attachment=True)

@app.route("/manifest.json")
def manifest():
    return jsonify({
        "name": "BD BLACK 2.0",
        "short_name": "BD BLACK",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#050505",
        "theme_color": "#050505",
        "description": "Video optimization studio"
    })

@app.route("/sw.js")
def service_worker():
    response = app.response_class(
        "self.addEventListener('fetch',e=>{});",
        mimetype="application/javascript"
    )
    response.headers["Service-Worker-Allowed"] = "/"
    return response

if __name__ == "__main__":
    print("BD BLACK 2.0 running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
