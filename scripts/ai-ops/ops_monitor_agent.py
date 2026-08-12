#!/usr/bin/env python3
"""
运维监控AgentCore示例
模拟SSH连接、日志解析、服务监控等运维任务
"""

import asyncio
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import random


class AlertLevel(Enum):
    """告警级别"""
    INFO = "信息"
    WARNING = "警告"
    ERROR = "错误"
    CRITICAL = "严重"


class ServiceStatus(Enum):
    """服务状态"""
    RUNNING = "运行中"
    STOPPED = "停止"
    FAILED = "失败"
    UNKNOWN = "未知"


@dataclass
class Alert:
    """告警信息"""
    level: AlertLevel
    message: str
    source: str
    timestamp: datetime
    resolved: bool = False
    auto_resolve_minutes: Optional[int] = None


@dataclass  
class ServiceCheckResult:
    """服务检查结果"""
    service_name: str
    status: ServiceStatus
    uptime: Optional[float] = None  # 运行时间（小时）
    pid: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    last_restart: Optional[datetime] = None


@dataclass
class DiskCheckResult:
    """磁盘检查结果"""
    filesystem: str
    mount_point: str
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    status: str  # "正常", "警告", "危险"


@dataclass
class LogAnalysisResult:
    """日志分析结果"""
    file_path: str
    total_lines: int
    error_count: int
    warning_count: int
    recent_errors: List[str]
    pattern_matches: Dict[str, int]


class OpsMonitorAgent:
    """
    运维监控AgentCore示例
    功能：
    1. SSH远程命令执行
    2. 磁盘使用率监控
    3. 服务状态检查
    4. 日志文件分析
    5. 告警生成和通知
    6. 报告生成
    """
    
    def __init__(self, name: str = "ops-monitor-agent"):
        self.name = name
        self.memory = {
            "alerts": [],  # 历史告警
            "metrics": [],  # 监控指标历史
            "scheduled_tasks": [],  # 计划任务
            "host_configs": {}  # 主机配置
        }
        self.active_alerts = []
        
    def _simulate_ssh_output(self, host: str, command: str) -> str:
        """模拟SSH命令输出"""
        simulation_data = {
            "df -h": """文件系统        容量  已用  可用 已用% 挂载点
/dev/nvme0n1p2   98G   45G   48G   49% /
/dev/nvme0n1p1   511M  6.1M  505M    2% /boot/efi
/dev/sda1        5.0T  2.1T  2.7T   44% /data""",
            
            "systemctl list-units --type=service --state=failed": """UNIT                       LOAD   ACTIVE SUB    DESCRIPTION
● redis-server.service    loaded failed failed Redis In-Memory Data Store
● postgresql.service      loaded active running PostgreSQL RDBMS""",
            
            "free -h": """              total        used        free      shared  buff/cache   available
Mem:            16G         4.2G         9.8G        456M         2.0G         11G
Swap:          2.0G          0B          2.0G""",
            
            "uptime": """10:30:00 up 15 days,  2:30,  1 user,  load average: 0.12, 0.08, 0.09""",
            
            "tail -20 /var/log/syslog": """Aug  5 10:25:01 web01 CRON[1234]: (root) CMD (command -v debian-sa1 > /dev/null && debian-sa1 1 1)
Aug  5 10:25:01 web01 systemd[1]: Started Run anacron jobs.
Aug  5 10:25:01 web01 anacron[1235]: Anacron 2.3 started on 2026-08-05
Aug  5 10:25:01 web01 anacron[1235]: Normal exit (0 jobs run)
Aug  5 10:25:01 web01 systemd[1]: anacron.service: Succeeded.""",
            
            "docker ps": """CONTAINER ID   IMAGE          COMMAND                  CREATED       STATUS       PORTS     NAMES
a1b2c3d4e5f6   nginx:alpine   "nginx -g 'daemon of…"   2 weeks ago   Up 2 weeks   80/tcp    web-server
d7e8f9g0h1i2   redis:7.0     "docker-entrypoint.s…"   3 weeks ago   Up 3 weeks   6379/tcp  cache-server"""
        }
        
        return simulation_data.get(
            command, 
            f"[{host}] 命令执行: {command}\n模拟输出: 命令执行成功"
        )
    
    async def ssh_execute(self, host: str, command: str) -> str:
        """模拟异步SSH命令执行"""
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return self._simulate_ssh_output(host, command)
    
    def analyze_disk_usage(self, df_output: str) -> List[DiskCheckResult]:
        """分析磁盘使用情况"""
        results = []
        lines = df_output.strip().split('\n')[1:]  # 跳过标题行
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                filesystem = parts[0]
                total_str = parts[1]
                used_str = parts[2]
                available_str = parts[3]
                usage_pct = float(parts[4].replace('%', ''))
                mount_point = parts[5]
                
                # 转换单位
                def convert_to_gb(size_str: str) -> float:
                    if 'T' in size_str:
                        return float(size_str.replace('T', '')) * 1024
                    elif 'G' in size_str:
                        return float(size_str.replace('G', ''))
                    elif 'M' in size_str:
                        return float(size_str.replace('M', '')) / 1024
                    else:
                        return float(size_str) / (1024 * 1024 * 1024)
                
                total_gb = convert_to_gb(total_str)
                used_gb = convert_to_gb(used_str)
                free_gb = convert_to_gb(available_str)
                
                # 判断状态
                if usage_pct > 90:
                    status = "危险"
                elif usage_pct > 80:
                    status = "警告"
                else:
                    status = "正常"
                
                results.append(DiskCheckResult(
                    filesystem=filesystem,
                    mount_point=mount_point,
                    total_gb=total_gb,
                    used_gb=used_gb,
                    free_gb=free_gb,
                    usage_percent=usage_pct,
                    status=status
                ))
        
        return results
    
    def analyze_service_status(self, status_output: str) -> List[ServiceCheckResult]:
        """分析服务状态"""
        results = []
        lines = status_output.strip().split('\n')
        
        for line in lines:
            if '●' in line or 'loaded' in line:
                parts = line.split()
                if len(parts) >= 4:
                    service_name = parts[0].replace('●', '').replace('.service', '').strip()
                    loaded = parts[1]
                    active = parts[2]
                    sub = parts[3]
                    
                    # 判断服务状态
                    if active == 'active' and sub == 'running':
                        status = ServiceStatus.RUNNING
                    elif active == 'failed':
                        status = ServiceStatus.FAILED
                    elif active == 'inactive':
                        status = ServiceStatus.STOPPED
                    else:
                        status = ServiceStatus.UNKNOWN
                    
                    # 模拟一些额外信息
                    uptime = random.uniform(24, 720) if status == ServiceStatus.RUNNING else None
                    pid = random.randint(1000, 9999) if status == ServiceStatus.RUNNING else None
                    memory_usage = random.uniform(50, 500) if status == ServiceStatus.RUNNING else None
                    
                    results.append(ServiceCheckResult(
                        service_name=service_name,
                        status=status,
                        uptime=uptime,
                        pid=pid,
                        memory_usage_mb=memory_usage,
                        last_restart=datetime.now() - timedelta(hours=uptime) if uptime else None
                    ))
        
        return results
    
    def analyze_logs(self, log_content: str, log_path: str = "/var/log/syslog") -> LogAnalysisResult:
        """分析日志内容"""
        lines = log_content.strip().split('\n')
        total_lines = len(lines)
        
        error_count = sum(1 for line in lines if 'ERROR' in line or 'error' in line.lower())
        warning_count = sum(1 for line in lines if 'WARN' in line or 'warning' in line.lower())
        
        # 最近的错误
        recent_errors = [line for line in lines[-10:] if 'ERROR' in line or 'error' in line.lower()]
        
        # 模式匹配
        pattern_matches = {
            "CRON": sum(1 for line in lines if 'CRON' in line),
            "systemd": sum(1 for line in lines if 'systemd' in line),
            "kernel": sum(1 for line in lines if 'kernel' in line),
            "authentication": sum(1 for line in lines if 'auth' in line.lower() or 'login' in line.lower())
        }
        
        return LogAnalysisResult(
            file_path=log_path,
            total_lines=total_lines,
            error_count=error_count,
            warning_count=warning_count,
            recent_errors=recent_errors[:5],  # 只取前5个
            pattern_matches=pattern_matches
        )
    
    def generate_alerts(self, disk_results: List[DiskCheckResult], 
                       service_results: List[ServiceCheckResult],
                       log_results: Optional[LogAnalysisResult] = None) -> List[Alert]:
        """生成告警"""
        alerts = []
        timestamp = datetime.now()
        
        # 磁盘告警
        for disk in disk_results:
            if disk.status == "危险":
                alerts.append(Alert(
                    level=AlertLevel.CRITICAL,
                    message=f"磁盘使用率超过90%: {disk.filesystem} ({disk.usage_percent}%)",
                    source=f"disk:{disk.filesystem}",
                    timestamp=timestamp
                ))
            elif disk.status == "警告":
                alerts.append(Alert(
                    level=AlertLevel.WARNING,
                    message=f"磁盘使用率超过80%: {disk.filesystem} ({disk.usage_percent}%)",
                    source=f"disk:{disk.filesystem}",
                    timestamp=timestamp
                ))
        
        # 服务告警
        for service in service_results:
            if service.status == ServiceStatus.FAILED:
                alerts.append(Alert(
                    level=AlertLevel.CRITICAL,
                    message=f"服务失败: {service.service_name}",
                    source=f"service:{service.service_name}",
                    timestamp=timestamp
                ))
            elif service.status == ServiceStatus.STOPPED:
                alerts.append(Alert(
                    level=AlertLevel.WARNING,
                    message=f"服务停止: {service.service_name}",
                    source=f"service:{service.service_name}",
                    timestamp=timestamp
                ))
        
        # 日志告警
        if log_results and log_results.error_count > 10:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                message=f"日志错误过多: {log_results.file_path} ({log_results.error_count}个错误)",
                source=f"log:{log_results.file_path}",
                timestamp=timestamp
            ))
        
        return alerts
    
    def generate_report(self, host: str, 
                       disk_results: List[DiskCheckResult],
                       service_results: List[ServiceCheckResult],
                       log_results: Optional[LogAnalysisResult],
                       alerts: List[Alert]) -> Dict[str, Any]:
        """生成监控报告"""
        timestamp = datetime.now()
        
        # 统计
        critical_alerts = [a for a in alerts if a.level == AlertLevel.CRITICAL]
        warning_alerts = [a for a in alerts if a.level == AlertLevel.WARNING]
        
        # 磁盘使用率最高的文件系统
        max_usage_disk = max(disk_results, key=lambda d: d.usage_percent) if disk_results else None
        
        # 运行最久的服务
        running_services = [s for s in service_results if s.status == ServiceStatus.RUNNING]
        oldest_service = max(running_services, key=lambda s: s.uptime) if running_services else None
        
        report = {
            "host": host,
            "timestamp": timestamp.isoformat(),
            "summary": {
                "overall_status": "正常" if not alerts else "警告" if not critical_alerts else "危险",
                "critical_alerts": len(critical_alerts),
                "warning_alerts": len(warning_alerts),
                "disks_checked": len(disk_results),
                "services_checked": len(service_results),
                "log_errors": log_results.error_count if log_results else 0
            },
            "details": {
                "disks": [
                    {
                        "filesystem": d.filesystem,
                        "mount_point": d.mount_point,
                        "usage_percent": d.usage_percent,
                        "status": d.status,
                        "total_gb": d.total_gb,
                        "used_gb": d.used_gb,
                        "free_gb": d.free_gb
                    } for d in disk_results
                ],
                "services": [
                    {
                        "name": s.service_name,
                        "status": s.status.value,
                        "uptime_hours": s.uptime,
                        "memory_mb": s.memory_usage_mb,
                        "pid": s.pid
                    } for s in service_results
                ],
                "log_analysis": {
                    "file": log_results.file_path if log_results else None,
                    "total_lines": log_results.total_lines if log_results else None,
                    "error_count": log_results.error_count if log_results else None,
                    "warning_count": log_results.warning_count if log_results else None,
                    "recent_errors": log_results.recent_errors if log_results else []
                } if log_results else None
            },
            "alerts": [
                {
                    "level": a.level.value,
                    "message": a.message,
                    "source": a.source,
                    "timestamp": a.timestamp.isoformat(),
                    "resolved": a.resolved
                } for a in alerts
            ],
            "recommendations": []
        }
        
        # 生成建议
        if max_usage_disk and max_usage_disk.usage_percent > 80:
            report["recommendations"].append(
                f"清理磁盘空间: {max_usage_disk.filesystem} ({max_usage_disk.usage_percent}%使用率)"
            )
        
        if any(s.status == ServiceStatus.FAILED for s in service_results):
            failed_services = [s.service_name for s in service_results if s.status == ServiceStatus.FAILED]
            report["recommendations"].append(
                f"重启失败服务: {', '.join(failed_services)}"
            )
        
        if log_results and log_results.error_count > 5:
            report["recommendations"].append(
                f"检查日志文件: {log_results.file_path} (发现{log_results.error_count}个错误)"
            )
        
        return report
    
    async def run_full_monitoring(self, host: str) -> Dict[str, Any]:
        """运行完整的监控检查"""
        print(f"🔍 开始监控主机: {host}")
        
        # 1. 检查磁盘使用率
        print("  检查磁盘使用率...")
        df_output = await self.ssh_execute(host, "df -h")
        disk_results = self.analyze_disk_usage(df_output)
        
        # 2. 检查服务状态
        print("  检查服务状态...")
        service_output = await self.ssh_execute(host, "systemctl list-units --type=service --state=failed")
        service_results = self.analyze_service_status(service_output)
        
        # 3. 检查系统日志
        print("  检查系统日志...")
        log_output = await self.ssh_execute(host, "tail -100 /var/log/syslog")
        log_results = self.analyze_logs(log_output)
        
        # 4. 生成告警
        print("  生成告警...")
        alerts = self.generate_alerts(disk_results, service_results, log_results)
        
        # 5. 生成报告
        print("  生成报告...")
        report = self.generate_report(host, disk_results, service_results, log_results, alerts)
        
        # 保存到内存
        self.memory["metrics"].append({
            "host": host,
            "timestamp": datetime.now().isoformat(),
            "disk_count": len(disk_results),
            "service_count": len(service_results),
            "alerts_count": len(alerts)
        })
        
        self.active_alerts.extend(alerts)
        
        return report


async def main():
    """主函数 - 演示运维监控agent"""
    print("🚀 运维监控AgentCore示例")
    print("=" * 60)
    
    # 创建agent实例
    agent = OpsMonitorAgent("production-ops-agent")
    
    # 监控的主机列表
    hosts = [
        "web-server-01.prod",
        "db-server-01.prod", 
        "cache-server-01.prod"
    ]
    
    print(f"\n📋 监控计划")
    print(f"  目标主机数: {len(hosts)}")
    print(f"  检查项: 磁盘使用率、服务状态、系统日志")
    print(f"  告警级别: 警告(>80%)、严重(>90%)、服务失败")
    
    # 并行监控所有主机
    print(f"\n🔍 开始并行监控...")
    tasks = [agent.run_full_monitoring(host) for host in hosts]
    results = await asyncio.gather(*tasks)
    
    # 汇总结果
    print(f"\n📊 监控结果汇总")
    print("-" * 60)
    
    total_critical = 0
    total_warnings = 0
    
    for i, report in enumerate(results):
        host = report["host"]
        summary = report["summary"]
        
        print(f"\n{host}:")
        print(f"  总体状态: {summary['overall_status']}")
        print(f"  严重告警: {summary['critical_alerts']}个")
        print(f"  警告告警: {summary['warning_alerts']}个")
        print(f"  检查磁盘数: {summary['disks_checked']}")
        print(f"  检查服务数: {summary['services_checked']}")
        
        total_critical += summary["critical_alerts"]
        total_warnings += summary["warning_alerts"]
        
        # 显示关键告警
        critical_alerts = [a for a in report["alerts"] if a["level"] == "严重"]
        if critical_alerts:
            print(f"  关键告警:")
            for alert in critical_alerts[:3]:  # 显示前3个
                print(f"    • {alert['message']}")
    
    print(f"\n📈 全局统计")
    print("-" * 60)
    print(f"  总监控主机: {len(hosts)}")
    print(f"  总严重告警: {total_critical}")
    print(f"  总警告告警: {total_warnings}")
    
    if total_critical > 0:
        print(f"  ⚠️ 发现严重问题，需要立即处理!")
    elif total_warnings > 0:
        print(f"  ⚠️ 发现警告问题，建议检查处理")
    else:
        print(f"  ✅ 所有系统运行正常")
    
    # 生成详细报告示例
    print(f"\n📄 详细报告示例")
    print("-" * 60)
    sample_report = results[0]
    print(f"主机: {sample_report['host']}")
    print(f"时间: {sample_report['timestamp']}")
    print(f"状态: {sample_report['summary']['overall_status']}")
    
    if sample_report['recommendations']:
        print(f"\n建议操作:")
        for rec in sample_report['recommendations']:
            print(f"  • {rec}")
    
    # AgentCore部署建议
    print(f"\n🎯 AgentCore部署建议")
    print("=" * 60)
    print("1. 配置文件:")
    print("   - 创建agent_config.json定义监控目标和频率")
    print("   - 配置SSH凭证和密钥")
    print("   - 设置告警通知渠道(Slack/Email)")
    
    print("\n2. 部署到AgentCore:")
    print("   agentcore deploy ops-monitor-agent \\")
    print("     --runtime-name ops-monitoring-runtime \\")
    print("     --schedule \"*/5 * * * *\"  # 每5分钟运行")
    
    print("\n3. 监控和告警:")
    print("   - AgentCore内置Observability监控agent运行")
    print("   - 配置自动扩缩容")
    print("   - 设置日志聚合到CloudWatch")
    
    print("\n4. 集成选项:")
    print("   - 集成到现有监控系统(Prometheus/Grafana)")
    print("   - 连接到CMDB获取主机清单")
    print("   - 自动化修复动作(自动重启服务)")


if __name__ == "__main__":
    asyncio.run(main())