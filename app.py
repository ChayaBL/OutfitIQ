from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import sqlite3
import os
app = Flask(__name__)
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

    cursor.execute("SELECT * FROM wardrobe")

    clothes = cursor.fetchall()

    connection.close()

    return render_template(
        "wardrobe.html",
        clothes=clothes
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