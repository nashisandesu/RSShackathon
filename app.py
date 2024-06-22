from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

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

@app.route('/')
def index():
    if len(answers) < len(questions):
        question = questions[len(answers)]
        return render_template('index.html', question=question)
    else:
        return redirect(url_for('result'))

@app.route('/answer', methods=['POST'])
def answer():
    answer = request.form['answer']
    answers.append(answer)
    
    if len(answers) >= len(questions):
        return redirect(url_for('result'))
    
    return redirect(url_for('index'))

@app.route('/result')
def result():
    character = infer_character(answers)
    return render_template('result.html', character=character)

@app.route('/reset')
def reset():
    global answers
    answers = []
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
