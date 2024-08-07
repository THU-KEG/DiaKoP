from fastchat.conversation import Conversation, get_conv_template
from fastchat.model.model_adapter import BaseModelAdapter

class Llama3Adapter(BaseModelAdapter):
    """The model adapter for Llama-3 (e.g., meta-llama/Meta-Llama-3-8B-Instruct)"""

    def match(self, model_path: str):
        return "llama-3" in model_path.lower()

    def load_model(self, model_path: str, from_pretrained_kwargs: dict):
        model, tokenizer = super().load_model(model_path, from_pretrained_kwargs)
        model.config.eos_token_id = tokenizer.eos_token_id
        model.config.pad_token_id = tokenizer.pad_token_id
        return model, tokenizer

    def get_default_conv_template(self, model_path: str) -> Conversation:
        return get_conv_template("llama-3")