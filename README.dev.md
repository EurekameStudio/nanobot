# nanobot 开发指南

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [Git 工作流](#git-工作流)
- [开发工具配置](#开发工具配置)
- [代码规范](#代码规范)
- [测试](#测试)
- [常用命令速查](#常用命令速查)

---

## 环境要求

- **Python**: 3.11+ (推荐 3.12)
- **Git**: 2.x
- **包管理器**: uv pip

## 快速开始

### 1. Fork & Clone

```bash
# 1. Clone
git clone https://github.com/EurekameStudio/nanobot
cd nanobot

# 2. 验证 remote 配置
git remote -v
# 输出应包含:
# origin    https://github.com/<你的用户名>/nanobot.git (fetch)
# origin    https://github.com/<你的用户名>/nanobot.git (push)
# upstream  https://github.com/HKUDS/nanobot.git (fetch)
# upstream  https://github.com/HKUDS/nanobot.git (push)
```

### 2. 安装依赖

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv sync # venv 会被自动创建
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装项目及开发依赖
uv pip install -e "."
```

### 3. 验证安装

```bash
# 运行测试
pytest

# 检查代码
ruff check nanobot/
```

---

## Git 工作流

### 创建功能分支

```bash
# 从 upstream 创建功能分支
git fetch upstream
git checkout -b feature/my-feature upstream/main  # 或 upstream/main

# 推送到你的 fork
git push -u origin feature/my-feature
```

### 同步 upstream 到功能分支

**Rebase (推荐，保持线性历史)**

```bash
# 1. 确保在功能分支上
git checkout feature/my-feature

# 2. 获取 upstream 最新代码
git fetch upstream

# 3. 变基到 upstream 的目标分支
git rebase upstream/nightly  # 或 upstream/main

# 4. 解决冲突（如果有）
#    - 查看冲突文件: git status
#    - 编辑冲突文件，解决冲突标记
#    - 标记已解决: git add <file>
#    - 继续 rebase: git rebase --continue

# 5. 强制推送（因为历史被重写）
git push origin feature/my-feature --force
```

### Git 配置技巧

```bash
# 设置默认编辑器
git config --global core.editor "vi"

# 设置 pull 默认使用 rebase
git config --global pull.rebase true

# 设置用户信息
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

## 开发工具配置

### VS Code 配置

推荐安装扩展:
- **Python** (ms-python.python)
- **Ruff** (charliermarsh.ruff)
- **Pylance** (ms-python.vscode-pylance)

---

## 代码规范

### Linting & Formatting

项目使用 [Ruff](https://docs.astral.sh/ruff/) 进行代码检查和格式化:

```bash
# 检查代码问题
ruff check nanobot/

# 自动修复可修复的问题
ruff check --fix nanobot/

# 格式化代码
ruff format nanobot/
```

### 代码风格指南

- **简洁**: 用最小的改动解决真正的问题
- **清晰**: 为下一个读者优化，而不是展示技巧
- **解耦**: 保持边界清晰，避免不必要的抽象
- **诚实**: 不隐藏复杂性，也不制造额外的复杂性
- **耐用**: 选择易于维护、测试和扩展的方案

---

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定测试文件
pytest tests/channels/test_feishu_reply.py

# 运行指定测试函数
pytest tests/channels/test_feishu_reply.py::test_reply_to_message

# 显示详细输出
pytest -v

# 显示 print 输出
pytest -s

# 只运行失败的测试
pytest --lf

# 停止于第一个失败
pytest -x
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=nanobot

# 生成 HTML 覆盖率报告
pytest --cov=nanobot --cov-report=html
# 然后打开 htmlcov/index.html
```

### 异步测试

项目使用 `pytest-asyncio`，异步测试自动支持:

```python
# 测试文件示例
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

---

## 常用命令速查

### Git 命令

| 操作 | 命令 |
|------|------|
| 查看状态 | `git status` |
| 查看远程 | `git remote -v` |
| 获取更新 | `git fetch upstream` |
| 切换分支 | `git checkout <branch>` |
| 创建分支 | `git checkout -b <new-branch> <base>` |
| 暂存更改 | `git stash` |
| 恢复暂存 | `git stash pop` |
| 查看日志 | `git log --oneline -20` |
| 撤销未提交更改 | `git checkout -- <file>` |
| 撤销最后一次 commit | `git reset HEAD~1` |

### Python/开发命令

| 操作 | 命令 |
|------|------|
| 激活虚拟环境 | `source .venv/bin/activate` |
| 安装依赖 | `pip install -e ".[dev]"` |
| 运行测试 | `pytest` |
| 代码检查 | `ruff check nanobot/` |
| 代码格式化 | `ruff format nanobot/` |
| 启动 nanobot | `nanobot` 或 `python -m nanobot` |

---

## 提交 PR

1. 确保所有测试通过: `pytest`
2. 确保代码符合规范: `ruff check nanobot/`
3. 推送到你的 fork: `git push origin feature/my-feature`
4. 在 GitHub 上创建 Pull Request
5. 选择正确的目标分支 (`main` 或 `nightly`)