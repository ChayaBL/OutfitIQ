from dotenv import load_dotenv
load_dotenv()
import traceback
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from groq import Groq
import sqlite3
import os
import re
import requests

print("GROQ KEY:", os.getenv("GROQ_API_KEY"))
app = Flask(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
app.secret_key = "outfitiq_secret_key"
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

users = []

@app.route("/wardrobe", methods=["GET", "POST"])
def wardrobe():

    if "name" not in session:
        return redirect(url_for("signin"))

    if request.method == "POST":

        category = request.form["category"]
        color = request.form["color"]
        season = request.form["season"]

        image = request.files["image"]

        filename = secure_filename(image.filename)

        image.save(
            os.path.join(app.config["UPLOAD_FOLDER"], filename)
        )

        connection = sqlite3.connect("outfitiq.db")
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO wardrobe(category, color, season, image)
            VALUES (?, ?, ?, ?)
            """,
            (category, color, season, filename)
        )

        connection.commit()
        connection.close()

        print(category)
        print(color)
        print(season)
        print(filename)

        return redirect(url_for("wardrobe"))

    connection = sqlite3.connect("outfitiq.db")
    cursor = connection.cursor()

    search = request.args.get("search", "")
    category = request.args.get("category", "")

    if search:
        cursor.execute(
            """
            SELECT * FROM wardrobe
            WHERE category LIKE ?
            OR color LIKE ?
            """,
            (f"%{search}%", f"%{search}%")
        )

    elif category:
        cursor.execute(
            """
            SELECT * FROM wardrobe
            WHERE category = ?
            """,
            (category,)
        )

    else:
        cursor.execute("SELECT * FROM wardrobe")

    clothes = cursor.fetchall()

    total_clothes = len(clothes)

    colors = len(set(cloth[2] for cloth in clothes))

    seasons = len(set(cloth[3] for cloth in clothes))

    connection.close()

    return render_template(
        "wardrobe.html",
        clothes=clothes,
        total_clothes=total_clothes,
        colors=colors,
        seasons=seasons
    )
@app.route("/delete/<int:id>")
def delete(id):

    connection = sqlite3.connect("outfitiq.db")
    cursor = connection.cursor()

    # Get image filename
    cursor.execute(
        "SELECT image FROM wardrobe WHERE id = ?",
        (id,)
    )

    image = cursor.fetchone()

    if image:
        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            image[0]
        )

        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete from database
    cursor.execute(
        "DELETE FROM wardrobe WHERE id = ?",
        (id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("wardrobe"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    connection = sqlite3.connect("outfitiq.db")
    cursor = connection.cursor()

    if request.method == "POST":

        category = request.form["category"]
        color = request.form["color"]
        season = request.form["season"]

        cursor.execute(
            """
            UPDATE wardrobe
            SET category = ?, color = ?, season = ?
            WHERE id = ?
            """,
            (category, color, season, id)
        )

        connection.commit()
        connection.close()

        return redirect(url_for("wardrobe"))

    cursor.execute(
        "SELECT * FROM wardrobe WHERE id = ?",
        (id,)
    )

    cloth = cursor.fetchone()

    connection.close()

    return render_template("edit.html", cloth=cloth)
@app.route("/dashboard")
def dashboard():

    if "name" not in session:
        return redirect(url_for("signin"))

    return render_template("dashboard.html", name=session["name"])

@app.route("/profile")
def profile():

    if "name" not in session:
        return redirect(url_for("signin"))

    connection = sqlite3.connect("outfitiq.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE name = ?",
        (session["name"],)
    )

    user = cursor.fetchone()

    connection.close()

    return render_template(
        "profile.html",
        user=user
    )

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if "name" not in session:
        return redirect(url_for("signin"))

    connection = sqlite3.connect("outfitiq.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE name = ?",
        (session["name"],)
    )

    user = cursor.fetchone()

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]

        cursor.execute(
            """
            UPDATE users
            SET name = ?, email = ?
            WHERE id = ?
            """,
            (name, email, user[0])
        )

        connection.commit()
        connection.close()

        session["name"] = name

        return redirect(url_for("profile"))

    connection.close()

    return render_template(
        "edit_profile.html",
        user=user
    )

@app.route("/recommend", methods=["GET", "POST"])
def recommend():

    if "name" not in session:
        return redirect(url_for("signin"))

    recommendation = None
    ai_response = ""

    if request.method == "POST":

        city = request.form["city"]
        occasion = request.form["occasion"]

        weather_data = get_weather(city)

        if weather_data:
            weather = weather_data["weather"]
            temperature = weather_data["temperature"]
        else:
            weather = "Unknown"
            temperature = "Unknown"

        connection = sqlite3.connect("outfitiq.db")
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM wardrobe")
        clothes = cursor.fetchall()

        connection.close()

        wardrobe_text = ""

        for cloth in clothes:
            wardrobe_text += (
                f"ID: {cloth[0]}, "
                f"Category: {cloth[1]}, "
                f"Color: {cloth[2]}, "
                f"Season: {cloth[3]}\n"
            )

        prompt = f"""
You are OutfitIQ, an AI fashion stylist.

Here is the user's wardrobe:

{wardrobe_text}

City: {city}
Weather: {weather}
Temperature: {temperature}°C
Occasion: {occasion}

Your task:

The user's occasion is: {occasion}

You MUST choose clothes that are appropriate for THIS occasion only.

Do NOT change the occasion.
Do NOT assume another occasion.
If the occasion is Casual, recommend only casual clothes.
If the occasion is College, recommend only college-appropriate clothes.
If the occasion is Party, recommend only party-appropriate clothes.
If the occasion is Office, recommend only office-appropriate clothes.

Use ONLY the clothes listed in the wardrobe.

Return in this exact format:

Top ID: <number>
Bottom ID: <number>

Explanation:
Write 2-3 sentences explaining why you chose this outfit.

IMPORTANT:
- Do NOT mention any clothing IDs in the explanation.
- Mention only the clothing names/colors.
"""

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            ai_response = response.choices[0].message.content
            print(ai_response)

            top_match = re.search(r"Top ID:\s*(\d+)", ai_response)
            bottom_match = re.search(r"Bottom ID:\s*(\d+)", ai_response)

            if top_match and bottom_match:

                top_id = int(top_match.group(1))
                bottom_id = int(bottom_match.group(1))

                connection = sqlite3.connect("outfitiq.db")
                cursor = connection.cursor()

                cursor.execute(
                    "SELECT * FROM wardrobe WHERE id = ?",
                    (top_id,)
                )
                top = cursor.fetchone()

                cursor.execute(
                    "SELECT * FROM wardrobe WHERE id = ?",
                    (bottom_id,)
                )
                bottom = cursor.fetchone()

                connection.close()

                recommendation = {
                    "top": top,
                    "bottom": bottom
                }

            ai_response = re.sub(
                r"Top ID:\s*\d+\s*Bottom ID:\s*\d+",
                "",
                ai_response,
                flags=re.IGNORECASE
            ).strip()

        except Exception as e:
            import traceback
            traceback.print_exc()
            ai_response = str(e)

    return render_template(
    "recommend.html",
    recommendation=recommendation,
    ai_response=ai_response,
    city=city if request.method == "POST" else "",
    occasion=occasion if request.method == "POST" else ""
)

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))

def get_weather(city):

    api_key = os.getenv("WEATHER_API_KEY")

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&units=metric"
    )

    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        return {
            "city": data["name"],
            "weather": data["weather"][0]["main"],
            "temperature": data["main"]["temp"]
        }

    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signin", methods=["GET", "POST"])
def signin():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("outfitiq.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        )

        user = cursor.fetchone()

        connection.close()

        if user:
            session["name"] = user[1]
            return redirect(url_for("dashboard"))
        return "Invalid email or password!"

    return render_template("signin.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        connection = sqlite3.connect("outfitiq.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            connection.close()
            return "Email already registered!"

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )

        connection.commit()
        connection.close()

        

        return redirect(url_for("signin"))

    return render_template("signup.html")

   

if __name__ == "__main__":
    app.run(debug=True)