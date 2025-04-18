import datetime
from datetime import datetime
import random

import bcrypt
import pymongo
from flask_login import UserMixin

from Utilities.movies import Movies

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["WatchWise"]

users_collection = db["users"]  # For user_id generation

moviesObj = Movies()
class User(UserMixin):
    def __init__(self, user_id, password):
        self.id = user_id  # Flask-Login requires .id
        self.password = password

    @staticmethod
    def hashPassword(password):
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed_password

    @staticmethod
    def get(user_id):
        login_collection = db["login"]
        user_data = login_collection.find_one({"user_id": user_id})
        if user_data:
            return User(user_data["user_id"], user_data["password"])
        return None

    @staticmethod
    def get_user(email):
        login_collection = db["login"]
        user_data = login_collection.find_one({"email": email})

        if user_data:
            return User(user_data["user_id"], user_data["password"])
        return None

    def verify_password(self, enteredPassword):
        if isinstance(self.password, str):
            stored_hash = self.password.encode("utf-8")
        else:
            stored_hash = self.password

        if bcrypt.checkpw(enteredPassword.encode("utf-8"), stored_hash):
            print("Password matches!")
            return True
        else:
            print("Incorrect password!")
            return False

    @staticmethod
    def is_user_id_exists(user_id):
        return users_collection.find_one({"user_id": user_id}) is not None

    @staticmethod
    def generate_user_id():
        while True:
            new_id = str(random.randint(100000, 2999999))
            if not User.is_user_id_exists(new_id):  # Check uniqueness in MongoDB
                return new_id

    @staticmethod
    def register_user(email, password, name, bio):
        user_id = User.generate_user_id()
        hashed_pwd = User.hashPassword(password)
        login_collection = db["login"]
        user_collection = db["users"]
        if login_collection.find_one({"email": email}):
            print("User already exists")
            return False
        login_data = {"user_id": user_id, "password": hashed_pwd, "email": email}

        current_date = datetime.today().date().isoformat()
        user_data = {
            "user_id": user_id,
            "name": name,
            "bio": bio,
            "created_at": current_date,
            "watch_history": [],
        }
        try:
            login_collection.insert_one(login_data)
            user_collection.insert_one(user_data)
            return True
        except:
            print("Error occurred in insertion")
            return False
        
    def removeFromWatchList(self, showid):
        remove_query = {"user_id": self.id}
        remove_update = {"$pull": {"watchlist": showid}}
        users_collection.update_one(remove_query, remove_update)

    def addRating(self, showid, rating):
        ratings = db["ratings"]

        ratings.insert_one({"User_ID": self.id, "Rating": rating, "show_id": showid})
        print("Added Rating")

        # Add the show to the watch history
        filter_query = {"user_id": self.id}
        update_query = {
            "$push": {"watch_history": {"show_id": showid, "rating": rating}}
        }
        users_collection.update_one(filter_query, update_query)
        
        self.removeFromWatchList(showid)
        
    def addToWatchlist(self, showid):
        filter_query = {"user_id": self.id}
        update_query = {"$push": {"watchlist": showid}}
        users_collection.update_one(filter_query, update_query)
        
    def fetchWatchList(self):
        filter_query = {"user_id": str(self.id)}
        projection = {"watchlist": 1, "_id": 0}  # Fetch only the 'watchlist' field

        user_data = users_collection.find_one(filter_query, projection)

        if user_data and "watchlist" in user_data:
            # print(user_data["watchlist"])
            
            data = moviesObj.fetch_details(user_data["watchlist"], user_id = self.id)
            return data

        return []
    
    def fetchHistory(self):
        filter_query = {"user_id": str(self.id)}
        projection = {"watch_history": 1, "_id": 0}  # Fetch only the 'watch_history' field

        user_data = users_collection.find_one(filter_query, projection)

        if user_data and "watch_history" in user_data:
            print(user_data["watch_history"])
            show_ids = [show.get('show_id') for show in user_data["watch_history"]]
            
            data = moviesObj.fetch_details(show_ids, user_id = self.id)
            return data

        return []