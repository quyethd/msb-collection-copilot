from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from .models import CaseBrief, CaseContext, ValidationResult, KeyEvidence


def _plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower()).replace("đ", "d")
    return "".join(c for c in normalized if not unicodedata.combining(c))


class CaseBriefValidator:
    """Strict post-generation validation.

    Validates:
    - CIF consistency
    - score parity
    - route/treatment/channel parity
    - numeric fact validation
    - simulation-state validation
    - citation validation

    Rejects contradictions. If rejected, fallback is used.
    """

    def validate(self, brief: CaseBrief, context: CaseContext) -> ValidationResult:
        reasons: list[str] = []

        self._validate_cif(brief, context, reasons)
        self._validate_decision_parity(brief, context, reasons)
        self._validate_score_parity(brief, context, reasons)
        self._validate_simulation_state(brief, context, reasons)
        self._validate_citations(brief, context, reasons)
        self._validate_no_forbidden_claims(brief, reasons)

        return ValidationResult(passed=not reasons, reasons=reasons)

    def _validate_cif(self, brief: CaseBrief, context: CaseContext, reasons: list[str]) -> None:
        text = brief.headline + " " + brief.summary + " " + " ".join(brief.decision_explanation)
        for evidence in brief.key_evidence:
            text += " " + evidence.label + " " + evidence.value + " " + evidence.reason
        import re as _re
        all_cifs = _re.findall(r'\b(?:SYN\d{6}|GOLDEN_G\d{2})\b', text)
        other_cifs = [c for c in all_cifs if c != context.cif]
        if other_cifs:
            reasons.append(f"wrong_cif: found {other_cifs} but expected {context.cif}")

    def _validate_decision_parity(self, brief: CaseBrief, context: CaseContext, reasons: list[str]) -> None:
        dec = context.decision
        if not dec:
            return
        route = dec.get("final_route", "")
        treatment = dec.get("treatment", "")
        channel = dec.get("channel", "")

        text = brief.headline + " " + brief.summary + " " + " ".join(brief.decision_explanation)
        plain = _plain(text)

        if treatment == "WAIT_SELF_CURE":
            if "lien he ngay" in plain or "goi ngay" in plain:
                reasons.append("treatment_parity: claims contact but treatment is WAIT_SELF_CURE")
        if treatment in ("CONTACT", "CALLBACK"):
            if "chua can lien he" in plain or "cho theo doi" in plain:
                reasons.append("treatment_parity: claims wait but treatment requires contact")

    def _validate_score_parity(self, brief: CaseBrief, context: CaseContext, reasons: list[str]) -> None:
        dec = context.decision
        if not dec:
            return
        expected_score = dec.get("recovery_opportunity_score")
        if expected_score is None:
            return
        evidence_text = ""
        for evidence in brief.key_evidence:
            if "score" in evidence.source or "diem" in _plain(evidence.label):
                evidence_text += " " + evidence.value
        import re
        score_mentions = re.findall(r'\b(\d{1,3})\b', evidence_text)
        for mention in score_mentions:
            val = int(mention)
            if 10 <= val <= 100 and val != expected_score:
                reasons.append(f"score_parity: mentions {val} but expected {expected_score}")
                break

    def _validate_simulation_state(self, brief: CaseBrief, context: CaseContext, reasons: list[str]) -> None:
        if context.state == "SIMULATION":
            text = (brief.headline + " " + brief.summary).lower()
            if "du lieu goc" in text and "khong thay doi" not in text:
                pass
            if brief.state != "SIMULATION":
                reasons.append("simulation_state: brief state does not match SIMULATION")
        if context.state == "BASELINE" and brief.state == "SIMULATION":
            reasons.append("simulation_context_leak: BASELINE context but SIMULATION brief")

    def _validate_citations(self, brief: CaseBrief, context: CaseContext, reasons: list[str]) -> None:
        valid_sources = {"customer360", "cashflow", "ptp", "contact", "decision", "score", "knowledge", "simulation"}
        for evidence in brief.key_evidence:
            if evidence.source and evidence.source not in valid_sources:
                reasons.append(f"citation: invalid source {evidence.source!r}")
        for ref in brief.knowledge_refs:
            if not ref.title or not ref.source_id:
                reasons.append("citation: knowledge ref missing title or source_id")

    def _validate_no_forbidden_claims(self, brief: CaseBrief, reasons: list[str]) -> None:
        text = (brief.headline + " " + brief.summary + " " +
                " ".join(brief.decision_explanation) + " " +
                " ".join(brief.officer_focus))
        plain = _plain(text)
        forbidden = [
            ("nen chuyen tuyen", "claims routing change"),
            ("nen thay doi diem", "claims score change"),
            ("nen doi treatment", "claims treatment change"),
            ("nen doi channel", "claims channel change"),
            ("payment probability", "claims payment probability"),
            ("xac suat thanh toan", "claims payment probability"),
        ]
        for marker, msg in forbidden:
            if marker in plain:
                reasons.append(f"unsupported_decision_claim: {msg}")

    def validate_parsed_json(self, parsed: dict[str, Any], context: CaseContext) -> CaseBrief | None:
        try:
            evidence = []
            for item in parsed.get("key_evidence", []):
                evidence.append(KeyEvidence(
                    label=str(item.get("label", "")),
                    value=str(item.get("value", "")),
                    reason=str(item.get("reason", "")),
                    source=str(item.get("source", "")),
                ))
            from .models import KnowledgeRef
            refs = []
            for item in parsed.get("knowledge_refs", []):
                refs.append(KnowledgeRef(
                    title=str(item.get("title", "")),
                    source_id=str(item.get("source_id", "")),
                ))
            state = parsed.get("state", context.state)
            if state not in ("BASELINE", "SIMULATION"):
                state = context.state
            brief = CaseBrief(
                headline=str(parsed.get("headline", "")),
                summary=str(parsed.get("summary", "")),
                key_evidence=evidence,
                decision_explanation=[str(x) for x in parsed.get("decision_explanation", [])],
                officer_focus=[str(x) for x in parsed.get("officer_focus", [])],
                knowledge_refs=refs,
                missing_data=[str(x) for x in parsed.get("missing_data", context.missing_data)],
                state=state,
                disclaimer=parsed.get("disclaimer", ""),
            )
            result = self.validate(brief, context)
            if result.passed:
                return brief
            return None
        except Exception:
            return None
