from typing import Any


class CompletionRuleInterpreter:
    def evaluate(self, rule: dict[str, Any], evidence: dict[str, Any]) -> bool:
        kind = str(rule.get("type", ""))
        if kind == "combined":
            return all(self.evaluate(child, evidence) for child in rule.get("rules", []))
        if kind == "resource_acknowledgement":
            return bool(evidence.get("acknowledged"))
        if kind == "evidence_summary":
            return len(str(evidence.get("summary", "")).strip()) >= int(rule.get("min_length", 20))
        if kind == "evidence_url":
            return bool(str(evidence.get("url", "")).strip())
        if kind == "quiz_threshold":
            return float(evidence.get("score", 0)) >= float(rule.get("threshold", 0))
        if kind in {"code_exercise", "repository_evidence"}:
            return bool(evidence.get("repository") or evidence.get("passed"))
        if kind == "instructor_approval":
            return bool(evidence.get("approved"))
        return False
