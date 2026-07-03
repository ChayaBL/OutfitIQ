from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signin")
def signin():
    return render_template("signin.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        print(name)
        print(email)
        print(password)

        return redirect(url_for("signin"))

    return render_template("signup.html")

   

if __name__ == "__main__":
    app.run(debug=True)