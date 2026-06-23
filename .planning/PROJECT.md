# 服务器日志智能分析系统

## What This Is

一个面向课堂演示的 AI 驱动安全运维平台。外部用户通过浏览器访问攻击模拟面板，发起真实攻击打到 Docker 服务器；运维人员通过 Streamlit 监控大屏实时观察检测、告警、自动救援全过程。演示完整的安全事件响应闭环。

**当前阶段：** 已有本地原型（攻击模拟 + 检测引擎 + 报告生成），需要从"单机自演"升级为"外部可访问的演示平台"。

## Core Value

让课堂演示中的每个人都参与进来——同学发起攻击，监控屏实时响应，展示真实的安全运维工作流。

## Requirements

### Validated

<!-- 代码库地图确认的已有能力 -->

- ✓ nginx 日志实时采集与解析 — 已有 (`log_monitor.py`)
- ✓ 规则引擎多模式检测（SQL注入/XSS/CC/暴力破解/路径遍历）— 已有 (`rule_engine.py`)
- ✓ LLM 深度语义分析（DeepSeek via LangChain）— 已有 (`llm_analyzer.py`)
- ✓ 告警去重与分级管理 — 已有 (`alert_manager.py`)
- ✓ SSH 救援执行器（paramiko + YAML playbooks）— 已有 (`rescue_executor.py`)
- ✓ LLM 安全报告生成 — 已有 (`report_generator.py`)
- ✓ matplotlib 趋势图表 + 水印 — 已有 (`chart_generator.py`)
- ✓ SMTP 邮件通知 — 已有 (`email_sender.py`)
- ✓ Docker 三容器环境（nginx + MySQL + SSH靶机）— 已有 (`docker/`)
- ✓ Streamlit 统一仪表盘 — 已有 (`app.py`)
- ✓ 攻击模拟器（真实 HTTP 请求）— 已有 (`attack_simulator.py`)
- ✓ 正常流量模拟器 — 已有 (`log_simulator.py`)
- ✓ 日志轮转管理 — 已有 (`log_rotator.py`)

### Active

<!-- 当前要做的 -->

- [ ] **EXT-01**: 外部用户可通过浏览器访问独立的攻击模拟面板页面
- [ ] **EXT-02**: 攻击面板通过内网穿透（ngrok/Cloudflare Tunnel）获得公开访问链接
- [ ] **EXT-03**: 外部用户选择攻击类型后一键发起，无需登录或配置
- [ ] **EXT-04**: 攻击请求真实打到 Docker nginx，产生真实 access.log 日志
- [ ] **EXT-05**: 攻击面板实时显示攻击状态（已发送 → 执行中 → 完成）
- [ ] **DET-01**: 检测引擎正确识别外部触发的攻击并区分攻击类型
- [ ] **DET-02**: LLM 深度分析对真实攻击流量给出准确判定
- [ ] **DET-03**: 监控大屏实时刷新展示攻击者 IP、攻击类型、告警级别
- [ ] **RES-01**: 严重攻击自动触发 SSH 救援（iptables 封禁 IP / nginx 规则重载）
- [ ] **RES-02**: 救援操作在监控大屏上实时可见（执行步骤、成功/失败状态）
- [ ] **RES-03**: 救援回滚机制在真实环境下正常工作
- [ ] **RPT-01**: 每次攻击事件自动生成安全报告
- [ ] **RPT-02**: 邮件通知在真实攻击场景下正常工作

### Out of Scope

<!-- 本次不做 -->

- 用户认证与权限管理 — 课堂演示无需登录
- 多租户隔离 — 单实例演示即可
- MySQL/SSH 日志监控 — 当前仅监控 nginx 日志
- CI/CD 管道 — 不在课程范围内
- 生产环境部署 — 仅课堂演示

## Context

**已有代码：** 16 个 Python 模块，Docker 三容器环境，完整的检测-告警-救援-报告管道。详见 `.planning/codebase/` 下的 7 份代码库分析文档。

**已知问题：**
- 全局单例架构，多用户并发有问题（但课堂演示场景可接受）
- 零测试覆盖
- `print()` 代替日志系统
- 硬编码凭据（SSH/MySQL）
- 同步阻塞（LLM 调用、SSH 救援阻塞 UI）
- 无 lockfile，依赖版本不可复现

**演示场景：**
```
课堂环境：
  同学A-Z → 攻击面板 (ngrok 公开链接) → Docker nginx → 日志
                                                  ↓
  老师/投屏 ←── Streamlit 监控大屏 ←── 检测引擎 ←──┘
                                   → 告警 → SSH救援 → 报告 → 邮件
```

**技术约束：**
- 不花钱租服务器（使用内网穿透）
- Windows 10 开发环境
- Docker Desktop / Podman 可用
- DeepSeek API 可用（LLM 分析）

## Constraints

- **成本**: 零服务器费用，使用免费内网穿透方案（ngrok 免费版）
- **网络**: 教室局域网环境，需支持外部访问
- **平台**: Windows 10 + Docker Desktop
- **性能**: 课堂演示级别，10-20 个同学同时访问的攻击面板压力可控
- **安全**: 仅演示环境使用，不暴露到生产网络

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 攻击面板与监控面板分离 | 外部用户只触发攻击，不接触监控；运维端独立观察 | — Pending |
| 攻击面板部署在 Docker nginx 上 | 复用现有 nginx 容器，攻击流量天然被记录 | — Pending |
| 内网穿透选 ngrok | 免安装、免费、自动 HTTPS、最简单 | — Pending |
| 攻击面板纯静态 + API 后端 | 轻量、零依赖、外网访问快 | — Pending |
| 救援操作用真实 SSH | 展示真实安全运维流程，而非模拟 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-23 after initialization*
