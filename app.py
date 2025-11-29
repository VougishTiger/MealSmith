from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

app= Flask(__name__)
app.config["SECRET_KEY"]= os.getenv("SECRET_KEY","6d8c3ac4ff7f1ac9b9c45e174a2fb0d65f298c0e33a7e587cdb4e8c1748c9aab")

database_url= os.getenv("DATABASE_URL","")
if database_url:
    if database_url.startswith("postgres://"):
        database_url= database_url.replace("postgres://","postgresql://",1)
    app.config["SQLALCHEMY_DATABASE_URI"]= database_url
else:
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
    unit= db.Column(db.String(64), nullable=True)
    expires_on= db.Column(db.Date, nullable=True)
    user_id= db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class SavedRecipe(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String(200), nullable=False)
    description= db.Column(db.Text, nullable=True)
    ingredients_text= db.Column(db.Text, nullable=False)
    steps_text= db.Column(db.Text, nullable=False)
    user_id= db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

with app.app_context():
    db.create_all()

# ------------------------
#  STATIC RECIPE LIBRARY
# ------------------------

STATIC_RECIPES= [
    {
        "title":"Garlic Butter Chicken",
        "description":"Golden pan-seared chicken with garlic, herbs, and rich butter sauce.",
        "ingredients":[
            "2 chicken breasts",
            "4 tbsp butter",
            "4 garlic cloves minced",
            "Salt and pepper",
            "Italian seasoning"
        ],
        "steps":[
            "Season chicken with salt, pepper, Italian seasoning.",
            "Sear chicken in butter until golden.",
            "Add garlic and cook 1 minute.",
            "Spoon butter over chicken.",
            "Serve hot with pasta or rice."
        ]
    },
    {
        "title":"Creamy Tomato Pasta",
        "description":"Simple Italian-style pasta with a rich tomato cream sauce.",
        "ingredients":[
            "Pasta of choice",
            "1 cup tomato sauce",
            "1/2 cup heavy cream",
            "Parmesan",
            "Garlic"
        ],
        "steps":[
            "Cook pasta.",
            "Sauté garlic, add tomato sauce.",
            "Stir in cream.",
            "Add pasta and toss.",
            "Top with parmesan."
        ]
    },
    {
        "title":"Beef Stir Fry",
        "description":"Savory Asian-style stir fry with veggies and quick sauce.",
        "ingredients":[
            "1 lb sliced beef",
            "Soy sauce",
            "Brown sugar",
            "Garlic and ginger",
            "Mixed veggies"
        ],
        "steps":[
            "Mix soy, garlic, ginger, sugar.",
            "Sear beef on high heat.",
            "Add vegetables.",
            "Pour sauce and cook 3 minutes.",
            "Serve with rice."
        ]
    },
    {
        "title":"Classic Tacos",
        "description":"Mexican-style tacos with seasoned meat and fresh toppings.",
        "ingredients":[
            "Ground beef or chicken",
            "Taco seasoning",
            "Tortillas",
            "Lettuce",
            "Cheese"
        ],
        "steps":[
            "Cook ground beef with seasoning.",
            "Warm tortillas.",
            "Assemble tacos with toppings.",
            "Add salsa or sour cream.",
            "Serve immediately."
        ]
    },
    {
        "title":"Vegetable Fried Rice",
        "description":"Fast Chinese-style fried rice loaded with vegetables.",
        "ingredients":[
            "Cooked rice",
            "Eggs",
            "Mixed veggies",
            "Soy sauce",
            "Green onion"
        ],
        "steps":[
            "Scramble eggs, set aside.",
            "Stir fry veggies.",
            "Add rice and soy sauce.",
            "Mix eggs back in.",
            "Finish with green onions."
        ]
    }
]

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route("/pantry", methods=["GET","POST"])
def pantry():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method== "POST":
        name= request.form.get("name","").strip()
        quantity= request.form.get("quantity","").strip()
        unit= request.form.get("unit","").strip()
        expires_raw= request.form.get("expires_on","").strip()
        expires_on= None
        if expires_raw:
            try:
                expires_on= datetime.strptime(expires_raw,"%Y-%m-%d").date()
            except ValueError:
                expires_on= None
        if name:
            item= Ingredient(name=name, quantity=quantity, unit=unit, expires_on=expires_on, user_id=session["user_id"])
            db.session.add(item)
            db.session.commit()
        return redirect(url_for("pantry"))
    items= Ingredient.query.filter_by(user_id=session["user_id"]).order_by(Ingredient.expires_on.is_(None),Ingredient.expires_on).all()
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

@app.route("/login", methods=["GET","POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))
    error= ""
    if request.method== "POST":
        username= request.form.get("username","").strip()
        password= request.form.get("password","").strip()
        user= User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash,password):
            session["user_id"]= user.id
            return redirect(url_for("home"))
        error= "Invalid username or password"
    return render_template("login.html", error=error)

@app.route("/register", methods=["GET","POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))
    error= ""
    if request.method== "POST":
        username= request.form.get("username","").strip()
        password= request.form.get("password","").strip()
        if not username or not password:
            error= "Username and password are required"
        else:
            existing= User.query.filter_by(username=username).first()
            if existing:
                error= "Username already taken"
            else:
                user= User(username=username, password_hash=generate_password_hash(password))
                db.session.add(user)
                db.session.commit()
                session["user_id"]= user.id
                return redirect(url_for("home"))
    return render_template("register.html", error=error)

@app.route("/recipes", methods=["GET","POST"])
def recipes():
    if "user_id" not in session:
        return redirect(url_for("login"))
    items= Ingredient.query.filter_by(user_id=session["user_id"]).all()
    recipes_list= random.sample(STATIC_RECIPES, min(5,len(STATIC_RECIPES)))
    to_cook= SavedRecipe.query.filter_by(user_id=session["user_id"]).order_by(SavedRecipe.id.desc()).all()
    return render_template("recipes.html", items=items, recipes=recipes_list, to_cook=to_cook)

@app.route("/save_recipe", methods=["POST"])
def save_recipe():
    if "user_id" not in session:
        return redirect(url_for("login"))
    title= request.form.get("title","")
    description= request.form.get("description","")
    ingredients= request.form.get("ingredients","")
    steps= request.form.get("steps","")
    entry= SavedRecipe(
        title=title,
        description=description,
        ingredients_text=ingredients,
        steps_text=steps,
        user_id=session["user_id"]
    )
    db.session.add(entry)
    db.session.commit()
    return redirect(url_for("recipes"))

@app.route("/delete_saved_recipe/<int:item_id>", methods=["POST"])
def delete_saved_recipe(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    entry= SavedRecipe.query.get_or_404(item_id)
    if entry.user_id!= session["user_id"]:
        return redirect(url_for("recipes"))
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for("recipes"))

@app.route("/logout")
def logout():
    session.pop("user_id",None)
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(debug=True)