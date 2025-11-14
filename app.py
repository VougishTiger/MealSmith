from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app= Flask(__name__)

base_dir= os.path.abspath(os.path.dirname(__file__))
db_path= os.path.join(base_dir, "mealsmith.dp")
app.config["SQLALCHEMY_DATABASE_URI"]= "sqlite:///"+ db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= False

db= SQLAlchemy(app)

class Ingredient(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(120), nullable=False)
    quantity= db.Column(db.String(64), nullable=True)
    unit= db.Column(db.String(64), nullable= True)
    expires_on= db.Column(db.Date, nullable=True)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return redirect(url_for("pantry"))

@app.route("/pantry", methods=["GET", "POST"])
def pantry():
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
            item= Ingredient(name=name, quantity=quantity, unit=unit, expires_on= expires_on)
            db.session.add(item)
            db.session.commit()
        return redirect(url_for("pantry"))
    items= Ingredient.query.order_by(Ingredient.expires_on.is_(None), Ingredient.expires_on).all()
    return render_template("pantry.html", items=items)

@app.route("/pantry/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    item= Ingredient.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("pantry"))

if __name__=="__main__":
    app.run(debug=True)