# DiaKoP: Dialogue-based Knowledge-oriented Programming for Neural-symbolic Knowledge Base Question Answering (CIKM 2024, Demo Track)

## Introduction
![Overview](./readme_assets/overview_v10.jpg)   
We proposed DiaKoP, a multi-turn KBQA system that consists of two main modules. 
The **Dialogue-based Explainable Interactive Frontend** features a chat interface that allows users to interact with a predefined knowledge base (a) and a program editing interface that enables users to correct incorrectly parsed logic forms (b). 
The **Multi-turn Question Answering Backend** is the core component responsible for processing and managing the conversation. It comprises several sub-modules: the Dialogue History Tracker (c) and Dialogue Policy (d) manage the conversation flow, while the Knowledge Source (e) stores the factual information to answer user's question. 

## Prerequisite
### Model
Download the following model from huggingface
1. Quantized Llama 3 - 70B Model
[Hugginface link](https://huggingface.co/casperhansen/llama-3-70b-instruct-awq)  
After downloading, modify env `MODEL_PATH` in `launch_worker_vllm.sh`

2. Semantic parsing model
[Huggingface link](https://huggingface.co/THU-KEG/kopl_semantic_parser)  
After downloading, modify env `CKPT_PATH` in `launch_semantic_parser.sh`

### Environment Setup 
```
# create conda environment
conda create --name diakop python=3.10

conda activate diakop 
pip install -r requirements.txt
conda install graphviz
```

## Run
Activate conda and change directory to the `scripts_bash`
```
conda activate diakop
cd scripts_bash
```

**RUN SCRIPTS BELOW IN DIFFERENT SHELL**


**1. Launch the controller**.   
This controller manages the distributed workers.
```bash
sh launch_controller.sh
```

**2. Launch the model workers.**  
Before running, modify `MODEL_PATH` and `NUM_GPUS`, `GPU_IDS` variables in `launch_worker_vllm.sh`. 
Wait until the process finishes loading the model and you see "Uvicorn running on ...". The model worker will register itself to the controller.  
```bash
sh launch_worker_vllm.sh
```

**3. Launch semantic parser.**  
Befor running, modify `CKPT_PATH` and `GPU_ID` variables in `launch_semantic_parser.sh`.  
```bash
sh launch_semantic_parser.sh
```

**4. Launch the Gradio web server.**
```bash
sh launch_gradio.sh
```

**5. Launch Program Editing Interface.**  
Make sure you have installed required packages before running code below.   
Refer [README](frontend-src/KoPL-vis/README.md) for package installation guide. 

```bash
cd DiaKoP/frontend-src/KoPL-vis/vis
npm run serve
```

**6. Deploying KoPL execution engine.**  
Please refer [Github](https://github.com/THU-KEG/KoPL) on how to deploy a KoPL program execution engine. 
After deploying the engine, modify the API link in the env variable `KOPL_EXEC_ENGINE_API`  in `launch_gradio.sh`.

## Note
To use glm-3-turbo api, create .env file and add your api key, example below:
```
CHATGLM_PRO_API_KEY=<YOUR API KEY>
```  
This API does not adopt the proposed multi-turn question-answering backend.
