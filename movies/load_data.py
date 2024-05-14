import json
from movies.models import Movie, Genre, Celebrity, Rating

DATA_PATH = "movies/data/movies.json"


def main():
    with open(DATA_PATH, "r") as f:
        movies = json.load(f)
    for movie in movies:
        print(f'Loading movie {movie["title"]}')
        if not Movie.objects.filter(id=movie["id"]).exists():
            print("Creating...")
            my_movie = Movie(id=movie["id"])
            my_movie.title = movie["title"]
            my_movie.year = movie["year"]
            rating = movie["rating"]
            if rating is None:
                rating = "Unrated"
            rating = Rating.objects.get_or_create(name=rating)[0]
            my_movie.rating = rating
            my_movie.runtime = movie["runtime"]
            my_movie.poster = movie["poster"]
            my_movie.userRating = movie["userRating"]
            my_movie.votes = movie["votes"]
            my_movie.save()
            genres = [
                Genre.objects.get_or_create(name=genre)[0] for genre in movie["genres"]
            ]
            my_movie.genres.set(genres)
            directors = [
                Celebrity.objects.get_or_create(name=genre)[0]
                for genre in movie["directors"]
            ]
            my_movie.directors.set(directors)
            cast = [
                Celebrity.objects.get_or_create(name=genre)[0]
                for genre in movie["cast"]
            ]
            my_movie.cast.set(cast)
    return
