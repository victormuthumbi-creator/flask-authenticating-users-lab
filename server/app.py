#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User, ArticlesSchema, UserSchema

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

class ClearSession(Resource):

    def delete(self):
    
        session['page_views'] = None
        session['user_id'] = None

        return {}, 204

class Login(Resource):
    """POST /login: log a user in by username and store their id in the session."""

    def post(self):
        # Read the username from the JSON body (empty dict if body is missing)
        username = (request.get_json(silent=True) or {}).get('username')

        user = User.query.filter(User.username == username).first()

        # Challenge: respond with 401 if no user matches the username
        if not user:
            return {'error': 'Invalid username'}, 401

        # Remember the user across requests via the signed session cookie
        session['user_id'] = user.id

        return UserSchema().dump(user), 200

class Logout(Resource):
    """DELETE /logout: remove the user's id from the session."""

    def delete(self):
        session['user_id'] = None

        return {}, 204

class CheckSession(Resource):
    """GET /check_session: return the logged-in user, or 401 if nobody is logged in."""

    def get(self):
        user_id = session.get('user_id')

        if user_id:
            user = User.query.filter(User.id == user_id).first()
            if user:
                return UserSchema().dump(user), 200

        return {}, 401

class IndexArticle(Resource):
    
    def get(self):
        articles = [ArticlesSchema().dump(article) for article in Article.query.all()]
        return articles, 200

class ShowArticle(Resource):

    def get(self, id):
        session['page_views'] = 0 if not session.get('page_views') else session.get('page_views')
        session['page_views'] += 1

        if session['page_views'] <= 3:

            article = Article.query.filter(Article.id == id).first()
            article_json = ArticlesSchema().dump(article)

            return make_response(article_json, 200)

        return {'message': 'Maximum pageview limit reached'}, 401

api.add_resource(ClearSession, '/clear')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
