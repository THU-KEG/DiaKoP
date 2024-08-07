import os

from dotenv import load_dotenv
load_dotenv()

from fastchat.utils import build_logger

logger = build_logger("gradio_web_server", "gradio_web_server.log")

def chatglm_pro_api_stream_iter(
    model_name,
    messages,
    temperature,
    top_p,
    api_base=None,
    api_key=None,
):
    from zhipuai import ZhipuAI

    client = ZhipuAI(api_key=os.getenv('CHATGLM_PRO_API_KEY')) # Create .env file and add CHATGLM_PRO_API_KEY

    # Make requests
    gen_params = {
        "model": "glm-3-turbo",
        "prompt": messages,
        "temperature": temperature,
        "top_p": top_p
    }
    logger.info(f"==== request ====\n{gen_params}")

    response = client.chat.completions.create(
        model="glm-3-turbo",  # 填写需要调用的模型名称
        messages=messages,
        stream=True,
        temperature=temperature,
        top_p=top_p,
        )   
    
    for chunk in response:
        data = {
            "text": chunk.choices[0].delta.content,
        }
        yield(data)


def test_chatglm_pro():
    model_name = "glm-3-turbo"
    messages=[
        {"role": "system", "content": "You are helpful assistant, you should always provide your response in English."},
        {"role": "user", "content": "Who are you?"},
    ]
    temperature = 0.95
    top_p = 0.7
    api_base = None
    api_key = os.getenv('CHATGLM_PRO_API_KEY')

    text = ""
    for data in chatglm_pro_api_stream_iter(
        model_name=model_name,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        api_base=api_base,
        api_key=api_key,
    ):
        text += data["text"]
    print(text)

if __name__ == "__main__":
    test_chatglm_pro()