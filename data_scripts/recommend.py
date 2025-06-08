import pandas as pd
print(pd.__file__)
from data_scripts.helpers import get_user_films, predict, process_letterboxd_csv
import numpy as np
from joblib import Parallel, delayed
import itertools
from collections import defaultdict

def recommend_username(username, randomness):
    userfilms = get_user_films(username)
    filminfo = pd.read_parquet('s3://letterboxdrecommender/filminfo.parquet')
    loaded_e = np.load("s3://letterboxdrecommender/item_embeddings.npz", allow_pickle=False)

    item_embeddings = {
        key: loaded_e[key].astype(np.float32)
        for key in loaded_e.files
    }
    loaded_e.close()

    loaded_b = np.load("s3://letterboxdrecommender/item_biases.npz", allow_pickle=False)
    item_biases = {
        key: float(loaded_b[key].item())  # .item() turns a 0-D array into a Python float
        for key in loaded_b.files
    }
    loaded_b.close()

    recommendations_df = predict(userfilms, item_embeddings, item_biases, randomness, filminfo)
    return recommendations_df.dropna()[:1000]

def recommend_csv(userfilms, randomness):
    filminfo = pd.read_parquet('s3://letterboxdrecommender/filminfo.parquet')
    print('Film Info')
    loaded_e = np.load("s3://letterboxdrecommender/item_embeddings.npz", allow_pickle=False)
    print('Embeddings')
    userfilms = process_letterboxd_csv(userfilms, filminfo)
    print('Processed')

    item_embeddings = {
        key: loaded_e[key].astype(np.float32)  # ensure dtype is float32
        for key in loaded_e.files
    }
    loaded_e.close()

    # 2) Load biases.npz
    loaded_b = np.load("s3://letterboxdrecommender/item_biases.npz", allow_pickle=False)
    item_biases = {
        key: float(loaded_b[key].item())  # .item() turns a 0-D array into a Python float
        for key in loaded_b.files
    }
    loaded_b.close()

    recommendations_df = predict(userfilms, item_embeddings, item_biases, randomness, filminfo)
    print('Recommended')
    recommendations_df.to_csv('recs.csv')
    return recommendations_df.dropna()[:1000]

