"""
The gradio demo server for chatting with a single model.
"""

import argparse
from collections import defaultdict
import datetime
import json
import os
import time
import urllib

import gradio as gr
import requests

import ast

from fastchat.constants import (
    LOGDIR,
    CONVERSATION_LIMIT_MSG,
    SERVER_ERROR_MSG,
    INPUT_CHAR_LEN_LIMIT,
    CONVERSATION_TURN_LIMIT,
    SESSION_EXPIRATION_TIME,
)
from fastchat.model.model_adapter import register_model_adapter
from fastchat.model.model_registry import register_model_info, get_model_info, model_info
from fastchat.utils import (
    build_logger,
    get_window_url_params_js,
    parse_gradio_auth_creds,
)
from api_provider import chatglm_pro_api_stream_iter

from model_adapter import Llama3Adapter
from utils import pretty_conversation_llama2, count_prompt_token, extract_and_load_json, model_worker_stream_iter, render_graph, enlarge_image
from conv_state import State
from chat_controllers import check_is_complete, check_need_clarify, check_has_answer, check_has_answer_from_hist, verify_kb_answer
from chat_components import (factual_state, contextual_state, 
                        casual_state, clarify_state, answer_from_llm_state,
                        edit_program_from_viskop_state, ans_from_hist_state,
                        append_agent_thought_act, append_agent_thought_obs)

logger = build_logger("gradio_web_server", "gradio_web_server.log")

no_change_btn = gr.Button.update()
enable_btn = gr.Button.update(interactive=True, visible=True)
disable_btn = gr.Button.update(interactive=False)
invisible_btn = gr.Button.update(interactive=False, visible=False)

controller_url = None
enable_moderation = False

ip_expiration_dict = defaultdict(lambda: 0)

openai_compatible_models_info = {}

def set_global_vars(controller_url_):
    global controller_url, enable_moderation
    controller_url = controller_url_

def get_conv_log_filename():
    t = datetime.datetime.now()
    name = os.path.join(LOGDIR, f"{t.year}-{t.month:02d}-{t.day:02d}-conv.json")
    return name


def get_model_list(
    controller_url, add_chatglm_pro,
):
    if controller_url:
        ret = requests.post(controller_url + "/refresh_all_workers")
        assert ret.status_code == 200
        ret = requests.post(controller_url + "/list_models")
        models = ret.json()["models"]
    else:
        models = []

    if add_chatglm_pro:
        models += ["glm-3-turbo"]
    models = list(set(models))

    for model_name in models:
       if "llama-3-70b" in model_name.lower():
            models.remove(model_name)
            models.append("DiaKoP")

    priority = {k: f"___{i:02d}" for i, k in enumerate(model_info)}
    models.sort(key=lambda x: priority.get(x, x))
    logger.info(f"Models: {models}")
    return models


def load_demo_single(models, url_params):
    selected_model = models[0] if len(models) > 0 else ""
    if "model" in url_params:
        model = url_params["model"]
        if model in models:
            selected_model = model

    dropdown_update = gr.Dropdown(choices=models, value=selected_model, visible=True)
    state = None
    return state, dropdown_update


def load_demo(url_params, request: gr.Request):
    global models

    ip = request.client.host
    logger.info(f"load_demo. ip: {ip}. params: {url_params}")
    ip_expiration_dict[ip] = time.time() + SESSION_EXPIRATION_TIME

    if args.model_list_mode == "reload":
        models = get_model_list(
            controller_url,
        )

    return load_demo_single(models, url_params)


def vote_last_response(state, vote_type, model_selector, request: gr.Request):
    with open(get_conv_log_filename(), "a") as fout:
        data = {
            "tstamp": round(time.time(), 4),
            "type": vote_type,
            "model": model_selector,
            "state": state.dict(),
            "ip": request.client.host,
        }
        fout.write(json.dumps(data) + "\n")


def upvote_last_response(state, model_selector, request: gr.Request):
    logger.info(f"upvote. ip: {request.client.host}")
    vote_last_response(state, "upvote", model_selector, request)
    return ("",) + (disable_btn,) * 3


def downvote_last_response(state, model_selector, request: gr.Request):
    logger.info(f"downvote. ip: {request.client.host}")
    vote_last_response(state, "downvote", model_selector, request)
    return ("",) + (disable_btn,) * 3


def flag_last_response(state, model_selector, request: gr.Request):
    logger.info(f"flag. ip: {request.client.host}")
    vote_last_response(state, "flag", model_selector, request)
    return ("",) + (disable_btn,) * 3


def regenerate(state, request: gr.Request):
    logger.info(f"regenerate. ip: {request.client.host}")

    state.reset_token_cnt()

    state.conv.update_last_message(None)
    state.conv.update_last_backend_messages(None)
    state.conv.update_last_short_answer_messages(None)
    return (state, state.to_gradio_chatbot(), "") + (disable_btn,) * 6


def clear_history(request: gr.Request):
    logger.info(f"clear_history. ip: {request.client.host}")
    state = None
    return (state, [], "") + (disable_btn,) * 6

def get_link(state, request: gr.Request):
    logger.info(f"get viskop link. ip: {request.client.host}")

    state.edit_program_viskop = True

    # we need question and kopl program to open window
    program_to_edit = state.program_to_edit
    print("-"*50, "PROGRAM_TO_EDIT", "-"*50)
    print(state.program_to_edit)

    if not isinstance(program_to_edit, str):
        program_to_edit = json.dumps(program_to_edit)

    encoded_kopl_program = urllib.parse.quote(program_to_edit) 

    viskop_link = f'http://localhost:{args.program_editing_port}/?data={encoded_kopl_program}'
    viskop_link_markdown = f"[Click here to edit KoPL program in interactive mode]({viskop_link})"

    conv = state.conv
    conv.append_message(conv.roles[0], None)
    conv.append_message(conv.roles[1], viskop_link_markdown)
    return (state, state.to_gradio_chatbot(), "") + (disable_btn,) * 6

def add_text(state, model_selector, text, request: gr.Request):
    ip = request.client.host
    logger.info(f"add_text. ip: {ip}. len: {len(text)}")

    if state is None:
        state = State(model_selector)

    if len(text) <= 0:
        state.skip_next = True
        return (state, state.to_gradio_chatbot(), "") + (no_change_btn,) * 6

    # if ip_expiration_dict[ip] < time.time():
    #     logger.info(f"inactive. ip: {request.client.host}. text: {text}")
    #     state.skip_next = True
    #     print("INACTIVEINACTIVE")
    #     return (state, state.to_gradio_chatbot(), INACTIVE_MSG) + (no_change_btn,) * 6

    # if enable_moderation:
    #     flagged = violates_moderation(text)
    #     if flagged:
    #         logger.info(f"violate moderation. ip: {request.client.host}. text: {text}")
    #         state.skip_next = True
    #         return (state, state.to_gradio_chatbot(), MODERATION_MSG) + (
    #             no_change_btn,
    #         ) * 6

    conv = state.conv
    if (len(conv.messages) - conv.offset) // 2 >= CONVERSATION_TURN_LIMIT:
        logger.info(f"conversation turn limit. ip: {request.client.host}. text: {text}")
        state.skip_next = True
        return (state, state.to_gradio_chatbot(), CONVERSATION_LIMIT_MSG) + (
            no_change_btn,
        ) * 6

    text = text[:INPUT_CHAR_LEN_LIMIT]  # Hard cut-off

    if text.strip().lower() == "/edit":
        # If user trigger edit mode by typing /edit
        state.edit_program = True
        conv.append_message(conv.roles[0], text)
        conv.append_message(conv.roles[1], None)
        return (state, state.to_gradio_chatbot(), "") + (disable_btn,) * 6
    
    if state.edit_program == True or state.edit_program_viskop == True:
        # If state.edit_program is True set from trigger_edit_program after viskop button is clicked
        conv.append_message(conv.roles[0], text)
        conv.append_message(conv.roles[1], None)
        return (state, state.to_gradio_chatbot(), "") + (disable_btn,) * 6
    
    state.reset_token_cnt()
    
    conv.append_message(conv.roles[0], text)
    conv.append_message(conv.roles[1], None)
    conv.append_backend_message(conv.roles[0], text)
    conv.append_backend_message(conv.roles[1], None)
    conv.append_short_answer_message(conv.roles[0], text)
    conv.append_short_answer_message(conv.roles[1], None)
    return (state, state.to_gradio_chatbot(), "") + (disable_btn,) * 6

def bot_response(state, temperature, top_p, max_new_tokens, request: gr.Request):
    logger.info(f"bot_response. ip: {request.client.host}")
    start_tstamp = time.time()
    temperature = float(temperature)
    top_p = float(top_p)
    max_new_tokens = int(max_new_tokens)

    conv, model_name = state.conv, state.model_name
    
    if model_name == "glm-3-turbo":
        prompt = conv.to_chatglm_pro_api_messages()
        stream_iter = chatglm_pro_api_stream_iter(
            model_name, prompt, temperature, top_p # not sure if need to add max_new_tokens
        )

        conv.update_last_message("▌")
        yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (disable_btn,) * 6

        output = ""
        for i, data in enumerate(stream_iter):
            # TO-DO: Stop generating when a complete json response generated
            output += data["text"]
            conv.update_last_message(output)
            yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (disable_btn,) * 6

        # print("-"* 30, "Prompt to chatglm_pro_api_stream_iter", "-"*30)
        # print(prompt)
        print("-"* 30, "Output from chatglm_pro_api_stream_iter", "-"*30)
        print(output)

        finish_tstamp = time.time()
        # logger.info(f"llm final output: {output}")

        with open(get_conv_log_filename(), "a") as fout:
            data = {
                "tstamp": round(finish_tstamp, 4),
                "type": "chat",
                "model": model_name,
                "gen_params": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_new_tokens": max_new_tokens,
                },
                "start": round(start_tstamp, 4),
                "finish": round(finish_tstamp, 4),
                "state": state.dict(),
                "ip": request.client.host,
            }
            fout.write(json.dumps(data) + "\n")
        return
        
    
    # elif model_name == "palm-2":
    #     stream_iter = palm_api_stream_iter(
    #         state.palm_chat, conv.messages[-2][1], temperature, top_p, max_new_tokens
    #     )
    # elif model_name in openai_compatible_models_info:
    #     model_info = openai_compatible_models_info[model_name]
    #     prompt = conv.to_openai_api_messages()
    #     stream_iter = openai_api_stream_iter(
    #         model_info["model_name"],
    #         prompt,
    #         temperature,
    #         top_p,
    #         max_new_tokens,
    #         api_base=model_info["api_base"],
    #         api_key=model_info["api_key"],
    #     )
    else:
        # Query worker address
        # TO-DO: Do not use bruce force to modify model name
        if model_name == "DiaKoP":
            model_name_tmp = "llama-3-70b-instruct-awq"
        else:
            model_name_tmp = model_name

        ret = requests.post(
            controller_url + "/get_worker_address", json={"model": model_name_tmp}
        )
        worker_addr = ret.json()["address"]
        logger.info(f"model_name_tmp: {model_name_tmp}, worker_addr: {worker_addr}")

        # No available worker
        if worker_addr == "":
            conv.update_last_message(SERVER_ERROR_MSG)
            yield (
                state,
                state.to_gradio_chatbot(),
                state.to_gradio_token_cnt(list(state.token_cnt.keys())),
                disable_btn,
                disable_btn,
                disable_btn,
                enable_btn,
                enable_btn,
            )
            return

        # Construct prompt.
        # We need to call it here, so it will not be affected by "▌".
        prompt = conv.get_backend_prompt()
        # print("-"*30, f"Pred action prompt", "-"*30)
        # print(prompt)
        # prompt = conv.get_one_time_prompt(conv.messages[-2][1], system_message=conv.system_message)

        logger.info(pretty_conversation_llama2(conv.backend_messages))
        logger.info("="*70)
        logger.info(pretty_conversation_llama2(conv.messages))
        logger.info("="*70)
        logger.info(pretty_conversation_llama2(conv.short_answer_messages))

        # Set repetition_penalty
        if "t5" in model_name:
            repetition_penalty = 1.2
        else:
            repetition_penalty = 1.0

        gen_config = {
            'model_name': model_name,
            'worker_addr': worker_addr,
            'temperature': temperature,
            'repetition_penalty': repetition_penalty,
            'top_p': top_p,
            'max_new_tokens': max_new_tokens,
        }
        
        if state.edit_program:
            user_message = conv.messages[-2][1]

            if user_message.strip().lower() == "/edit":
                # this is the first round of conversation, hence return the dot graph
                timestamp = time.time()
                img_id = str(timestamp).split('.')[0]
                dot_graph = render_graph(img_id, state.program_to_edit)
                # print("-"*30, f"program_to_edit", "-"*30)
                # print(state.program_to_edit)

                filename = os.path.join(LOGDIR, 'graphs', f"graph_output_{img_id}.png")
                enlarge_image(filename)
                assert os.path.exists(filename), f"{filename} does not exists"
                graph_html = f"\n<p align=\"center\"><img src='file={filename}' style='width: 100%; height: 100px; max-width:100%; max-height:100%'></img></p> " #html way

                # output = f"{graph_html}"
                conv.update_last_message(graph_html)
                yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6
                return
            else:
                # not implement
                return
        
        if state.edit_program_viskop:
            program_from_viskop = conv.messages[-2][1] # this message should be a list of program copied from viskop

            # TO-DO: make assertion to make sure user input a list of program copied from viskop
            try:
                program_from_viskop = ast.literal_eval(program_from_viskop)
                state.program_to_edit = program_from_viskop
                state.edit_program_viskop = False
                yield from edit_program_from_viskop_state(program_from_viskop, conv, gen_config, state, enable_btn, args.kopl_exec_engine_url)
                return
            except:
                print("User did not input a list of program copied from viskop")

        # Calculate number of token
        state.token_cnt['casual_or_factual'] = count_prompt_token(worker_addr, prompt)

        # print("-"*30, f"Pred action prompt", "-"*30)
        # print(prompt)

        # Prompt model to decide action
        stream_iter = model_worker_stream_iter(
            conv,
            gen_config['model_name'],
            gen_config['worker_addr'],
            prompt,
            gen_config['temperature'],
            gen_config['repetition_penalty'],
            gen_config['top_p'],
            gen_config['max_new_tokens'],
        )

    conv.update_last_message("▌")
    yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (disable_btn,) * 6

    conv.agent_thought = "Act: &nbsp;&nbsp;&nbsp;&nbsp;&nbspChecking is the question factual or non-factual?"
    conv.update_last_message(conv.get_agent_thought())
    yield (state, state.to_gradio_chatbot(), state.to_gradio_token_cnt(list(state.token_cnt.keys()))) + (enable_btn,) * 6

    # msg = "Checking is the question factual or non-factual?"
    # yield from append_agent_thought_act(msg, conv, state, enable_btn)
    
    # try:
    for i, data in enumerate(stream_iter):
        if data["error_code"] == 0:
            if i % 8 != 0:  # reduce gradio's overhead
                continue
            # TO-DO: Stop generating when a complete json response generated
            output = data["text"].strip()
            if "<s>" in output: # avoid LLM go crazy
                break
        else:
            output = data["text"] + f"\n\n(error_code: {data['error_code']})"
            conv.update_last_message(output)
            yield (state, state.to_gradio_chatbot(), "ERROR") + (
                disable_btn,
                disable_btn,
                disable_btn,
                enable_btn,
                enable_btn,
                enable_btn,
            )
            return
        
    user_question = conv.messages[-2][1]
    output = data["text"].split("<s>")[0].strip()
    output = data["text"].split("<|start_header_id|>assistant<|end_header_id|>")[0].strip()
    llm_output = output.lower()
    llm_output_dict = extract_and_load_json(llm_output, target_keys=["reasoning", "chatmode"])

    try:
        predicted_mode = llm_output_dict['chatmode']
        llm_output_str = json.dumps(llm_output_dict, indent=2)
    except:
        predicted_mode = llm_output
        llm_output_str = llm_output

    print("-"*30, f"LLM state controller's decision", "-"*30)
    print(f"{llm_output_str}")

    if '[casual]' in predicted_mode:
        message = '[casual]'
    elif '[factual]' in predicted_mode:
        message = '[factual]'
    else:
        message = llm_output_str
        print("WARNING: Failed to predict chat mode.")
    conv.update_last_backend_messages(llm_output_str)

    ########## Perform state prediction/state transfer ##########
    if message == '[casual]':
        # casual chat
        msg = "Casual chat mode detected."
        yield from append_agent_thought_obs(msg, conv, state, enable_btn)

        yield from casual_state(user_question, conv, gen_config, state, enable_btn)

    elif message == '[factual]':
        msg = "Factual chat mode detected."
        yield from append_agent_thought_obs(msg, conv, state, enable_btn)

        # # check if sentence is a complete query
        msg = f"Checking whether '{user_question}' is a complete question."
        yield from append_agent_thought_act(msg, conv, state, enable_btn)

        is_complete_question = check_is_complete(user_question, conv, gen_config, state)
        
        if "yes" in is_complete_question:
            msg = "Yes! it is a complete question."
            yield from append_agent_thought_obs(msg, conv, state, enable_btn)
            
            msg = f"Checking whether '{user_question}' has answer in KB."
            yield from append_agent_thought_act(msg, conv, state, enable_btn)
            
            has_answer, program, result = check_has_answer(user_question, args.kopl_exec_engine_url)
            state.program_to_edit = program
            if has_answer:
                msg = f"Yes! '{user_question}' has answer in KB."
                yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                # Verify if the answer is correct
                answer_from_kb = (', ').join(result['inner_content'][-1]['content'][:5])

                msg = f"Verifying answer from KB: {answer_from_kb}."
                yield from append_agent_thought_act(msg, conv, state, enable_btn)

                kb_ans_is_correct = verify_kb_answer(user_question, answer_from_kb, conv, gen_config, state)

                if "yes" in kb_ans_is_correct:
                    msg = f"Yes! answer from kb: '{answer_from_kb}' is correct."
                    yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                    msg = f"Providing answer from KB."
                    yield from append_agent_thought_act(msg, conv, state, enable_btn)

                    yield from factual_state(user_question, program, result, conv, gen_config, state, enable_btn)
                else:
                    msg = f"No! answer from kb: '{answer_from_kb}' is incorrect."
                    yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                    # check if answer exists in the chat history, using short_answer_messages
                    msg = f"Checking whether '{user_question}' has answer in chat history."
                    yield from append_agent_thought_act(msg, conv, state, enable_btn)
                    
                    has_answer_from_hist = check_has_answer_from_hist(user_question, conv, gen_config, state)

                    if "yes" in has_answer_from_hist:
                        msg = f"Yes! Answer can be inference from chat history."
                        yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                        msg = f"Providing answer from chat history."
                        yield from append_agent_thought_act(msg, conv, state, enable_btn)

                        # return response from chat history
                        yield from ans_from_hist_state(user_question, conv, gen_config, state, enable_btn)
                    else:
                        msg = f"No! '{user_question}' has no answer in chat history."
                        yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                        msg = f"Providing answer from parametric knowledge."
                        yield from append_agent_thought_act(msg, conv, state, enable_btn)

                        yield from answer_from_llm_state(user_question, conv, gen_config, state, enable_btn)
            else:
                # else if KB has no answer
                msg = f"No! '{user_question}' has no answer from KB."
                yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                # check if answer exists in the chat history, using short_answer_messages
                msg = f"Checking whether '{user_question}' has answer in chat history."
                yield from append_agent_thought_act(msg, conv, state, enable_btn)
                
                has_answer_from_hist = check_has_answer_from_hist(user_question, conv, gen_config, state)

                if "yes" in has_answer_from_hist:
                    msg = f"Yes! Answer can be inference from chat history."
                    yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                    msg = f"Providing answer from chat history."
                    yield from append_agent_thought_act(msg, conv, state, enable_btn)

                    # return response from chat history
                    yield from ans_from_hist_state(user_question, conv, gen_config, state, enable_btn)
                else:
                    msg = f"No! '{user_question}' has no answer in chat history."
                    yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                    msg = f"Providing answer from parametric knowledge."
                    yield from append_agent_thought_act(msg, conv, state, enable_btn)

                    yield from answer_from_llm_state(user_question, conv, gen_config, state, enable_btn)

        elif "no" in is_complete_question:
            # else if sentence is not a complete question
            msg = f"No! it is not a complete question."
            yield from append_agent_thought_obs(msg, conv, state, enable_btn)

            # check if there is context
            msg = f"Checking whether '{user_question}' requires clarification."
            yield from append_agent_thought_act(msg, conv, state, enable_btn)
            
            need_clarify = check_need_clarify(user_question, conv, gen_config, state)

            if "yes" in need_clarify:
                msg = f"Yes! Clarification requires."
                yield from append_agent_thought_obs(msg, conv, state, enable_btn)
                
                # enter clarify mode
                yield from clarify_state(user_question, conv, gen_config, state, enable_btn)

            elif "no" in need_clarify:
                msg = f"No! Clarification not required."
                yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                # enter contextual mode
                rewritten_question = contextual_state(user_question, conv, gen_config, state)
                msg = f"Rewrite user's question into '{rewritten_question}.'"
                yield from append_agent_thought_act(msg, conv, state, enable_btn)

                msg = f"Checking whether '{rewritten_question}' has answer in KB."
                yield from append_agent_thought_act(msg, conv, state, enable_btn)

                has_answer, program, result = check_has_answer(rewritten_question, args.kopl_exec_engine_url)
                state.program_to_edit = program
                if has_answer:
                    msg = f"Yes! '{rewritten_question}' has answer in KB."
                    yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                    # Verify if the answer is correct
                    answer_from_kb = (', ').join(result['inner_content'][-1]['content'][:5])

                    msg = f"Verifying whether answer from kb: '{answer_from_kb}' is correct."
                    yield from append_agent_thought_act(msg, conv, state, enable_btn)

                    kb_ans_is_correct = verify_kb_answer(rewritten_question, answer_from_kb, conv, gen_config, state)

                    if "yes" in kb_ans_is_correct:
                        msg = f"Yes! answer from kb: '{answer_from_kb}' is correct."
                        yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                        msg = f"Providing answer from KB."
                        yield from append_agent_thought_act(msg, conv, state, enable_btn)

                        yield from factual_state(rewritten_question, program, result, conv, gen_config, state, enable_btn)
                    else:
                        msg = f"No! answer from kb: '{answer_from_kb}' is incorrect."
                        yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                        # check if answer exists in the chat history, using short_answer_messages
                        msg = f"Checking whether '{rewritten_question}' has answer in chat history."
                        yield from append_agent_thought_act(msg, conv, state, enable_btn)
                        
                        has_answer_from_hist = check_has_answer_from_hist(rewritten_question, conv, gen_config, state)

                        if "yes" in has_answer_from_hist:
                            msg = f"Yes! Answer can be inference from chat history."
                            yield from append_agent_thought_obs(msg, conv, state, enable_btn)
                            
                            msg = f"Providing answer from chat history."
                            yield from append_agent_thought_act(msg, conv, state, enable_btn)

                            # return response from chat history
                            yield from ans_from_hist_state(rewritten_question, conv, gen_config, state, enable_btn)
                        else:
                            msg = f"No! '{rewritten_question}' has no answer in chat history."
                            yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                            msg = f"Providing answer from parametric knowledge."
                            yield from append_agent_thought_act(msg, conv, state, enable_btn)

                            yield from answer_from_llm_state(rewritten_question, conv, gen_config, state, enable_btn)
                else:
                    msg = f"No! '{rewritten_question}' has no answer from KB."
                    yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                    # check if answer exists in the chat history, using short_answer_messages
                    msg = f"Checking whether '{rewritten_question}' has answer in chat history."
                    yield from append_agent_thought_act(msg, conv, state, enable_btn)
                    
                    has_answer_from_hist = check_has_answer_from_hist(rewritten_question, conv, gen_config, state)

                    if "yes" in has_answer_from_hist:
                        msg = f"Yes! Answer can be inference from chat history."
                        yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                        msg = f"Providing answer from chat history."
                        yield from append_agent_thought_act(msg, conv, state, enable_btn)
                        
                        # return response from chat history
                        yield from ans_from_hist_state(rewritten_question, conv, gen_config, state, enable_btn)
                    else:
                        msg = f"No! '{rewritten_question}' has no answer."
                        yield from append_agent_thought_obs(msg, conv, state, enable_btn)

                        msg = f"Providing answer from parametric knowledge."
                        yield from append_agent_thought_act(msg, conv, state, enable_btn)

                        yield from answer_from_llm_state(rewritten_question, conv, gen_config, state, enable_btn)

            else:
                print("WARNING: Unable to extract correct token from check_need_clarify")
        else:
            print("WARNING: Unable to extract correct token from is_complete_question")
    ############################################################

    finish_tstamp = time.time()
    # logger.info(f"llm final output: {output}")

    with open(get_conv_log_filename(), "a") as fout:
        data = {
            "tstamp": round(finish_tstamp, 4),
            "type": "chat",
            "model": model_name,
            "gen_params": {
                "temperature": temperature,
                "top_p": top_p,
                "max_new_tokens": max_new_tokens,
            },
            "start": round(start_tstamp, 4),
            "finish": round(finish_tstamp, 4),
            "state": state.dict(),
            "ip": request.client.host,
        }
        fout.write(json.dumps(data) + "\n")


block_css = """
#notice_markdown {
    font-size: 104%
}
#notice_markdown th {
    display: none;
}
#notice_markdown td {
    padding-top: 6px;
    padding-bottom: 6px;
}
#leaderboard_markdown {
    font-size: 104%
}
#leaderboard_markdown td {
    padding-top: 6px;
    padding-bottom: 6px;
}
#leaderboard_dataframe td {
    line-height: 0.1em;
}
#input_box textarea {
}
footer {
    display:none !important
}

/* Container styling */
.agent-thought-container {
    display: block; /* Ensure the container is block-level */
}

/* Box styling */
.agent-thought-box {
    border: 1px solid #ccc;
    padding: 1em;
    margin: 1em 0;
    border-radius: 8px;
    width: max-content;
    box-shadow: 0 4px 8px rgba(0,0,0,0.5);
    display: inline-block; /* Adjusted to inline-block */
    word-wrap: break-word; /* Ensure long words wrap onto the next line */
    min-width: 200px; /* Set a minimum width */
}

/* Light theme */
@media (prefers-color-scheme: light) {
    .agent-thought-box {
        background-color: #ECECEC; /* Light grey */
    }
}

/* Dark theme */
@media (prefers-color-scheme: dark) {
    .agent-thought-box {
        background-color: #333; /* Dark grey */
        color: #EEE; /* Light text color for dark background */
    }
}

/* Summary styling */
.foldable-summary {
    cursor: pointer;
    outline: none;
    font-weight: bold;
    display: flex;
    align-items: center; /* Align the arrow and text vertically */
    position: relative; /* Position the arrow relative to the summary */
}

/* Summary hover effect */
.foldable-summary:hover {
    color: #007bff;
}

/* Change arrow direction when the details are open */
.agent-thought-box[open] .foldable-summary::after {
    border-width: 0 5px 5px 5px;
    transform: translateY(-50%) rotate(180deg); /* Rotate the arrow 180 degrees */
}

"""


def get_model_description_md(models):
    model_description_md = """
| | | |
| ---- | ---- | ---- |
"""
    ct = 0
    visited = set()
    for i, name in enumerate(models):
        minfo = get_model_info(name)
        if minfo.simple_name in visited:
            continue
        visited.add(minfo.simple_name)
        one_model_md = f"[{minfo.simple_name}]({minfo.link}): {minfo.description}"

        if ct % 3 == 0:
            model_description_md += "|"
        model_description_md += f" {one_model_md} |"
        if ct % 3 == 2:
            model_description_md += "\n"
        ct += 1
    return model_description_md


def build_single_model_ui(models):
    notice_markdown = f"""
<p style="text-align: left; font-size: 24px; font-weight: bold;">DiaKoP: Dialogue-based Knowledge-oriented Programming for Neural-symbolic Knowledge Base Question Answering</p>
### Choose a model/system to chat with:
"""

    state = gr.State()
    model_description_md = get_model_description_md(models)
    gr.Markdown(notice_markdown + model_description_md, elem_id="notice_markdown")

    with gr.Row(elem_id="model_selector_row"):
        model_selector = gr.Dropdown(
            choices=models,
            value=models[0] if len(models) > 0 else "",
            interactive=True,
            show_label=False,
            container=False,
        )
        cnt_prompt_token = gr.Textbox(label="Token count", scale=3)

    chatbot = gr.Chatbot(
        elem_id="chatbot",
        label="Scroll down and start chatting",
        show_copy_button=True,
        height=500,
    )
    with gr.Row():
        with gr.Column(scale=20):
            textbox = gr.Textbox(
                show_label=False,
                placeholder="Enter your prompt here and press ENTER",
                container=False,
                elem_id="input_box",
            )
        with gr.Column(scale=1, min_width=50):
            send_btn = gr.Button(value="Send", variant="primary")

    with gr.Row() as button_row:
        upvote_btn = gr.Button(value="👍  Upvote", interactive=False)
        downvote_btn = gr.Button(value="👎  Downvote", interactive=False)
        flag_btn = gr.Button(value="⚠️  Flag", interactive=False)
        regenerate_btn = gr.Button(value="🔄  Regenerate", interactive=False)
        clear_btn = gr.Button(value="🗑️  Clear history", interactive=False)
        viskop_btn = gr.Button(value="Edit Program", interactive=False)

    with gr.Accordion("Parameters", open=False) as parameter_row:
        temperature = gr.Slider(
            minimum=0.0,
            maximum=1.0,
            value=0.7,
            step=0.1,
            interactive=True,
            label="Temperature",
        )
        top_p = gr.Slider(
            minimum=0.0,
            maximum=1.0,
            value=1.0,
            step=0.1,
            interactive=True,
            label="Top P",
        )
        max_output_tokens = gr.Slider(
            minimum=16,
            maximum=1024,
            value=512,
            step=64,
            interactive=True,
            label="Max output tokens",
        )

    # with gr.Row(elem_id="graph_visualization"):
    #     graph_viz = gr.Image(type="pil", show_label=False)

    # if add_promotion_links:
    #     gr.Markdown(acknowledgment_md)

    # Register listeners
    btn_list = [upvote_btn, downvote_btn, flag_btn, regenerate_btn, clear_btn, viskop_btn]
    upvote_btn.click(
        upvote_last_response,
        [state, model_selector],
        [textbox, upvote_btn, downvote_btn, flag_btn],
    )
    downvote_btn.click(
        downvote_last_response,
        [state, model_selector],
        [textbox, upvote_btn, downvote_btn, flag_btn],
    )
    flag_btn.click(
        flag_last_response,
        [state, model_selector],
        [textbox, upvote_btn, downvote_btn, flag_btn],
    )
    regenerate_btn.click(regenerate, state, [state, chatbot, textbox] + btn_list).then(
        bot_response,
        [state, temperature, top_p, max_output_tokens],
        [state, chatbot, cnt_prompt_token] + btn_list,
    )
    clear_btn.click(clear_history, None, [state, chatbot, textbox] + btn_list)

    model_selector.change(clear_history, None, [state, chatbot, textbox] + btn_list)

    textbox.submit(
        add_text, [state, model_selector, textbox], [state, chatbot, textbox] + btn_list
    ).then(
        bot_response,
        [state, temperature, top_p, max_output_tokens],
        [state, chatbot, cnt_prompt_token] + btn_list,
    )
    send_btn.click(
        add_text,
        [state, model_selector, textbox],
        [state, chatbot, textbox] + btn_list,
    ).then(
        bot_response,
        [state, temperature, top_p, max_output_tokens],
        [state, chatbot, cnt_prompt_token] + btn_list,
    )

    viskop_btn.click(
        get_link, 
        [state], 
        [state, chatbot, textbox] + btn_list
    )

    return [state, model_selector]


def build_demo(models):
    with gr.Blocks(
        title="DiaKoP",
        theme=gr.themes.Default(),
        css=block_css,
    ) as demo:
        url_params = gr.JSON(visible=False)

        state, model_selector = build_single_model_ui(models)

        if args.model_list_mode not in ["once", "reload"]:
            raise ValueError(f"Unknown model list mode: {args.model_list_mode}")

        load_js = get_window_url_params_js

        demo.load(
            load_demo,
            [url_params],
            [
                state,
                model_selector,
            ],
            _js=load_js,
        )

    return demo


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int)
    parser.add_argument(
        "--share",
        action="store_true",
        help="Whether to generate a public, shareable link",
    )
    parser.add_argument(
        "--controller-url",
        type=str,
        default="http://localhost:21001",
        help="The address of the controller",
    )
    parser.add_argument(
        "--kopl-exec-engine-url",
        type=str,
        help="The address of the kopl execution engine",
    )
    parser.add_argument(
        "--model-list-mode",
        type=str,
        default="once",
        choices=["once", "reload"],
        help="Whether to load the model list once or reload the model list every time",
    )
    parser.add_argument(
        "--add-chatglm-pro",
        action="store_true",
        help="Add ChatGLM Pro",
    )
    parser.add_argument(
        "--gradio-auth-path",
        type=str,
        help='Set the gradio authentication file path. The file should contain one or more user:password pairs in this format: "u1:p1,u2:p2,u3:p3"',
    )
    parser.add_argument(
        "--program-editing-port",
        type=int,
        help='Port for program editing interface (VisKoP)',
    )
    args = parser.parse_args()
    logger.info(f"args: {args}")

    if not os.path.exists(os.path.join(LOGDIR, 'graphs')):
        os.makedirs(os.path.join(LOGDIR, 'graphs'))
    
    register_model_adapter(Llama3Adapter)
    
    register_model_info(
        ["DiaKoP"],
        "DiaKoP",
        "https://github.com/THU-KEG/DiaKoP",
        "A dialogue-based KBQA system by KEG from Tsinghua University",
    )
    
    # Register chatglm-pro
    register_model_info(
        ["glm-3-turbo"], 
        "ChatGLM3 - Turbo", 
        "https://open.bigmodel.cn/dev/api#glm-3-turbo", 
        "GLM-3-Turbo by Zhipu AI, without the proposed multi-turn question-answering backend"
    )

    # Set global variables
    set_global_vars(args.controller_url)
    models = get_model_list(
        args.controller_url,
        args.add_chatglm_pro,
    )

    # Set authorization credentials
    auth = None
    if args.gradio_auth_path is not None:
        auth = parse_gradio_auth_creds(args.gradio_auth_path)

    # Launch the demo
    demo = build_demo(models)
    demo.queue(
        status_update_rate=10, api_open=False
    ).launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        max_threads=200,
        auth=auth,
    )
