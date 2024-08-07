import json

from prompts import get_check_complete_sentence_prompt, get_check_need_clarify_prompt, get_check_has_answer_from_hist_prompt, get_verify_kb_answer_prompt
from utils import extract_and_load_json, get_response, pretty_conversation_llama2, \
                kopl_engine_exec_api, semantic_parsing_api, program_is_valid, count_prompt_token

def check_has_answer(user_question, kopl_engine_url):
    print(f"LLM MONOLOGUE: Checking whether '{user_question}' has answer...")
    # 1. Execute semantic parsing api
    program = semantic_parsing_api(user_question)
    
    # 1.1 Preprocess program
    program = program_is_valid(program)

    # 2. Execute kopl engine
    result = kopl_engine_exec_api(program, kopl_engine_url)

    answer = result['inner_content'][-1]['content']
    has_answer = len(answer) > 0

    if not has_answer:
        print(f"LLM MONOLOGUE: No! '{user_question}' has no answer.")
        return False, program, result
    else:
        print(f"LLM MONOLOGUE: Yes! '{user_question}' has answer.")
        return True, program, result

def check_is_complete(user_question, conv, config, state):
    print(f"LLM MONOLOGUE: Checking whether '{user_question}' is a complete question...")

    # prepare prompt
    check_complete_prompt = get_check_complete_sentence_prompt(user_question)
    new_prompt = conv.get_one_time_prompt(check_complete_prompt)
    # print("-"*30, f"check_is_complete prompt", "-"*30)
    # print(new_prompt)

    state.token_cnt['isComplete'] = count_prompt_token(config['worker_addr'], new_prompt)

    # get response
    tmp = get_response(conv, config['model_name'], config['worker_addr'], new_prompt, config)
    output = tmp.replace("<|start_header_id|>assistant<|end_header_id|>", "").strip()

    # extract response
    llm_output = output.lower()
    llm_output_dict = extract_and_load_json(llm_output, target_keys=["reasoning", "is_complete_question"])

    try:
        is_complete_question = llm_output_dict['is_complete_question']
        llm_output_str = json.dumps(llm_output_dict, indent=2)
    except:
        is_complete_question = llm_output
        llm_output_str = llm_output

    print("-"*30, f"LLM check_is_complete's decision'", "-"*30)
    print(f"{llm_output_str}")

    return is_complete_question

def check_need_clarify(user_question, conv, config, state):
    print(f"LLM MONOLOGUE: Checking whether '{user_question}' needs clarification...")

    # prepare prompt
    context = pretty_conversation_llama2(conv.short_answer_messages[:-2], replace_token=False)
    check_need_clarify_prompt = get_check_need_clarify_prompt(user_question, context)
    new_prompt = conv.get_one_time_prompt(check_need_clarify_prompt)
    print("-"*30, f"check_need_clarify_prompt prompt", "-"*30)
    print(new_prompt)

    state.token_cnt['needClarify'] = count_prompt_token(config['worker_addr'], new_prompt)

    # get response
    tmp = get_response(conv, config['model_name'], config['worker_addr'], new_prompt, config)
    output = tmp.replace("<|start_header_id|>assistant<|end_header_id|>", "")

    # extract response
    llm_output = output.lower()
    llm_output_dict = extract_and_load_json(llm_output, target_keys=["reasoning", "need_clarify"])

    try:
        need_clarify = llm_output_dict['need_clarify']
        llm_output_str = json.dumps(llm_output_dict, indent=2)
    except:
        need_clarify = llm_output
        llm_output_str = llm_output

    print("-"*30, f"LLM check_need_clarify's decision'", "-"*30)
    print(f"{llm_output_str}")
        
    return need_clarify

def check_has_answer_from_hist(user_question, conv, config, state):
    print(f"LLM MONOLOGUE: Checking whether '{user_question}' has answer from chat history...")

    # prepare prompt
    context = pretty_conversation_llama2(conv.short_answer_messages[:-2], replace_token=False)
    check_has_answer_from_hist_prompt = get_check_has_answer_from_hist_prompt(user_question, context)
    new_prompt = conv.get_one_time_prompt(check_has_answer_from_hist_prompt)
    print("-"*30, f"check_has_answer_from_hist_prompt prompt", "-"*30)
    print(new_prompt)

    state.token_cnt['hasAnswerFromHist'] = count_prompt_token(config['worker_addr'], new_prompt)

    # get response
    tmp = get_response(conv, config['model_name'], config['worker_addr'], new_prompt, config)
    output = tmp.replace("<|start_header_id|>assistant<|end_header_id|>", "")

    # extract response
    llm_output = output.lower()
    llm_output_dict = extract_and_load_json(llm_output, target_keys=["reasoning", "decision"])

    try:
        has_ans_from_his = llm_output_dict['decision']
        llm_output_str = json.dumps(llm_output_dict, indent=2)
    except:
        has_ans_from_his = llm_output
        llm_output_str = llm_output

    print("-"*30, f"LLM check_has_answer_from_hist's decision'", "-"*30)
    print(f"{llm_output_str}")
        
    return has_ans_from_his

def verify_kb_answer(user_question, answer_from_kb, conv, config, state):
    print(f"LLM MONOLOGUE: Checking whether '{user_question}' answer from KB is correct")

    # prepare prompt
    context = pretty_conversation_llama2(conv.short_answer_messages[:-2], replace_token=False)
    verify_kb_answer_prompt = get_verify_kb_answer_prompt(user_question, context, answer_from_kb)
    new_prompt = conv.get_one_time_prompt(verify_kb_answer_prompt)
    print("-"*30, f"verify_kb_answer_prompt prompt", "-"*30)
    print(new_prompt)

    state.token_cnt['verifyKBAnswer'] = count_prompt_token(config['worker_addr'], new_prompt)

    # get response
    tmp = get_response(conv, config['model_name'], config['worker_addr'], new_prompt, config)
    output = tmp.replace("<|start_header_id|>assistant<|end_header_id|>", "")

    # extract response
    llm_output = output.lower()
    llm_output_dict = extract_and_load_json(llm_output, target_keys=["reasoning", "isreasonable"])

    try:
        has_ans_from_his = llm_output_dict['isreasonable']
        llm_output_str = json.dumps(llm_output_dict, indent=2)
    except:
        has_ans_from_his = llm_output
        llm_output_str = llm_output

    print("-"*30, f"LLM verify_kb_answer's decision'", "-"*30)
    print(f"{llm_output_str}")
        
    return has_ans_from_his