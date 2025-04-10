#!/bin/bash

# 激活虚拟环境（如果有的话）
# source venv/bin/activate

# 使用gunicorn启动服务器
gunicorn -w 4 -b 0.0.0.0:5001 server:app 