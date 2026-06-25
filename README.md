# 🛡️ AI-OPS 服务器日志智能分析系统

> 一个 AI 驱动的安全运维演示平台，集成攻击模拟、智能检测、自动救援、报告生成全流程。

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-red.svg)](https://streamlit.io/)
[![Podman](https://img.shields.io/badge/Podman-Compose-blue.svg)](https://podman.io/)
[![LLM](https://img.shields.io/badge/LLM-DeepSeek-green.svg)](https://www.deepseek.com/)

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🔫 **攻击模拟** | SQL注入 / XSS / CC洪水 / 暴力破解，支持多线程并发 |
| 🧠 **智能检测** | 规则引擎(60s滑动窗口) + DeepSeek LLM 语义分析，两阶段流水线 |
| 🚑 **自动救援** | 按 playbook 执行 iptables 封禁 → nginx 重载 → 日志审计，支持事务回滚 |
| 🔓 **解封管理** | 攻击面板 + Streamlit 双端解封，30分钟自动过期 |
| 📝 **报告生成** | LLM 驱动的 Markdown 安全事件分析报告，自动保存到磁盘 |
| 📊 **可视化图表** | 请求趋势折线图 / 攻击类型饼图 / IP 统计柱状图（matplotlib） |
| 📧 **邮件通知** | HTML 邮件 + 内嵌图表 + 报告附件，后台异步发送 |
| 🌐 **外部攻击面板** | 独立 Web 页面，同学浏览器一键发起攻击 |

---

## 🏗️ 系统架构

```
┌─ 攻击面板 (attack.html, :8080) ────┐
│  POST /api/attacks/launch           │
└──────────┬──────────────────────────┘
           │ nginx 反向代理 /api/* → attack-api:9000
           ▼
┌─ AttackAPI (FastAPI :9000) ─────────┐
│  调 AttackSimulator 发送 HTTP 请求   │
└──────────┬──────────────────────────┘
           │ 写入 access.log
           ▼
┌─ Streamlit 监控大屏 (:8501) ────────┐
│  poll 日志 → 解析 → 两阶段检测       │
│  → 告警 → 救援 → 报告 → 图表 → 邮件  │
└─────────────────────────────────────┘
```

### Podman 容器

| 容器 | 端口 | 用途 |
|------|------|------|
| `log-analyzer-nginx` | 8080:80 | Web 服务器 + 攻击面板 + iptables 执行 |
| `log-analyzer-mysql` | 3306:3306 | MySQL 数据库 |
| `log-analyzer-ssh` | 2222:22 | SSH 靶机（救援命令执行目标） |
| `log-analyzer-api` | 9000:9000 | FastAPI 攻击面板后端 |

---

## 🚀 快速开始

### 环境要求

- **Python 3.12+**
- **Podman**（容器运行时）
- **DeepSeek API Key**（LLM 分析）
- **QQ 邮箱授权码**（告警邮件通知）

### Windows

```bash
# 1. 一键初始化（创建 venv + 安装依赖 + 生成 .env 模板）
setup.bat

# 2. 编辑 .env 填入你的 API Key 和邮箱授权码
notepad .env

# 3. 一键启动（启动容器 + 打开 Streamlit）
run.bat
```

### Linux / Mac

```bash
# 1. 一键初始化（创建 venv + 安装依赖 + 生成 .env 模板）
bash setup.sh

# 2. 编辑 .env 填入你的 API Key 和邮箱授权码
vim .env

# 3. 一键启动（启动容器 + 打开 Streamlit）
bash run.sh
```

### 访问

| 地址 | 说明 |
|------|------|
| http://localhost:8501 | Streamlit 智能运维仪表板 |
| http://localhost:8080/attack.html | 外部攻击面板 |
| http://localhost:8080 | nginx 网站 |

---

## 📖 使用指南

### 发起攻击

**方式一：外部攻击面板**（推荐演示用）
1. 浏览器打开 `http://localhost:8080/attack.html`
2. 选择攻击类型，点击发起

**方式二：Streamlit 侧边栏**
1. 打开 `http://localhost:8501`
2. 左侧「攻击控制」面板选择并启动

### 观察检测流程

1. 监控大屏实时滚动日志，攻击关键词自动高亮
2. 告警列表自动弹出新告警，展开可查看 LLM 分析详情
3. HIGH/CRITICAL 告警自动触发救援（iptables 封禁 IP）
4. 后台异步生成报告、图表并发送邮件
5. 分析报告页面可查看 Markdown 报告预览

### 解除封禁

- **攻击面板**：点击「解除封禁」按钮
- **Streamlit**：告警列表中点击「🔓 解除封禁」

---

## 📁 项目结构

```
server-log-analyzer/
├── docker/                         # Podman 容器环境
│   ├── docker-compose.yml          # 4 容器编排 (兼容 podman-compose)
│   ├── nginx/                      # nginx + 攻击面板 + entrypoint
│   ├── mysql/                      # MySQL 数据库
│   ├── ssh-target/                 # SSH 靶机
│   └── attack-api/                 # FastAPI 后端
├── src/                            # Python 核心源码
│   ├── app.py                      # Streamlit 主控台 (核心)
│   ├── config.py                   # 全局配置 + 常量
│   ├── models.py                   # Pydantic 数据模型
│   ├── attack_simulator.py         # 攻击模拟器 (真实 HTTP 请求)
│   ├── attack_panel_api.py         # FastAPI 攻击面板后端
│   ├── log_simulator.py            # 正常流量生成
│   ├── log_monitor.py              # 日志文件监控 + 解析
│   ├── log_rotator.py              # 日志轮转管理
│   ├── rule_engine.py              # 规则引擎 (滑动窗口 + 正则)
│   ├── llm_analyzer.py             # LLM 语义分析 (DeepSeek)
│   ├── alert_manager.py            # 告警工厂 + 去重
│   ├── rescue_executor.py          # 救援执行器 (SSH + iptables)
│   ├── report_generator.py         # LLM 报告生成
│   ├── chart_generator.py          # matplotlib 图表
│   ├── email_sender.py             # SMTP 邮件发送
│   ├── event_bus.py                # 异步事件总线
│   ├── playbooks.yaml              # 救援剧本定义
│   └── scenarios.yaml              # 演示场景定义
├── logs/                           # 日志文件 (运行时生成)
├── reports/                        # 分析报告 (运行时生成)
├── charts/                         # 图表文件 (运行时生成)
├── requirements.txt
└── README.md
```

---

## 🔧 技术栈

| 领域 | 技术 |
|------|------|
| **LLM** | DeepSeek API + LangChain StructuredOutput |
| **Web UI** | Streamlit（4 页面仪表板） |
| **API** | FastAPI + uvicorn |
| **容器化** | Podman Compose（4 容器） |
| **远程执行** | paramiko SSH + subprocess |
| **图表** | matplotlib + pillow 水印 |
| **邮件** | smtplib + MIME（HTML + 内嵌图片） |
| **数据模型** | Pydantic v2 |
| **配置** | YAML + .env |

---

## 🔄 检测流水线

```
日志行 → LogMonitor 解析 → RuleEngine 规则筛选
    → 可疑事件 ≥ 5 → LLM 语义分析 (DeepSeek)
    → 每攻击类型独立告警
    → [HIGH/CRITICAL] → RescueExecutor 救援
    → [异步] → ReportGenerator → ChartGenerator → EmailSender
```

- **规则引擎**：频率检测 / SQL注入正则 / XSS正则 / 路径遍历 / 错误率 / 暴力破解
- **LLM 分析**：提取攻击类型、置信度、受影响端点、处置建议（StructuredOutput）
- **降级策略**：LLM 调用失败时自动降级为规则启发式分析
- **告警去重**：120s 窗口内同类型告警合并

---

## 🎯 演示场景

1. 启动 Podman 环境 + Streamlit
2. 在「系统设置」页面启动正常流量模拟
3. 通过攻击面板发起 SQL 注入扫描
4. 观察监控大屏：日志高亮 → 告警弹出 → 自动救援 → 报告生成
5. 切换到分析报告页面查看生成的报告
6. 检查邮箱确认收到告警邮件（含图表附件）
7. 通过解封面板解除 IP 封禁

---

## 📝 License

MIT
