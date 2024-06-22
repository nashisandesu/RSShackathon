import openai_api, other
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import random
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# AWS RDSの接続情報を設定
load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ユーザーモデルを定義
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# キャラクターとその特徴を定義
characters = [
    {
        'name': 'ピカチュウ',
        'features': {
            '実在': False,
            '有名': True,
            '男性': False
        }
    },
    {
        'name': '安倍晋三',
        'features': {
            '実在': True,
            '有名': True,
            '男性': True
        }
    }
    # 他のキャラクターも追加
]

# 質問と特徴の対応を定義
questions = [
    "あなたのキャラクターは実在しますか？",
    "あなたのキャラクターは有名ですか？",
    "あなたのキャラクターは男性ですか？"
]

features_map = {
    "あなたのキャラクターは実在しますか？": '実在',
    "あなたのキャラクターは有名ですか？": '有名',
    "あなたのキャラクターは男性ですか？": '男性'
}

# 推論エンジンを実装
def infer_character(answers):
    possible_characters = characters
    
    for question, answer in zip(questions, answers):
        feature = features_map[question]
        if answer == 'はい':
            possible_characters = [char for char in possible_characters if char['features'][feature] is True]
        else:
            possible_characters = [char for char in possible_characters if char['features'][feature] is False]
    
    if len(possible_characters) == 1:
        return possible_characters[0]['name']
    else:
        return "特定のキャラクターを見つけることができませんでした。"

answers = []
qa_history = []
current_idx = 0
answer = None
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/select_mode', methods = ['POST'])
def select_mode():
    global answer
    mode = request.form['mode']
    if mode == 'アキネーター':
        return redirect(url_for('mode_akinator'))
    elif mode == 'ウミガメ':
        answer = random.choice(other.simple)
        return redirect(url_for('mode_umigame'))
    else:
        return redirect(url_for('index'))

@app.route('/mode_umigame', methods=['POST', 'GET'])
def mode_umigame():
    global answer, qa_history, current_idx, answer
    if request.method == 'POST':
        # 質問内容
        question = request.form['question']
        # 「はい」か「いいえ」
        for _ in range(10):
            ai_answer = openai_api.answer_ai(answer=answer, question=question,tem=0.5)["answer"]
            if ai_answer == 'Yes':
                yn_answer = 'Yes'
                break
            elif ai_answer == 'No':
                yn_answer = 'No'
                break
            else:
                continue
        else:
            exit()

        answers.append(yn_answer)
        qa_history.append((question, yn_answer))
        current_idx += 1
        return render_template('mode_umigame.html', qa_history=qa_history)
    else:
        return render_template('mode_umigame.html', qa_history=qa_history)
    
@app.route('/mode_umigame_answer', methods=['POST', 'GET'])
def mode_umigame_answer():
    global answer
    return render_template('mode_umigame_answer.html', elements = other.simple, qa_history = qa_history)

def get_image_path(symbol):
    png_path = os.path.join(app.static_folder, f'elements/{symbol}.png')
    jpg_path = os.path.join(app.static_folder, f'elements/{symbol}.jpg')

    if os.path.exists(png_path):
        image_path = url_for('static', filename=f'elements/{symbol}.png')
    elif os.path.exists(jpg_path):
        image_path = url_for('static', filename=f'elements/{symbol}.jpg')
    else:
        image_path = None
    return image_path

@app.route('/result', methods=['POST', 'GET'])
def result():
    global answer
    user_answer_name = request.form['user_answer_name']
    image_path = get_image_path(answer[1])
    if answer[0] == user_answer_name:
        return render_template('result.html', judge=True, user_answer = user_answer_name, true_answer = answer[0], qa_history = qa_history, image_path = image_path)
    else:
        return render_template('result.html', judge=False, user_answer = user_answer_name, true_answer = answer[0], qa_history = qa_history, image_path = image_path)

@app.route('/reset')
@login_required
def reset():
    global answers, current_idx, qa_history, answer
    answers = []
    current_idx = 0
    qa_history = []
    answer = None
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        user = User.query.filter_by(name=name).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        if not name or not password:
            return "name and password are required"
        # ユーザーが既に存在するか確認
        existing_user = User.query.filter_by(name=name).first()
        if existing_user:
            return "User already exists"
        # 新しいユーザーを作成
        new_user = User(name=name, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    if os.getenv('DOCKER'):
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        app.run(debug=True, port = 5001)