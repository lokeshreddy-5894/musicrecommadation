from flask import Flask, render_template_string, request, redirect, url_for, session
import pandas as pd
import random


# ---------------------------
# Load dataset
# ---------------------------
def load_songs(file_path="songs.csv"):
    try:
        df = pd.read_csv(file_path)
        if 'id' not in df.columns:
            df['id'] = range(1, len(df) + 1)
        # Normalize mood and language columns for consistent matching
        df['mood'] = df['mood'].str.capitalize()
        df['language'] = df['language'].str.capitalize()
        return df
    except Exception as e:
        print("Error loading dataset:", e)
        return None


# ---------------------------
# Recommendation function
# ---------------------------
def recommend_songs_no_repeat(df, selected_moods=None, language=None, n_per_mood=5):
    if df is None:
        return {}
    recommendations = {}
    used_ids = set()

    # Use selected_moods if provided, otherwise use all moods
    moods_to_recommend = [m.capitalize() for m in selected_moods] if selected_moods else df['mood'].dropna().unique()

    for mood in moods_to_recommend:
        filtered = df[df['mood'] == mood]

        if language:
            filtered = filtered[filtered['language'] == language.capitalize()]

        filtered = filtered[~filtered['id'].isin(used_ids)]

        if filtered.empty:
            recommendations[mood] = [{"title": f"No songs found for mood '{mood}' in language '{language}'.",
                                      "artist": "", "language": "", "mood": ""}]
        else:
            count = min(n_per_mood, len(filtered))
            selected = filtered.sample(count, replace=False)
            used_ids.update(selected['id'].tolist())
            recommendations[mood] = selected.to_dict('records')

    return recommendations


# ---------------------------
# Flask App
# ---------------------------
app = Flask(__name__)
app.secret_key = "mood_music_secret"
songs_df = load_songs()

# ---------- Landing Page ----------
LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>🎵 Mood Music Recommender</title>
<style>
body {
  font-family: Arial, sans-serif;
  margin:0; min-height:100vh; display:flex; justify-content:center; align-items:center; flex-direction:column;
  background: linear-gradient(45deg, #ff4e50, #fc913a, #f9d423, #eae374, #00f260, #0575e6);
  background-size: 600% 600%;
  animation: gradientBG 20s ease infinite;
  color:white; text-align:center; overflow:hidden;
}
@keyframes gradientBG { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
h1 { font-size:3em; margin-bottom:40px; text-shadow: 2px 2px 10px #000; animation: fadeIn 2s ease forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
button { padding: 15px 50px; font-size:1.5em; border-radius:50px; border:none; background-color:#9258ff; color:white; cursor:pointer; animation:bounce 2s infinite, fadeIn 2.5s ease forwards; transition:0.3s; }
button:hover { background-color:#a77bff; transform:scale(1.1); }
@keyframes bounce {0%,20%,50%,80%,100%{transform:translateY(0);}40%{transform:translateY(-15px);}60%{transform:translateY(-7px);}}
</style>
</head>
<body>
<h1>🎵 Mood Music Recommender</h1>
<form action="{{ url_for('select_mood') }}">
    <button type="submit">START</button>
</form>
</body>
</html>
"""

# ---------- Selection Page ----------
SELECT_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Select Mood & Language</title>
<style>
body {
    font-family: Arial, sans-serif;
    margin: 0;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    background: linear-gradient(45deg, #1a1a2e, #272744, #1a1a2e, #3b3b5c);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    color: #e4e4e4;
    text-align: center;
    overflow: hidden;
}
@keyframes gradientBG { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
.container { background-color: rgba(39, 39, 68, 0.8); backdrop-filter: blur(10px); padding: 40px; border-radius: 12px; max-width: 800px; box-shadow: 0 0 20px rgba(0,0,0,0.7); animation: fadeIn 1s ease forwards; opacity: 0; }
@keyframes fadeIn { to { opacity: 1; } }
h1 { color: #9258ff; margin-bottom: 20px; }
h3 { color: #ffcc70; }
button[type=submit] { padding: 10px 20px; border-radius: 25px; border: none; background-color: #9258ff; color: white; cursor: pointer; margin-top: 20px; font-size: 1em; transition: 0.3s; }
button[type=submit]:hover { background-color: #a77bff; transform: scale(1.05); }
.mood-buttons, .language-buttons { display: flex; justify-content: center; flex-wrap: wrap; margin: 20px 0; }
.option-btn {
    padding: 12px 24px;
    margin: 5px;
    border-radius: 25px;
    border: 2px solid #9258ff;
    background-color: transparent;
    color: #e4e4e4;
    cursor: pointer;
    transition: all 0.3s;
}
.option-btn.selected { background-color: #9258ff; color: white; transform: scale(1.1); animation: glow 1s infinite alternate; }
.option-btn:hover { background-color: #5a5a7c; transform: scale(1.05); }
@keyframes glow { from { box-shadow:0 0 10px #9258ff; } to { box-shadow:0 0 25px #a77bff; } }
</style>
</head>
<body>
<div class="container">
<h1>🎵 Select Mood & Language</h1>
<form method="post">
    <h3>Moods</h3>
    <div class="mood-buttons">
        <button type="button" class="option-btn" data-type="mood" data-value="Happy">Happy</button>
        <button type="button" class="option-btn" data-type="mood" data-value="Sad">Sad</button>
        <button type="button" class="option-btn" data-type="mood" data-value="Romantic">Romantic</button>
        <button type="button" class="option-btn" data-type="mood" data-value="Energetic">Energetic</button>
        <button type="button" class="option-btn" data-type="mood" data-value="Calm">Calm</button>
    </div>
    <input type="hidden" name="moods" id="selectedMoods">

    <h3>Language</h3>
    <div class="language-buttons">
        <button type="button" class="option-btn" data-type="language" data-value="Telugu">Telugu</button>
        <button type="button" class="option-btn" data-type="language" data-value="Hindi">Hindi</button>
        <button type="button" class="option-btn" data-type="language" data-value="English">English</button>
    </div>
    <input type="hidden" name="language" id="selectedLanguage">

    <br><br>
    <button type="submit">Get Recommendations</button>
</form>
</div>

<script>
const optionButtons = document.querySelectorAll('.option-btn');
const selectedMoods = document.getElementById('selectedMoods');
const selectedLanguage = document.getElementById('selectedLanguage');
optionButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const type = btn.dataset.type;
        const value = btn.dataset.value;
        if (type === "mood") {
            btn.classList.toggle('selected');
            const moods = Array.from(document.querySelectorAll('.option-btn[data-type="mood"].selected'))
                               .map(b => b.dataset.value);
            selectedMoods.value = moods.join(',');
        }
        if (type === "language") {
            document.querySelectorAll('.option-btn[data-type="language"]').forEach(b => b.classList.remove('selected'));
            if (selectedLanguage.value === value) { selectedLanguage.value = ""; }
            else { btn.classList.add('selected'); selectedLanguage.value = value; }
        }
    });
});
</script>
</body>
</html>
"""

# ---------- Recommendations Page ----------
RESULT_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Recommended Songs</title>
<style>
body {
    font-family: Arial, sans-serif;
    margin: 0;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    background: linear-gradient(135deg, #ff6a00, #ee0979, #00f260, #0575e6);
    background-size: 600% 600%;
    animation: gradientBG 15s ease infinite;
    color: #e4e4e4;
    text-align: center;
    overflow: hidden;
}
@keyframes gradientBG { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
.container { background-color: rgba(39, 39, 68, 0.8); backdrop-filter: blur(10px); padding: 40px; border-radius: 12px; max-width: 800px; box-shadow: 0 0 20px rgba(0,0,0,0.7); animation: fadeIn 1s ease forwards; opacity: 0; }
@keyframes fadeIn { to { opacity: 1; } }
h1 { color: #9258ff; margin-bottom: 20px; }
h3 { color: #ffcc70; margin-top: 20px; animation: fadeInUp 0.5s ease forwards; opacity: 0; }
ul { padding: 0; }
li { opacity: 0; transform: translateY(20px); list-style: none; margin: 5px; padding: 12px; background: rgba(59, 59, 92, 0.7); border-radius: 6px; display: flex; justify-content: space-between; align-items: center; animation: fadeInUp 0.5s forwards; animation-delay: calc(0.1s * var(--i)); }
@keyframes fadeInUp { to { opacity: 1; transform: translateY(0); } }
/* Now Playing bars */
.now-playing { display: flex; gap: 2px; height: 20px; width: 80px; }
.now-playing span { width: 5px; background: #00ffcc; display: inline-block; animation: bounce 1s infinite ease-in-out; }
.now-playing span:nth-child(2){animation-delay:0.2s;} span:nth-child(3){animation-delay:0.4s;} span:nth-child(4){animation-delay:0.6s;} span:nth-child(5){animation-delay:0.8s;}
@keyframes bounce { 0%,100%{height:4px;}50%{height:20px;} }
button { padding: 10px 20px; border-radius: 25px; border: none; background-color: #9258ff; color: white; cursor: pointer; margin-top: 20px; transition: 0.3s; animation: fadeIn 2s ease forwards; }
button:hover { background-color: #a77bff; transform: scale(1.05); }
</style>
</head>
<body>
<div class="container">
<h1>🎶 Recommended Songs</h1>
{% for mood, result in recommendations.items() %}
    <h3>{{ mood }}</h3>
    <ul>
    {% for row in result %}
        <li style="--i:{{ loop.index0 }}">
            <span><b>{{ row['title'] }}</b> by {{ row['artist'] }} <br> ({{ row['language'] }}, {{ row['mood'] }})</span>
            <div class="now-playing"><span></span><span></span><span></span><span></span><span></span></div>
        </li>
    {% endfor %}
    </ul>
{% endfor %}
<form action="{{ url_for('select_mood') }}">
    <button type="submit">Back</button>
</form>
</div>
</body>
</html>
"""


# --------------------------- Routes ---------------------------
@app.route("/", methods=["GET"])
def home():
    return render_template_string(LANDING_PAGE)


@app.route("/select", methods=["GET", "POST"])
def select_mood():
    if request.method == "POST":
        moods_str = request.form.get("moods", "")
        language = request.form.get("language")
        session['selected_moods'] = moods_str
        session['language'] = language
        return redirect(url_for('results'))
    return render_template_string(SELECT_PAGE)


@app.route("/results", methods=["GET"])
def results():
    moods_str = session.get('selected_moods', '')
    language = session.get('language', '')
    selected_moods = [m.strip() for m in moods_str.split(",")] if moods_str else None

    # Check if selected_moods is empty, if so, get all moods from the dataframe
    if not selected_moods and songs_df is not None:
        selected_moods = songs_df['mood'].dropna().unique().tolist()

    recs = recommend_songs_no_repeat(songs_df,
                                     selected_moods,
                                     language if language else None)

    return render_template_string(RESULT_PAGE, recommendations=recs)


# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)