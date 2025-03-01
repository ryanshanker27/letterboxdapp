from bs4 import BeautifulSoup
import requests
import pandas as pd
print(pd.__file__)
import time as tm
from numpy.linalg import svd 
from data_scripts.helpers import get_user_films, fit_svd_and_predict
from surprise.prediction_algorithms import SVD, KNNBasic, KNNBaseline, SVDpp, NMF, KNNWithMeans
from surprise import Dataset, Reader, accuracy
from tqdm import tqdm
import numpy as np
from joblib import Parallel, delayed
import itertools
from collections import defaultdict
import logging

def recommend(username, user_speed):
    print(type(user_speed))
    user_speed = int(user_speed)
    # pull all films the user has watched (even ones that are unrated)
    userfilms = get_user_films(username)
    # return None if no ratings recorded
    if len(userfilms.dropna()) == 0:
        return None
    
    # grab dataframes from S3 bucket
    ratings_df = pd.read_parquet('s3://letterboxdrecommender/ratings_db.parquet')
    filminfo = pd.read_parquet('s3://letterboxdrecommender/filminfo.parquet')
    # isolate films user has rated
    user_ratings = userfilms[userfilms.rating.notna()]
    # add user ratings to ratings database
    df = pd.concat([ratings_df, user_ratings], ignore_index=False).dropna(subset=['rating']).copy()

    if user_speed >= 50 and len(user_ratings) > 100:
       # set importance ratio for user and item rating averages
        ratio = 0.5
        # take user and item averages
        df["user_avg"] = df.groupby("username")["rating"].transform("mean")
        df["item_avg"] = df.groupby("film_id")["rating"].transform("mean")
        # subtract averages weighted by ratio (so mean of all ratings is zero)
        df["adj_rating"] = df["rating"] - (ratio * df["user_avg"] + (1 - ratio) * df["item_avg"])
        # normalize ratings to 1-10
        adj_min, adj_max = df["adj_rating"].min(), df["adj_rating"].max()
        df["adj_rating"] = 1 + (df["adj_rating"] - adj_min)*9/(adj_max - adj_min)
    else:
        df["adj_rating"] = df["rating"]

    # sample ratings randomly
    sample = 500000 + int((2000000 - 500000)*int(user_speed)/100)
    new_df = df.sample(sample, replace = False)
    # split the sample into equal chunks
    n_chunks = 5
    chunks = np.array_split(new_df, n_chunks)

    # fit individual SVD models to each chunk
    preds = Parallel(n_jobs=-1)(delayed(fit_svd_and_predict)(chunk, userfilms) for chunk in chunks)
    # aggregate results in dictionary
    fullpreds = list(itertools.chain(*preds))
    sums = defaultdict(float)
    counts = defaultdict(int)
    for film_id, score in fullpreds:
        sums[film_id] += score
        counts[film_id] += 1
    result = {film_id: sums[film_id] / counts[film_id] for film_id in sums}

    # sort results by recommendation score
    result = sorted(result.items(), key=lambda x: x[1], reverse = True)
    # take the top 1000 films
    top_films = result[:1000]
    # find the film IDs and rec scores for the top 1000 films
    top_film_movieids = [film_id for film_id, score in top_films]
    top_film_moviescores = [round(score, 3) for film_id, score in top_films]
    # organize into a dataframe
    top_film_df = pd.DataFrame({'film_id': top_film_movieids, 
                            'rec_score': top_film_moviescores})
    # merge with film information table before returning
    recommendations_df = pd.merge(left=top_film_df, right=filminfo, how='left', on = 'film_id')

    return recommendations_df.dropna()

# if __name__ == '__main__':
#     import sys
#     if len(sys.argv) != 2:
#         print("Usage: python recommend.py username")
#         sys.exit(1)
#     username = sys.argv[1]
#     start = tm.time()
#     films = recommend(username)
#     films.to_csv('recommendations.csv')
#     print(tm.time() - start)

