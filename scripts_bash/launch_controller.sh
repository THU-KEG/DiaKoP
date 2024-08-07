PORT=3836

export LOGDIR="logs"
mkdir -p $LOGDIR
python -m fastchat.serve.controller --port $PORT --host 0.0.0.0
