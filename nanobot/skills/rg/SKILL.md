---
name: rg
description: "使用 ripgrep (rg) 进行快速代码搜索。支持在代码库中搜索文本模式，自动遵循 .gitignore，支持正则表达式，搜索速度快。"
metadata:
  requires:
    bins: ["rg"]
  install:
    - id: brew
      kind: brew
      formula: ripgrep
      bins: ["rg"]
      label: "安装 ripgrep (brew)"
    - id: apt
      kind: apt
      package: ripgrep
      bins: ["rg"]
      label: "安装 ripgrep (apt)"
---

# ripgrep (rg) 技能

快速递归搜索工具，默认遵循 `.gitignore` 文件。

## 快速开始

```bash
rg "pattern"                    # 在当前目录搜索模式
rg "pattern" /path/to/dir       # 在指定目录搜索
rg -i "pattern"                 # 忽略大小写搜索
rg -l "pattern"                 # 只列出匹配的文件
rg -n "pattern"                 # 显示行号（默认）
rg -C 3 "pattern"               # 显示匹配行前后3行上下文
```

## 常用选项

| 选项 | 说明 |
|------|------|
| `-i` | 忽略大小写 |
| `-v` | 反向匹配（排除） |
| `-l` | 只列出匹配的文件 |
| `-L` | 只列出不匹配的文件 |
| `-n` | 显示行号 |
| `-N` | 隐藏行号 |
| `-c` | 统计每个文件的匹配数 |
| `-C N` | 显示匹配行前后 N 行上下文 |
| `-B N` | 显示匹配行前 N 行 |
| `-A N` | 显示匹配行后 N 行 |
| `-w` | 匹配整个单词 |
| `-F` | 固定字符串（不使用正则） |
| `-t TYPE` | 按文件类型过滤（如 `-t py`、`-t js`） |
| `-g GLOB` | 包含/排除 glob 模式 |
| `--hidden` | 搜索隐藏文件 |
| `--no-ignore` | 不遵循 .gitignore |
| `--max-depth N` | 限制搜索深度 |

## 文件类型过滤

```bash
rg "function" -t py             # 只搜索 Python 文件
rg "import" -t js -t ts         # 搜索 JS 和 TS 文件
rg --type-list                  # 列出所有文件类型
```

## 高级模式

```bash
rg "class \w+"                  # 正则：class 后跟单词
rg "TODO|FIXME"                 # 匹配任一模式
rg "^def " -t py                # 以 "def " 开头的行
rg "\basync\b"                  # 单词边界匹配
```

## 实用示例

```bash
# 查找 Python 文件中的所有 TODO 注释
rg "TODO|FIXME|XXX" -t py

# 搜索函数定义
rg "^\s*def \w+" -t py
rg "^\s*function\s+\w+" -t js

# 查找导入特定模块的文件
rg "^import requests" -t py -l

# 只在特定目录中搜索
rg "pattern" --glob="*.md" --glob="*.txt"

# 排除目录
rg "pattern" -g '!node_modules/' -g '!*.log'

# 带上下文搜索，便于理解
rg -C 5 "class User" -t py
```

## 与 grep 对比

| 任务 | grep | rg |
|------|------|-----|
| 递归搜索 | `grep -r` | `rg`（默认） |
| 遵循 .gitignore | 手动配置 | 自动遵循 |
| 速度 | 较慢 | 更快 |
| 默认输出 | 无行号 | 带行号 |
| 文件类型过滤 | 手动 | 内置 (`-t`) |

## 使用技巧

1. **使用 `-l`** 当你只需要知道哪些文件包含该模式时
2. **使用 `-C N`** 查看匹配行周围的上下文
3. **使用 `-t`** 进行特定语言的搜索
4. **使用 `-F`** 搜索包含特殊字符的纯文本字符串时
5. **使用 `--hidden`** 包含点文件（隐藏文件）在搜索中
