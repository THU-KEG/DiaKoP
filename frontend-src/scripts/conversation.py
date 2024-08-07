
from fastchat.conversation import Conversation, SeparatorStyle, register_conv_template
from typing import List
from enum import auto

class SeparatorStyle_Custom():
    LLAMA3 = auto()

class Conversation_Custom(Conversation):
    """
    Inherit Conversation base class. Added backend_messages list for action prediction.
    """
    # backend_messages: List[List[str]] = ()
    def __init__(self, name,
                        system_template = "{system_message}",
                        system_message = "",
                        roles = ("USER", "ASSISTANT"),
                        messages = (),
                        backend_messages = (),
                        short_answer_messages = (),
                        offset = 0,
                        sep_style = SeparatorStyle.ADD_COLON_SINGLE,
                        sep = "\n",
                        sep2 = None,
                        stop_str = None,
                        stop_token_ids= None):
        super().__init__(   
                        name=name,
                        system_template=system_template,
                        system_message=system_message,
                        messages=messages,
                        offset=offset,
                        roles=roles,
                        sep_style=sep_style,
                        sep=sep,
                        sep2=sep2,
                        stop_str=stop_str,
                        stop_token_ids=stop_token_ids)

        self.backend_messages = backend_messages
        self.short_answer_messages = short_answer_messages
        self.agent_thought = ""

    def append_backend_message(self, role: str, message: str):
        """Append a new backend messages."""
        self.backend_messages.append([role, message])

    def append_short_answer_message(self, role: str, message: str):
        """Append a new short answer messages."""
        self.short_answer_messages.append([role, message])
    
    def update_last_backend_messages(self, message: str):
        """Update the last output for backend.

        The last message is typically set to be None when constructing the prompt,
        so we need to update it in-place after getting the response from a model.
        """
        self.backend_messages[-1][1] = message 
    
    def update_last_short_answer_messages(self, message: str):
        """Update the last output for short answer message chain.

        The last message is typically set to be None when constructing the prompt,
        so we need to update it in-place after getting the response from a model.
        """
        self.short_answer_messages[-1][1] = message 

    def get_custom_prompt(self, messages, system_message="") -> str:
        """Format message with chat template of the model"""
        system_prompt = self.system_template.format(system_message=system_message)

        if self.sep_style == SeparatorStyle.LLAMA2:
            seps = [self.sep, self.sep2]
            if system_message:
                ret = system_prompt
            else:
                ret = "[INST] "
            for i, (role, message) in enumerate(messages):
                tag = self.roles[i % 2]
                if message:
                    if i == 0:
                        ret += message + " "
                    else:
                        ret += tag + " " + message + seps[i % 2]
                else:
                    ret += tag
            return ret

        elif self.sep_style == SeparatorStyle_Custom.LLAMA3:
            ret = "<|begin_of_text|>"
            if self.system_message:
                ret += system_prompt
            else:
                ret += ""
            for i, (role, message) in enumerate(messages):
                if message:
                    ret += f"<|start_header_id|>{role}<|end_header_id|>\n\n"
                    ret += f"{message.strip()}<|eot_id|>"
                else:
                    ret += f"<|start_header_id|>{role}<|end_header_id|>\n\n"
            return ret

        else:
            raise ValueError(f"Invalid style: {self.sep_style}")
        
    def get_backend_prompt(self) -> str:
        """Get the backend prompt for action decision."""

        ret = self.get_custom_prompt(messages=self.backend_messages, system_message=self.system_message)
        
        return ret
    
    def get_one_time_prompt(self, message, system_message="") -> str:
        """Format message with chat template of the model"""
        
        messages = [[self.roles[0], message], [self.roles[1], None]]
        ret = self.get_custom_prompt(messages=messages, system_message=system_message)
        
        return ret

    def get_short_answer_prompt(self, system_message=None) -> str:
        """Get the prompt with short answer chat history chain"""

        if system_message is not None:
            ret = self.get_custom_prompt(messages=self.short_answer_messages, system_message=system_message)
        else:
            ret = self.get_custom_prompt(messages=self.short_answer_messages, system_message=self.system_message)
        
        return ret
        
    def get_agent_thought(self):
        agent_thought_box = f"""<div class="agent-thought-container">
<div class="agent-thought-box">
    <details open>
        <!-- <summary><span class="spinner"></span> Thought...</summary> -->
        <summary class="foldable-summary">DiaKoP's thought</summary>
        <div class="content">
{self.agent_thought}
        </div>
    </details>
</div>
</div>
        """

        return agent_thought_box
        
    def copy(self):
        return Conversation_Custom(
            name=self.name,
            system_template=self.system_template,
            system_message=self.system_message,
            roles=self.roles,
            messages=[[x, y] for x, y in self.messages],
            backend_messages=[[x, y] for x, y in self.backend_messages],
            short_answer_messages=[[x, y] for x, y in self.short_answer_messages],
            offset=self.offset,
            sep_style=self.sep_style,
            sep=self.sep,
            sep2=self.sep2,
            stop_str=self.stop_str,
            stop_token_ids=self.stop_token_ids,
        )

class Conversation_ChatGLMPRO(Conversation_Custom):  # create a subclass

    def to_chatglm_pro_api_messages(self):
        """Convert the conversation to ChatGLM chat completion format."""
        ret = []

        if len(self.system_message) > 0:
            ret.append({"role": "system", "content": self.system_message})

        for i, (_, msg) in enumerate(self.messages[self.offset :]):
            if i % 2 == 0:
                ret.append({"role": "user", "content": msg})
            else:
                if msg is not None:
                    ret.append({"role": "assistant", "content": msg})
        return ret
    
    def copy(self):
        return Conversation_ChatGLMPRO(
            name=self.name,
            system_template=self.system_template,
            system_message=self.system_message,
            roles=self.roles,
            messages=[[x, y] for x, y in self.messages],
            backend_messages=[[x, y] for x, y in self.backend_messages],
            short_answer_messages=[[x, y] for x, y in self.short_answer_messages],
            offset=self.offset,
            sep_style=self.sep_style,
            sep=self.sep,
            sep2=self.sep2,
            stop_str=self.stop_str,
            stop_token_ids=self.stop_token_ids,
        )

register_conv_template(
    Conversation_Custom(
        name="llama-3",
        system_template="<|start_header_id|>system<|end_header_id|>\n\n{system_message}<|eot_id|>",
        roles=("user", "assistant"),
        sep_style=SeparatorStyle_Custom.LLAMA3,
        sep="",
        stop_str="<|eot_id|>",
        stop_token_ids=[128001, 128009],
    )
)

if __name__ == "__main__":
    from fastchat.conversation import get_conv_template

    print("-- ChatGPT template --")
    conv = get_conv_template("chatgpt")
    conv.append_message(conv.roles[0], "Hello!")
    conv.append_message(conv.roles[1], "Hi!")
    conv.append_message(conv.roles[0], "How are you?")
    conv.append_message(conv.roles[1], None)
    print(conv.to_openai_api_messages())

    print("\n")

    print("-- ChatGLM Pro template --")
    conv_glm = Conversation_ChatGLMPRO(
        name="chatglm-pro",
        roles=("user", "assistant"),
        sep_style=None,
        sep=None,
    ).copy()

    conv_glm.append_message(conv_glm.roles[0], "Hello!")
    conv_glm.append_message(conv_glm.roles[1], "Hi!")
    conv_glm.append_message(conv_glm.roles[0], "How are you?")
    conv_glm.append_message(conv_glm.roles[1], None)
    print(conv_glm.to_chatglm_pro_api_messages())