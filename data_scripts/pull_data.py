from helpers import build_films_database, build_rating_database
import pandas as pd
# from sqlalchemy import create_engine
import time as tm
import os
import boto3
import io

start = tm.time()

# os.environ["AWS_ACCESS_KEY_ID"] = "AKIATHVQLJPYKZH4HSNC"
# os.environ["AWS_SECRET_ACCESS_KEY"] = "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"
# os.environ["AWS_DEFAULT_REGION"] = "us-east-2"

ratings_db = build_rating_database(121)
ratings_db.to_csv('ratings_db.csv')
ratings_db = pd.read_csv('ratings_db.csv')
ratings2 = ratings_db[['film_id', 'username', 'rating', 'film_slug']]

# ratings2.to_sql('ratings', engine, if_exists='replace', index=False)

filminfo = build_films_database(ratings_db)
filminfo.to_csv('filminfo.csv')
filminfo = pd.read_csv('filminfo.csv')
filminfo = filminfo[['film_id', 'film_slug', 'film_title', 'poster', 'actors', 'film_genres',
                     'director', 'avg_rating', 'rating_count', 'runtime', 'year', 'streaming']]

buffer = io.BytesIO()
filminfo.to_parquet(buffer, engine='pyarrow', index=False)
buffer.seek(0)

# Upload to S3
s3_client = boto3.client('s3')
s3_client.upload_fileobj(
    Fileobj=buffer, 
    Bucket='letterboxdrecommender', 
    Key='filminfo.parquet'
)

ratings2 = ratings2[ratings2.film_id.isin(filminfo.film_id)]
buffer = io.BytesIO()
ratings2.to_parquet(buffer, engine='pyarrow', index=False)
buffer.seek(0)

s3_client.upload_fileobj(
    Fileobj=buffer, 
    Bucket='letterboxdrecommender', 
    Key='ratings_db.parquet'
)
# filminfo.to_sql('films', engine, if_exists='replace', index=False)
print("Time Elapsed: ", tm.time() - start)
