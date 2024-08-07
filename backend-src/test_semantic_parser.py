import requests

def semantic_parsing_api(question):
    url = "http://localhost:6061/predict"

    payload = {'question': question}
    files=[

    ]
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    return response.json()['program']

question = 'In which city is Tsinghua University located at?'
program = semantic_parsing_api(question)
print(program)