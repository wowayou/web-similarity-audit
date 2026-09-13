#!/bin/bash
# 项目打包脚本 - 生成可迁移的发布包

set -e

PROJECT_NAME="web-similarity-audit"
VERSION=$(grep "version =" pyproject.toml | cut -d'"' -f2)
PACKAGE_NAME="${PROJECT_NAME}-${VERSION}"

echo "📦 打包 ${PACKAGE_NAME}..."

# 创建临时目录
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="${TEMP_DIR}/${PACKAGE_NAME}"

# 复制必要文件
echo "📋 复制文件..."
mkdir -p "${PACKAGE_DIR}"
cp -r src "${PACKAGE_DIR}/"
cp -r tests "${PACKAGE_DIR}/"
cp -r examples "${PACKAGE_DIR}/"
cp -r .github "${PACKAGE_DIR}/"
cp pyproject.toml "${PACKAGE_DIR}/"
cp README.md "${PACKAGE_DIR}/"
cp CHANGELOG.md "${PACKAGE_DIR}/"
cp LICENSE "${PACKAGE_DIR}/"
cp DEMO.md "${PACKAGE_DIR}/"
cp FINAL_PACKAGE.md "${PACKAGE_DIR}/"
cp .gitignore "${PACKAGE_DIR}/"

# 创建安装脚本
cat > "${PACKAGE_DIR}/install.sh" << 'EOF'
#!/bin/bash
echo "🚀 安装 web-similarity-audit..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
echo "✅ 安装完成！"
echo ""
echo "使用方法："
echo "  source venv/bin/activate"
echo "  web-similarity-audit --help"
EOF
chmod +x "${PACKAGE_DIR}/install.sh"

cat > "${PACKAGE_DIR}/install.bat" << 'EOF'
@echo off
echo 🚀 安装 web-similarity-audit...
python -m venv venv
call venv\Scripts\activate
pip install --upgrade pip
pip install -e .
echo ✅ 安装完成！
echo.
echo 使用方法：
echo   venv\Scripts\activate
echo   web-similarity-audit --help
EOF

# 创建 README
cat > "${PACKAGE_DIR}/INSTALL.txt" << 'EOF'
Web Similarity Audit - 安装指南
================================

## Linux/macOS 安装

1. 解压包：
   tar -xzf web-similarity-audit-*.tar.gz
   cd web-similarity-audit-*

2. 运行安装脚本：
   ./install.sh

3. 激活环境：
   source venv/bin/activate

4. 测试：
   web-similarity-audit --help
   pytest tests/ -v

## Windows 安装

1. 解压包到任意目录

2. 双击运行 install.bat

3. 激活环境：
   venv\Scripts\activate

4. 测试：
   web-similarity-audit --help
   pytest tests/ -v

## 手动安装

如果自动脚本失败：

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -e .

## 快速开始

# 整站审计
web-similarity-audit --crawl https://example.com --max-pages 50

# URL 列表审计
web-similarity-audit url1 url2 url3

# 查看结果
cat audit-results/report.md

详细文档请查看 README.md 和 DEMO.md
EOF

# 打包
echo "📦 压缩..."
cd "${TEMP_DIR}"
tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"
zip -r "${PACKAGE_NAME}.zip" "${PACKAGE_NAME}" > /dev/null 2>&1 || echo "⚠️  zip 不可用，跳过 .zip 生成"

# 移动到项目目录
OUTPUT_DIR="${OLDPWD}/dist"
mkdir -p "${OUTPUT_DIR}"
mv "${PACKAGE_NAME}.tar.gz" "${OUTPUT_DIR}/"
[ -f "${PACKAGE_NAME}.zip" ] && mv "${PACKAGE_NAME}.zip" "${OUTPUT_DIR}/"

# 清理
rm -rf "${TEMP_DIR}"

echo "✅ 打包完成！"
echo ""
echo "输出位置："
echo "  ${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz"
[ -f "${OUTPUT_DIR}/${PACKAGE_NAME}.zip" ] && echo "  ${OUTPUT_DIR}/${PACKAGE_NAME}.zip"
echo ""
echo "迁移到另一台机器："
echo "  scp ${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz user@remote:/path/"
echo "  ssh user@remote"
echo "  cd /path && tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "  cd ${PACKAGE_NAME} && ./install.sh"
