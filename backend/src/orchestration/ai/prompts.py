from typing import Any, Dict, List

PROMPT_VERSION = "1.0.0"

SYSTEM_PROMPT = f"""You are a production incident root cause analysis expert (prompt v{PROMPT_VERSION}).
Analyse the provided evidence and incident context to determine:

Output the following JSON structure:
{{
  "summary": "2-3 paragraph explanation of what happened and why",
  "root_cause": "short label for the primary cause (e.g. Resource Exhaustion, Network Timeout, Configuration Error)",
  "confidence": 0.0-1.0,
  "severity": "low|medium|high|critical",
  "affected_components": ["component1", "component2"],
  "possible_causes": ["possible cause 1", "possible cause 2"],
  "suggested_fixes": ["actionable step 1", "actionable step 2"],
  "preventive_actions": ["preventive measure 1", "preventive measure 2"],
  "similar_patterns": ["pattern1", "pattern2"],
  "risk_assessment": "assessment of business and operational risk",
  "estimated_resolution_time": "e.g. 30-60 minutes, 2-4 hours",
  "requires_human": false
}}

Respond ONLY with a valid JSON object. No markdown, no extra text."""


def _summarize_evidence_content(content: Any, max_chars: int = 500) -> str:
    if isinstance(content, str):
        if len(content) > max_chars:
            return content[:max_chars] + "... [TRUNCATED]"
        return content
    if isinstance(content, dict):
        text = ", ".join(f"{k}={v}" for k, v in content.items() if not isinstance(v, (dict, list)))
        if len(text) > max_chars:
            return text[:max_chars] + "... [TRUNCATED]"
        return text
    return str(content)


def build_incident_prompt(
    incident: Dict[str, Any],
    evidence_items: List[Dict[str, Any]],
    timeline: List[Dict[str, Any]],
    related_incidents: List[Dict[str, Any]],
) -> str:
    lines = ["=== INCIDENT CONTEXT ==="]
    lines.append(f"Title: {incident.get('title', 'N/A')}")
    desc = incident.get("description", incident.get("summary", "N/A"))
    if isinstance(desc, str) and len(desc) > 1000:
        desc = desc[:1000] + "... [TRUNCATED]"
    lines.append(f"Description: {desc}")
    lines.append(f"Repository: {incident.get('repository', 'N/A')}")
    lines.append(f"Branch: {incident.get('branch', 'N/A')}")
    lines.append(f"Commit: {incident.get('commit_sha', 'N/A')}")
    lines.append(f"Build: #{incident.get('build_number', 'N/A')}")
    lines.append(f"Environment: {incident.get('environment', 'N/A')}")
    lines.append(f"Severity: {incident.get('severity', 'N/A')}")
    lines.append(f"Status: {incident.get('status', 'N/A')}")
    lines.append(f"Started: {incident.get('created_at', 'N/A')}")

    lines.append("")
    lines.append(f"=== EVIDENCE ({len(evidence_items)} items) ===")
    for i, ev in enumerate(evidence_items, 1):
        source = ev.get("source", "N/A")
        etype = ev.get("evidence_type", ev.get("type", "N/A"))
        lines.append(f"[{i}] Source={source}, Type={etype}")
        content = ev.get("data") or ev.get("content") or ""
        summarized = _summarize_evidence_content(content)
        if summarized:
            lines.append(f"    Data: {summarized}")

    lines.append("")
    lines.append(f"=== TIMELINE ({len(timeline)} events) ===")
    for ev in timeline:
        ts = ev.get("timestamp", ev.get("time", "N/A"))
        desc = ev.get("description", ev.get("event", "N/A"))
        lines.append(f"  {ts} - {desc}")

    if related_incidents:
        lines.append("")
        lines.append(f"=== RELATED INCIDENTS ({len(related_incidents)}) ===")
        for ri in related_incidents:
            lines.append(f"  - {ri.get('title', ri.get('incident_id', 'N/A'))} ({ri.get('status', 'N/A')})")

    return "\n".join(lines)
