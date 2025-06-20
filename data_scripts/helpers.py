from bs4 import BeautifulSoup
import requests
import pandas as pd
import time as tm
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from surprise.prediction_algorithms import SVD
from surprise import Dataset, Reader
import numpy as np

def get_user_films_page(username, page, session):
    # construct URL for current page
    url = f'https://letterboxd.com/{username}/films/by/popular/page/{str(page)}/'
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
    return pd.DataFrame(films)


def get_user_ratings(username):
    # create session for repeated requests
    session = requests.Session()
    # initialize page counter
    page = 1
    # initialize empty list to store dictionary for each film
    films = []
    print(username)
    # create loop to fetch pages until no more films are found
    while True:
        # construct URL for current page
        url = f'https://letterboxd.com/{username}/films/rated/.5-5/page/{str(page)}/by/date'
        # send get request and parse HTML content
        site = session.get(url)
        soup = BeautifulSoup(site.text, 'html.parser')
        # check if there are no films or poster containers on the page
        if soup.find_all('div', class_='film-poster') == []:
            # exit loop if no films found
            break
        # iterate over the films on the page
        for film in soup.find_all('div', class_='film-poster'):
            # pull the film id and film slug variables
            film_id = int(film['data-film-id'])
            film_slug = film['data-film-slug']
            # pull user rating of film
            rating = int(film.find_next('span', class_='rating')['class'][-1][6:])
            # pull film title from image element
            film_title = film.find('img', class_='image')['alt']
            # append dictionary with all of the pulled information to the list
            films.append({'username': username, 'film_id': film_id, 'film_title': film_title, 
                          'film_slug': film_slug, 'rating': rating})
        # increment page counter
        page += 1
    # return list of dictionaries
    return films

# initialize headers and set of streaming services
def get_streaming_services(tmdb, 
                           headers = { "accept": "application/json",
                                      "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzM2EwNWQ0NGNhNmI0NDBhZWUwYzU4ZWY2ODc2ZTc4ZCIsIm5iZiI6MTczMjY3OTc1NC40MjM1ODA2LCJzdWIiOiI2NzQ2NzYyYzAyNjY4MmI5MmViMDU4NDciLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.iF58TGPLs4d60w2PvQr1LFVQj2680XDxhdYl_xXEEwY"}, 
                           streamset = set(['Netflix', 'Hulu', 'Max', 'Amazon Prime Video', 'Apple TV Plus', 'Peacock Premium', 'Paramount Plus', 'Disney Plus', 'Crunchyroll', 'Pluto TV', 'Tubi TV'])):
    # grab stub of URL that can be used to index API
    stub = tmdb[27:-6]
    # initialize empty list for streaming services
    services = []
    # create URL for API
    url = f"https://api.themoviedb.org/3/{stub}/watch/providers"
    # send get request
    response = requests.get(url, headers=headers)
    # check if there are streaming options for US
    if 'US' in set(json.loads(response.text)['results'].keys()):
        # grab US results
        watch_types = [i for i in json.loads(response.text)['results']['US']]
        # add the paid streaming services (flatrate) to the list
        if 'flatrate' in watch_types:
            services.extend([x['provider_name'] for x in json.loads(response.text)['results']['US']['flatrate']])
        # add the free with ads streaming services (ads) to the list
        if 'ads' in watch_types:
            services.extend([x['provider_name'] for x in json.loads(response.text)['results']['US']['ads']])
    # return only the services within the set specified above
    return set(services).intersection(streamset)

def get_film_info(film_title, film_slug, film_id = None):
    try:
        # create the film url
        url = f'https://letterboxd.com/film/{film_slug}'
        print(film_title)
        # send get request and parse content
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'lxml')
        # find script tage with JSON data
        json_script = soup.select_one('script[type="application/ld+json"]')
        # extract the JSON data
        json_data = json.loads(json_script.text.split(' */')[1].split('/* ]]>')[0])
        # extract individual information
        poster = json_data['image']
        genres = ', '.join(json_data['genre'])
        actors = ', '.join([actor['name'] for actor in json_data['actors'][:3]])
        director = ', '.join([director['name'] for director in json_data['director']])
        avg_rating = json_data.get('aggregateRating', {}).get('ratingValue', None)
        num_rating = json_data.get('aggregateRating', {}).get('ratingCount', None)
        year = json_data['releasedEvent'][0]['startDate']
        runtime_text = soup.find('p', class_ = 'text-link').text
        runtime = int(re.findall(r'\b\d+\b', runtime_text)[0])
        url = 'https://letterboxd.com/film/' + film_slug
        # find tmdb link
        tmdb = soup.find('a', {'data-track-action': 'TMDB'})['href'] + 'watch'
        # pull the streaming services
        streaming = get_streaming_services(tmdb)
    except Exception as e:
        print(f"Error: {film_slug}, Error: {e}")
        return
    return {"film_title": film_title, "film_slug": film_slug,
            "film_id": film_id,  'poster': poster, 
            "film_genres": genres, 'actors': actors, 
            "director": director, "avg_rating": avg_rating, 
            "rating_count": num_rating, "runtime": runtime, 
            "year": year, "streaming": streaming, "url": url}

def build_rating_database(pages):
    # create empty list to hold the usernames of the accounts within the database
    usernames = []
    # create empty list to hold dictionaries of each user's ratings
    ratings = []
    start1 = tm.time()
    # loop over the number of member pages to pull usernames from
    for page in range(1, pages):
        print(f"Page {page}")
        # create URL
        url = f'https://letterboxd.com/members/popular/this/all-time/page/{page}'
        # send get request and parse content
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'lxml')
        # members page has the top 5 reviewers on every page, remove to ensure no redundance
        user_links = soup.find_all('a', class_ = 'name')[:-5]
        # grab the usernames from the hyperlinks
        page_users = [a['href'].strip('/') for a in user_links]
        # add to the list
        usernames.extend(page_users)
    # remove duplicates to ensure no redundance again
    usernames = list(set(usernames))
    # parallelize the pulling of ratings, distribute over 10 workers
    with ThreadPoolExecutor(max_workers=10) as executor:
        # schedule function calls for each of the worker threads
        future_to_username = {executor.submit(get_user_ratings, username): username for username in usernames}
        # iterates over threads as they are completed
        for future in as_completed(future_to_username):
            # grab the username
            username = future_to_username[future]
            try:
                # retrieve returned ratings
                user_ratings = future.result()
                # add to list
                ratings.extend(user_ratings)
            except Exception as e:
                print(f"Error fetching ratings for {username}: {e}")
    # convert to a dataframe
    ratings = pd.DataFrame(ratings)
    # keep only the films that at least 5% of the users in the database have seen
    num_users = ratings['username'].nunique()
    film_counts = ratings.groupby('film_id').size()
    valid_films = film_counts[film_counts >= (0.05 * num_users)].index
    ratings = ratings[ratings.film_id.isin(valid_films)]
    end = tm.time()
    return ratings

def build_films_database(df):
    films = []
    # take ratings database in and grab the unique films
    pairs = df[['film_title', 'film_slug', 'film_id']].drop_duplicates()
    # separate the titles, slugs, and ids
    titles = list(pairs['film_title'])
    slugs = list(pairs['film_slug'])
    ids = list(pairs['film_id'])
    # parallelize the pulling of film information, distribute over 10 workers
    with ThreadPoolExecutor(max_workers=10) as executor:
            # schedule function calls for each of the worker threads
            results = executor.map(get_film_info, titles, slugs, ids)
            # retrieve film info if info is available
            for result in results:
                if result is not None:
                    films.append(result)
    films = pd.DataFrame(films)    
    films = films[(films.runtime >= 45) & (films.runtime <= 240)]
    return pd.DataFrame(films)

def fit_svd_and_predict(df, userfilms):
    # adjust scale for SVD model
    scale = (min(df.adj_rating), max(df.adj_rating))
    # load the trainset with appropriate scale
    fulldata = Dataset.load_from_df(df[['username', 'film_id', 'adj_rating']], 
                                    reader = Reader(rating_scale = scale)).build_full_trainset()
    # initialize SVD and fit
    svd_all = SVD(n_factors = 350, 
          reg_all = 0.075, 
          lr_all = 0.005, biased = False)
    svd_all.fit(fulldata)
    # find film IDs that the user watched
    raw_watched = set(userfilms.film_id.astype(int))
    # convert to SVD item ID
    all_raw_ids = [int(fulldata.to_raw_iid(innerid)) for innerid in fulldata.all_items()]
    # return all SVD item IDs that the user has not seen
    not_watched = [item_id for item_id in all_raw_ids if item_id not in raw_watched]
    # predict for all items that the user has not seen
    preds = [(item_id, svd_all.predict(userfilms.username.unique()[0], item_id).est) for item_id in not_watched]
    return preds

def process_letterboxd_csv(csv_df, films_database):
    processed_data = []
    username = "csv_user"
    
    for _, row in csv_df.iterrows():
        try:
            title = row['Name']
            year = str(row['Year'])
            rating = float(row['Rating'])
            
            if pd.isna(title) or pd.isna(year) or pd.isna(rating):
                continue
            
            # exact title and year match
            matches = films_database[
                (films_database['film_title'] == title) &
                (films_database['year'] == year)
            ]
            
            if len(matches) > 0:
                film_info = matches.iloc[0]
                processed_data.append({
                    'username': username,
                    'film_id': film_info['film_id'],
                    'film_title': title,
                    'film_slug': film_info['film_slug'],
                    'rating': rating * 2 
                })
            # if no match found, ignore   
        except Exception as e:
            continue
    
    result_df = pd.DataFrame(processed_data)
    return result_df

def create_user_embedding(user_ratings, item_embeddings, n_factors = 1000):
    embedding = np.zeros(n_factors)
    weight_total = 0
    for _, row in user_ratings.iterrows():
        film_id = int(row['film_id'])
        rating = float(row['rating'])

        if film_id in item_embeddings:
            weight = abs(rating - 5.5) + 1
            embedding += weight * item_embeddings[str(film_id)]
            weight_total += weight

    if weight_total > 0:
        embedding /= weight_total
    
    return embedding

def calculate_user_bias(user_ratings):
    return user_ratings['rating'].mean()

def predict_user(item_embeddings, item_biases, userfilms):
    user_ratings = userfilms[userfilms.rating.notna()]
    user_embedding = create_user_embedding(user_ratings, item_embeddings)
    user_bias = calculate_user_bias(user_ratings)
    watched = set(userfilms.film_id.astype(int))
    predictions = [(item_id, (user_bias + item_biases.get(item_id, 0) + np.dot(user_embedding, item_embedding))) \
                    for item_id, item_embedding in item_embeddings.items() if int(item_id) not in watched]
    return sorted(predictions, key=lambda x: x[1], reverse = True)

def predict(userfilms, item_embeddings, item_biases, randomness, filminfo):
    predictions = pd.DataFrame(predict_user(item_embeddings, item_biases, userfilms), 
                               columns = ['film_id', 'rec_score'])
    recommendations_df = randomize(predictions, randomness, filminfo)
    return recommendations_df 

def randomize(predictions, randomness, filminfo):
    if randomness == 0:
        return pd.merge(left=predictions, right=filminfo, how='left', on = 'film_id')
    noise = np.random.normal(loc = 0.0, scale = 0.5 * 100 * np.std(predictions.rec_score)/100, size = predictions.rec_score.shape)
    predictions['rec_score'] = predictions['rec_score'] + noise
    predictions['film_id'] = predictions['film_id'].astype(int)
    predictions.to_csv('preds.csv')
    recommendations_df = pd.merge(left=predictions, right=filminfo, how='left', on = 'film_id')
    recommendations_df.to_csv('recdf.csv')
    N = len(recommendations_df)
    max_p = np.max(recommendations_df.rating_count)
    norm_popularity = recommendations_df.rating_count / max_p 
    weights = (1.0 - norm_popularity) ** 1.5
    sigma_base = np.std(recommendations_df.rec_score) 
    noise = np.random.normal(loc = 0.0, scale = 1.0, size = N)
    perturbation_mag = 0.1 * sigma_base * weights * noise
    recommendations_df['rec_score'] = recommendations_df['rec_score'] + perturbation_mag
    recommendations_df['rec_score'] = 1 + 9 * (recommendations_df.rec_score - min(recommendations_df.rec_score)) / (max(recommendations_df.rec_score) - min(recommendations_df.rec_score))
    recommendations_df['rec_score'] = recommendations_df['rec_score'].round(2)
    return recommendations_df.sort_values(by = 'rec_score', ascending = False)






