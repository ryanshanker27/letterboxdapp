from bs4 import BeautifulSoup
import requests
import pandas as pd
import time as tm
from helpers import get_user_films, fit_svd_and_predict
from surprise.prediction_algorithms import SVD, KNNBasic, KNNBaseline, SVDpp, NMF, KNNWithMeans
from surprise import Dataset, Reader, accuracy
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import itertools

def recommend(username, user_speed):
    user_speed = int(user_speed)
    userfilms = get_user_films(username)
    # return None if no ratings recorded
    if len(userfilms.dropna()) == 0:
        return None

    
    # grab dataframes from S3 bucket
    ratings_df = pd.read_parquet('s3://letterboxdrecommender/ratings_db.parquet')
    filminfo = pd.read_parquet('s3://letterboxdrecommender/filminfo.parquet')
    # isolate films user has rated
    user_ratings = userfilms[userfilms.rating.isna() == False]
    # print(user_ratings.columns)
    # add user ratings to ratings database
    df1 = pd.concat([ratings_df, pd.DataFrame(user_ratings)], ignore_index = False)
    df = df1.dropna(subset=['rating']).copy()

    if user_speed >= 60 and len(user_ratings) > 100:
       # set importance ratio for user and item rating averages
        ratio = 0.4
        # take user and item averages
        df["user_avg"] = df.groupby("username")["rating"].transform("mean")
        df["item_avg"] = df.groupby("film_id")["rating"].transform("mean")
        # subtract averages weighted by ratio (so mean of all ratings is zero)
        df["adj_rating"] = df["rating"] - (ratio * df["user_avg"] + (1 - ratio) * df["item_avg"])
        df["adj_rating"] = 1 + (df["adj_rating"] - df["adj_rating"].min())*9/(df["adj_rating"].max() - df["adj_rating"].min())
    else:
        df["adj_rating"] = df["rating"]

    # sample ratings randomly
    sample = 500000 + int((2000000 - 500000)*int(user_speed)/100)
    new_df = df.sample(sample, replace = False)
    # split the sample into equal chunks
    n_chunks = 5
    size = len(new_df) // n_chunks
    chunks = [new_df[i:i+size] for i in range(0, len(new_df), size)]

    # fit individual SVD models to each chunk
    with ProcessPoolExecutor(max_workers=n_chunks) as executor:
        futures = [executor.submit(fit_svd_and_predict, chunk, userfilms) for chunk in chunks]
        preds = [future.result() for future in as_completed(futures)]
    # preds = Parallel(n_jobs=-1)(delayed(fit_svd_and_predict)(chunk, userfilms) for chunk in chunks)
    # aggregate results in dictionary
    fullpreds = list(itertools.chain(*preds))
    sum = {}
    count = {}
    for lst in fullpreds:
        key, value = lst
        if key in sum:
            sum[key] += value
            count[key] += 1
        else:
            sum[key] = value
            count[key] = 1
    result = { key: sum[key] / count[key] for key in sum }

    # sort results by recommendation score
    result = sorted(result.items(), key=lambda x: x[1], reverse = True)
    # take the top 1000 films
    top_films = result[:1000]
    # find the film IDs and rec scores for the top 1000 films
    top_film_movieids = [x[0] for x in top_films]
    top_film_moviescores = [round(x[1], 3) for x in top_films]
    # organize into a dataframe
    top_film_df = pd.DataFrame({'film_id': top_film_movieids, 
                            'rec_score': top_film_moviescores})
    # merge with film information table before returning
    recommendations_df = pd.merge(left=top_film_df, right=filminfo, how='left', on = 'film_id')

    return recommendations_df.dropna()

