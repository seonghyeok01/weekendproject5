import hashlib
from datetime import datetime, timedelta

from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
import jwt


app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client.dbStock
SECRET_KEY='sparta'

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/article', methods=['POST'])
def save_post():
    title = request.form.get('title')
    content = request.form.get('content')
    article_count = db.article.count()
    if article_count == 0:
        max_value = 1
    else:
        max_value = db.article.find_one(sort=[("idx", -1)])['idx'] + 1

    post = {
        'idx': max_value,
        'title': title,
        'content': content,
        'read_count': 0,
        'reg_date': datetime.now()
    }
    db.article.insert_one(post)
    return {"result": "success"}


@app.route('/articles', methods=['GET'])
def get_posts():
    order = request.args.get('order')
    per_page = request.args.get('perPage')
    cur_page = request.args.get('curPage')
    search_title = request.args.get('searchTitle')
    search_condition = {}
    if search_title is not None:
        search_condition = {"title": {"$regex": search_title}}

    limit = int(per_page)
    skip = limit * (int(cur_page) - 1)
    total_count = db.article.find(search_condition).count()
    total_page = int(total_count / limit) + (1 if total_count % limit > 0 else 0)

    if order == "desc":
        articles = list(db.article.find(search_condition, {'_id': False})
                        .sort([("read_count", -1)]).skip(skip).limit(limit))
    else:
        articles = list(db.article.find(search_condition, {'_id': False})
                        .sort([("reg_date", -1)]).skip(skip).limit(limit))

    for a in articles:
        a['reg_date'] = a['reg_date'].strftime('%Y.%m.%d %H:%M:%S')

    paging_info = {
        "totalCount": total_count,
        "totalPage": total_page,
        "perPage": per_page,
        "curPage": cur_page,
        "searchTitle": search_title
    }

    return jsonify({"articles": articles, "pagingInfo": paging_info})


@app.route('/article', methods=['DELETE'])
def delete_post():
    idx = request.args.get('idx')
    db.article.delete_one({'idx': int(idx)})
    return {"result": "success"}


@app.route('/article', methods=['GET'])
def get_post():
    idx = request.args['idx']
    article = db.article.find_one({'idx': int(idx)}, {'_id': False})
    return jsonify({"article": article})


@app.route('/article', methods=['PUT'])
def update_post():
    idx = request.form.get('idx')
    title = request.form.get('title')
    content = request.form.get('content')
    db.article.update_one({'idx': int(idx)}, {'$set': {'title': title, 'content': content}})
    return {"result": "success"}


@app.route('/article/<idx>', methods=['PUT'])
def update_read_count(idx):
    db.article.update_one({'idx': int(idx)}, {'$inc': {'read_count': 1}})
    article = db.article.find_one({'idx': int(idx)}, {'_id': False})
    return jsonify({"article": article})


@app.route("/sign-up", methods=["POST"])
def sign_up():
    username=request.form ['user_id']
    user_password=request.form['user_password']
    password_hash = hashlib.sha256(user_password.encode('utf-8')).hexdigest()

    doc = {
        'username' : username,
        'password' : password_hash
    }

    db.users.insert_one(doc)
    return jsonify({'result' : 'success'})


@app.route("/sign-in", methods=["POST"])
def sign_in(jwt=None):
    username=request.form ['user_id']
    password=request.form['user_password']

    pw_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username' : username, 'password' : pw_hash})
    print(result)
    if result is not None :
        payload = {
            'id' : username,
            'exp' : datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        print(payload)
        token= jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result' : 'success', 'token' : token})
    # 찾지 못하면
    else :
        return jsonify({'result' : 'fail', 'msg' : '아이디/비밀번호가 일치하지 않습니다.'})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)