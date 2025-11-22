from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

app= Flask(__name__)
app.config["SECRET_KEY"]= "changeme"

base_dir= os.path.abspath(os.path.dirname(__file__))
db_path= os.path.join(base_dir, "mealsmith.db")
app.config["SQLALCHEMY_DATABASE_URI"]= "sqlite:///"+ db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= False

db= SQLAlchemy(app)

class User(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    username= db.Column(db.String(80), unique=True, nullable=False)
    password_hash= db.Column(db.String(255), nullable=False)

class Ingredient(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(120), nullable=False)
    quantity= db.Column(db.String(64), nullable=True)
    unit= db.Column(db.String(64), nullable= True)
    expires_on= db.Column(db.Date, nullable=True)
    user_id= db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route("/pantry", methods=["GET", "POST"])
def pantry():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method== "POST":
        name= request.form.get("name", "").strip()
        quantity= request.form.get("quantity", "").strip()
        unit= request.form.get("unit", "").strip()
        expires_raw= request.form.get("expires_on", "").strip()
        expires_on= None
        if expires_raw:
            try:
                expires_on= datetime.strptime(expires_raw, "%Y-%m-%d").date()
            except ValueError:
                expires_on= None
        if name:
            item= Ingredient(name=name, quantity=quantity, unit=unit, expires_on= expires_on, user_id= session["user_id"])
            db.session.add(item)
            db.session.commit()
        return redirect(url_for("pantry"))
    items= Ingredient.query.filter_by(user_id=session["user_id"]).order_by(Ingredient.expires_on.is_(None), Ingredient.expires_on).all()
    return render_template("pantry.html", items=items)

@app.route("/pantry/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    item= Ingredient.query.get_or_404(item_id)
    if item.user_id!= session["user_id"]:
        return redirect(url_for("pantry"))
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("pantry"))

@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))
    error= ""
    if request.method== "POST":
        username= request.form.get("username", "").strip()
        password= request.form.get("password", "").strip()
        user= User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"]= user.id
            return redirect(url_for("home"))
        error= "Invalid username or password"
    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))
    error= ""
    if request.method== "POST":
        username= request.form.get("username", "").strip()
        password= request.form.get("password", "").strip()
        if not username or not password:
            error= "Username and password are required"
        else:
            existing= User.query.filter_by(username=username).first()
            if existing:
                error= "Username already taken"
            else:
                user= User(username=username, password_hash= generate_password_hash(password))
                db.session.add(user)
                db.session.commit()
                session["user_id"]= user.id
                return redirect(url_for("home"))
    return render_template("register.html", error=error)

@app.route("/recipes", methods=["GET", "POST"])
def recipes():
    if "user_id" not in session:
        return redirect(url_for("login"))
    items= Ingredient.query.filter_by(user_id=session["user_id"]).order_by(Ingredient.expires_on.is_(None), Ingredient.expires_on).all()
    recipe= None
    if request.method== "POST":
        notes= request.form.get("notes", "").strip()
        recipe= generate_recipe(items, notes)
    return render_template("recipes.html", items=items, recipe=recipe)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

def generate_recipe(items, notes):
    names=[i.name for i in items if i.name]
    base_title= "Pantry Recipe"
    if names:
        main= names[0]
        base_title= f"Easy {main} skillet"
    ingredients= []
    for i in items[:8]:
        line= i.name
        if i.quantity: 
            line+= f" {i.quantity}"
        if i.unit:
            line+= f" {i.unit}"
        ingredients.append(line)
    if not ingredients:
        ingredients= ["Pick any 3 ingredients you have on hand"]
    steps= []
    if notes:
        steps.append(f"Keep in mind: {notes}")
    steps.extend([
        "Gather all listed ingredients and preheat your pan or oven if needed.",
        "Prep ingredients: chop vegetables, trim proteins, and measure seasonings.",
        "Cook your main ingredient first, then add supporting ingredients in layers.",
        "Taste as you go and adjust salt, pepper, and spices.",
        "Plate the dish, add any fresh toppings, and serve warm."
    ])
    return {
        "title": base_title,
        "description": "A quick idea built from what you already have in your pantry.",
        "ingredients": ingredients,
        "steps": steps}

if __name__=="__main__":
    app.run(debug=True)