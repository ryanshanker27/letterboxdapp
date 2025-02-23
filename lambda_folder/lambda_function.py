import os

os.environ['HOME'] = '/tmp'
os.environ['SURPRISE_DATASET_DIR'] = '/tmp'
os.environ['JOBLIB_MULTIPROCESSING'] = '0'

import json
import pandas as pd
import re
from helpers import get_user_films, fit_svd_and_predict
from recommend import recommend 

def lambda_handler(event, context):
    username = event.get("username")
    user_speed = int(event.get("user_speed", 50))

    result = recommend(username, user_speed)
    if result is None:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "No recommendations found for the user"})
        }
    
    result['url'] = 'https://letterboxd.com/film/' + result['film_slug']
    result = result[['poster', 'film_title', 'year', 'rec_score', 'avg_rating',
                     'film_genres', 'actors', 'director', 'runtime', 'streaming', 'url']]
    result['film_genres'] = result['film_genres'].str.replace(r'[\[\]"\'{}]', '', regex=True)
    result['streaming'] = result['streaming'].str.replace(r'[\[\]"\'{}]', '', regex=True)
    table_data = result.to_dict(orient='records')

    return {
        "statusCode": 200,
        "body": json.dumps({"recommendations": table_data})
    }