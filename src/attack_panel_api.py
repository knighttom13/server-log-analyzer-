"""
攻击面板 API (FastAPI 后端, 端口 9000)
为外部攻击面板提供 REST API，包装 AttackSimulator
"""

import time
import threading
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.attack_simulator import AttackSimulator
from src.config import ATTACK_CONFIG

# ============================================
# FastAPI 应用
# ============================================
app = FastAPI(
    title="攻击面板 API",
    description="服务器日志智能分析系统 - 攻击模拟面板后端",
    version="1.0.0",
)

# 允许所有来源 (ngrok 内网穿透场景)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# 全局状态
# ============================================
attack_sim = AttackSimulator()
# 容器内使用 nginx 容器名而非 localhost
import os
if os.environ.get("CONTAINERIZED") or os.path.exists("/.dockerenv"):
    attack_sim.base_url = "http://nginx:80"
    print("[AttackAPI] 🐳 容器模式: 攻击目标 -> nginx:80")

# 攻击元信息
ATTACK_META = {
    "sql_injection": {
        "display_name": "SQL注入扫描",
        "icon": "💉",
        "description": "模拟SQL注入探测，发送包含UNION SELECT、OR 1=1等特征payload的恶意请求",
        "risk": "高",
        "risk_color": "#e74c3c",
        "config": ATTACK_CONFIG["sql_injection"],
        "default_ip": "10.0.0.100",
    },
    "xss": {
        "display_name": "XSS跨站脚本",
        "icon": "⚠️",
        "description": "模拟跨站脚本攻击，发送包含&lt;script&gt;、onerror等XSS payload的请求",
        "risk": "中",
        "risk_color": "#f39c12",
        "config": ATTACK_CONFIG["xss"],
        "default_ip": "10.0.0.200",
    },
    "cc_flood": {
        "display_name": "CC并发洪水",
        "icon": "🌊",
        "description": "模拟CC攻击，大量并发线程高频请求服务器资源，造成服务压力",
        "risk": "高",
        "risk_color": "#e74c3c",
        "config": ATTACK_CONFIG["cc_flood"],
        "default_ip": "10.0.0.50",
    },
    "brute_force": {
        "display_name": "暴力破解",
        "icon": "🔓",
        "description": "模拟SSH/登录暴力破解，使用常见用户名密码字典批量尝试登录",
        "risk": "高",
        "risk_color": "#e74c3c",
        "config": ATTACK_CONFIG["brute_force"],
        "default_ip": "172.16.0.100",
    },
}

# 攻击运行状态: attack_type -> {"status": "idle"|"running"|"done", "started_at": str, "done_at": str | None}
_attack_status: dict[str, dict] = {k: {"status": "idle", "started_at": None, "done_at": None} for k in ATTACK_META}

# 启动时间
_startup_time = datetime.now()


# ============================================
# Pydantic 模型
# ============================================
class LaunchRequest(BaseModel):
    attack_type: str


class AttackTypeInfo(BaseModel):
    key: str
    display_name: str
    icon: str
    description: str
    risk: str
    risk_color: str
    threads: int
    requests: int


class AttackStatusInfo(BaseModel):
    key: str
    display_name: str
    icon: str
    status: str
    started_at: str | None
    done_at: str | None
    sent: int
    errors: int


# ============================================
# 辅助函数
# ============================================
def _estimate_duration(attack_type: str) -> float:
    """估算攻击持续时间 (秒)"""
    config = ATTACK_CONFIG[attack_type]
    if attack_type == "brute_force":
        return config["attempts_per_thread"] * config["delay_between_attempts"] * 1.5
    else:
        return config["requests_per_thread"] * config["delay_between_requests"] * 1.5


def _mark_done_after(attack_type: str, delay: float):
    """后台线程: 等待攻击完成后标记为 done"""
    time.sleep(delay)
    _attack_status[attack_type]["status"] = "done"
    _attack_status[attack_type]["done_at"] = datetime.now().isoformat()
    print(f"[AttackAPI] ✅ {attack_type} 攻击完成 (延迟 {delay:.1f}s)")


# ============================================
# API 端点
# ============================================
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "attack-panel-api",
        "version": "1.0.0",
    }


@app.get("/api/status")
async def system_status():
    """系统状态 (兼容旧 nginx mock /api/status)"""
    uptime = (datetime.now() - _startup_time).total_seconds()
    return {
        "status": "ok",
        "uptime": uptime,
        "timestamp": datetime.now().isoformat(),
        "attacks_running": sum(1 for s in _attack_status.values() if s["status"] == "running"),
    }


@app.get("/api/attacks/types")
async def get_attack_types() -> list[AttackTypeInfo]:
    """返回所有攻击类型及配置"""
    types = []
    for key, meta in ATTACK_META.items():
        config = meta["config"]
        types.append(AttackTypeInfo(
            key=key,
            display_name=meta["display_name"],
            icon=meta["icon"],
            description=meta["description"],
            risk=meta["risk"],
            risk_color=meta["risk_color"],
            threads=config.get("threads", 0),
            requests=config.get("requests_per_thread", config.get("attempts_per_thread", 0)),
        ))
    return types


@app.post("/api/attacks/launch")
async def launch_attack(req: LaunchRequest):
    """启动攻击 (fire-and-forget)"""
    attack_type = req.attack_type

    if attack_type not in ATTACK_META:
        raise HTTPException(status_code=400, detail=f"未知攻击类型: {attack_type}")

    if _attack_status[attack_type]["status"] == "running":
        raise HTTPException(status_code=409, detail=f"{ATTACK_META[attack_type]['display_name']} 正在执行中")

    # 标记为运行中
    _attack_status[attack_type]["status"] = "running"
    _attack_status[attack_type]["started_at"] = datetime.now().isoformat()
    _attack_status[attack_type]["done_at"] = None

    # 清空之前的统计
    attack_sim.attack_stats.pop(attack_type, None)

    # 启动攻击
    meta = ATTACK_META[attack_type]
    attack_sim.launch_attack(attack_type)
    print(f"[AttackAPI] 🔥 攻击已触发: {meta['display_name']} ({attack_type})")

    # 后台估算完成时间
    estimated = _estimate_duration(attack_type)
    threading.Thread(target=_mark_done_after, args=(attack_type, estimated), daemon=True).start()

    return {
        "status": "launched",
        "attack_type": attack_type,
        "display_name": meta["display_name"],
        "estimated_duration_seconds": round(estimated, 1),
        "message": f"🔥 {meta['display_name']} 已启动",
    }


@app.get("/api/attacks/status")
async def get_attack_status() -> list[AttackStatusInfo]:
    """返回所有攻击的实时状态"""
    stats = attack_sim.get_stats()
    result = []
    for key, meta in ATTACK_META.items():
        state = _attack_status[key]
        s = stats.get(key, {})
        result.append(AttackStatusInfo(
            key=key,
            display_name=meta["display_name"],
            icon=meta["icon"],
            status=state["status"],
            started_at=state["started_at"],
            done_at=state["done_at"],
            sent=s.get("sent", 0),
            errors=s.get("errors", 0),
        ))
    return result


# ============================================
# 启动入口
# ============================================
if __name__ == "__main__":
    import uvicorn
    import sys
    import io
    import asyncio
    # Windows 控制台 UTF-8 编码兼容
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        # 修复 Windows ProactorEventLoop 连接断开报错
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("[AttackAPI] 🚀 启动攻击面板 API (端口 9000)")
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info")
