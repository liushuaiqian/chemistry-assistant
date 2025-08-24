# 化学助手项目 Docker 部署指南

本文档提供了化学助手项目的完整Docker部署方案，包括单机部署和生产环境部署配置。

## 📋 目录

- [快速开始](#快速开始)
- [环境要求](#环境要求)
- [配置说明](#配置说明)
- [部署方式](#部署方式)
- [管理命令](#管理命令)
- [故障排除](#故障排除)
- [性能优化](#性能优化)
- [安全配置](#安全配置)

## 🚀 快速开始

### 1. 环境准备

确保您的系统已安装以下软件：

- **Docker**: 20.10.0+
- **Docker Compose**: 2.0.0+
- **Git**: 用于克隆项目

#### Windows 安装
```bash
# 下载并安装 Docker Desktop
# https://www.docker.com/products/docker-desktop

# 验证安装
docker --version
docker-compose --version
```

#### Linux 安装
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# CentOS/RHEL
sudo yum install docker docker-compose

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. 项目准备

```bash
# 进入项目目录
cd chemistry-assistant

# 进入Docker配置目录
cd Docker
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.docker .env.docker.local

# 编辑配置文件
nano .env.docker.local  # Linux
notepad .env.docker.local  # Windows
```

**必须配置的API密钥：**
```bash
# 至少配置以下一个API密钥
ZHIPU_API_KEY=your_zhipu_api_key_here
TONGYI_API_KEY=your_tongyi_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. 启动服务

#### Windows
```cmd
# 使用批处理脚本
start-docker.bat start

# 或手动启动
docker-compose up -d
```

#### Linux/macOS
```bash
# 使用Shell脚本
./start-docker.sh start

# 或手动启动
docker-compose up -d
```

### 5. 访问应用

启动成功后，访问以下地址：

- **Web界面**: http://localhost:7860
- **健康检查**: http://localhost:7860/health

## 📋 环境要求

### 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 存储 | 10GB | 20GB+ |
| 网络 | 稳定互联网连接 | 高速宽带 |

### Docker要求

- **Docker Engine**: 20.10.0+
- **Docker Compose**: 2.0.0+
- **可用内存**: 至少4GB分配给Docker
- **可用存储**: 至少10GB用于镜像和数据

## ⚙️ 配置说明

### 环境变量配置

#### 核心配置
```bash
# API密钥配置 (必填)
ZHIPU_API_KEY=your_zhipu_api_key
TONGYI_API_KEY=your_tongyi_api_key
OPENAI_API_KEY=your_openai_api_key

# 应用配置
WEB_PORT=7860
LOG_LEVEL=INFO
ENABLE_ADAPTIVE=true
USE_RERANKER=true
```

#### 性能配置
```bash
# 并发配置
MAX_WORKERS=4
MAX_CONCURRENT_REQUESTS=10

# 超时配置
REQUEST_TIMEOUT=60
API_TIMEOUT=30

# 缓存配置
ENABLE_CACHE=true
CACHE_TTL=3600
```

#### 安全配置
```bash
# 访问控制
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=*

# JWT配置 (如果启用认证)
JWT_SECRET_KEY=your_secret_key
```

### Docker Compose 服务

#### 主要服务

1. **chemistry-assistant**: 主应用服务
   - 端口: 7860
   - 资源限制: 4GB内存, 2CPU
   - 健康检查: 启用

2. **redis** (可选): 缓存服务
   - 端口: 6379
   - 数据持久化: 启用

3. **nginx** (可选): 反向代理
   - 端口: 80, 443
   - SSL支持: 可配置

#### 服务启用/禁用

```yaml
# 禁用Redis服务
# 注释掉docker-compose.yml中的redis部分

# 禁用Nginx服务
# 注释掉docker-compose.yml中的nginx部分
```

## 🛠️ 部署方式

### 开发环境部署

```bash
# 启动基础服务
docker-compose up chemistry-assistant

# 查看日志
docker-compose logs -f chemistry-assistant
```

### 生产环境部署

```bash
# 启动所有服务
docker-compose up -d

# 检查服务状态
docker-compose ps

# 查看资源使用
docker stats
```

### 集群部署 (Docker Swarm)

```bash
# 初始化Swarm
docker swarm init

# 部署Stack
docker stack deploy -c docker-compose.yml chemistry

# 查看服务
docker service ls
```

## 📝 管理命令

### 使用管理脚本

#### Windows
```cmd
start-docker.bat [命令]

# 可用命令:
start-docker.bat start    # 启动服务
start-docker.bat stop     # 停止服务
start-docker.bat restart  # 重启服务
start-docker.bat build    # 构建镜像
start-docker.bat logs     # 查看日志
start-docker.bat status   # 查看状态
start-docker.bat cleanup  # 清理资源
```

#### Linux/macOS
```bash
./start-docker.sh [命令]

# 可用命令:
./start-docker.sh start    # 启动服务
./start-docker.sh stop     # 停止服务
./start-docker.sh restart  # 重启服务
./start-docker.sh build    # 构建镜像
./start-docker.sh logs     # 查看日志
./start-docker.sh status   # 查看状态
./start-docker.sh cleanup  # 清理资源
```

### 手动管理命令

#### 基础操作
```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f [service_name]
```

#### 镜像管理
```bash
# 构建镜像
docker-compose build --no-cache

# 拉取镜像
docker-compose pull

# 删除镜像
docker-compose down --rmi all
```

#### 数据管理
```bash
# 备份数据
docker run --rm -v chemistry-assistant_chemistry-data:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz -C /data .

# 恢复数据
docker run --rm -v chemistry-assistant_chemistry-data:/data -v $(pwd):/backup alpine tar xzf /backup/data-backup.tar.gz -C /data

# 清理数据
docker-compose down -v
```

## 🔧 故障排除

### 常见问题

#### 1. 服务启动失败

**症状**: 容器无法启动或立即退出

**解决方案**:
```bash
# 查看详细日志
docker-compose logs chemistry-assistant

# 检查配置文件
docker-compose config

# 检查端口占用
netstat -tulpn | grep 7860  # Linux
netstat -an | findstr 7860  # Windows
```

#### 2. API密钥配置错误

**症状**: 应用启动但无法调用AI模型

**解决方案**:
```bash
# 检查环境变量
docker-compose exec chemistry-assistant env | grep API_KEY

# 重新配置环境变量
vim .env.docker
docker-compose restart
```

#### 3. 内存不足

**症状**: 容器被OOM Killer终止

**解决方案**:
```bash
# 检查内存使用
docker stats

# 调整内存限制
# 编辑docker-compose.yml中的memory限制

# 增加系统内存或减少并发数
```

#### 4. 网络连接问题

**症状**: 无法访问外部API或Web界面

**解决方案**:
```bash
# 检查网络配置
docker network ls
docker network inspect chemistry-assistant_chemistry-net

# 重建网络
docker-compose down
docker network prune
docker-compose up -d
```

### 日志分析

#### 应用日志
```bash
# 实时查看日志
docker-compose logs -f chemistry-assistant

# 查看最近的日志
docker-compose logs --tail=100 chemistry-assistant

# 查看特定时间的日志
docker-compose logs --since="2024-01-01T00:00:00" chemistry-assistant
```

#### 系统日志
```bash
# Docker守护进程日志
sudo journalctl -u docker.service  # Linux

# 容器系统日志
docker exec chemistry-assistant tail -f /var/log/syslog
```

### 性能监控

```bash
# 资源使用监控
docker stats --no-stream

# 详细性能信息
docker exec chemistry-assistant top
docker exec chemistry-assistant free -h
docker exec chemistry-assistant df -h
```

## ⚡ 性能优化

### 资源配置优化

#### CPU优化
```yaml
# docker-compose.yml
services:
  chemistry-assistant:
    deploy:
      resources:
        limits:
          cpus: '4.0'  # 根据实际CPU核数调整
        reservations:
          cpus: '2.0'
```

#### 内存优化
```yaml
# docker-compose.yml
services:
  chemistry-assistant:
    deploy:
      resources:
        limits:
          memory: 8G  # 根据实际内存调整
        reservations:
          memory: 4G
```

#### 存储优化
```yaml
# 使用SSD存储
volumes:
  chemistry-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/ssd/storage
```

### 应用配置优化

#### 并发配置
```bash
# .env.docker
MAX_WORKERS=8  # 根据CPU核数调整
MAX_CONCURRENT_REQUESTS=20
```

#### 缓存配置
```bash
# 启用Redis缓存
ENABLE_CACHE=true
CACHE_TTL=7200
REDIS_HOST=redis
```

#### 超时配置
```bash
# 根据网络情况调整
REQUEST_TIMEOUT=120
API_TIMEOUT=60
KNOWLEDGE_API_TIMEOUT=90
```

### 网络优化

#### Nginx配置
```nginx
# nginx/nginx.conf
worker_processes auto;
worker_connections 2048;

# 启用HTTP/2
listen 443 ssl http2;

# 启用缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🔒 安全配置

### SSL/TLS配置

#### 生成自签名证书
```bash
# 创建SSL目录
mkdir -p nginx/ssl

# 生成私钥
openssl genrsa -out nginx/ssl/key.pem 2048

# 生成证书
openssl req -new -x509 -key nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365
```

#### 使用Let's Encrypt
```bash
# 安装certbot
sudo apt install certbot

# 获取证书
sudo certbot certonly --standalone -d your-domain.com

# 配置自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 访问控制

#### IP白名单
```nginx
# nginx/nginx.conf
server {
    # 只允许特定IP访问
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
}
```

#### 基础认证
```nginx
# 生成密码文件
htpasswd -c nginx/.htpasswd admin

# nginx配置
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

### 环境变量安全

```bash
# 设置文件权限
chmod 600 .env.docker

# 使用Docker secrets (Swarm模式)
docker secret create zhipu_api_key zhipu_key.txt
```

### 容器安全

```yaml
# docker-compose.yml
services:
  chemistry-assistant:
    # 使用非root用户
    user: "1000:1000"
    
    # 只读根文件系统
    read_only: true
    
    # 临时文件系统
    tmpfs:
      - /tmp
      - /var/tmp
    
    # 安全选项
    security_opt:
      - no-new-privileges:true
    
    # 限制能力
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
```

## 📚 附录

### 文件结构

```
Docker/
├── README.md              # 本文档
├── Dockerfile             # Docker镜像构建文件
├── docker-compose.yml     # Docker Compose配置
├── .dockerignore          # Docker忽略文件
├── .env.docker            # 环境变量模板
├── start-docker.sh        # Linux启动脚本
├── start-docker.bat       # Windows启动脚本
└── nginx/
    └── nginx.conf         # Nginx配置文件
```

### 端口说明

| 服务 | 内部端口 | 外部端口 | 说明 |
|------|----------|----------|------|
| chemistry-assistant | 7860 | 7860 | Web界面 |
| redis | 6379 | 6379 | 缓存服务 |
| nginx | 80/443 | 80/443 | 反向代理 |

### 环境变量参考

完整的环境变量列表请参考 `.env.docker` 文件。

### 相关链接

- [Docker官方文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [Nginx官方文档](https://nginx.org/en/docs/)
- [项目主页](../README.md)

---

## 📞 支持

如果您在部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目的Issue页面
3. 提交新的Issue并提供详细的错误信息

---

**最后更新**: 2024年1月
**版本**: 1.0.0