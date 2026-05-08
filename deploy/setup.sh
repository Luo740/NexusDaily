#!/bin/bash
# ============================================
# NexusDaily 服务器部署脚本
# 用途：首次部署或更新后在服务器上执行
# 用法：chmod +x deploy/setup.sh && ./deploy/setup.sh
# ============================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="nexusdaily"

echo "=== NexusDaily 部署脚本 ==="

# 1. 复制 systemd 配置文件到系统目录
echo "[1/4] 安装 systemd 单元文件..."
sudo cp deploy/nexusdaily.service /etc/systemd/system/
sudo cp deploy/nexusdaily.timer /etc/systemd/system/

# 2. 重新加载 systemd 配置
echo "[2/4] 重载 systemd..."
sudo systemctl daemon-reload

# 3. 启用并启动定时器
echo "[3/4] 启用定时器（开机自启 + 立即生效）..."
sudo systemctl enable nexusdaily.timer
sudo systemctl start nexusdaily.timer

# 4. 验证状态
echo "[4/4] 验证部署状态..."
echo ""
echo "--- timer 状态 ---"
sudo systemctl status nexusdaily.timer --no-pager
echo ""
echo "--- 下一次触发时间 ---"
systemctl list-timers nexusdaily.timer --no-pager

echo ""
echo "=== 部署完成 ==="
echo ""
echo "常用命令："
echo "  手动触发一次:    sudo systemctl start nexusdaily.service"
echo "  查看运行日志:    sudo journalctl -u nexusdaily.service -f"
echo "  查看定时器状态:  systemctl list-timers nexusdaily.timer"
echo "  停止定时器:      sudo systemctl stop nexusdaily.timer"
echo "  禁用定时器:      sudo systemctl disable nexusdaily.timer"
