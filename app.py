from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

users = []

@app.route("/dashboard")
def dashboard():
    return redirect(url_for("signin"))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signin", methods=["GET", "POST"])
def signin():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        

        for user in users:
            
            if user["email"] == email and user["password"] == password:
                return render_template("dashboard.html", name=user["name"])

        

        return "Invalid email or password!"

    return render_template("signin.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        for user in users:
            if user["email"] == email:
                return "Email already registered!"

        users.append({
            "name": name,
            "email": email,
            "password": password
        })

        print(users)

        return redirect(url_for("signin"))

    return render_template("signup.html")

   

if __name__ == "__main__":
    app.run(debug=True)