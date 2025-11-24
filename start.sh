#!/bin/bash

# 实体管理API服务启动脚本
# 
# 此脚本用于启动基于Flask的实体管理API服务。
# 默认在开发环境中运行，监听0.0.0.0:5000。

# 设置错误时退出
set -e

# 打印启动信息
echo "======================================"
echo "实体管理API服务启动脚本"
echo "======================================"

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "警告: .env 文件不存在，将使用默认配置"
    echo "建议创建.env文件并配置必要的环境变量"
fi

# 检查Python版本
echo "检查Python版本..."
python3 --version

# 确保依赖已安装（可选）
read -p "是否安装/更新依赖包？(y/n) " -n 1 -r
echo
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "安装依赖包..."
    python3 -m pip install -r requirements.txt
    echo "依赖包安装完成"
    echo ""
fi

# 启动服务
echo "启动Flask应用服务..."
echo "服务地址: http://0.0.0.0:5000"
echo "API文档地址: http://0.0.0.0:5000/"
echo "健康检查地址: http://0.0.0.0:5000/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo "======================================"

# 设置环境变量并运行应用
FLASK_APP=app.py FLASK_ENV=development python3 -m flask run --host=0.0.0.0 --port=5000