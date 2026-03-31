#!/bin/bash
# ppt-master 安装脚本（灵活版）

set -e

echo "============================================"
echo "  ppt-master 安装脚本"
echo "============================================"
echo ""

# 检测操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
else
    OS="Windows (请使用 PowerShell)"
fi

echo "检测到操作系统: $OS"
echo ""

# 查找 tar.gz 位置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TGZ_FILE=""

if [ -f "$SCRIPT_DIR/ppt-master.tar.gz" ]; then
    TGZ_FILE="$SCRIPT_DIR/ppt-master.tar.gz"
elif [ -f "$HOME/ppt-master.tar.gz" ]; then
    TGZ_FILE="$HOME/ppt-master.tar.gz"
elif [ -f "$(pwd)/ppt-master.tar.gz" ]; then
    TGZ_FILE="$(pwd)/ppt-master.tar.gz"
fi

if [ -z "$TGZ_FILE" ]; then
    echo "[错误] 未找到 ppt-master.tar.gz"
    echo "请将此脚本和 tar.gz 放在同一目录"
    exit 1
fi

echo "找到安装包: $TGZ_FILE"
echo ""

# 让用户选择安装目录
echo "请选择安装目录（输入编号或直接输入路径）:"
echo ""
echo "  1. ~/.claude/skills/ppt-master  (Claude Code 用户)"
echo "  2. ~/tools/ppt-master           (自定义工具目录)"
echo "  3. 自定义路径"
echo ""

read -p "请输入 [1/2/3]: " choice

case $choice in
    1)
        INSTALL_DIR="$HOME/.claude/skills/ppt-master"
        mkdir -p "$HOME/.claude/skills"
        ;;
    2)
        INSTALL_DIR="$HOME/tools/ppt-master"
        mkdir -p "$HOME/tools"
        ;;
    3)
        echo -n "请输入完整路径: "
        read CUSTOM_PATH
        INSTALL_DIR="$CUSTOM_PATH"
        mkdir -p "$INSTALL_DIR"
        ;;
    *)
        echo "[信息] 使用默认路径 ~/.claude/skills/ppt-master"
        INSTALL_DIR="$HOME/.claude/skills/ppt-master"
        mkdir -p "$HOME/.claude/skills"
        ;;
esac

echo ""
echo "[1/3] 解压到 $INSTALL_DIR ..."

# 解压
rm -rf "$INSTALL_DIR"
tar -xzvf "$TGZ_FILE"
mv ppt-master-pkg "$INSTALL_DIR"

echo ""
echo "[2/3] 安装 Python 依赖 ..."

cd "$INSTALL_DIR"

if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt
else
    echo "[错误] 未找到 pip，请先安装 Python"
    exit 1
fi

echo ""
echo "[3/3] 检查系统依赖 ..."

if [[ "$OS" == "macOS" ]]; then
    if ! command -v pandoc &> /dev/null; then
        echo "[建议] 运行以下命令安装 pandoc:"
        echo "  brew install pandoc"
    fi
elif [[ "$OS" == "Linux" ]]; then
    if ! command -v pandoc &> /dev/null; then
        echo "[建议] 运行以下命令安装 pandoc:"
        echo "  sudo apt install pandoc"
    fi
fi

echo ""
echo "============================================"
echo "  安装完成！"
echo "============================================"
echo ""
echo "安装位置: $INSTALL_DIR"
echo ""
echo "下一步:"
if [[ "$INSTALL_DIR" == *".claude/skills"* ]]; then
    echo "  在 Claude Code 中使用 /learn ppt-master"
else
    echo "  在 Claude Code 中指定路径或添加到 PATH"
    echo "  例如: export PATH=\"\$PATH:$INSTALL_DIR/scripts\""
fi
echo ""
