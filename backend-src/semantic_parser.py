from transformers import BartConfig, BartForConditionalGeneration, BartTokenizer
import os
import torch
import argparse
import re

from flask import Flask, request, jsonify
# from flask_cors import CORS

from utils import seed_everything, get_dep

device = 'cuda' if torch.cuda.is_available() else 'cpu'

def predict(text, model, tokenizer):
    pattern = re.compile(r'(.*?)\((.*?)\)')
    
    with torch.no_grad():
        input_ids = tokenizer.batch_encode_plus([text], max_length=512, pad_to_max_length=True, return_tensors="pt", truncation=True)
        source_ids = input_ids['input_ids'].to(device)
        outputs = model.generate(
            input_ids=source_ids,
            max_length=500,
        )
        outputs = [tokenizer.decode(output_id, skip_special_tokens=True, clean_up_tokenization_spaces=True) for output_id in outputs]
        output = outputs[0]
        chunks = output.split('<b>')
        func_list = []
        inputs_list = []
        for chunk in chunks:
            res = pattern.findall(chunk)
            if len(res) == 0:
                continue
            res = res[0]
            func, inputs = res[0], res[1]
            if inputs == '':
                inputs = []
            else:
                inputs = inputs.split('<c>')
            func_list.append(func)
            inputs_list.append(inputs)
        assert len(func_list) == len(inputs_list)
        
        dep_list = get_dep(func_list, inputs_list)
        assert len(dep_list) == len(func_list)
        assert len(func_list) == len(inputs_list)
        
    program = []
    for func, inputs, dep in zip(func_list, inputs_list, dep_list):
        program.append({'func': func, 'inputs': inputs, 'dep': dep})
    return program, func_list, inputs_list

def load_model(args):
    config_class, model_class, tokenizer_class = (BartConfig, BartForConditionalGeneration, BartTokenizer)
    tokenizer = tokenizer_class.from_pretrained(os.path.join(args.ckpt))
    model = model_class.from_pretrained(os.path.join(args.ckpt))
    model = model.to(device)

    return model, tokenizer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ckpt', default="/mnt/lzc/MODELS/semantic_parser_bart/checkpoint-188608")
    parser.add_argument('--seed', type=int, default=666, help='random seed')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the Flask app')
    parser.add_argument('--port', type=int, default=6061, help='Port to run the Flask app')
    
    args = parser.parse_args()

    seed_everything(args.seed)

    model, tokenizer = load_model(args)

    # Flask app initialization
    app = Flask(__name__)

    @app.route('/predict', methods=['POST'])
    def predict_route():
        data = request.form
        text = data.get('question', None)
        program, func_list, inputs_list = predict(text, model, tokenizer)
        return jsonify({
            'program': program
        })

    app.run(host=args.host, port=args.port, threaded=True)

if __name__ == '__main__':
    main()
