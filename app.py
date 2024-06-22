import openai_api, other
from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import random
import os
import time
import threading

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

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    ai_answer = db.Column(db.Boolean, nullable=False)
    ask_id = db.Column(db.Integer, nullable=False)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ask_id = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Numeric(18, 9), nullable=False)
    difficulty_level = db.Column(db.String(100), nullable=False)
    time = db.Column(db.Numeric(18, 9), nullable=False)

class Ask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    real_answer = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

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

def save_ask(user_id, real_answer):
    try:
        with app.app_context():
            db.session.add(Ask(user_id=user_id, real_answer=real_answer))
            db.session.commit()
            print("Ask saved successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Error saving data: {e}")

def save_data(user_id, question, answer, real_answer):
    boolean_answer = True if answer.lower() == 'yes' else False
    try:
        with app.app_context():
            db.session.add(Data(user_id=user_id, question=question, ai_answer=boolean_answer, real_answer=real_answer))
            db.session.commit()
            print("Data saved successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Error saving data: {e}")

def save_score(user_id, start_date, difficulty_level, time):
    session.pop('start_time', None)
    try:
        with app.app_context():
            db.session.add(Data(user_id=user_id, start_date=start_date, difficulty_level=difficulty_level, time=time))
            db.session.commit()
            print("Score saved successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Error saving data: {e}")

answers = []
qa_history = []
current_idx = 0
answer = None
elements_list = []
@app.route('/')
@login_required
def index():
    print('index')

    if 'start_time' not in session:
        session['start_time'] = time.time()
    
    elapsed_time = time.time() - session['start_time'] if 'start_time' in session else 0
    return render_template('index.html')

@app.route('/select_mode', methods = ['POST'])
def select_mode():
    global answer, elements_list
    mode = request.form['mode']
    elements_list = other.all_mode_elements[mode]
    answer = answer = random.choice(elements_list)
    if mode in {'初級', '中級', '上級', '超上級'}:
        return redirect(url_for('mode_umigame'))
    else:
        return redirect(url_for('index'))

@app.route('/mode_umigame', methods=['POST', 'GET'])
def mode_umigame():
    global answer, qa_history, current_idx, answer
    elapsed_time = time.time() - session['start_time']
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

        user_id = session.get('user_id')
        if user_id and yn_answer:
            threading.Thread(target=save_data, args=(user_id, question, yn_answer, answer[0])).start()

        answers.append(yn_answer)
        qa_history.append((question, yn_answer))
        current_idx += 1
        return render_template('mode_umigame.html', qa_history=qa_history, elapsed_time=elapsed_time)
    else:
        return render_template('mode_umigame.html', qa_history=qa_history, elapsed_time=elapsed_time)
    
@app.route('/mode_umigame_answer', methods=['POST', 'GET'])
def mode_umigame_answer():
    global answer, elements_list
    return render_template('mode_umigame_answer.html', elements = elements_list, qa_history = qa_history)

def get_image_path(symbol):
    jpg_path = os.path.join(app.static_folder, f'elementsJPG/{symbol}.jpg')
    if os.path.exists(jpg_path):
        image_path = url_for('static', filename=f'elementsJPG/{symbol}.jpg')
    else:
        image_path = None
    return image_path

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
    elapsed_time = time.time() - session['start_time']
    if answer[0] == user_answer_name:
        user_id = session.get('user_id')
        if user_id:
            threading.Thread(target=save_score, args=(user_id, session['start_time'], "ウミガメ", elapsed_time)).start()
        print('Yes')
        return render_template('result.html', judge=True, user_answer = user_answer_name, true_answer = answer[0], qa_history = qa_history, image_path = image_path, elapsed_time=elapsed_time)
    else:
        return render_template('result.html', judge=False, user_answer = user_answer_name, true_answer = answer[0], qa_history = qa_history, image_path = image_path, elapsed_time=elapsed_time)

@app.route('/reset')
@login_required
def reset():
    global answers, current_idx, qa_history, answer
    answers = []
    current_idx = 0
    qa_history = []
    answer = None
    session.pop('start_time', None)
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        user = User.query.filter_by(name=name).first()
        if user and user.password == password:
            login_user(user)
            session['user_id'] = user.id
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
        login_user(new_user)
        session['user_id'] = user.id

        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    if os.getenv('DOCKER'):
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        app.run(debug=True, port = 5001)