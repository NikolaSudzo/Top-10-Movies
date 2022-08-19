from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests
import os

MOVIE_DATABASE_ENDPOINT = "https://api.themoviedb.org/3/search/movie"
MOVIE_DATABASE_ENDPOINT_BY_ID = "https://api.themoviedb.org/3/movie/"
MOVIE_DATABASE_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
API_KEY = os.getenv("API_KEY_MOVIE")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my-top-movie-collection.db'
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY_MOVIE")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
db = SQLAlchemy(app)


# CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float)
    ranking = db.Column(db.String)
    review = db.Column(db.String)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return '<Movie %r>' % self.title


# CREATE WTF TORMS

class MyForm(FlaskForm):
    rating = FloatField(label='Your rating out of 10', validators=[DataRequired(), NumberRange(min=1, max=10)])
    review = StringField(label='Your review', validators=[DataRequired()])
    submit = SubmitField(label="Submit")


class MyFormAdd(FlaskForm):
    movie_name = StringField(label='Movie title', validators=[DataRequired()])
    submit = SubmitField(label="Add movie")


@app.route("/", methods=["GET", "POST"])
def home():
    all_movies = Movie.query.order_by(Movie.rating.desc()).all()
    i = 1
    for movie in all_movies:
        movie.ranking = i
        i += 1
    db.session.commit()
    return render_template("index.html", all_movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    edit_form = MyForm()
    movie_id = request.args.get("id")
    movie_to_update = Movie.query.get(movie_id)
    if edit_form.validate_on_submit():
        # print(edit_form.rating.data)
        movie_to_update.rating = request.form["rating"]
        movie_to_update.review = request.form["review"]
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", form=edit_form, movie=movie_to_update)


@app.route("/delete")
def delete():
    book_id = request.args.get('id')

    # DELETE A RECORD BY ID
    book_to_delete = Movie.query.get(book_id)
    db.session.delete(book_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    add_movie_form = MyFormAdd()
    if add_movie_form.validate_on_submit():
        movie_name = add_movie_form.movie_name.data
        query = {
            "api_key": API_KEY,
            "query": movie_name,
            "language": "en-US",
        }
        response = requests.get(url=MOVIE_DATABASE_ENDPOINT, params=query)
        results = response.json()
        movie_list = [dictionary for dictionary in results["results"]]
        return render_template("select.html", movie_list=movie_list)
    return render_template("add.html", form=add_movie_form)


@app.route("/find")
def find_movie():
    movie_id = request.args.get("id")
    if movie_id:
        query = {
            "api_key": API_KEY,
            "language": "en-US",
        }
        response = requests.get(url=f"{MOVIE_DATABASE_ENDPOINT_BY_ID}{movie_id}", params=query)
        results = response.json()
        new_movie = Movie(title=results["original_title"], year=results["release_date"],
                          description=results["overview"], img_url=f"{MOVIE_DATABASE_IMAGE_URL}{results['poster_path']}")
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
