from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from groq import Groq
import sqlite3
import os
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

        weather = request.form["weather"]
        occasion = request.form["occasion"]

        connection = sqlite3.connect("outfitiq.db")
        cursor = connection.cursor()

        if weather == "Sunny":
            season = ("Summer", "All Seasons")
        elif weather == "Rainy":
            season = ("Rainy", "All Seasons")
        else:
            season = ("Winter", "All Seasons")

        # Find a top
        cursor.execute("""
        SELECT * FROM wardrobe
        WHERE category IN ('Shirt', 'T-Shirt')
        AND season IN (?, ?)
        ORDER BY RANDOM()
        LIMIT 1
        """, season)

        top = cursor.fetchone()

        # Find a bottom
        cursor.execute("""
        SELECT * FROM wardrobe
        WHERE category IN ('Jeans', 'Trousers')
        AND season IN (?, ?)
        ORDER BY RANDOM()
        LIMIT 1
        """, season)

        bottom = cursor.fetchone()

        connection.close()

        recommendation = {
            "top": top,
            "bottom": bottom
        }
    

        if top and bottom:
            prompt = f"""
            You are OutfitIQ, an AI fashion stylist.

            Use ONLY the information below.

            Top:
            - Category: {top[1]}
            - Color: {top[2]}
            - Season: {top[3]}

            Bottom:
            - Category: {bottom[1]}
            - Color: {bottom[2]}
            - Season: {bottom[3]}

            Weather: {weather}
            Occasion: {occasion}

            Rules:
            1. Do NOT change the weather.
            2. Do NOT change the occasion.
            3. Recommend ONLY these clothes.
            4. Explain in 2-3 sentences why they are suitable.
            """

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

            
    return render_template(
        "recommend.html",
        recommendation=recommendation,
        ai_response=ai_response
        )

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))

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