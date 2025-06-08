from flask import Blueprint, request, render_template
from data_scripts import recommend
import re
import pandas as pd
import io

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
    input_method = request.form.get("input_method", "username")
    randomness = request.form.get("slider_value")
    print(input_method, randomness)
    print("Input Good")
    if input_method == 'username':
        user_input = request.form.get("user_input")
        if not user_input:
            table_data = 1
            return render_template('form_template.html', table_data=table_data)
        result = recommend.recommend_user(user_input, randomness)
    elif input_method == 'csv':
        if 'csv_file' not in request.files:
            table_data = 1
            print('No file')
            return render_template('form_template.html', table_data=table_data)
        
        file = request.files['csv_file']
        if file.filename == '':
            table_data = 1
            print('Empty filename')
            return render_template('form_template.html', table_data=table_data)
        
        if file and file.filename.endswith('.csv'):
            try:
                csv_data = file.read().decode('utf-8')
                df = pd.read_csv(io.StringIO(csv_data))
                print('CSV read')
                # validate CSV
                required_columns = ['Date', 'Name', 'Year', 'Letterboxd URI', 'Rating']
                missing_columns = [col for col in required_columns if col not in df.columns]
                print('CSV validated')
                if missing_columns:
                    table_data = 1
                    print('Missing columns')
                    return render_template('form_template.html', table_data=table_data)
                
                if len(df) == 0:
                    table_data = 1
                    print('No rows')
                    return render_template('form_template.html', table_data=table_data)
                print('Recommending')
                result = recommend.recommend_csv(df, randomness)
                
            except Exception as e:
                table_data = 1
                return render_template('form_template.html', table_data=table_data)
        else:
            table_data = 1
            return render_template('form_template.html', table_data=table_data)
    else:
        table_data = 1
        return render_template('form_template.html', table_data=table_data) 

    if result is None:
        table_data = 1
        return render_template('form_template.html', table_data = table_data)
    else:
        result['url'] = 'https://letterboxd.com/film/' + result['film_slug']
        result = result[['poster', 'film_title', 'year', 'rec_score', 'avg_rating',
                        'film_genres', 'actors', 'director', 'runtime', 'streaming', 'url']]
        result['film_genres'] = result['film_genres'].str.replace(r'[\[\]"\'{}]', '', regex=True)
        print(result['streaming'][:20])
        result['streaming'] = result['streaming'].str.join(', ')
        print(result['streaming'][:20])
        table_data = result.to_dict(orient='records')
        return render_template('form_template.html', table_data = table_data)