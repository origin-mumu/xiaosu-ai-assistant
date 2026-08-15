import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx


def load_cases() -> list[dict[str, Any]]:
    path = Path(__file__).with_name("cases.json")
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
    answer = str(result.get("answer", ""))
    reasons: list[str] = []
    contains_all = case.get("contains_all", [])
    contains_any = case.get("contains_any", [])
    if contains_all and not all(keyword in answer for keyword in contains_all):
        reasons.append(f"缺少必备关键词：{contains_all}")
    if contains_any and not any(keyword in answer for keyword in contains_any):
        reasons.append(f"未命中任一关键词：{contains_any}")
    if case.get("citation") and not result.get("citations"):
        reasons.append("缺少引用")
    expected_tool = case.get("tool")
    called_tools = [call.get("name") for call in result.get("tool_calls", [])]
    if expected_tool and expected_tool not in called_tools:
        reasons.append(f"未调用工具 {expected_tool}，实际为 {called_tools}")
    if result.get("status") != "completed":
        reasons.append(f"回答状态为 {result.get('status')}")
    return not reasons, reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Xiaosu's 20-case HTTP evaluation set")
    parser.add_argument("--base-url", default="http://localhost:8000/api/v1")
    parser.add_argument("--threshold", type=float, default=0.8)
    args = parser.parse_args()
    cases = load_cases()
    passed = 0
    with httpx.Client(timeout=90) as client:
        for case in cases:
            conversation = case.get("conversation", f"eval-{case['id']}")
            response = client.post(
                f"{args.base_url}/chat/completions",
                json={
                    "message": case["question"],
                    "platform": "web",
                    "tenant_id": "eval",
                    "conversation_id": conversation,
                    "user_id": "evaluator",
                    "user_name": "自动评测",
                },
            )
            response.raise_for_status()
            result = response.json()
            success, reasons = evaluate(case, result)
            passed += int(success)
            marker = "PASS" if success else "FAIL"
            detail = "" if success else "；".join(reasons)
            print(f"[{marker}] {case['id']} {case['question']} {detail}")
    score = passed / len(cases)
    print(f"\nResult: {passed}/{len(cases)} = {score:.1%}")
    return 0 if score >= args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
