import requests
import sseclient
from datetime import datetime
import time
import os
import pytz  # make sure to pip install pytz

# Zeno metadata subscription URL
STREAM_URL = "https://api.zeno.fm/mounts/metadata/subscribe/gvefnvis2mzvv"

# Track current and history
last_song = None
song_history = []

# Absolute path to your 026.html
REPO_INDEX = os.path.join(os.path.dirname(__file__), "026.html")

def format_page(now_playing, history, timestamp):
    lines = []
    lines.append(f"<b>Now on Crystallite</b><br>{now_playing}")
    lines.append("<br><b>The last ten songs on Crystallite</b><br>")

    # pad history to 10 entries with "---"
    padded = history + ["---"] * (10 - len(history))
    padded = padded[:10]

    for song in padded:
        lines.append(f"{song}<div style='height:4px;'></div>")

    lines.append(f"<div id='update'>Updated: {timestamp}</div>")
    return "\n".join(lines)

def write_page(content):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Refresh" content="180">
<title>Crystallite - What's Playing Now</title>
<link rel="stylesheet" href="wpnpop.css" type="text/css" media="all">
</head>
<body>
<table width="300" border="0" align="center" cellpadding="5" cellspacing="4" bgcolor="#FFFFFF">
<tr>
<td bgcolor="#666666" align="center">
<img src="whatsplayingnow220.gif" width="220" height="40" alt="What's Playing Now">
</td>
</tr>
<tr>
<td>
<div id="titles">
{content}
</div>
</td>
</tr>
<tr>
<td bgcolor="#666666" align="center">
<a href="javascript:self.close()">
<img src="close100.gif" width="100" height="19" border="0" alt="Close">
</a>
</td>
</tr>
</table>
</body>
</html>
"""
    with open(REPO_INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {REPO_INDEX}")

def connect_and_stream():
    global last_song, song_history
    print("Connecting to Zeno event stream…")
    response = requests.get(STREAM_URL, stream=True, timeout=60)
    client = sseclient.SSEClient(response)

    for event in client.events():
        try:
            if event.event == "message":
                data = event.data
                if '"streamTitle":' in data:
                    start = data.find('"streamTitle":"') + len('"streamTitle":"')
                    end = data.find('"', start)
                    current_song = data[start:end]

                    if current_song != last_song:
                        # push old song into history if it exists
                        if last_song is not None:
                            song_history.insert(0, last_song)
                            song_history = song_history[:10]

                        last_song = current_song

                        # FIX: use Eastern time for timestamp
                        eastern = pytz.timezone("US/Eastern")
                        timestamp = datetime.now(eastern).strftime("%a %b %d %I:%M:%S %p EDT %Y")

                        content = format_page(current_song, song_history, timestamp)
                        write_page(content)

                        print(f"Updated page with: {current_song}")

        except Exception as e:
            print(f"Warning: skipped bad event -> {e}")
            continue

def main():
    while True:
        try:
            connect_and_stream()
        except Exception as e:
            print(f"Stream error: {e}")
            print("Reconnecting to Zeno event stream…")
            time.sleep(1)

if __name__ == "__main__":
    main()
