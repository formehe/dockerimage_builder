#!/bin/bash

# 捕获退出信号
trap 'exit_handler' SIGTERM SIGINT

exit_handler() {
    echo "Stopping services..."
    # 停止所有后台进程
    kill $(jobs -p)
    wait
    echo "Services stopped. Exiting."
    exit 0
}

# 启动 Docker 守护进程
dockerd-entrypoint.sh &

echo "docker-entrypoint.sh run successful"

# 定义检查间隔时间（秒）
CHECK_INTERVAL=3

# 循环检查文件是否存在
while true; do
    if [[ -e /var/run/docker.sock && -e /etc/config/config.ini ]]; then
        echo "/var/run/docker.sock and /etc/config/config.ini exists."
        break
    else
        echo "/var/run/docker.sock or /etc/config/config.ini does not exist. Checking again in $CHECK_INTERVAL seconds."
        sleep $CHECK_INTERVAL
    fi
done

# 启动 Python 应用程序
python3 app.py --config /etc/config/config.ini &

echo "app run successful"
# 等待所有后台进程
wait
echo "all apps are exited"