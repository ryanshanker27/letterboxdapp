from flask import Blueprint, request, render_template
from data_scripts import recommend  # Assuming your recommend module is inside data_scripts
import re

# Create a Blueprint named 'main'
main = Blueprint('main', __name__)

@main.route("/", methods=["GET"])
def index():
    print("Good")
    # Render the form for user input.
    return render_template('form_template.html')

@main.route("/submit", methods=["GET", "POST"])
def submit():
    # Retrieve the text input from the form
    user_input = request.form.get("user_input")
    if user_input:
        # Feed input into function
        user_speed = request.form.get("slider_value")
        result = recommend.recommend(user_input, user_speed)
        if result is None:
            table_data = 1
            return render_template('form_template.html', table_data = table_data)
        else:
            result['url'] = 'https://letterboxd.com/film/' + result['film_slug']
            result = result[['poster', 'film_title', 'year', 'rec_score', 'avg_rating',
                            'film_genres', 'actors', 'director', 'runtime', 'streaming', 'url']]
            result['film_genres'] = result['film_genres'].str.replace(r'[\[\]"\'{}]', '', regex=True)
            result['streaming'] = result['streaming'].str.replace(r'[\[\]"\'{}]', '', regex=True)
            table_data = result.to_dict(orient='records')
            return render_template('form_template.html', table_data = table_data)