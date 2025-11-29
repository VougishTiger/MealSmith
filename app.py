from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

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

class SavedRecipe(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String(200), nullable=False)
    description= db.Column(db.String(400), nullable=True)
    ingredients_text= db.Column(db.Text, nullable=True)
    steps_text= db.Column(db.Text, nullable=True)
    user_id= db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

STATIC_RECIPES= [
    {
        "title": "Garlic Butter Chicken with Rice",
        "description": "Pan-seared chicken in garlic butter sauce served over fluffy rice.",
        "ingredients": [
            "2 chicken breasts",
            "2 tbsp butter",
            "3 cloves garlic, minced",
            "1 cup cooked rice",
            "Salt and black pepper",
            "1 tbsp olive oil"
        ],
        "steps": [
            "Season the chicken with salt and pepper.",
            "Heat olive oil in a pan and sear chicken on both sides until golden and cooked through.",
            "Add butter and garlic to the pan and cook until fragrant.",
            "Spoon the garlic butter over the chicken.",
            "Serve sliced chicken over warm rice."
        ]
    },
    {
        "title": "Creamy Tomato Pasta",
        "description": "Simple Italian-style pasta in a creamy tomato sauce.",
        "ingredients": [
            "8 oz pasta",
            "1 cup tomato sauce",
            "1/2 cup heavy cream or milk",
            "2 cloves garlic, minced",
            "2 tbsp grated parmesan",
            "Salt, pepper, dried basil"
        ],
        "steps": [
            "Cook pasta according to package directions and drain.",
            "In a pan, sauté garlic briefly in a little oil.",
            "Add tomato sauce and simmer for a few minutes.",
            "Stir in cream and season with salt, pepper, and dried basil.",
            "Toss pasta with sauce and top with parmesan."
        ]
    },
    {
        "title": "Veggie Fried Rice",
        "description": "Quick Asian-inspired fried rice using mixed vegetables.",
        "ingredients": [
            "2 cups cooked rice, chilled",
            "1 cup mixed vegetables",
            "2 eggs, beaten",
            "2 tbsp soy sauce",
            "1 tbsp sesame oil",
            "2 green onions, sliced"
        ],
        "steps": [
            "Heat a pan and scramble the eggs, then set aside.",
            "Add a little oil and cook the mixed vegetables until tender.",
            "Add the rice and stir-fry until heated through.",
            "Stir in soy sauce and sesame oil.",
            "Add scrambled eggs back in and top with green onions."
        ]
    },
    {
        "title": "Mexican Bean and Cheese Quesadillas",
        "description": "Cheesy tortillas filled with seasoned beans and spices.",
        "ingredients": [
            "4 flour tortillas",
            "1 cup shredded cheese",
            "1 cup cooked beans",
            "1/2 tsp cumin",
            "1/2 tsp chili powder",
            "Salt and pepper"
        ],
        "steps": [
            "Mash beans lightly with cumin, chili powder, salt, and pepper.",
            "Spread bean mixture on half of each tortilla.",
            "Sprinkle cheese over beans and fold tortillas in half.",
            "Cook in a dry pan until golden and cheese is melted.",
            "Slice and serve with salsa or sour cream if you have it."
        ]
    },
    {
        "title": "Simple Teriyaki Stir-Fry",
        "description": "Quick Asian stir-fry with vegetables and your choice of protein.",
        "ingredients": [
            "2 cups mixed vegetables",
            "1 cup diced chicken or tofu",
            "3 tbsp teriyaki sauce",
            "1 tbsp oil",
            "1 cup cooked rice or noodles"
        ],
        "steps": [
            "Heat oil in a pan and cook chicken or tofu until browned.",
            "Add vegetables and stir-fry until crisp-tender.",
            "Pour in teriyaki sauce and toss to coat.",
            "Serve over warm rice or noodles."
        ]
    },
    {
        "title": "Chickpea Curry Bowl",
        "description": "Indian-inspired chickpea curry served over rice.",
        "ingredients": [
            "1 can chickpeas, drained",
            "1 cup tomato sauce",
            "1/2 cup coconut milk or cream",
            "1 small onion, chopped",
            "1 clove garlic, minced",
            "1 tsp curry powder",
            "1 cup cooked rice"
        ],
        "steps": [
            "Sauté onion and garlic in a little oil until soft.",
            "Add curry powder and stir for 30 seconds.",
            "Add chickpeas and tomato sauce and simmer for a few minutes.",
            "Stir in coconut milk or cream and simmer until slightly thickened.",
            "Serve over rice."
        ]
    },
    {
        "title": "Baked Salmon with Lemon and Herbs",
        "description": "Oven-baked salmon fillets with fresh lemon and herbs.",
        "ingredients": [
            "2 salmon fillets",
            "1 tbsp olive oil",
            "1 lemon, sliced",
            "Salt and pepper",
            "Dried or fresh herbs"
        ],
        "steps": [
            "Preheat oven to 400°F (200°C).",
            "Place salmon on a lined baking tray and drizzle with olive oil.",
            "Season with salt, pepper, and herbs.",
            "Top with lemon slices and bake for 12–15 minutes.",
            "Serve with a side of vegetables or rice."
        ]
    }
]

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

def build_recipes_with_pantry(items):
    if len(STATIC_RECIPES)>= 5:
        chosen= random.sample(STATIC_RECIPES, 5)
    else:
        chosen= STATIC_RECIPES

    lower_pantry= [i.name.lower() for i in items if i.name]

    result= []
    for r in chosen:
        have= []
        missing= []
        for ing in r["ingredients"]:
            ing_lower= ing.lower()
            matched= False
            for name in lower_pantry:
                if name and (name in ing_lower or ing_lower in name):
                    matched= True
                    break
            if matched:
                have.append(ing)
            else:
                missing.append(ing)
        result.append({
            "title": r["title"],
            "description": r.get("description",""),
            "ingredients": r["ingredients"],
            "steps": r["steps"],
            "have": have,
            "missing": missing
        })
    return result

@app.route("/recipes")
def recipes():
    if "user_id" not in session:
        return redirect(url_for("login"))
    items= Ingredient.query.filter_by(user_id=session["user_id"]).order_by(Ingredient.expires_on.is_(None), Ingredient.expires_on).all()
    recipes_list= build_recipes_with_pantry(items)
    to_cook= SavedRecipe.query.filter_by(user_id=session["user_id"]).order_by(SavedRecipe.id.desc()).all()
    return render_template("recipes.html", items=items, recipes=recipes_list, to_cook=to_cook)

@app.route("/save_recipe", methods=["POST"])
def save_recipe():
    if "user_id" not in session:
        return redirect(url_for("login"))
    title= request.form.get("title","").strip()
    description= request.form.get("description","").strip()
    ingredients_text= request.form.get("ingredients","").strip()
    steps_text= request.form.get("steps","").strip()
    if title:
        entry= SavedRecipe(title=title, description=description, ingredients_text=ingredients_text, steps_text=steps_text, user_id=session["user_id"])
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
    session.pop("user_id", None)
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(debug=True)