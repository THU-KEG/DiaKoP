from prompts import (get_factual_prompt, get_question_rewrite_prompt, 
                    get_clarify_prompt, get_edit_program_prompt, get_ans_from_llm_prompt,
                    get_exec_program_prompt, get_exec_viskop_program_prompt, get_ans_from_hist_prompt)
from utils import (
                preprocess_factual_prompt, count_prompt_token, 
                pretty_conversation_llama2, extract_rewrite_tag,  
                get_response, model_worker_stream_iter, extract_and_load_json,
                program_is_valid, kopl_engine_exec_api
)

def casual_state(user_question, conv, config, state=None, enable_btn=None):
    # new_prompt = conv.get_one_time_prompt(user_question)
    casual_system_message = "You are helpful and friendly assistant named as DiaKoP that will provide factual answer based on knowledge graph as well as casual chat with user."
    new_prompt = conv.get_short_answer_prompt(casual_system_message)
    # print("-"*30, f"Casual prompt", "-"*30)
    # print(new_prompt)

    # Calculate number of token
    state.token_cnt['casual'] = count_prompt_token(config['worker_addr'], new_prompt)

    stream_iter = model_worker_stream_iter(
                    conv,
                    config['model_name'],
                    config['worker_addr'],
                    new_prompt,
                    config['temperature'],
                    config['repetition_penalty'],
                    config['top_p'],
                    config['max_new_tokens'],
                )

    for i, data in enumerate(stream_iter):
        tmp = data["text"].replace("<|start_header_id|>assistant<|end_header_id|>", "")
        output = conv.get_agent_thought() + tmp
        # output = conv.get_agent_thought() + data["text"].strip()
        conv.update_last_message(output)
        yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

    conv.update_last_message(output)
    conv.update_last_short_answer_messages(data["text"].strip())
    yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

def no_answer_state(conv, config, state=None, enable_btn=None):
    tmp_prompt = "You tried to retrieve answer from knowledge graph but don't have the factual answer to user's question. Hence, reply like this 'Sorry that I don't have the answer to your question. I tried to search for answer from KB using the KoPL program you entered, but I couldn't find any relevant information to answer the question'."
    new_prompt = conv.get_one_time_prompt(tmp_prompt)
    # print("-"*30, f"No answer prompt", "-"*30)
    # print(new_prompt)

    # Calculate number of token
    state.token_cnt['no_answer'] = count_prompt_token(config['worker_addr'], new_prompt)

    stream_iter = model_worker_stream_iter(
                    conv,
                    config['model_name'],
                    config['worker_addr'],
                    new_prompt,
                    config['temperature'],
                    config['repetition_penalty'],
                    config['top_p'],
                    config['max_new_tokens'],
                )

    for i, data in enumerate(stream_iter):
        tmp = data["text"].replace("<|start_header_id|>assistant<|end_header_id|>", "")
        output = tmp
        conv.update_last_message(output)
        yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

    conv.update_last_message(output)
    conv.update_last_short_answer_messages(data["text"].strip())
    yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

def factual_state(user_question, program, result, conv, config, state=None, enable_btn=None):
    parsed_intermediate_result, graph_html = preprocess_factual_prompt(program, result)
    answer_str = (', ').join(result['inner_content'][-1]['content'])
    fact_prompt = get_factual_prompt(user_question, program, parsed_intermediate_result, answer_str)
    new_prompt = conv.get_one_time_prompt(fact_prompt)
    print("-"*30, f"Factual prompt", "-"*30)
    print(new_prompt)

    # Calculate number of token
    state.token_cnt['ans_from_kb'] = count_prompt_token(config['worker_addr'], new_prompt)

    stream_iter = model_worker_stream_iter(
                    conv,
                    config['model_name'],
                    config['worker_addr'],
                    new_prompt,
                    config['temperature'],
                    config['repetition_penalty'],
                    config['top_p'],
                    config['max_new_tokens'],
                )

    for i, data in enumerate(stream_iter):
        tmp = data["text"].replace("<|start_header_id|>assistant<|end_header_id|>", "")
        output = conv.get_agent_thought() + tmp
        conv.update_last_message(output)
        yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

    print("-"*30, f"output from Factual prompt", "-"*30)
    print(output)

    # Add the foldable Summary and Graph
    output += f"\n\nThe final answer to your question is {answer_str}. "
    output += f"\n{parsed_intermediate_result}"
    output += f"\n{graph_html}"
    conv.update_last_message(output)
    conv.update_last_short_answer_messages(answer_str)
    yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

def ans_from_hist_state(user_question, conv, config, state=None, enable_btn=None):
    context = pretty_conversation_llama2(conv.short_answer_messages[:-2], replace_token=False)

    ans_from_hist_prompt = get_ans_from_hist_prompt(user_question, context)
    new_prompt = conv.get_one_time_prompt(ans_from_hist_prompt)
    print("-"*30, f"ANS_FROM_HIST_STATE prompt", "-"*30)
    print(new_prompt)

    # Calculate number of token
    state.token_cnt['ans_from_hist'] = count_prompt_token(config['worker_addr'], new_prompt)

    stream_iter = model_worker_stream_iter(
                    conv,
                    config['model_name'],
                    config['worker_addr'],
                    new_prompt,
                    config['temperature'],
                    config['repetition_penalty'],
                    config['top_p'],
                    config['max_new_tokens'],
                )

    for i, data in enumerate(stream_iter):
        tmp = data["text"].replace("<|start_header_id|>assistant<|end_header_id|>", "")
        output = conv.get_agent_thought() + tmp
        conv.update_last_message(output)
        yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

    conv.update_last_message(output)
    conv.update_last_short_answer_messages(output)
    yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

def answer_from_llm_state(user_question, conv, config, state=None, enable_btn=None):
    context = pretty_conversation_llama2(conv.short_answer_messages[:-2], replace_token=False)

    ans_from_hist_prompt = get_ans_from_llm_prompt(user_question, context)
    new_prompt = conv.get_one_time_prompt(ans_from_hist_prompt)
    print("-"*30, f"ANS_FROM_LLM_STATE prompt", "-"*30)
    print(new_prompt)

    # Calculate number of token
    state.token_cnt['ans_from_llm'] = count_prompt_token(config['worker_addr'], new_prompt)

    stream_iter = model_worker_stream_iter(
                    conv,
                    config['model_name'],
                    config['worker_addr'],
                    new_prompt,
                    config['temperature'],
                    config['repetition_penalty'],
                    config['top_p'],
                    config['max_new_tokens'],
                )

    for i, data in enumerate(stream_iter):
        tmp = data["text"].replace("<|start_header_id|>assistant<|end_header_id|>", "")
        output = conv.get_agent_thought() + tmp
        conv.update_last_message(output)
        yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

    conv.update_last_message(output)
    conv.update_last_short_answer_messages(output)
    yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6


def contextual_state(user_question, conv, config, state):
    """
    Perform question rewrite
    """
    context = pretty_conversation_llama2(conv.short_answer_messages[:-2], replace_token=False)
    question_rewrite_prompt = get_question_rewrite_prompt(context, user_question)
    new_prompt = conv.get_one_time_prompt(question_rewrite_prompt)
    print("-"*30, f"Question rewrite prompt", "-"*30)
    print(new_prompt)

    # Calculate number of token
    state.token_cnt['ques_rewrite'] = count_prompt_token(config['worker_addr'], new_prompt)
    tmp = get_response(conv, config['model_name'], config['worker_addr'], new_prompt, config)
    output = tmp.replace("<|start_header_id|>assistant<|end_header_id|>", "")

    # Feed rephrased question to get factual answer 
    user_question = extract_rewrite_tag(output)
    # print("-"*30, f"Rephrased user question", "-"*30)
    # print(f"{output} extracted to -> {user_question}")

    conv.short_answer_messages[-2][1] = user_question 
    return user_question

def clarify_state(user_question, conv, config, state=None, enable_btn=None):
    context = pretty_conversation_llama2(conv.short_answer_messages[:-2], replace_token=False)
    fact_prompt = get_clarify_prompt(user_question, context)
    new_prompt = conv.get_one_time_prompt(fact_prompt)
    # print("-"*30, f"clarify prompt", "-"*30)
    # print(new_prompt)

    # Calculate number of token
    state.token_cnt['clarify'] = count_prompt_token(config['worker_addr'], new_prompt)

    stream_iter = model_worker_stream_iter(
                    conv,
                    config['model_name'],
                    config['worker_addr'],
                    new_prompt,
                    config['temperature'],
                    config['repetition_penalty'],
                    config['top_p'],
                    config['max_new_tokens'],
                )

    for i, data in enumerate(stream_iter):
        tmp = data["text"].replace("<|start_header_id|>assistant<|end_header_id|>", "")
        output = conv.get_agent_thought() + tmp
        conv.update_last_message(output)
        yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

    conv.update_last_message(output)
    conv.update_last_short_answer_messages(data["text"].strip())
    yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

def edit_program_from_viskop_state(program_from_viskop, conv, config, state, enable_btn, kopl_engine_url):
    # conv.agent_thought = "Act: &nbsp;&nbsp;&nbsp;&nbsp;&nbspExecuting the new program"
    # conv.update_last_message(conv.get_agent_thought())
    # yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

    # 1. Send the program to kopl engine for excution
    program_from_viskop = program_is_valid(program_from_viskop)
    state.program_to_edit = program_from_viskop
    result = kopl_engine_exec_api(program_from_viskop, kopl_engine_url)
    answer = result['inner_content'][-1]['content']
    answer_str = (', ').join(answer)
    has_answer = len(answer) > 0
    
    # 2. Return the result
    if has_answer:
        # msg = f"Yes! The new program has answer."
        # yield from append_agent_thought_obs(msg, conv, state, enable_btn)

        parsed_intermediate_result, graph_html = preprocess_factual_prompt(program_from_viskop, result)
        exec_new_program_prompt = get_exec_viskop_program_prompt(program_from_viskop, parsed_intermediate_result, answer_str)

        # Calculate number of token
        state.token_cnt['answer_edit_program'] = count_prompt_token(config['worker_addr'], exec_new_program_prompt)

        stream_iter = model_worker_stream_iter(
                        conv,
                        config['model_name'],
                        config['worker_addr'],
                        exec_new_program_prompt,
                        config['temperature'],
                        config['repetition_penalty'],
                        config['top_p'],
                        config['max_new_tokens'],
                    )

        for i, data in enumerate(stream_iter):
            tmp = data["text"].replace("<|start_header_id|>assistant<|end_header_id|>", "")
            output = tmp
            conv.update_last_message(output)
            yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

        # Add the foldable Summary and Graph
        output += f"\n{parsed_intermediate_result}"
        output += f"\n{graph_html}"

        conv.update_last_message(output)
        conv.update_last_short_answer_messages(answer_str)
        yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

    else:
        # msg = f"No! The new program has no answer."
        # yield from append_agent_thought_obs(msg, conv, state, enable_btn)

        yield from no_answer_state(conv, config, state, enable_btn)
    
def append_agent_thought_act(message, conv, state, enable_btn):
    if len(conv.agent_thought) == 0:
        conv.agent_thought += f"Act: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp{message}"
    else:
        conv.agent_thought += f"<br>\nAct: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp{message}"
    conv.update_last_message(conv.get_agent_thought())
    yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

def append_agent_thought_obs(message, conv, state, enable_btn):
    conv.agent_thought += f"<br>\nObs: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp{message}"
    conv.update_last_message(conv.get_agent_thought())
    yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6
