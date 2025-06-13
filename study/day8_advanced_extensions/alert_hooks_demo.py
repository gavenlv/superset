#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day 8 告警钩子演示：告警报告系统扩展机制
=====================================

本脚本演示如何扩展 Superset 的告警报告系统：
- 自定义通知渠道
- 告警钩子机制
- 调度器扩展
- 验证器扩展
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ReportState(Enum):
    """报告状态"""
    SUCCESS = "Success"
    WORKING = "Working"
    ERROR = "Error"
    NOOP = "Not triggered"
    GRACE = "Grace period"


class ReportScheduleType(Enum):
    """报告调度类型"""
    ALERT = "Alert"
    REPORT = "Report"


class NotificationMethod(Enum):
    """通知方法"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    TEAMS = "teams"
    DISCORD = "discord"


@dataclass
class NotificationContent:
    """通知内容"""
    name: str
    body: str
    screenshots: List[bytes] = None
    header_data: Dict[str, Any] = None


@dataclass
class ReportRecipient:
    """报告接收者"""
    type: NotificationMethod
    recipient_config: Dict[str, Any]


@dataclass
class ReportSchedule:
    """报告调度"""
    id: int
    name: str
    type: ReportScheduleType
    active: bool
    crontab: str
    timezone: str = "UTC"
    
    # 验证器配置
    validator_type: Optional[str] = None
    validator_config: Dict[str, Any] = None
    
    # 执行配置
    grace_period: int = 14400  # 4小时
    working_timeout: int = 3600  # 1小时
    log_retention: int = 90  # 90天
    
    # 状态信息
    last_eval_dttm: Optional[datetime] = None
    last_state: ReportState = ReportState.NOOP
    last_value: Optional[float] = None
    
    # 接收者
    recipients: List[ReportRecipient] = None
    
    def __post_init__(self):
        if self.recipients is None:
            self.recipients = []
        if self.validator_config is None:
            self.validator_config = {}


class BaseNotification(ABC):
    """通知基类"""
    
    def __init__(self, recipient: ReportRecipient, content: NotificationContent):
        self._recipient = recipient
        self._content = content
    
    @abstractmethod
    def send(self) -> bool:
        """发送通知"""
        pass
    
    @abstractmethod
    def send_error(self, name: str, message: str) -> bool:
        """发送错误通知"""
        pass


class EmailNotification(BaseNotification):
    """邮件通知"""
    
    def send(self) -> bool:
        """发送邮件通知"""
        to_email = self._recipient.recipient_config.get("target")
        subject = self._content.header_data.get("subject", self._content.name) if self._content.header_data else self._content.name
        
        print(f"📧 发送邮件通知:")
        print(f"   收件人: {to_email}")
        print(f"   主题: {subject}")
        print(f"   内容长度: {len(self._content.body)} 字符")
        
        if self._content.screenshots:
            print(f"   附件: {len(self._content.screenshots)} 个截图")
        
        # 模拟邮件发送
        return True
    
    def send_error(self, name: str, message: str) -> bool:
        """发送错误邮件"""
        to_email = self._recipient.recipient_config.get("target")
        
        print(f"📧 发送错误邮件:")
        print(f"   收件人: {to_email}")
        print(f"   主题: [Alert Error] {name}")
        print(f"   错误信息: {message}")
        
        return True


class SlackNotification(BaseNotification):
    """Slack通知"""
    
    def send(self) -> bool:
        """发送Slack通知"""
        channel = self._recipient.recipient_config.get("target")
        webhook_url = self._recipient.recipient_config.get("webhook_url")
        
        print(f"💬 发送Slack通知:")
        print(f"   频道: {channel}")
        print(f"   Webhook: {webhook_url}")
        print(f"   消息: {self._content.name}")
        
        # 构建Slack消息
        slack_message = {
            "channel": channel,
            "text": self._content.name,
            "attachments": [
                {
                    "color": "good",
                    "text": self._content.body[:500],  # 限制长度
                    "ts": int(time.time())
                }
            ]
        }
        
        print(f"   消息结构: {json.dumps(slack_message, indent=2)}")
        return True
    
    def send_error(self, name: str, message: str) -> bool:
        """发送Slack错误通知"""
        channel = self._recipient.recipient_config.get("target")
        
        print(f"💬 发送Slack错误通知:")
        print(f"   频道: {channel}")
        print(f"   错误: {name} - {message}")
        
        return True


class WebhookNotification(BaseNotification):
    """Webhook通知"""
    
    def send(self) -> bool:
        """发送Webhook通知"""
        url = self._recipient.recipient_config.get("url")
        headers = self._recipient.recipient_config.get("headers", {})
        
        print(f"🔗 发送Webhook通知:")
        print(f"   URL: {url}")
        print(f"   Headers: {headers}")
        
        # 构建Webhook负载
        payload = {
            "name": self._content.name,
            "body": self._content.body,
            "timestamp": datetime.now().isoformat(),
            "type": "alert"
        }
        
        print(f"   负载: {json.dumps(payload, indent=2)}")
        return True
    
    def send_error(self, name: str, message: str) -> bool:
        """发送Webhook错误通知"""
        url = self._recipient.recipient_config.get("url")
        
        print(f"🔗 发送Webhook错误通知:")
        print(f"   URL: {url}")
        print(f"   错误: {name} - {message}")
        
        return True


class SMSNotification(BaseNotification):
    """短信通知"""
    
    def send(self) -> bool:
        """发送短信通知"""
        phone = self._recipient.recipient_config.get("phone")
        provider = self._recipient.recipient_config.get("provider", "twilio")
        
        print(f"📱 发送短信通知:")
        print(f"   手机号: {phone}")
        print(f"   提供商: {provider}")
        
        # 短信内容需要简化
        sms_content = f"{self._content.name}: {self._content.body[:100]}..."
        print(f"   内容: {sms_content}")
        
        return True
    
    def send_error(self, name: str, message: str) -> bool:
        """发送短信错误通知"""
        phone = self._recipient.recipient_config.get("phone")
        
        print(f"📱 发送短信错误通知:")
        print(f"   手机号: {phone}")
        print(f"   错误: {name} - {message}")
        
        return True


class NotificationFactory:
    """通知工厂"""
    
    _notification_classes = {
        NotificationMethod.EMAIL: EmailNotification,
        NotificationMethod.SLACK: SlackNotification,
        NotificationMethod.WEBHOOK: WebhookNotification,
        NotificationMethod.SMS: SMSNotification,
    }
    
    @classmethod
    def create_notification(
        cls, 
        recipient: ReportRecipient, 
        content: NotificationContent
    ) -> BaseNotification:
        """创建通知实例"""
        notification_class = cls._notification_classes.get(recipient.type)
        if not notification_class:
            raise ValueError(f"Unsupported notification method: {recipient.type}")
        
        return notification_class(recipient, content)
    
    @classmethod
    def register_notification_method(
        cls, 
        method: NotificationMethod, 
        notification_class: type
    ) -> None:
        """注册新的通知方法"""
        cls._notification_classes[method] = notification_class
        print(f"✓ 注册通知方法: {method.value} -> {notification_class.__name__}")


class BaseValidator(ABC):
    """验证器基类"""
    
    @abstractmethod
    def validate(self, data: Any, config: Dict[str, Any]) -> bool:
        """验证数据"""
        pass
    
    @abstractmethod
    def get_error_message(self, data: Any, config: Dict[str, Any]) -> str:
        """获取错误消息"""
        pass


class ThresholdValidator(BaseValidator):
    """阈值验证器"""
    
    def validate(self, data: Any, config: Dict[str, Any]) -> bool:
        """验证阈值"""
        if not isinstance(data, (int, float)):
            return False
        
        operator = config.get("op", ">=")
        threshold = config.get("threshold", 0)
        
        if operator == ">=":
            return data >= threshold
        elif operator == "<=":
            return data <= threshold
        elif operator == ">":
            return data > threshold
        elif operator == "<":
            return data < threshold
        elif operator == "==":
            return data == threshold
        elif operator == "!=":
            return data != threshold
        else:
            return False
    
    def get_error_message(self, data: Any, config: Dict[str, Any]) -> str:
        """获取错误消息"""
        operator = config.get("op", ">=")
        threshold = config.get("threshold", 0)
        return f"Value {data} does not meet condition: {operator} {threshold}"


class NotNullValidator(BaseValidator):
    """非空验证器"""
    
    def validate(self, data: Any, config: Dict[str, Any]) -> bool:
        """验证非空"""
        return data is not None and data != ""
    
    def get_error_message(self, data: Any, config: Dict[str, Any]) -> str:
        """获取错误消息"""
        return f"Value is null or empty: {data}"


class ValidatorFactory:
    """验证器工厂"""
    
    _validators = {
        "threshold": ThresholdValidator,
        "not_null": NotNullValidator,
    }
    
    @classmethod
    def create_validator(cls, validator_type: str) -> BaseValidator:
        """创建验证器"""
        validator_class = cls._validators.get(validator_type)
        if not validator_class:
            raise ValueError(f"Unknown validator type: {validator_type}")
        
        return validator_class()
    
    @classmethod
    def register_validator(cls, validator_type: str, validator_class: type) -> None:
        """注册验证器"""
        cls._validators[validator_type] = validator_class
        print(f"✓ 注册验证器: {validator_type} -> {validator_class.__name__}")


class AlertHook(ABC):
    """告警钩子基类"""
    
    @abstractmethod
    def before_execute(self, schedule: ReportSchedule) -> bool:
        """执行前钩子"""
        pass
    
    @abstractmethod
    def after_execute(self, schedule: ReportSchedule, result: Dict[str, Any]) -> None:
        """执行后钩子"""
        pass
    
    @abstractmethod
    def on_success(self, schedule: ReportSchedule, data: Any) -> None:
        """成功钩子"""
        pass
    
    @abstractmethod
    def on_error(self, schedule: ReportSchedule, error: Exception) -> None:
        """错误钩子"""
        pass


class LoggingHook(AlertHook):
    """日志钩子"""
    
    def before_execute(self, schedule: ReportSchedule) -> bool:
        """执行前记录日志"""
        print(f"📝 [LOG] 开始执行告警: {schedule.name} (ID: {schedule.id})")
        print(f"📝 [LOG] 调度类型: {schedule.type.value}")
        print(f"📝 [LOG] Cron表达式: {schedule.crontab}")
        return True
    
    def after_execute(self, schedule: ReportSchedule, result: Dict[str, Any]) -> None:
        """执行后记录日志"""
        print(f"📝 [LOG] 完成执行告警: {schedule.name}")
        print(f"📝 [LOG] 执行结果: {result.get('status', 'unknown')}")
        print(f"📝 [LOG] 耗时: {result.get('duration', 0):.2f}秒")
    
    def on_success(self, schedule: ReportSchedule, data: Any) -> None:
        """成功日志"""
        print(f"✅ [LOG] 告警成功: {schedule.name}")
        print(f"✅ [LOG] 数据值: {data}")
    
    def on_error(self, schedule: ReportSchedule, error: Exception) -> None:
        """错误日志"""
        print(f"❌ [LOG] 告警失败: {schedule.name}")
        print(f"❌ [LOG] 错误信息: {str(error)}")


class MetricsHook(AlertHook):
    """指标钩子"""
    
    def __init__(self):
        self.metrics = {
            "executions": 0,
            "successes": 0,
            "errors": 0,
            "total_duration": 0,
        }
    
    def before_execute(self, schedule: ReportSchedule) -> bool:
        """执行前更新指标"""
        self.metrics["executions"] += 1
        print(f"📊 [METRICS] 执行次数: {self.metrics['executions']}")
        return True
    
    def after_execute(self, schedule: ReportSchedule, result: Dict[str, Any]) -> None:
        """执行后更新指标"""
        duration = result.get("duration", 0)
        self.metrics["total_duration"] += duration
        
        avg_duration = self.metrics["total_duration"] / self.metrics["executions"]
        print(f"📊 [METRICS] 平均耗时: {avg_duration:.2f}秒")
    
    def on_success(self, schedule: ReportSchedule, data: Any) -> None:
        """成功指标"""
        self.metrics["successes"] += 1
        success_rate = (self.metrics["successes"] / self.metrics["executions"]) * 100
        print(f"📊 [METRICS] 成功率: {success_rate:.1f}%")
    
    def on_error(self, schedule: ReportSchedule, error: Exception) -> None:
        """错误指标"""
        self.metrics["errors"] += 1
        error_rate = (self.metrics["errors"] / self.metrics["executions"]) * 100
        print(f"📊 [METRICS] 错误率: {error_rate:.1f}%")
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        return self.metrics.copy()


class RateLimitHook(AlertHook):
    """限流钩子"""
    
    def __init__(self, max_executions_per_hour: int = 60):
        self.max_executions_per_hour = max_executions_per_hour
        self.executions = []
    
    def before_execute(self, schedule: ReportSchedule) -> bool:
        """执行前检查限流"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # 清理过期记录
        self.executions = [exec_time for exec_time in self.executions if exec_time > one_hour_ago]
        
        # 检查是否超过限制
        if len(self.executions) >= self.max_executions_per_hour:
            print(f"🚫 [RATE_LIMIT] 超过限流: {len(self.executions)}/{self.max_executions_per_hour}")
            return False
        
        # 记录执行时间
        self.executions.append(now)
        print(f"✅ [RATE_LIMIT] 通过限流检查: {len(self.executions)}/{self.max_executions_per_hour}")
        return True
    
    def after_execute(self, schedule: ReportSchedule, result: Dict[str, Any]) -> None:
        """执行后处理"""
        pass
    
    def on_success(self, schedule: ReportSchedule, data: Any) -> None:
        """成功处理"""
        pass
    
    def on_error(self, schedule: ReportSchedule, error: Exception) -> None:
        """错误处理"""
        pass


class AlertExecutor:
    """告警执行器"""
    
    def __init__(self):
        self.hooks: List[AlertHook] = []
        self.notification_factory = NotificationFactory()
        self.validator_factory = ValidatorFactory()
    
    def add_hook(self, hook: AlertHook) -> None:
        """添加钩子"""
        self.hooks.append(hook)
        print(f"✓ 添加钩子: {hook.__class__.__name__}")
    
    def execute_alert(self, schedule: ReportSchedule, data: Any) -> Dict[str, Any]:
        """执行告警"""
        start_time = time.time()
        result = {"status": "unknown", "duration": 0}
        
        try:
            # 执行前钩子
            for hook in self.hooks:
                if not hook.before_execute(schedule):
                    result["status"] = "blocked"
                    return result
            
            # 验证数据
            if schedule.validator_type:
                validator = self.validator_factory.create_validator(schedule.validator_type)
                if not validator.validate(data, schedule.validator_config):
                    error_msg = validator.get_error_message(data, schedule.validator_config)
                    raise ValueError(error_msg)
            
            # 发送通知
            content = NotificationContent(
                name=schedule.name,
                body=f"Alert triggered with value: {data}",
                header_data={"subject": f"[Alert] {schedule.name}"}
            )
            
            for recipient in schedule.recipients:
                notification = self.notification_factory.create_notification(recipient, content)
                notification.send()
            
            # 更新状态
            schedule.last_eval_dttm = datetime.now()
            schedule.last_state = ReportState.SUCCESS
            schedule.last_value = float(data) if isinstance(data, (int, float)) else None
            
            result["status"] = "success"
            
            # 成功钩子
            for hook in self.hooks:
                hook.on_success(schedule, data)
        
        except Exception as error:
            result["status"] = "error"
            result["error"] = str(error)
            
            # 更新状态
            schedule.last_eval_dttm = datetime.now()
            schedule.last_state = ReportState.ERROR
            
            # 发送错误通知
            for recipient in schedule.recipients:
                notification = self.notification_factory.create_notification(recipient, content)
                notification.send_error(schedule.name, str(error))
            
            # 错误钩子
            for hook in self.hooks:
                hook.on_error(schedule, error)
        
        finally:
            # 计算耗时
            result["duration"] = time.time() - start_time
            
            # 执行后钩子
            for hook in self.hooks:
                hook.after_execute(schedule, result)
        
        return result


def demo_notification_system():
    """演示通知系统"""
    print("📢 通知系统演示")
    print("=" * 60)
    
    # 创建通知内容
    content = NotificationContent(
        name="Sales Alert",
        body="Daily sales have exceeded the threshold of $100,000. Current value: $125,000",
        header_data={"subject": "[Alert] Daily Sales Threshold Exceeded"}
    )
    
    # 演示不同通知方法
    recipients = [
        ReportRecipient(
            type=NotificationMethod.EMAIL,
            recipient_config={"target": "admin@company.com"}
        ),
        ReportRecipient(
            type=NotificationMethod.SLACK,
            recipient_config={
                "target": "#alerts",
                "webhook_url": "https://hooks.slack.com/services/xxx"
            }
        ),
        ReportRecipient(
            type=NotificationMethod.WEBHOOK,
            recipient_config={
                "url": "https://api.company.com/alerts",
                "headers": {"Authorization": "Bearer token123"}
            }
        ),
        ReportRecipient(
            type=NotificationMethod.SMS,
            recipient_config={
                "phone": "+1234567890",
                "provider": "twilio"
            }
        ),
    ]
    
    # 发送通知
    for recipient in recipients:
        print(f"\n📤 发送 {recipient.type.value} 通知:")
        notification = NotificationFactory.create_notification(recipient, content)
        success = notification.send()
        print(f"   结果: {'成功' if success else '失败'}")


def demo_validator_system():
    """演示验证器系统"""
    print("\n🔍 验证器系统演示")
    print("=" * 60)
    
    # 演示阈值验证器
    print("1. 阈值验证器:")
    threshold_validator = ValidatorFactory.create_validator("threshold")
    
    test_cases = [
        (125000, {"op": ">=", "threshold": 100000}),
        (85000, {"op": ">=", "threshold": 100000}),
        (50, {"op": "<=", "threshold": 100}),
        (150, {"op": "<=", "threshold": 100}),
    ]
    
    for value, config in test_cases:
        is_valid = threshold_validator.validate(value, config)
        print(f"   值 {value} 配置 {config}: {'✅ 通过' if is_valid else '❌ 失败'}")
        if not is_valid:
            print(f"     错误: {threshold_validator.get_error_message(value, config)}")
    
    # 演示非空验证器
    print("\n2. 非空验证器:")
    not_null_validator = ValidatorFactory.create_validator("not_null")
    
    test_values = ["hello", "", None, 0, False, []]
    for value in test_values:
        is_valid = not_null_validator.validate(value, {})
        print(f"   值 {repr(value)}: {'✅ 通过' if is_valid else '❌ 失败'}")


def demo_hook_system():
    """演示钩子系统"""
    print("\n🪝 钩子系统演示")
    print("=" * 60)
    
    # 创建执行器
    executor = AlertExecutor()
    
    # 添加钩子
    logging_hook = LoggingHook()
    metrics_hook = MetricsHook()
    rate_limit_hook = RateLimitHook(max_executions_per_hour=5)
    
    executor.add_hook(logging_hook)
    executor.add_hook(metrics_hook)
    executor.add_hook(rate_limit_hook)
    
    # 创建告警调度
    schedule = ReportSchedule(
        id=1,
        name="Daily Sales Alert",
        type=ReportScheduleType.ALERT,
        active=True,
        crontab="0 9 * * *",
        validator_type="threshold",
        validator_config={"op": ">=", "threshold": 100000},
        recipients=[
            ReportRecipient(
                type=NotificationMethod.EMAIL,
                recipient_config={"target": "sales@company.com"}
            )
        ]
    )
    
    # 执行多次告警
    test_data = [125000, 95000, 150000, 80000, 200000, 75000]
    
    for i, data in enumerate(test_data, 1):
        print(f"\n🚨 执行告警 #{i}:")
        result = executor.execute_alert(schedule, data)
        print(f"   最终结果: {result}")
        
        # 短暂延迟
        time.sleep(0.1)
    
    # 显示最终指标
    print(f"\n📊 最终指标: {metrics_hook.get_metrics()}")


def demo_custom_extensions():
    """演示自定义扩展"""
    print("\n🔧 自定义扩展演示")
    print("=" * 60)
    
    # 自定义通知方法 - Teams
    class TeamsNotification(BaseNotification):
        def send(self) -> bool:
            webhook_url = self._recipient.recipient_config.get("webhook_url")
            print(f"👥 发送Teams通知:")
            print(f"   Webhook: {webhook_url}")
            print(f"   消息: {self._content.name}")
            return True
        
        def send_error(self, name: str, message: str) -> bool:
            print(f"👥 发送Teams错误通知: {name} - {message}")
            return True
    
    # 注册自定义通知方法
    NotificationFactory.register_notification_method(
        NotificationMethod.TEAMS, 
        TeamsNotification
    )
    
    # 自定义验证器 - 范围验证
    class RangeValidator(BaseValidator):
        def validate(self, data: Any, config: Dict[str, Any]) -> bool:
            if not isinstance(data, (int, float)):
                return False
            min_val = config.get("min", float("-inf"))
            max_val = config.get("max", float("inf"))
            return min_val <= data <= max_val
        
        def get_error_message(self, data: Any, config: Dict[str, Any]) -> str:
            min_val = config.get("min", float("-inf"))
            max_val = config.get("max", float("inf"))
            return f"Value {data} not in range [{min_val}, {max_val}]"
    
    # 注册自定义验证器
    ValidatorFactory.register_validator("range", RangeValidator)
    
    # 测试自定义扩展
    print("\n测试自定义Teams通知:")
    teams_recipient = ReportRecipient(
        type=NotificationMethod.TEAMS,
        recipient_config={"webhook_url": "https://outlook.office.com/webhook/xxx"}
    )
    
    content = NotificationContent(
        name="Custom Teams Alert",
        body="This is a test message for Teams integration"
    )
    
    teams_notification = NotificationFactory.create_notification(teams_recipient, content)
    teams_notification.send()
    
    print("\n测试自定义范围验证器:")
    range_validator = ValidatorFactory.create_validator("range")
    
    test_cases = [
        (50, {"min": 0, "max": 100}),
        (150, {"min": 0, "max": 100}),
        (-10, {"min": 0, "max": 100}),
    ]
    
    for value, config in test_cases:
        is_valid = range_validator.validate(value, config)
        print(f"   值 {value} 范围 {config}: {'✅ 通过' if is_valid else '❌ 失败'}")
        if not is_valid:
            print(f"     错误: {range_validator.get_error_message(value, config)}")


def main():
    """主演示函数"""
    print("🚨 Day 8 告警钩子系统演示")
    print("=" * 60)
    
    try:
        # 演示通知系统
        demo_notification_system()
        
        # 演示验证器系统
        demo_validator_system()
        
        # 演示钩子系统
        demo_hook_system()
        
        # 演示自定义扩展
        demo_custom_extensions()
        
        print("\n" + "="*60)
        print("✅ 告警钩子系统演示完成！")
        print("\n📚 告警系统要点总结:")
        print("- 通知系统：支持多种通知渠道的可扩展架构")
        print("- 验证器系统：灵活的数据验证机制")
        print("- 钩子机制：在关键节点提供扩展点")
        print("- 工厂模式：统一的组件创建和管理")
        print("- 状态管理：完整的执行状态跟踪")
        print("- 错误处理：健壮的异常处理和恢复")
        print("- 指标监控：实时的性能和成功率监控")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 