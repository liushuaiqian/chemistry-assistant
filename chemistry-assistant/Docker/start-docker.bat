@echo off
REM 化学助手项目 Docker 启动脚本 (Windows版本)
REM 用于快速启动和管理Docker容器

setlocal enabledelayedexpansion

REM 项目信息
set PROJECT_NAME=chemistry-assistant
set DOCKER_DIR=%~dp0
set PROJECT_DIR=%DOCKER_DIR%..\

REM 颜色定义 (Windows 10+)
for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RED=%ESC%[91m"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "BLUE=%ESC%[94m"
set "NC=%ESC%[0m"

REM 日志函数
:log_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %~1
goto :eof

REM 检查Docker是否安装
:check_docker
call :log_info "检查Docker环境..."

docker --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Docker未安装，请先安装Docker Desktop"
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        call :log_error "Docker Compose未安装，请先安装Docker Compose"
        pause
        exit /b 1
    )
)

call :log_success "Docker环境检查通过"
goto :eof

REM 检查环境变量文件
:check_env_file
set ENV_FILE=%DOCKER_DIR%.env.docker

if not exist "%ENV_FILE%" (
    call :log_error "环境变量文件不存在: %ENV_FILE%"
    call :log_info "请复制 .env.docker.template 并配置相应的API密钥"
    pause
    exit /b 1
)

REM 检查是否配置了API密钥
findstr /C:"your_" "%ENV_FILE%" >nul 2>&1
if not errorlevel 1 (
    call :log_warning "检测到未配置的API密钥，请确保已正确配置环境变量"
    call :log_info "编辑文件: %ENV_FILE%"
    set /p "continue=是否继续启动? (y/N): "
    if /i not "!continue!"=="y" (
        exit /b 1
    )
)

call :log_success "环境变量文件检查通过"
goto :eof

REM 创建必要的目录
:create_directories
call :log_info "检查目录结构..."

set DIRS=data\vector_store data\textbooks data\question_bank logs

for %%d in (%DIRS%) do (
    set FULL_PATH=%PROJECT_DIR%%%d
    if not exist "!FULL_PATH!" (
        mkdir "!FULL_PATH!"
        call :log_info "创建目录: !FULL_PATH!"
    )
)

call :log_success "目录结构检查完成"
goto :eof

REM 构建Docker镜像
:build_image
call :log_info "开始构建Docker镜像..."

cd /d "%DOCKER_DIR%"

docker-compose --version >nul 2>&1
if not errorlevel 1 (
    docker-compose build --no-cache
) else (
    docker compose build --no-cache
)

if errorlevel 1 (
    call :log_error "Docker镜像构建失败"
    pause
    exit /b 1
)

call :log_success "Docker镜像构建完成"
goto :eof

REM 启动服务
:start_services
call :log_info "启动化学助手服务..."

cd /d "%DOCKER_DIR%"

docker-compose --version >nul 2>&1
if not errorlevel 1 (
    docker-compose up -d
) else (
    docker compose up -d
)

if errorlevel 1 (
    call :log_error "服务启动失败"
    pause
    exit /b 1
)

call :log_success "服务启动完成"

REM 等待服务启动
call :log_info "等待服务启动..."
timeout /t 10 /nobreak >nul

REM 检查服务状态
call :check_service_status
goto :eof

REM 检查服务状态
:check_service_status
call :log_info "检查服务状态..."

cd /d "%DOCKER_DIR%"

docker-compose --version >nul 2>&1
if not errorlevel 1 (
    docker-compose ps
) else (
    docker compose ps
)

REM 检查Web服务是否可访问
set MAX_ATTEMPTS=30
set ATTEMPT=1

:check_loop
if %ATTEMPT% gtr %MAX_ATTEMPTS% goto :check_failed

curl -f http://localhost:7860/ >nul 2>&1
if not errorlevel 1 (
    call :log_success "Web服务已启动，访问地址: http://localhost:7860"
    goto :eof
)

call :log_info "等待Web服务启动... (%ATTEMPT%/%MAX_ATTEMPTS%)"
timeout /t 2 /nobreak >nul
set /a ATTEMPT+=1
goto :check_loop

:check_failed
call :log_warning "Web服务可能未正常启动，请检查日志"
goto :eof

REM 停止服务
:stop_services
call :log_info "停止化学助手服务..."

cd /d "%DOCKER_DIR%"

docker-compose --version >nul 2>&1
if not errorlevel 1 (
    docker-compose down
) else (
    docker compose down
)

call :log_success "服务已停止"
goto :eof

REM 重启服务
:restart_services
call :log_info "重启化学助手服务..."
call :stop_services
call :start_services
goto :eof

REM 查看日志
:view_logs
cd /d "%DOCKER_DIR%"

docker-compose --version >nul 2>&1
if not errorlevel 1 (
    docker-compose logs -f chemistry-assistant
) else (
    docker compose logs -f chemistry-assistant
)
goto :eof

REM 清理资源
:cleanup
call :log_info "清理Docker资源..."

cd /d "%DOCKER_DIR%"

REM 停止并删除容器
docker-compose --version >nul 2>&1
if not errorlevel 1 (
    docker-compose down -v --rmi all
) else (
    docker compose down -v --rmi all
)

REM 清理未使用的镜像
docker image prune -f

call :log_success "清理完成"
goto :eof

REM 显示帮助信息
:show_help
echo 化学助手 Docker 管理脚本 (Windows版本)
echo.
echo 用法: %~nx0 [命令]
echo.
echo 命令:
echo   start     启动服务 (默认)
echo   stop      停止服务
echo   restart   重启服务
echo   build     构建镜像
echo   logs      查看日志
echo   status    查看状态
echo   cleanup   清理资源
echo   help      显示帮助
echo.
echo 示例:
echo   %~nx0 start    # 启动服务
echo   %~nx0 logs     # 查看日志
echo   %~nx0 cleanup  # 清理所有资源
echo.
goto :eof

REM 主函数
:main
set COMMAND=%~1
if "%COMMAND%"=="" set COMMAND=start

echo ===========================================
echo 化学助手 Docker 管理脚本 (Windows版本)
echo ===========================================
echo.

if "%COMMAND%"=="start" (
    call :check_docker
    call :check_env_file
    call :create_directories
    call :start_services
) else if "%COMMAND%"=="stop" (
    call :check_docker
    call :stop_services
) else if "%COMMAND%"=="restart" (
    call :check_docker
    call :restart_services
) else if "%COMMAND%"=="build" (
    call :check_docker
    call :check_env_file
    call :create_directories
    call :build_image
) else if "%COMMAND%"=="logs" (
    call :check_docker
    call :view_logs
) else if "%COMMAND%"=="status" (
    call :check_docker
    call :check_service_status
) else if "%COMMAND%"=="cleanup" (
    call :check_docker
    call :cleanup
) else if "%COMMAND%"=="help" (
    call :show_help
) else (
    call :log_error "未知命令: %COMMAND%"
    call :show_help
    pause
    exit /b 1
)

echo.
echo 操作完成！
if "%COMMAND%"=="start" (
    echo 访问地址: http://localhost:7860
)
pause
goto :eof

REM 执行主函数
call :main %*