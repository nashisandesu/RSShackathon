from flask import Flask, render_template, request, redirect, url_for, session
import os
import openai_api, other
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)

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
def index():
    print('index')
    return render_template('index.html')
    # select_mode = []
    # session['possible_characters'] = characters[:]
    # if len(answers) < len(questions):
    #     question = questions[len(answers)]
    #     # return render_template('index.html', question=question)
    #     return render_template('index.html', question=question, qa_history=qa_history)
    # else:
    #     return redirect(url_for('result'))

@app.route('/select_mode', methods = ['POST'])
def select_mode():
    global answer
    print('select_mode')
    mode = request.form['mode']
    if mode == 'アキネーター':
        # answer = random.choice(other.simple)
        return redirect(url_for('mode_akinator'))
    elif mode == 'ウミガメ':
        answer = random.choice(other.simple)
        return redirect(url_for('mode_umigame'))
        # return redirect(url_for('result'))
    else:
        return redirect(url_for('index'))

@app.route('/mode_umigame', methods=['POST', 'GET'])
def mode_umigame():
    global answer, qa_history, current_idx, answer
    print('test')
    
    if request.method == 'POST':
        # 質問内容
        question = request.form['question']
        # 「はい」か「いいえ」
        while True:
            ai_answer = openai_api.answer_ai(answer=answer, question=question)["answer"]
            if ai_answer == 'Yes':
                yn_answer = 'Yes'
                break
            elif ai_answer == 'No':
                yn_answer = 'No'
                break
            else:
                continue

        answers.append(yn_answer)
        qa_history.append((question, yn_answer))
        current_idx += 1
        
        if len(answers) >= 3:
            return redirect(url_for('result'))
        else:
            return render_template('mode_umigame.html', qa_history=qa_history)
    else:
        return render_template('mode_umigame.html', qa_history=qa_history)

@app.route('/result')
def result():
    character = infer_character(answers)
    return render_template('result.html', character=character, qa_history = qa_history)

@app.route('/reset')
def reset():
    global answers, current_idx, qa_history, answer
    answers = []
    current_idx = 0
    qa_history = []
    answer = None
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5002)
