HOST=0.0.0.0
PORT=6061
CKPT_PATH="<PATH>"
GPU_ID=1

CUDA_VISIBLE_DEVICES=$GPU_ID python ../backend-src/semantic_parser.py \
        --host $HOST \
        --port $PORT \
        --ckpt $CKPT_PATH