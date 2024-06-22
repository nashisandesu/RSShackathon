from flask import Flask, render_template, request, redirect, url_for, session
import os
import openai_api, other
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)

answers = []
qa_history = []
current_idx = 0
answer = None
@app.route('/')
def index():
    print('index')
    return render_template('index.html')

@app.route('/select_mode', methods = ['POST'])
def select_mode():
    global answer
    print('select_mode')
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
        return render_template('mode_umigame.html', qa_history=qa_history)
    else:
        return render_template('mode_umigame.html', qa_history=qa_history)
    
@app.route('/mode_umigame_answer', methods=['POST', 'GET'])
def mode_umigame_answer():
    global answer
    return render_template('mode_umigame_answer.html', elements = other.simple, qa_history = qa_history)

@app.route('/result', methods=['POST', 'GET'])
def result():
    global answer
    user_answer_name = request.form['user_answer_name']
    if answer[0] == user_answer_name:
        print('Yes')
        return render_template('result.html', comment="正解！おめでとう！", user_answer = user_answer_name, true_answer = answer[0])
    else:
        return render_template('result.html', comment="残念！答えと違うよ！", user_answer = user_answer_name, true_answer = answer[0])

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
