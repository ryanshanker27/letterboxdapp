from bs4 import BeautifulSoup
import requests
import pandas as pd
import time as tm
from concurrent.futures import ThreadPoolExecutor, as_completed
from surprise.prediction_algorithms import SVD, KNNBasic, KNNBaseline, SVDpp, NMF, KNNWithMeans
from surprise import Dataset, Reader, accuracy
import itertools

def get_user_films_page(username, page, session):
    # construct URL for current page
    url = f'https://letterboxd.com/{username}/films/page/{str(page)}/'
    # send get request and parse HTML content
    site = session.get(url)
    soup = BeautifulSoup(site.text, 'html.parser')
    # initialize empty list to store dictionary for each film
    films = []
    for film in soup.find_all('li', class_='poster-container'):
        # find all div elements corresponding to the poster
        info = film.find('div', class_ = 'film-poster')
        # pull the film id and film slug variables
        film_id = int(info['data-film-id'])
        film_slug = info['data-film-slug']
        # pull user rating of film, return None if no rating found
        try:
            rating = int(film.find('span', class_ = 'rating')['class'][-1][6:])
        except:
            rating = None
        # pull film title from image element
        film_title = film.find('img', class_='image')['alt']
        # append dictionary with all of the pulled information to the list
        films.append({'username': username, 
                    'film_id': film_id, 
                    'film_title': film_title, 
                    'film_slug': film_slug, 
                    'rating': rating})
    return films

def get_user_films(username):
    # find the number of pages with films for the given user
    url = f'https://letterboxd.com/{username}/films/page/1/'
    # create session for repeated requests
    session = requests.Session()
    # send get request and parse HTML content
    site = session.get(url)
    soup = BeautifulSoup(site.text, 'html.parser')
    # find number of film pages by indexing pagination counter, only 1 page if no counter exists
    try:
        num_pages = int(soup.find_all('li', class_='paginate-page')[-1].text)
    except:
        num_pages = 1
    # parallelize pulling of films and ratings
    with ThreadPoolExecutor() as executor:
        # schedule function calls for each of the worker threads
        results = executor.map(get_user_films_page, [username]*num_pages, range(1, num_pages+1), [session]*num_pages)
        # retrieve film info if info is available
        films = []
        for result in results:
            films.extend(result)
    # films = Parallel(n_jobs=-1)(delayed(get_user_films_page)(username, page, session) for page in range(1, num_pages+1))
    return pd.DataFrame(films)

def fit_svd_and_predict(df, userfilms):
    # adjust scale for SVD model
    scale = (min(df.adj_rating), max(df.adj_rating))
    # load the trainset with appropriate scale
    fulldata = Dataset.load_from_df(df[['username', 'film_id', 'adj_rating']], 
                                    reader = Reader(rating_scale = scale)).build_full_trainset()
    # initialize SVD and fit
    svd_all = SVD(n_factors = 500, 
          reg_all = 0.075, 
          lr_all = 0.005, biased = False)
    svd_all.fit(fulldata)
    # find film IDs that the user watched
    raw_watched = set(userfilms.film_id)
    # convert to SVD item ID
    all_raw_ids = [fulldata.to_raw_iid(innerid) for innerid in fulldata.all_items()]
    # return all SVD item IDs that the user has not seen
    not_watched = [item_id for item_id in all_raw_ids if item_id not in raw_watched]
    # predict for all items that the user has not seen
    preds = [(item_id, svd_all.predict(userfilms.username.unique()[0], item_id).est) for item_id in not_watched]
    return preds







