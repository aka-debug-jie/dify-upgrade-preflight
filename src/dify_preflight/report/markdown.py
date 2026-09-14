from __future__ import annotations

from collections.abc import Mapping


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# Dify Upgrade Preflight report",
        "",
        f"- Verdict: `{report['verdict']}`",
        f"- Upgrade: `{report['source_version']} → {report['target_version']}`",
        f"- Synthetic input: `{str(report['synthetic']).lower()}`",
        "",
        "## Findings",
        "",
        "| Rule | Result | Severity | Phase | Official evidence | Manual action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    findings = report.get("findings", [])
    if findings:
        for finding in findings:
            if isinstance(finding, Mapping):
                refs = ", ".join(str(item) for item in finding.get("evidence_refs", [])) or "none"
                lines.append(f"| {finding.get('rule_id')} | {finding.get('result')} | {finding.get('severity')} | {finding.get('remediation_phase')} | {refs} | {finding.get('remediation_summary')} |")
    else:
        lines.append("| none | not evaluated | n/a | n/a | none | none |")
    coverage = report.get("coverage", {})
    if isinstance(coverage, Mapping):
        unknown = ", ".join(str(item) for item in coverage.get("unknown_required_rules", [])) or "none"
        excluded = ", ".join(str(item) for item in coverage.get("excluded_checks", [])) or "none"
        lines.extend(["", "## Scope and manual action", "", f"- Required facts still unknown: {unknown}", f"- Excluded checks: {excluded}", "- Runtime observations are not substituted for declared facts.", "- Resolve failed findings in their stated phase, and manually confirm excluded checks."])
    return "\n".join(lines) + "\n"
