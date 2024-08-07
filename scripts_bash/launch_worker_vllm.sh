MODEL_PATH="<PATH>"
PORT=3837
WORKER_ADDRESS=http://localhost:3837
CONTROLLER_ADDRESS=http://localhost:3836
NUM_GPUS="4"
GPU_IDS="4,5,6,7"

export CUDA_VISIBLE_DEVICES=$GPU_IDS
export LOGDIR="logs"
mkdir -p $LOGDIR

# IMPORTANT: Set --enforce-eager for vllm 0.2.7 to prevent cuda memory leak
python -m fastchat.serve.vllm_worker --model-path $MODEL_PATH \
        --num-gpus $NUM_GPUS \
        --host 0.0.0.0 \
        --port $PORT \
        --controller-address $CONTROLLER_ADDRESS \
        --worker-address $WORKER_ADDRESS \
        --enforce-eager \
        --quantization awq