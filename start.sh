#!/bin/bash

# Neo4j LangChain Backend 启动脚本

set -e

echo "=========================================="
echo "Neo4j LangChain Backend 启动脚本"
echo "=========================================="

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "警告: .env文件不存在，从.env.example复制..."
    cp .env.example .env
    echo "请编辑.env文件，配置必要的环境变量"
    echo "特别是以下变量："
    echo "  - OPENAI_API_KEY"
    echo "  - SECRET_KEY"
    echo "  - OSS_ACCESS_KEY_ID"
    echo "  - OSS_ACCESS_KEY_SECRET"
    echo "  - OSS_BUCKET_NAME"
    echo "  - OSS_ENDPOINT"
    echo ""
    read -p "是否继续启动？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 构建并启动服务
echo "正在构建Docker镜像..."
docker-compose build

echo "正在启动服务..."
docker-compose up -d

echo ""
echo "=========================================="
echo "服务启动中，请稍候..."
echo "=========================================="

# 等待服务启动
echo "等待MySQL启动..."
sleep 10

echo "等待Neo4j启动..."
sleep 10

echo "等待Redis启动..."
sleep 5

echo "等待应用启动..."
sleep 10

echo ""
echo "=========================================="
echo "服务启动完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  - API文档: http://localhost:8000/docs"
echo "  - 健康检查: http://localhost:8000/health"
echo "  - Neo4j浏览器: http://localhost:7474"
echo ""
echo "查看日志："
echo "  docker-compose logs -f app"
echo ""
echo "停止服务："
echo "  docker-compose down"
echo ""
