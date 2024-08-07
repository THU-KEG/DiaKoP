# old gradio version 3.50.2
HOST=0.0.0.0
PORT=3860
PROGRAM_EDITING_PORT=8080
WORKER_ADDRESS=http://localhost:3837
CONTROLLER_ADDRESS=http://localhost:3836
KOPL_EXEC_ENGINE_ADDRESS="<change your address here>" # url to kopl execution engine

export LOGDIR="logs"
mkdir -p $LOGDIR

python ../frontend-src/scripts/gradio_web_server.py \
        --host $HOST \
        --port $PORT \
        --program-editing-port $PROGRAM_EDITING_PORT \
        --controller-url $CONTROLLER_ADDRESS \
        --kopl-exec-engine-url $KOPL_EXEC_ENGINE_ADDRESS \
        --add-chatglm-pro 