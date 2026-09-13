#!/bin/bash
# 项目统计脚本

echo "📊 Web Similarity Audit - 项目统计"
echo "===================================="
echo ""

# 代码统计
echo "📝 代码统计"
echo "----------"
echo "核心模块:"
wc -l src/web_similarity_audit/*.py | grep -v __pycache__ | tail -n +1
echo ""

echo "测试代码:"
wc -l tests/*.py tests/fixtures/*.py 2>/dev/null | tail -n +1
echo ""

echo "示例代码:"
wc -l examples/*.py 2>/dev/null | tail -n +1
echo ""

# 文档统计
echo "📚 文档统计"
echo "----------"
find . -name "*.md" -type f | grep -v venv | grep -v node_modules | while read file; do
    lines=$(wc -l < "$file")
    printf "%-40s %6d 行\n" "$file" "$lines"
done
echo ""

# 测试统计
echo "🧪 测试统计"
echo "----------"
if [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null
fi
test_count=$(pytest --collect-only -q 2>/dev/null | tail -1 | awk '{print $1}')
echo "测试数量: ${test_count:-未知}"
echo ""

# 依赖统计
echo "📦 依赖统计"
echo "----------"
echo "直接依赖:"
grep "dependencies = " pyproject.toml -A 10 | grep '"' | head -4
echo ""

# 文件统计
echo "📁 文件统计"
echo "----------"
echo "Python 文件: $(find src tests examples -name "*.py" 2>/dev/null | wc -l)"
echo "Markdown 文件: $(find . -name "*.md" -not -path "*/venv/*" 2>/dev/null | wc -l)"
echo "配置文件: $(find . -maxdepth 1 -name "*.toml" -o -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l)"
echo ""

# 发布包大小
echo "📦 发布包"
echo "--------"
if [ -f "dist/web-similarity-audit-0.1.0.tar.gz" ]; then
    ls -lh dist/web-similarity-audit-0.1.0.tar.gz | awk '{print "大小: " $5}'
else
    echo "未找到发布包 (运行 ./package.sh 生成)"
fi
echo ""

# Git 统计（如果有）
if [ -d ".git" ]; then
    echo "📊 Git 统计"
    echo "----------"
    echo "提交数: $(git rev-list --all --count 2>/dev/null || echo '未初始化')"
    echo "分支数: $(git branch 2>/dev/null | wc -l || echo '未初始化')"
    echo ""
fi

echo "✅ 统计完成"
