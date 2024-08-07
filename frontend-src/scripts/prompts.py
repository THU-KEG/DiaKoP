def get_system_prompt_v5():
    """
    Format into json response
    """
    system_message = """### Examples 
# Example 1, the user first asks a casual question "Hey, how's it going?"
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question and I think the user is doing a casual greeting, so I should switch to [casual]",
    "chatmode": "[casual]"
} 
```

# Example 2, the user first asks a factual question "When did China join the WTO?"
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question and I think the user is asking the date China join WTO which requires a factual answer, so I should switch to [factual]",
    "chatmode":  "[factual]"
} 
``` 
# Example 2-1, then the user asks a follow-up question "How about Japan?"
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question and I think the user is asking the date Japan join WTO based on the previous context, which requires a factual answer, so I should switch to [factual]",
    "chatmode": "[factual]"
} 
```
# Example 2-2, then the user asks a follow-up question "What are the requirements?"
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question and I think the user is asking for a factual answer about the requirements of joining the WTO based on the previous conversation. Hence, I should switch to [factual] to provide factual answer",
    "chatmode": "[factual]"
}

# Example 3, the user first asks a casual question "Have you tried the new café downtown?"
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question and I think the user is asking my opinion casually, so I should switch to [casual]",
    "chatmode": "[casual]"
} 

# Example 4, the user first asks a factual question, "Which national team does Kylian Mbappé play soccer for?"
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question and I think the user is asking for a factual answer about the national soccer team that Kylian Mbappé played for, so I should switch to [factual]",
    "chatmode": "[factual]"
} 
```
# Example 4-1, then the user asks a follow-up question "place of his birth?"
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question and I think the user is asking the place of birth of Kylian Mbappé based on previous chat history, which requires a factual answer, so I should switch to [factual]",
    "chatmode": "[factual]"
} 
```
# Example 4-2, then the user asks a follow-up question "How many goals did he score for his home country in 2018?
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question and I think the user is asking number of goals Kylian Mbappé scored for his home country in 2018, so I should switch to [factual] to give factual answer",
    "chatmode": "[factual]"
} 
```
# Example 4-3, then the user asks a follow-up question "How about Lionel Messi?"
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question and by referring prior conversation, I think the user is asking number of goals Lionel Messi scored for his home country in 2018, so I should switch to [factual] to give factual answe",
    "chatmode": "[factual]"
} 
```

### Instruction
You are an agent given a task to predict two different chat mode based on user's input because further instruction will be given based on your prediction. The two modes are:

Casual chat: An informal and relaxed conversation that does not require factual answer. Example of casual chat include "Hey, how's it going?", "Have you tried the new café downtown?", and "Do you like vegetables?".
Factual chat: A conversation based on facts that can be retrieved from knowledge graph and focus on sharing accurate and verifiable information. Example of factual chat include "When did China join the WTO?", "What is the higher education institution headquartered in the city whose postal code is 20157?", and "How many film genres are released in a region that has a form of government whose Dewey Decimal Classification is 2--436?".

If you think you should retrieve answer from knowledge graph, switch to factual mode.

You must always respond in JSON format containing `"reasoning"` and `"chatmode"` key-value pairs, where `"reasoning"` is your thought process of why you think you should switch to the `"chatmode"`.
You can only select from [casual] or [factual] as the value for `"chatmode"`.
During reasoning, you should start with "Let's think step by step." First, analyze the original question to determine if it requires a factual answer, then give a reason why you decide on a particular chat mode.
Give only one JSON response at a time! Response such as your monologue, notes or clarification is strictly prohibited, do not respond other than JSON!"""
    return system_message

def get_factual_prompt(user_question, program, parsed_intermediate_result, final_answer):
    prompt = f"""### User's question: {user_question}
### Program: {program}
### Intermediate results: {parsed_intermediate_result}
The program above is your chain-of-thoughts to answer user queries.
The intermediate results are the intermediate result of each function in the program. Note that there might be function got None as intermediate result. In this case, you don't need to explain the intermediate result, but you need to explain the program.
The intermediate results the most reliable factual answer because they are retrieved from knowledge graphs. Hence, do not try to correct the retrived answer.
Give your response according to the structure below. Explain the your chain-of-thoughts with its corresponding intermediate result, in a steps by steps numbered list way, do not use HTML.

Remember, only explain the prgram, do not try to give your opinion on the correctness of the answer.

### Structure
So your question is ... (rephrase user's questions)
My thought process based on the program is ..."""
    
    return prompt

def get_question_rewrite_prompt(context, user_question):
    new_prompt = f"""
Enclose the rewrited question with <rewrite> </rewrite> tokens, as shown in examples below:
# Examples
## Example 1
### Conversation
USER		: Who played Jaime Lannister in Game of Throne?
ASSISTANT	: Nikolaj Coster-Waldau
USER		: What about the dwarf?
### Result
<rewrite> Who played the dwarf in Game of Throne? </rewrite>

## Example 2
### Conversation
USER		: Who played Jaime Lannister in Game of Throne?
ASSISTANT	: Nikolaj Coster-Waldau
USER		: Who played the dwarf in Game of Throne?
ASSISTANT	: Peter Dinklage
USER		: his nationality?
### Result
<rewrite> What is the nationality of Peter Dinklage? </rewrite>

## Example 3
### Conversation
USER		: Which national team does Kylian Mbappé play soccer for?
ASSISTANT	: France football team
USER		: place of his birth?
### Result
<rewrite> What is the place of birth of Kylian Mbappé? </rewrite>
 
## Example 4
### Conversation
USER		: Who is the most popular football player from France?
ASSISTANT	: Kylian Mbappé
USER		: what is the place of his birth?
ASSISTANT	: Paris
USER		: What awards did he achieved in 2001?
### Result
<rewrite> What awards did Kylian Mbappé achieved in 2001? </rewrite>

# Task 
## Instruction
By default, the current question is a follow-up question to the last question in the conversation. Hence you should not merge the context when rewriting current question. Keep the rewrited question as simple as possible.

## Things you should not do
As shown in Example 4, the rewrited question is short and simple. You should not merge into complex sentence such as "What awards did Kylian Mbappé, the player who played for France football team, achieved in 2001?" 

## Conversation{context}USER\t\t: {user_question}
## Result"""
    
    return new_prompt

def get_check_complete_sentence_prompt(user_question):
    prompt = """### Examples 
USER: Hey, how's it going?
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question "Hey, how's it going?" and determine that it is a complete query sentence without ambiguity. Finally, since it's a complete sentence, I should output [yes]",
    "is_complete_question": "[yes]"
} 
```

USER: Have you tried the new café downtown?
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question "Have you tried the new café downtown?" and determine that it is a complete query sentence without ambiguity. Finally, since it's a complete sentence, I should output [yes]",
    "is_complete_question": "[yes]"
} 
```

USER: Which national team does Kylian Mbappé play soccer for?
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question "Which national team does Kylian Mbappé play soccer for?" and determine it is a complete query sentence without ambiguity. Finally, since it's a complete sentence, I should output [yes]",
    "is_complete_question": "[yes]"
} 
```

USER: place of his birth?
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question "place of his birth?" and determine it is both ellipsis and coreference query sentence, a type of incomplete question that refers previous conversation. Finally, since it's both ellipsis and coreference query sentence and not a complete sentence, so I should output [no]",
    "is_complete_question": "[no]"
} 
```

USER: How many goals did he score for his home country in 2018?
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question "How many goals did he score for his home country in 2018?" and determine that it is a coreference query sentence, a type of incomplete question where the word "he" refers previous conversation. Finally, since it's a coreference query sentence and not a complete sentence, so I should output [no]",
    "is_complete_question": "[no]"
} 
```

USER: How about Lionel Messi?
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question "How about Lionel Messi?" and determine that it is an ellipsis and ambiguous without clear context, it is a type of incomplete question that refers prior conversation. Finally, since it's an ellipsis and not a complete sentence, so I should output [no]",
    "is_complete_question": "[no]"
} 
```

USER: When did China join the WTO?
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question "When did China join the WTO?" and determine that it is a complete query sentence without ambiguity. Finally, since it's a complete sentence, so I should output [yes]",
    "is_complete_question":  "[yes]"
} 
``` 

USER: What are the requirements?
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question "What are the requirements?" and determine that it is an ellipsis, a type of incomplete question that refers prior conversation. Finally, since it's an ellipsis and not a complete sentence, so I should output [no]",
    "is_complete_question": "[no]"
} 
```

USER: How about Japan?
```json
{
    "reasoning": "Let's think step by step. First, I analyze the question "How about Japan?" and determine that it is an ellipsis and ambiguous without clear context, it is a type of incomplete question that refers prior conversation. Finally, since it's an ellipsis and not a complete sentence, so I should output [no]",
    "is_complete_question": "[no]"
} 
```

### Instruction
You are an agent given a task to predict whether user's question is a complete query sentence or not.

Complete sentence are sentences with explicit meaning without ambiguity. You should output [yes] if user's question is a complete sentence, examples are:
* "Hey, how's it going?"
* "Do you like vegetables?"
* "When did China join the WTO?"
* "What is the higher education institution headquartered in the city whose postal code is 20157?"

Incomplete sentence are usually follow-up sentences with implicit meaning or exhibit ambiguity. There are two major types of incomplete sentences namely ellipsis and coreference.

Ellipsis sentence is defined as the omission of one or more words that are obviously understood but that must be supplied to make a construction grammatically complete, examples:
* "What are the requirements?" is an ellipsis for "What are the requirements of joining WTO"
* "How about Japan?" is an ellipsis for "When did Japan join WTO?"

Coreference is defined as a linguistic phenomenon where two or more linguistic expressions refer to the same entity in a text, examples:
* "place of his birth?", the word "his" refers "Kylian Mbappé".
* "John went to the store. He bought some groceries" the word "He" refers "John".

Both ellipsis and coreference sentence types are considered as incomplete sentence. You should output [no] in these cases.

You must always respond in JSON format containing `"reasoning"` and `"is_complete_question"` key-value pairs, where `"reasoning"` is your thought process of why you think you should predict `"is_complete_question"`.
You can only select from [yes] or [no] as the value for `"is_complete_question"`.
During reasoning, you should start with "Let's think step by step." First, analyze the original question by repeating the question, then check if the question is a complete sentence or an incomplete sentence (such as ellipsis, or coreference query sentence) that requires context from previous chat history. Finally, give a reason why you decide on a particular chat mode.
It is crucial to identify ellipsis and coreference query sentence because they are incomplete query sentence and requires question rewriting. Failing in identifying an incomplete query sentence will make my semantic parsing in next tasks failed. 
Give only one JSON response at a time! Response such as your monologue, notes or clarification is strictly prohibited, do not respond other than JSON!
The user's question is as shown below after ###Task
"""

    prompt += f"""
### Task
USER: {user_question} """
    
    return prompt

def get_check_need_clarify_prompt(user_question, context):
    prompt = """
# Examples
## Example 1
USER		: how many goal did he score?
```json
{
    "reasoning": "Let's think step by step. The user's question refers to a singular person and the action of scoring goals, but there is no context or subject provided. I need to clarify the subject of the question before providing an answer. ",
    "need_clarify": "[yes]"
}
```

## Example 2
USER		: What is Marvel's most popular movie?
ASSISTANT	: Avengers Endgame holds the title for the highest-grossing Marvel film of all time, both domestically and worldwide
USER		: How about DreamWorks Animation LLC?
```json
{
    "reasoning": "Let's think step by step. Based on the previous chat, the user is asking about the most popular movie from DreamWorks Animation LLC. I have understand the question, so I do not need to clarify anything. ",
    "need_clarify": "[no]"
}
```

## Example 3
USER		: How about London?
```json
{
    "reasoning": "Let's think step by step. The user's question is open-ended and does not contain enough context for me to provide a specific answer. I am not sure what the user trying to ask about London, therefore, I need to clarify what the user wants to know about pizza before providing an answer. ",
    "need_clarify": "[yes]"
}
```

## Example 4
USER		: When did China join WTO?
ASSISTANT	: 2001-12-11
USER		: What is the name of the capital city?
ASSISTANT	: Beijing
USER		: How about Japan?
```json
{
    "reasoning": "Let's think step by step. The user is asking about the Japan, based on the last question, the user is asking the name of the capital city, so I assume the user is asking the capital city of Japan. I have understand the question, so I do not need to clarify anything. ",
    "need_clarify": "[no]"
}
```
"""

    prompt += f"""
# Instruction
Examples above shows when you should or should not clarify with user. Hence, you should only consider section #Conversation as your chat history.
First, analyze if context from chat history in #Conversation is missing for user's question. If context exists, do not clarify with the user by answering "[no]", else answer "[yes]" in the "need_clarify" field.
Give your reasoning and decision in the form of JSON as shown in the examples. During reasoning, analyze each question in the conversation from the user in detail, always starting with "Let's think step by step."
"""
    prompt += f"""
#Conversation{context}USER: {user_question} """
    
    return prompt

def get_clarify_prompt(user_question, context):
    prompt = f"""

### User's question
{user_question}
    
### Context{context}

### Instruction
Based on the context and user's question above, please clarify with user what is the exact question the user is asking.
When guessing what the user is actually asking, do not merge multiple questions into a complex question.
Begin your reply with "Dear user, I would like to clarify with you are you asking..."
End your reply with "Please reenter your question again."
"""

    return prompt

def get_edit_program_prompt(user_question, program_to_edit):
    prompt = """

### Available functions details, note that each function has 2 kinds of inputs: 
1. "functional inputs" are the inputs depends on the output from previous functions
2. "inputs" come from the question. 
{{
    "function": "FindAll",
    "description": "Return all entities in KB",
    "functional inputs": [],
    "inputs: [],
    "outputs": ["Entities"],
}},
{{
    "function": "Find",
    "description": "Return all entities with the given name",
    "functional inputs": [],
    "inputs: ["Entity Name"],
    "outputs": ["Entities"],
}},
{{
    "function": "QueryRelation",
    "description": "Return the relation between two entities",
    "functional inputs": ["Entities", "Entities"],
    "inputs: [],
    "outputs": ["Relation"],
}},
{{
    "function": "FilterConcept", 
    "description": "Find those belonging to the given concept",
    "functional inputs": ["Entities"],
    "inputs: ["Concept"],
    "outputs": ["Entities"],
}},
{{
    "function": "FilterStr",
    "description": "Filter entities with an attribute condition of string type, return entities and corresponding facts",
    "functional inputs": ["Entities"],
    "inputs: ["Attribute Key", "Attribute Value"],
    "outputs": ["Entities", "Facts"],
}},
{{
    "function": "FilterNum",
    "description": "Similar to FilterStr, except that the attribute type is number",
    "functional inputs": ["Entities"],
    "inputs: ["Attribute Key", "Attribute Value", "Operator"],
    "outputs": ["Entities", "Facts"],
}},
{{
    "function": "FilterYear",
    "description": "Similar to FilterStr, except that the attribute type is year",
    "functional inputs": ["Entities"],
    "inputs: ["Attribute Key", "Attribute Value", "Operator"],
    "outputs": ["Entities", "Facts"],
}},
{{
    "function": "FilterDate",
    "description": "Similar to FilterStr, except that the attribute type is date",
    "functional inputs": ["Entities"],
    "inputs: ["Attribute Key", "Attribute Value", "Operator"],
    "outputs": ["Entities", "Facts"],
}},
{{
    "function": "QFilterStr",
    "description": "Filter entities and corresponding facts with a qualifier condition of string type",
    "functional inputs": ["Entities", "Facts"],
    "inputs: ["Qualifier Key", "Qualifier Value"],
    "outputs": ["Entities", "Facts"],
}},
{{
    "function": "QFilterNum",
    "description": "Filter entities and corresponding facts with a qualifier condition of number type", 
    "functional inputs": ["Entities", "Facts"],
    "inputs: ["Qualifier Key", "Qualifier Value", "Operator"],
    "outputs": ["Entities", "Facts"],
}},
{{
    "function": "QFilterYear",
    "description": "Filter entities and corresponding facts with a qualifier condition of year type",
    "functional inputs": ["Entities", "Facts"],
    "inputs: ["Qualifier Key", "Qualifier Value", "Operator"],
    "outputs": ["Entities", "Facts"],
}},
{{
    "function": "QFilterDate",
    "description": "Filter entities and corresponding facts with a qualifier condition of date type",
    "functional inputs": ["Entities", "Facts"],
    "inputs: ["Qualifier Key", "Qualifier Value", "Operator"],
    "outputs": ["Entities", "Facts"],
}},
{{
    "function": "Relate",
    "description": "Find entities that have a specific relation with the given entity",
    "functional inputs": ["Entities"],
    "inputs: ["Relation", "Direction"],
    "outputs": ["Entities", "Facts"],
}},
{{
    "function": "And",
    "description": "Return the intersection of two entity setsy",
    "functional inputs": ["Entities", "Entities"],
    "inputs: [],
    "outputs": ["Entities"],
}},
{{
    "function": "Or",
    "description": " Return the union of two entity sets",
    "functional inputs": ["Entities", "Entities"],
    "inputs: [],
    "outputs": ["Entities"],
}},
{{
    "function": "QueryName",
    "description": "Return the entity name",
    "functional inputs": ["Entities"],
    "inputs: [],
    "outputs": ["string"],
}},
{{
    "function": "Count",
    "description": "Return the number of entities",
    "functional inputs": ["Entities"],
    "inputs: [],
    "outputs": ["number"],
}},
{{
    "function": "QueryAttr",
    "description": "Return the attribute value of the entity", 
    "functional inputs": ["Entities"],
    "inputs: ["Attribute Key"],
    "outputs": ["Value"],
}},
{{
    "function": "QueryAttrUnderCondition",
    "description": "Return the attribute value, whose corresponding fact should satisfy the qualifier condition",
    "functional inputs": ["Entities"],
    "inputs: ["Attribute Key", "Qualifier Key", "Qualifier Value"],
    "outputs": ["Value"],
}},
{{
    "function": "SelectBetween",
    "description": "From the two entities, find the one whose attribute value is greater or less and return its name",
    "functional inputs": ["Entities", "Entities"],
    "inputs: ["Attribute Key", "Operator"],
    "outputs": ["string"],
}},
{{
    "function": "SelectAmong",
    "description": "From the entity set, find the one whose attribute value is the largest or smallest",
    "functional inputs": ["Entities"],
    "inputs: ["Attribute Key", "Operator"],
    "outputs": ["string"],
}},
{{
    "function": "VerifyStr",
    "description": "Return whether the output of QueryAttr or QueryAttrUnderCondition and the given value are equal as string",
    "functional inputs": ["Value"],
    "inputs: ["Target Str"],
    "outputs": ["boolean"],
}},
{{
    "function": "VerifyNum", 
    "description": "Return whether the two numbers satisfy the condition",
    "functional inputs": ["Value"],
    "inputs: ["Target Num", "Operator"],
    "outputs": ["boolean"],
}},
{{
    "function": "VerifyYear",
    "description": " Return whether the two years satisfy the condition", 
    "functional inputs": ["Value"],
    "inputs: ["Target Year", "Operator"],
    "outputs": ["boolean"],
}},
{{
    "function": "VerifyDate",
    "description": " Return whether the two date satisfy the condition",
    "functional inputs": ["Value"],
    "inputs: ["Target Date", "Operator"],
    "outputs": ["boolean"],
}},
{{
    "function": "QueryAttrQualifier",
    "description": "Return the qualifier value of the fact (Entity, Key, Value)",
    "functional inputs": ["Entities"],
    "inputs: ["Attribute Key", "Attribute Value", "Operator"],
    "outputs": ["Qualifier Value"],
}},
{{
    "function": "QueryRelationQualifier",
    "description": "Return the qualifier value of the fact (Entity, Relation, Entity)",
    "functional inputs": ["Entities", "Entities"],
    "inputs: ["Relation", "Qualifier Key"],
    "outputs": ["Qualifier Value"],
}}

### Examples usage
Question: How many Pennsylvania counties have a population greater than 7800 or a population less than 40000000? 
program: [{{'function': 'FindAll', 'dependencies': [], 'inputs': []}}, {{'function': 'FilterNum', 'dependencies': [0], 'inputs': ['population', '7800', '>']}}, {{'function': 'FilterConcept', 'dependencies': [1], 'inputs': ['county of Pennsylvania']}}, {{'function': 'FindAll', 'dependencies': [], 'inputs': []}}, {{'function': 'FilterNum', 'dependencies': [3], 'inputs': ['population', '40000000', '<']}}, {{'function': 'FilterConcept', 'dependencies': [4], 'inputs': ['county of Pennsylvania']}}, {{'function': 'Or', 'dependencies': [2, 5], 'inputs': []}}, {{'function': 'Count', 'dependencies': [6], 'inputs': []}}]

Question: Does My Neighbor Totoro or Hannah Arendt, originally in German, possess the longer run-time?
program: [{{'function': 'Find', 'dependencies': [], 'inputs': ['My Neighbor Totoro']}}, {{'function': 'Find', 'dependencies': [], 'inputs': ['German']}}, {{'function': 'Relate', 'dependencies': [1], 'inputs': ['original language of film or TV show', 'backward']}}, {{'function': 'Find', 'dependencies': [], 'inputs': ['Hannah Arendt']}}, {{'function': 'And', 'dependencies': [2, 3], 'inputs': []}}, {{'function': 'SelectBetween', 'dependencies': [0, 4], 'inputs': ['duration', 'greater']}}]

### User's instruction
{}

### Current program
{}

### Instruction
Your task is to edit the current program based on user's instruction. You can only use the available functions above and their details to help you edit the program. Do not fake a function that does not exist.
Give response in valid JSON format with only two keys "explanation" and "new_program", as shown below:
{{
    "explanation": <your explanation on what have you changed>,
    "new_program": <the editied program>
}}

Only one JSON response as shown above. Response such as your monologue, notes or clarification is strictly prohibited!

### Response
""" 
    return prompt.format(user_question, program_to_edit)

def get_exec_program_prompt(new_program, explanation, parsed_intermediate_result, final_answer):
    prompt = f"""### Explanation: 
{explanation}

### New program: 
{new_program}

### Intermediate results: 
{parsed_intermediate_result}

The program above is your chain-of-thoughts to answer user queries.
The intermediate results are the intermediate result of each function in the program. Note that there might be function got None as intermediate result. In this case, you don't need to explain the intermediate result, but you need to explain the program.
The intermediate results the most reliable factual answer because they are retrieved from knowledge graphs. Hence, do not try to correct the retrived answer.

Before this, you have given the task to edit the program based on user input.
Now, give your response according to the structure below. First tell the user what have you changed, then explain the your chain-of-thoughts with its corresponding intermediate result, in a steps by steps numbered list way, do not use HTML. Finally, tell the user the final answer.

So I have edited the program to ... 
My thought process based on the program is ...
The final answer to your question is {final_answer}. 

### Response
"""
    
    return prompt

def get_exec_viskop_program_prompt(program_from_viskop, parsed_intermediate_result, final_answer):
    prompt = f"""### New program: 
{program_from_viskop}

### Intermediate results: 
{parsed_intermediate_result}

The new program above is your chain-of-thoughts to answer a query.
The intermediate results are the intermediate result of each function in the new program. Note that there might be function got None as intermediate result. In this case, you don't need to explain the intermediate result, but you need to explain the program.
The intermediate results are the most reliable factual answer because they are retrieved from knowledge graphs. Hence, do not try to correct the retrived answer.
Now, give your response according to the structure below. 
Explain the your chain-of-thoughts with its corresponding intermediate result, in a steps by steps numbered list way. List them in separate line. Do not use HTML. Then, tell the user the final answer.

### Structure
I have executed the program, and here is my thought process based on the program:
<your explanation>
The final answer after executing the progam is {final_answer}. 

### Explanation
"""
    
    return prompt

def get_ans_from_llm_prompt(user_question, context):
    prompt = f"""
### User's question
{user_question}
    
### Context{context}

### Instruction
Based on the context and user's question above, provide factual answer to users.
You should admit "I don't know" if you cannot provide factual answer. Make sure your answer is not hallucinated.
To admit you don't know, you should say "Sorry that I don't have the answer to your question. I tried to search for answer from KB using KoPL program and chat history, but I couldn't find any relevant information to answer the question. Click the 'Edit Program' below to modify the KoPL program."
"""

    return prompt

def get_ans_from_hist_prompt(user_question, context):
    prompt = f"""
### User's question
{user_question}
    
### Context{context}

### Instruction
Based on the context and user's question above, please answer the user's question using information in the context.
"""

    return prompt

def get_check_has_answer_from_hist_prompt(user_question, context):
    prompt = f"""
# Examples
## Example 1
USER		: What are some of the countries in WTO?
ASSISTANT	: China, United States, Brazil, Canada, Japan
USER		: Among which, which are from Asia?
ASSISTANT	: China, Japan
USER		: What is not in Asia?
```json
{{
    "reasoning": "Let's think step by step. The user first asks about countries in WTO, then asks countries in Asia, and finally asks what is not in Asia. I can give the answer based on previous response by performing difference, which is excluding China and Japan from the first response, so I should set the field 'decision' to [yes]",
    "decision": "[yes]"
}}

## Example 2
USER		: What are some of the countries in Europe?
ASSISTANT	: Italy, Germany, France, Spain, United Kingdom
USER		: What are some of the countries in South East Asia?
ASSISTANT	: Malaysia, Indonesia, Thailand, Vietnam, Philippines
USER		: What are the countries from Europe and South East Asia?
```json
{{
    "reasoning": "Let's think step by step. The user first asks about countries in Europe, then asks countries in South East Asia, and finally asks what are the countries in Asia and Europe. I can give the answer based on previous response by performing union, so I should set the field 'decision' to [yes]",
    "decision": "[yes]"
}}

## Example 3
USER		: What are some of the countries in WTO?
ASSISTANT	: China, United States, Brazil, Canada, Japan
USER		: How about Columbia?
```json
{{
    "reasoning": "Let's think step by step. The user first asks about countries in WTO, then asks about does Columbia one of the member of WTO, this cannot be answered by performing union, difference, or intersection of previous answers, therefore, I should set the field 'decision' to [no]",
    "decision": "[no]"
}}

# Instruction
Your task is to decide if you can perform union, difference, or intersection of previous answers in order to answer user's question.
Give your reasoning and decision in the form of JSON as shown in the examples. During reasoning, always starting with "Let's think step by step."
Do not consider chat in the examples as your chat history.  

{context}
USER    : {user_question}
```json
{{
    "reasoning": "Let's think step by step. ",
    "decision": 
}}
"""

    return prompt

def get_verify_kb_answer_prompt(user_question, context, answer_from_kb):
    prompt = f"""
# Examples
## Example 1
USER		    : What are countries from Asia?
ANSWER FROM KB	: Asia countries.
```json
{{
    "reasoning": "Let's think step by step. The user asks about countries from Asia, but the answer from KB is 'Asia countries' which is not a country name and therefore not reasonable, so I should set the field 'isreasonable' to [no]",
    "isreasonable": "[no]"
}}

## Example 2
USER		    : What are countries from Asia?
ANSWER FROM KB	: China, Japan, Korea, United States, Brazil, Canada
```json
{{
    "reasoning": "Let's think step by step. The user asks about countries from Asia, and the answer from KB include countries name which is reasonable, so I should set the field 'isreasonable' to [yes]",
    "isreasonable": "[yes]"
}}

## Example 3
USER		    : What is the nationality of Lionel Messi?
ANSWER FROM KB	: Inter Miami CF 
```json
{{
    "reasoning": "Let's think step by step. The user asks about the nationality of Lionle Messi, but the answer from KB is Inter Miami CF, the name of a football team, which is not reasonable, so I should set the field 'isreasonable' to [no]",
    "isreasonable": "[no]"
}}
    
# Instruction
The answer from KB is the factual answer and reliable, but it might return a response that is not reasonable.
Your task is to verify if the answer from knowledge base is reasonable based on the context and user's question. 
For example, if the question asks for countries, but the answer from KB return a response that is not a country name, it's not reasonable.
If the question asks for countries, but the answer from KB return a response that is country name, although the country name is incorrect to the question, it's still reasonable.
Give your reasoning and decision in the form of JSON as shown in the examples. During reasoning, always starting with "Let's think step by step."

{context}
USER            : {user_question}
ANSWER FROM KB	: {answer_from_kb}
```json
{{
    "reasoning": "Let's think step by step. ",
    "isreasonable": 
}}
"""

    return prompt

if __name__ == "__main__":
    print(get_exec_program_prompt("this is a new program", 
                                  "parsed_intermediate_result", "final_answer", "explanation"))

