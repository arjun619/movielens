from flask import Flask,render_template,request,redirect
from flask import *
import numpy as np
import pandas as pd
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
movie = pd.read_csv('movie.csv')
rating = pd.read_csv('small_rating')
user_movie_df= pd.read_csv("user_movie_df")
@app.route("/")
def item_based_collaborative():
    result= pd.read_csv("model1_small.csv")
    q = request.args['q']
    movie_name = result[q]
    val=result.corrwith(movie_name).sort_values(ascending=False)[1:11]
    print(type(val))
    print(val.index)
    # print(val)
    return jsonify({"item_based_collaborative":list(val.index)})
    
@app.route("/user/")
def user_based_collaborative():
    # movie = pd.read_csv('movie.csv')
    df_M=movie
    # rating = pd.read_csv('small_rating')
    df_R=rating
    print("hello")
    # user_movie_df= pd.read_csv("user_movie_df")
    random_user = request.args['q']
    print(random_user)
    random_user=int(random_user)
    print(random_user)
    random_user_df = user_movie_df[user_movie_df.index == random_user]
    movies_watched = random_user_df.columns[random_user_df.notna().any()].tolist() # list of movies watched by the user
    movies_watched=movies_watched[1:20]
    movies_watched_df = user_movie_df[movies_watched]
    movies_watched_df=movies_watched_df[~movies_watched_df[movies_watched[0]].isnull()]
    user_movie_count = movies_watched_df.T.notnull().sum().reset_index() #Discarding null values and making some index corrections
    user_movie_count.columns = ["userId", "movie_count"]
    k=len(movies_watched)*0.60 
    users_same_movies=user_movie_count[user_movie_count["movie_count"] > k]["userId"]
    final_df = pd.concat([movies_watched_df[movies_watched_df.index.isin(users_same_movies)],
                      random_user_df[movies_watched]])
    corr_df=final_df.T.corr().unstack().sort_values().drop_duplicates() 
    corr_df = pd.DataFrame(corr_df, columns=["corr"])
    corr_df.index.names = ['user_id_1', 'user_id_2']
    corr_df = corr_df.reset_index()
    top_users=corr_df[(corr_df["user_id_1"] == random_user) & (corr_df["corr"] >= 0.50)][["user_id_2","corr"]].reset_index(drop=True)
    top_users = top_users.sort_values(by='corr', ascending=False)
    top_users.rename(columns={"user_id_2": "userId"}, inplace=True)
    top_users=top_users[top_users["userId"]!=random_user]
    top_users_ratings = top_users.merge(df_R[["userId", "movieId", "rating"]], how='inner')
    top_users_ratings['weighted_rating'] = top_users_ratings['corr'] * top_users_ratings['rating']
    recommendation_df=top_users_ratings.groupby('movieId').agg({"weighted_rating": "mean"})
    recommendation_df = recommendation_df.reset_index()
    recommendation_df[recommendation_df["weighted_rating"] > 2]
    movies_to_be_recommend = recommendation_df[recommendation_df["weighted_rating"] > 2].\
sort_values("weighted_rating", ascending=False)

    print(movies_to_be_recommend.merge(df_M[["movieId", "title"]])["title"][:10])
    result=list(movies_to_be_recommend.merge(df_M[["movieId", "title"]])["title"][:10])
    
    return jsonify({"result": result})
if __name__ == '__main__':
    app.run(debug=True)