import uuid

from fastchat.conversation import SeparatorStyle
from fastchat.model.model_adapter import get_conversation_template
# from fastchat.serve.api_provider import (
#     init_palm_chat,
# )
from conversation import Conversation_ChatGLMPRO, Conversation_Custom, SeparatorStyle_Custom
from prompts import get_system_prompt_v5


class State:
    def __init__(self, model_name):
        if model_name == 'glm-3-turbo':
            self.conv = Conversation_ChatGLMPRO(
                            name="chatglm-pro",
                            roles=("user", "assistant"),
                            sep_style=None,
                            sep=None,
                        ).copy()
            system_message = """You are helpful assistant, you should always provide your response in English."""
            self.conv.set_system_message(system_message)
            
        elif "diakop" in model_name.lower():
            # If use custom conv template
            self.conv = Conversation_Custom(
                        name="llama-3",
                        system_template="<|start_header_id|>system<|end_header_id|>\n\n{system_message}<|eot_id|>",
                        roles=("user", "assistant"),
                        sep_style=SeparatorStyle_Custom.LLAMA3,
                        sep="",
                        stop_str="<|eot_id|>",
                        stop_token_ids=[128001, 128009],
                    ).copy()

            system_message = get_system_prompt_v5()
            self.conv.set_system_message(system_message)
        else:
            self.conv = get_conversation_template(model_name)

        self.conv_id = uuid.uuid4().hex
        self.skip_next = False
        self.edit_program = False           # edit program
        self.edit_program_viskop = False    # edit program from viskop
        self.program_to_edit = ""
        self.model_name = model_name

        self.token_cnt = {
            "casual_or_factual": 0,
            "casual": 0,
            "ans_from_kb": 0,
            "ans_from_hist": 0,
            "ans_from_llm": 0,
            "ques_rewrite": 0,
            "clarify": 0,
            "no_answer": 0,
            "edit_program": 0,
            "answer_edit_program": 0,
            "isComplete": 0,
            "needClarify": 0,
            "hasAnswerFromHist": 0,
            "verifyKBAnswer": 0,
        }
    def reset_token_cnt(self):
        for key in self.token_cnt:
            self.token_cnt[key] = 0

    def to_gradio_token_cnt(self, keys):
        txt_out = ""

        n_keys_added = 0
        if isinstance(keys, list):
            for idx, key in enumerate(keys):
                txt_out += f"{key}: {self.token_cnt[key]}"
                n_keys_added += 1
                
                if n_keys_added % 8 == 0:
                    txt_out += "\n"
                elif idx == len(keys) - 1:
                    txt_out += ""
                else:
                    txt_out += " \t| "

        elif isinstance(keys, str):
            txt_out += f"{keys}: {self.token_cnt[keys]}"
            n_keys_added += 1

        return txt_out

    def to_gradio_chatbot(self):
        return self.conv.to_gradio_chatbot()

    def dict(self):
        base = self.conv.dict()
        base.update(
            {
                "conv_id": self.conv_id,
                "model_name": self.model_name,
            }
        )
        return base