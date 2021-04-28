from flask import Flask, abort, request, jsonify, g, url_for
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import uuid
import os
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from datetime import datetime
import json
app = Flask(__name__)

es = Elasticsearch(hosts="127.0.0.1")

ES_INDEX = "mytest"
ES_DOC_TYPE = "test"

PAGE_RECORD = 10

db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    auth_key = db.Column(db.String(128))

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

def authorize(f):
    @wraps(f)
    def decorated_function(*args, **kws):

            if "Authorization" not in request.headers:
                abort(401)

            data = request.headers["Authorization"].replace("Bearer ", '')

            # if not request.is_json:
            #     abort(401)
                
            # data = request.json

            # if not data.get("key"):
            #     abort(401)


            db_data = User.query.get_or_404(ident=1)
            if not data == db_data.auth_key:
                abort(401)

            return f(*args, **kws)            
    return decorated_function


@app.route('/api/search', methods=['GET'])
@authorize
def es_search_data():
    body = {
        "query":{
            "bool": {
                "must": [],
                "filter": [],
                "should": [],
                "must_not": []
              }
            
        },
        "sort": [
            {"created_date" : "desc"}
        ]
    }

    request_json = request.json
    if request_json == None:
        response = {}
        response["error_msg"] = "pass the data having content-type: application/json"

        return jsonify(response)

    from_date = request_json.get("from_date")
    to_date = request_json.get("to_date")
    sort_by = request_json.get("sort_by")

    # Sorting data according to create date, by default it will sort in descending order
    if sort_by and sort_by == "asc":
        body["sort"][0]["created_date"] = "asc"
        

    try:
        from_date = datetime.strptime(from_date, "%Y-%m-%d")
    except (ValueError,TypeError):
        from_date = ""

        # response = {}
        # response["error_msg"] = "invalid from_date"

        # return jsonify(response)

    try:
        to_date = datetime.strptime(to_date, "%Y-%m-%d")
    except (ValueError,TypeError):
        to_date = ""

        # response = {}
        # response["error_msg"] = "invalid to_date"

        # return jsonify(response)

    # Date Range Search
    if from_date and to_date:
        body["query"]["bool"]["filter"].append({
                                        "range": {
                                            "created_date": {
                                            "gte": f"{from_date.date()}",
                                            "lte": f"{to_date.date()}",
                                            "format": "yyyy-MM-dd"
                                            }
                                        }
                                    })

    # For pagination
    if request_json.get('page'):
        try:
            page = int(request_json["page"])
        except ValueError:
            page = 1
    else:
        page = 1

    keyword = request_json.get("keyword")
    search = request_json.get("search")

    # For Keyword filed query
    if keyword:
        body["query"]["bool"]["filter"].append({
                                        "bool": {
                                            "should": [
                                            {
                                                "match": {
                                                "keyword.keyword": keyword
                                                }
                                            }
                                            ],
                                            "minimum_should_match": 1
                                        }
                                    })

    # For Overall data search
    if search:
        # body["query"]["bool"]["filter"].append({
        #                             "multi_match": {
        #                             "type": "best_fields",
        #                             "query": search
        #                             }
        #                         })

        body["query"]["bool"]["must"].append({
                                                "query_string": {
                                                    "query": search,
                                                    "analyze_wildcard": True
                                                }
                                            })


    
    if page > 1:
        body["from"] = (page - 1) * PAGE_RECORD

    if page < 1:
        page = 1

    if not body["query"]:
        body["query"]["match_all"] = {}

    es_response = es.search(index=ES_INDEX, doc_type=ES_DOC_TYPE, body=body)

    response = {}
    response["data"] = es_response['hits']['hits']
    # print(json.dumps(es_response))
    total_record = es_response["hits"]['total']
    total_page = total_record/PAGE_RECORD

    if not total_page.is_integer():
        total_page += 1

    response["total_pages"] = int(total_page)
    response["page"] = page

    return jsonify(response)


@app.route('/api/data/<id>', methods=['GET'])
@authorize
def get_es_data(id):
    try:
        response = es.get(index=ES_INDEX, doc_type=ES_DOC_TYPE, id=id)
    except NotFoundError:
        response = {}
        response["_source"] = {}
    return jsonify(response['_source'])


#for creating new user
# @app.route('/api/users', methods=['POST'])
# def new_user():
#     username = request.json.get('username')
#     password = request.json.get('password')
#     auth_key = str(uuid.uuid4())
#     if username is None or password is None:
#         abort(400)    # missing arguments
#     if User.query.filter_by(username=username).first() is not None:
#         abort(400)    # existing user
#     user = User(username=username,auth_key=auth_key)
#     user.hash_password(password)
#     db.session.add(user)
#     db.session.commit()
#     return (jsonify({'username': user.username, "auth_key": auth_key}), 201)

if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()

    app.run(debug=True)
