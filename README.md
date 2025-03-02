# Letterboxd Recommendation Website

This project is a web-based recommendation engine that uses data from the user's Letterboxd profile to generate personalized movie recommendations. 
By comparing user ratings with a large dataset of over 5 million ratings from over 1000 popular Letterboxd profiles, the engine finds films tailored
to the user's unique taste and preferences.

## Features
- **Personalized Recommendations**: Enter your Letterboxd username to generate the list of recommended movies
- **Recommendation Speed**: Adjust the slider for faster or more personalized recommendations
- **Filterable and Sortable Results**: Recommendations can be sorted or filtered by genre, film runtime, or release year
- **Streaming Information**: Recommendations can also be filtered by streaming service, so you can find the movies most accessible to you (thanks to TMDB)

## Recommendation Algorithm
The recommendation engine is powered by SVD (Singular Value Decomposition). Below is a short description on how SVD works and how it was utilized in this engine.
- SVD decomposes a matrix of user-item rating pairs into three matrices:
  -   U: represents latent factors related to each user/profile
  -   S: represents the importance of each latent factor
  -   V: represents tje latent factors related to each item/film
-   The decomposition identifies latent factors or hidden features that explain observed item preferences for each user
-   A new rating matrix is reconstructed from the latent factors to predict how users may rate items/films they have not previously rated.
    The items with the highest rating predictions are delivered as recommendations.

Adjusting the recommendation speed alters how many ratings are included in the initial ratings matrix for model-building. 
A lower speed means a smaller matrix and faster training/prediction. A higher speed leads to a larger, more comprehensive rating matrix and slower prediction. 

## Libraries and Software Used
- Flask: Used for app development and handling server-side logic.
- DataTables: A jQuery plugin for creating interactive, feature-rich tables to display movie recommendations.
- jQuery & jQuery UI: Provide essential DOM manipulation, slider components, and other interactive UI elements.
- Select2: Enhances select boxes for improved filter controls.
- Surprise: A Python library for recommendation systems, such as SVD.
- BeautifulSoup: Used to web scrape ratings off of Letterboxd user profiles
- Railway: The deployment platform used to host the web application.
- Amazon S3: Employed for storing data assets and backups securely.

## Suggestions
If anyone has any suggestions on how this site/engine can be improved, feel free to reach out at theryanshanker@gmail.com. Happy watching!
