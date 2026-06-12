"""
JSON Parser - استخراج وإصلاح JSON من استجابات LLM
"""
import json
import re
from typing import Optional, Dict, Any

from utils.result import Result
from schemas.tool_schema import ToolRequest


def extract_json(text: str) -> Result:
    """استخراج JSON من نص مع معالجة كل الحالات الممكنة"""
    if not text or not isinstance(text, str):
        return Result.fail("نص فارغ أو غير صالح", action="extract_json")
    
    # محاولة 1: JSON مباشر
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            json_str = text[start:end]
            data = json.loads(json_str)
            
            # معالجة حالة "actions" (قائمة)
            if "actions" in data and isinstance(data["actions"], list):
                actions = data["actions"]
                if len(actions) > 0:
                    first = actions[0]
                    return Result.ok(
                        data={
                            "action": first.get("action", "none"),
                            "parameters": {k: v for k, v in first.items() if k != "action"},
                        },
                        action="extract_json"
                    )
            
            # تحويل الصيغة القديمة إلى الجديدة
            if "action" in data:
                action = data["action"]
                parameters = data.get("parameters", {})
                
                # إذا لم يكن parameters موجود، نبنيه من الحقول الأخرى
                if not parameters:
                    skip = {"action"}
                    parameters = {k: v for k, v in data.items() if k not in skip}
                
                return Result.ok(
                    data={"action": action, "parameters": parameters},
                    action="extract_json"
                )
            
            return Result.fail("JSON لا يحتوي على حقل action", action="extract_json")
    
    except json.JSONDecodeError:
        pass
    
    # محاولة 2: إصلاح JSON
    try:
        repaired = _repair_json(text)
        if repaired:
            data = json.loads(repaired)
            if "action" in data:
                action = data["action"]
                parameters = data.get("parameters", {})
                if not parameters:
                    parameters = {k: v for k, v in data.items() if k != "action"}
                return Result.ok(
                    data={"action": action, "parameters": parameters},
                    action="extract_json"
                )
    except Exception:
        pass
    
    # محاولة 3: Regex
    try:
        data = _regex_extract(text)
        if data and "action" in data:
            action = data.pop("action")
            return Result.ok(
                data={"action": action, "parameters": data},
                action="extract_json"
            )
    except Exception:
        pass
    
    return Result.fail(f"فشل استخراج JSON: {text[:100]}...", action="extract_json")


def _repair_json(text: str) -> Optional[str]:
    """إصلاح JSON الشائع"""
    if not text:
        return None
    
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= start:
        return None
    
    text = text[start:end]
    text = re.sub(r'\\(?!["\\bfnrtu])', r'\\\\', text)
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
    text = re.sub(r"(?<!\\)'", '"', text)
    
    return text


def _regex_extract(text: str) -> Optional[Dict[str, Any]]:
    """استخراج الحقول باستخدام regex"""
    action_match = re.search(r'"action"\s*:\s*"([^"]+)"', text)
    if not action_match:
        return None
    
    result = {"action": action_match.group(1)}
    
    fields = ["path", "content", "cmd", "key_path", "value_name",
              "value_type", "value_data", "service_name", "username",
              "password", "var_name", "var_value", "task_name",
              "command", "time", "name", "description"]
    
    for field in fields:
        match = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
        if match:
            value = match.group(1).replace('\\n', '\n').replace('\\"', '"')
            result[field] = value
    
    return result if len(result) > 1 else None


def parse_to_tool_request(text: str) -> Result:
    """تحويل النص إلى ToolRequest صالح"""
    extract_result = extract_json(text)
    
    if not extract_result.success:
        return extract_result
    
    try:
        data = extract_result.data
        request = ToolRequest(
            action=data["action"],
            parameters=data.get("parameters", {})
        )
        return Result.ok(data=request, action="parse_to_tool_request")
    except Exception as e:
        return Result.fail(f"فشل تحويل إلى ToolRequest: {e}", action="parse_to_tool_request")


if __name__ == "__main__":
    print("🧪 اختبار JSON Parser...")
    
    # JSON صحيح
    test1 = '{"action": "write_file", "parameters": {"path": "test.txt", "content": "hello"}}'
    r1 = parse_to_tool_request(test1)
    print(f"Test 1: {r1.success} | {r1.data}")
    
    # JSON بصيغة قديمة
    test2 = '{"action": "run_cmd", "cmd": "dir"}'
    r2 = parse_to_tool_request(test2)
    print(f"Test 2: {r2.success} | {r2.data}")
    
    # JSON خاطئ (actions)
    test3 = '{"actions": [{"action": "write_file", "path": "test.txt"}]}'
    r3 = parse_to_tool_request(test3)
    print(f"Test 3: {r3.success} | {r3.data}")
    
    # أداة غير معروفة
    test4 = '{"action": "unknown_tool", "parameters": {}}'
    r4 = parse_to_tool_request(test4)
    print(f"Test 4: {r4.success} | {r4.error}")
