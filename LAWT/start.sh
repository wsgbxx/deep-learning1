#!/bin/bash

# LAWT项目启动脚本

echo "🚀 启动LAWT (Linear Algebra with Transformers) 系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查必要的Python包
echo "📦 检查Python依赖..."
python3 -c "import numpy" 2>/dev/null || {
    echo "❌ 错误: 未找到NumPy，请运行: pip install numpy"
    exit 1
}

# 创建必要的目录
mkdir -p frontend
mkdir -p logs

# 设置权限
chmod +x server.py

# 启动服务器
echo "🌐 启动前端服务器..."
echo "📍 服务器地址: http://localhost:8080"
echo "📍 服务器地址: http://59.110.18.228:8080 (公网访问)"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动服务器
python3 server.py 8080
