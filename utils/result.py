"""
Result Pattern - توحيد طريقة إرجاع النتائج
"""
from dataclasses import dataclass, field
from typing import Any, Optional, Dict


@dataclass
class Result:
    """كائن نتيجة موحد لكل العمليات"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    action: Optional[str] = None
    provider: Optional[str] = None
    requires_confirmation: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def ok(cls, data: Any, **kwargs) -> "Result":
        return cls(success=True, data=data, **kwargs)
    
    @classmethod
    def fail(cls, error: str, **kwargs) -> "Result":
        return cls(success=False, error=error, **kwargs)
    
    @classmethod
    def needs_confirmation(cls, action: str, data: Any = None) -> "Result":
        return cls(
            success=False, data=data, action=action,
            requires_confirmation=True,
            error="يتطلب تأكيد المستخدم"
        )
    
    def is_success(self) -> bool:
        return self.success
    
    def is_error(self) -> bool:
        return not self.success
    
    def __str__(self) -> str:
        if self.success:
            return f"✅ {self.action}: {self.data}"
        else:
            return f"❌ {self.action}: {self.error}"


if __name__ == "__main__":
    r1 = Result.ok("تم إنشاء الملف", action="write_file", provider="groq")
    print(r1)
    
    r2 = Result.fail("الملف غير موجود", action="read_file")
    print(r2)
    
    r3 = Result.needs_confirmation("system_power", {"action": "shutdown"})
    print(f"{r3} | يتطلب تأكيد؟ {r3.requires_confirmation}")
