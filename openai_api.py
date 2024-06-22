import os
import openai
import json

# APIキーの設定
openai.api_key = os.environ["OPENAI_API_KEY"]

def answer_ai(answer, question, res_format="json_object",tem = 0.5):
    prompt = """You are a helpful assistant designed to output JSON.Include questions and their answers in the content. For example, {
    "question": "Is an apple red?",
    "answer": "Yes"
    }
    Whatever the question is, the answer must always output 'Yes' or 'No'
    """
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": answer[0] + answer[1] + "について、" + question}
    ]
    response = openai.chat.completions.create(
    temperature = tem,
    model = "gpt-4o",
    messages = messages,
    response_format = {"type": res_format}
    )
    res_json = json.loads(response.choices[0].message.content)

    return res_json

if __name__ == '__main__':  
    # メッセージのリストを設定
    prompt = """You are a helpful assistant designed to output JSON.Include questions and their answers in the content. For example, {
    "question": "Is an apple red?",
    "answer": "Yes"
    }"""
    question = "Is hydrogen a transition element?"
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question}
    ]
    print(answer_ai(messages).choices[0].message.content)