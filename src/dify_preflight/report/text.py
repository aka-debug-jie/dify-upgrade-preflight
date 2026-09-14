from __future__ import annotations

from collections.abc import Mapping


def render_text(report: Mapping[str, object]) -> str:
    lines = [
        f"Verdict: {report['verdict']}",
        f"Upgrade: {report['source_version']} -> {report['target_version']}",
        f"Synthetic input: {str(report['synthetic']).lower()}",
    ]
    findings = report.get("findings", [])
    if findings:
        lines.append("Findings:")
        for finding in findings:
            if isinstance(finding, Mapping):
                refs = ", ".join(str(item) for item in finding.get("evidence_refs", []))
                origins = ", ".join(f"{item.get('fact')} ({item.get('origin')})" for item in finding.get("fact_evidence", []) if isinstance(item, Mapping))
                lines.append(f"- {finding.get('rule_id')}: {finding.get('result')} ({finding.get('severity')}); phase={finding.get('remediation_phase')}; evidence={refs or 'none'}")
                lines.append(f"  Fact origins: {origins or 'none'}")
                lines.append(f"  Manual action: {finding.get('remediation_summary')}")
    else:
        lines.append("Findings: none evaluated.")
    coverage = report.get("coverage", {})
    if isinstance(coverage, Mapping):
        unknown = ", ".join(str(item) for item in coverage.get("unknown_required_rules", []))
        excluded = ", ".join(str(item) for item in coverage.get("excluded_checks", []))
        lines.append(f"Required facts still unknown: {unknown or 'none'}")
        lines.append(f"Excluded checks requiring manual confirmation: {excluded or 'none'}")
    lines.append("Runtime observations are not substituted for declared facts; excluded checks require manual confirmation.")
    lines.append("Next action: resolve failed findings in their stated phase; confirm excluded checks manually.")
    return "\n".join(lines) + "\n"
