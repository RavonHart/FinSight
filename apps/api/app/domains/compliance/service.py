import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.models.profiles import FinancialProfile
from app.db.models.simulations import SimulationRun
from app.db.models.research import ResearchRun, Evidence, Source, Claim
from app.db.models.jev import JevEvaluation
from app.domains.compliance.schemas import (
    ComplianceAuditMetadata,
    ComplianceProfileAudit,
    ComplianceSimulationAudit,
    ComplianceResearchAudit,
    ComplianceTutorAudit,
    FullComplianceAuditBundle,
)


async def generate_compliance_audit_bundle(
    session: AsyncSession,
    user_id: UUID,
    include_simulations: bool = True,
    include_research: bool = True,
    include_tutor: bool = True,
) -> FullComplianceAuditBundle:
    """
    Generates an institutional compliance and regulatory audit bundle (§20, §32, §69).
    Includes registered risk profile, deterministic simulations, research provenance,
    and AI Tutor advisory guardrail enforcement records.
    """
    audit_id = f"AUDIT-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)

    # 1. Fetch latest profile
    stmt_profile = (
        select(FinancialProfile)
        .where(FinancialProfile.user_id == user_id)
        .order_by(desc(FinancialProfile.profile_version), desc(FinancialProfile.id))
        .limit(1)
    )
    res_profile = await session.execute(stmt_profile)
    profile_record = res_profile.scalar_one_or_none()

    profile_audit = None
    if profile_record:
        tier_str = str(profile_record.risk_tolerance or "MODERATE")
        profile_audit = ComplianceProfileAudit(
            user_id=profile_record.user_id,
            assessment_date=profile_record.created_at,
            risk_tier=tier_str,
            risk_tolerance=tier_str,
            risk_capacity=profile_record.risk_capacity,
            investment_horizon=profile_record.investment_horizon,
            primary_goal=profile_record.primary_goal,
            experience_level=profile_record.experience_level,
            liquidity_requirement=profile_record.liquidity_requirement,
            profile_version=profile_record.profile_version,
        )

    # 2. Fetch simulations
    simulations_audit = []
    if include_simulations:
        stmt_sims = (
            select(SimulationRun)
            .where(SimulationRun.user_id == user_id)
            .order_by(desc(SimulationRun.created_at), desc(SimulationRun.id))
            .limit(20)
        )
        res_sims = await session.execute(stmt_sims)
        for s in res_sims.scalars().all():
            term_vals = {}
            res_json = s.result_json or {}
            scenarios = res_json.get("scenarios", {})
            for sc_name, sc_data in scenarios.items():
                res_obj = sc_data.get("result", {})
                term_vals[sc_name] = str(res_obj.get("nominal_ending_value", res_obj.get("terminal_balance", "0.00")))
            
            in_json = s.input_json or {}
            simulations_audit.append(
                ComplianceSimulationAudit(
                    simulation_id=s.id,
                    engine_version=s.engine_version,
                    initial_capital=str(in_json.get("initial_capital", "0.00")),
                    monthly_contribution=str(in_json.get("monthly_contribution", "0.00")),
                    time_horizon_years=int(in_json.get("duration_years", in_json.get("time_horizon_years", 10))),
                    annual_return_rate=str(in_json.get("annual_return_pct", in_json.get("annual_return_rate", "0.07"))),
                    annual_fee_drag=str(in_json.get("annual_fee_pct", in_json.get("annual_fee_drag", "0.002"))),
                    created_at=s.created_at,
                    scenario_terminal_values=term_vals,
                )
            )

    # 3. Fetch research runs
    research_audit = []
    if include_research:
        stmt_research = (
            select(ResearchRun)
            .where(ResearchRun.user_id == user_id)
            .order_by(desc(ResearchRun.created_at), desc(ResearchRun.id))
            .limit(10)
        )
        res_research = await session.execute(stmt_research)
        for r in res_research.scalars().all():
            # fetch evidence joined with source (deterministic secondary sort)
            stmt_ev = (
                select(Evidence, Source)
                .join(Source, Evidence.source_id == Source.id)
                .where(Evidence.research_run_id == r.id)
                .order_by(Evidence.id)
            )
            ev_res = await session.execute(stmt_ev)
            ev_pairs = ev_res.all()
            sources = [
                {
                    "citation_index": (ev.metadata_json or {}).get("citation_index", 1),
                    "title": src.title,
                    "url": src.url,
                    "source_tier": src.source_type,
                    "credibility_score": float(ev.relevance_score) if ev.relevance_score else 1.0,
                }
                for ev, src in ev_pairs
            ]

            # fetch claims/jev claim evaluations for this run (deterministic secondary sort)
            stmt_claims = (
                select(Claim)
                .where(Claim.research_run_id == r.id)
                .order_by(Claim.id)
            )
            claim_res = await session.execute(stmt_claims)
            claim_items = [
                {
                    "claim_text": c.claim_text,
                    "status": c.status,
                    "confidence": float(c.confidence) if c.confidence else None,
                }
                for c in claim_res.scalars().all()
            ]

            synthesis_md = (r.model_metadata_json or {}).get("synthesis_report") or ""
            research_audit.append(
                ComplianceResearchAudit(
                    run_id=r.id,
                    query=r.question,
                    ticker=(r.model_metadata_json or {}).get("ticker"),
                    status=r.status,
                    created_at=r.created_at,
                    synthesis_markdown=synthesis_md,
                    evidence_count=len(ev_pairs),
                    citation_sources=sources,
                    jev_claim_evaluations=claim_items,
                )
            )

    # 4. Fetch tutor safety & advisory intent evaluations
    tutor_audit = []
    if include_tutor:
        stmt_tutor = (
            select(JevEvaluation)
            .join(FinancialProfile, JevEvaluation.financial_profile_id == FinancialProfile.id)
            .where(
                FinancialProfile.user_id == user_id,
                JevEvaluation.question_id == "advisory_intent_check",
            )
            .order_by(desc(JevEvaluation.created_at), desc(JevEvaluation.id))
            .limit(50)
        )
        res_tutor = await session.execute(stmt_tutor)
        for t in res_tutor.scalars().all():
            is_refusal = (
                t.choice_value == "ADVISORY_ACTIONABLE"
                or (t.choice_value and "advisory" in t.choice_value.lower())
            )
            input_st = t.input_state_json or {}
            input_text = input_st.get("query", input_st.get("text", ""))
            tutor_audit.append(
                ComplianceTutorAudit(
                    evaluation_id=t.id,
                    timestamp=t.created_at,
                    question_id=t.question_id,
                    judgment=t.choice_value or "UNKNOWN",
                    confidence_score=float(t.confidence),
                    routing_action="refuse_advisory" if is_refusal else "allow_educational",
                    is_advisory_refusal=is_refusal,
                    context_type=input_st.get("context_type", "input"),
                    input_text=input_text,
                )
            )

    # Compute deterministic SHA-256 digest over canonical substantive audit content
    canonical_digest = compute_canonical_audit_digest(
        user_profile=profile_audit,
        simulations=simulations_audit,
        research_reports=research_audit,
        tutor_safety_logs=tutor_audit,
    )

    metadata = ComplianceAuditMetadata(
        audit_id=audit_id,
        export_timestamp=now,
        sha256_digest=canonical_digest,
    )

    return FullComplianceAuditBundle(
        metadata=metadata,
        user_profile=profile_audit,
        simulations=simulations_audit,
        research_reports=research_audit,
        tutor_safety_logs=tutor_audit,
    )


def compute_canonical_audit_digest(
    user_profile: Optional[ComplianceProfileAudit],
    simulations: list[ComplianceSimulationAudit],
    research_reports: list[ComplianceResearchAudit],
    tutor_safety_logs: list[ComplianceTutorAudit],
) -> str:
    """
    Computes a deterministic, tamper-evident SHA-256 digest over the canonical substantive
    financial and compliance payload.
    
    Excludes transient metadata (audit_id, export_timestamp, digest itself) so that repeated
    exports over identical underlying data produce identical, reproducible cryptographic hashes.
    Uses canonical JSON formatting with sorted keys and compact separators.
    """
    substantive_payload = {
        "user_profile": user_profile.model_dump(mode="json") if user_profile else None,
        "simulations": [s.model_dump(mode="json") for s in simulations],
        "research_reports": [r.model_dump(mode="json") for r in research_reports],
        "tutor_safety_logs": [t.model_dump(mode="json") for t in tutor_safety_logs],
    }
    canonical_json = json.dumps(
        substantive_payload,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def verify_audit_bundle_digest(bundle: FullComplianceAuditBundle | dict) -> bool:
    """
    Verifies that a compliance audit bundle's sha256_digest matches the canonical hash
    of its substantive audit contents. Returns True if authentic and untampered, False otherwise.
    """
    if isinstance(bundle, dict):
        payload = {
            "user_profile": bundle.get("user_profile"),
            "simulations": bundle.get("simulations", []),
            "research_reports": bundle.get("research_reports", []),
            "tutor_safety_logs": bundle.get("tutor_safety_logs", []),
        }
        meta = bundle.get("metadata", {})
        expected_digest = meta.get("sha256_digest") if isinstance(meta, dict) else getattr(meta, "sha256_digest", None)
    else:
        payload = {
            "user_profile": bundle.user_profile.model_dump(mode="json") if bundle.user_profile else None,
            "simulations": [s.model_dump(mode="json") for s in bundle.simulations],
            "research_reports": [r.model_dump(mode="json") for r in bundle.research_reports],
            "tutor_safety_logs": [t.model_dump(mode="json") for t in bundle.tutor_safety_logs],
        }
        expected_digest = bundle.metadata.sha256_digest

    if not expected_digest:
        return False

    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    actual_digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return actual_digest == expected_digest


def render_compliance_audit_html(bundle: FullComplianceAuditBundle) -> str:
    """
    Renders an institutional, print-ready HTML compliance document.
    Complies with §20 & §32 disclosure guidelines with zero external fonts or CSS dependencies.
    """
    meta = bundle.metadata
    profile = bundle.user_profile

    # Profile section
    profile_html = "<p><em>No completed profile on record.</em></p>"
    if profile:
        profile_html = f"""
        <table class="audit-table">
            <tr><th>User ID</th><td><code>{profile.user_id}</code></td></tr>
            <tr><th>Profile Version</th><td>v{profile.profile_version or 1}</td></tr>
            <tr><th>Risk Tier</th><td><strong>{profile.risk_tier or 'N/A'}</strong></td></tr>
            <tr><th>Risk Capacity</th><td>{profile.risk_capacity or 'N/A'}</td></tr>
            <tr><th>Time Horizon</th><td>{profile.investment_horizon or 'N/A'}</td></tr>
            <tr><th>Primary Goal</th><td>{profile.primary_goal or 'N/A'}</td></tr>
            <tr><th>Experience Level</th><td>{profile.experience_level or 'N/A'}</td></tr>
            <tr><th>Liquidity Requirement</th><td>{profile.liquidity_requirement or 'N/A'}</td></tr>
            <tr><th>Assessment Date</th><td>{profile.assessment_date.strftime('%Y-%m-%d %H:%M:%S UTC') if profile.assessment_date else 'N/A'}</td></tr>
        </table>
        """

    # Simulations section
    sims_html = "<p><em>No simulations recorded.</em></p>"
    if bundle.simulations:
        sim_rows = ""
        for s in bundle.simulations:
            terms = ", ".join([f"{k}: ${float(v):,.2f}" for k, v in s.scenario_terminal_values.items()])
            sim_rows += f"""
            <tr>
                <td><code>{s.simulation_id}</code></td>
                <td>{s.created_at.strftime('%Y-%m-%d %H:%M')}</td>
                <td>${float(s.initial_capital):,.2f}</td>
                <td>${float(s.monthly_contribution):,.2f}/mo</td>
                <td>{s.time_horizon_years}y</td>
                <td><code>{s.engine_version}</code></td>
                <td>{terms}</td>
            </tr>
            """
        sims_html = f"""
        <table class="audit-table">
            <thead>
                <tr>
                    <th>Simulation ID</th>
                    <th>Date</th>
                    <th>Initial</th>
                    <th>Monthly</th>
                    <th>Horizon</th>
                    <th>Engine</th>
                    <th>Deterministic Outcomes</th>
                </tr>
            </thead>
            <tbody>{sim_rows}</tbody>
        </table>
        """

    # Research section
    research_html = "<p><em>No research runs recorded.</em></p>"
    if bundle.research_reports:
        r_blocks = ""
        for r in bundle.research_reports:
            ev_list = "".join([f"<li>[{s.get('citation_index', '?')}] <strong>{s.get('title')}</strong> ({s.get('source_tier', 'Tier 2')}) — {s.get('url')}</li>" for s in r.citation_sources])
            r_blocks += f"""
            <div class="report-box">
                <h4>{r.query} {f'({r.ticker})' if r.ticker else ''} — <code>{r.status}</code></h4>
                <div class="meta-line">Run ID: <code>{r.run_id}</code> | Timestamp: {r.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')} | Evidence items: {r.evidence_count}</div>
                <h5>Citations & Verified Sources:</h5>
                <ul>{ev_list or '<li>None</li>'}</ul>
            </div>
            """
        research_html = r_blocks

    # Tutor section
    tutor_html = "<p><em>No AI Tutor interactions recorded.</em></p>"
    if bundle.tutor_safety_logs:
        t_rows = ""
        for t in bundle.tutor_safety_logs:
            refusal_badge = '<span class="badge badge-rose">REFUSED (ADVISORY BLOCKED)</span>' if t.is_advisory_refusal else '<span class="badge badge-emerald">ALLOWED (EDUCATIONAL)</span>'
            prompt_preview = (t.input_text[:120] + "...") if t.input_text and len(t.input_text) > 120 else (t.input_text or "N/A")
            t_rows += f"""
            <tr>
                <td>{t.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                <td><code>{t.question_id}</code></td>
                <td>{refusal_badge}</td>
                <td><code>{t.judgment}</code> ({t.confidence_score:.2f})</td>
                <td><em>{prompt_preview}</em></td>
            </tr>
            """
        tutor_html = f"""
        <table class="audit-table">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Question ID</th>
                    <th>Status</th>
                    <th>Jev Calibrated Decision</th>
                    <th>User Prompt Preview</th>
                </tr>
            </thead>
            <tbody>{t_rows}</tbody>
        </table>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinSight Compliance Audit Package — {meta.audit_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #111827;
            background: #ffffff;
            margin: 40px auto;
            max-width: 900px;
            line-height: 1.5;
        }}
        h1 {{ font-size: 24px; margin-bottom: 4px; color: #0f172a; border-bottom: 2px solid #0f172a; padding-bottom: 8px; }}
        h2 {{ font-size: 18px; margin-top: 32px; color: #1e293b; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }}
        h3 {{ font-size: 15px; margin-top: 20px; color: #334155; }}
        .header-meta {{ font-size: 13px; color: #64748b; margin-bottom: 24px; }}
        .disclaimer-box {{
            background: #f8fafc;
            border-left: 4px solid #6366f1;
            padding: 12px 16px;
            margin: 20px 0;
            font-size: 12px;
            color: #475569;
        }}
        .digest-box {{
            background: #f1f5f9;
            padding: 8px 12px;
            font-family: monospace;
            font-size: 12px;
            margin-top: 16px;
            word-break: break-all;
            border: 1px solid #cbd5e1;
        }}
        .audit-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 13px;
        }}
        .audit-table th, .audit-table td {{
            border: 1px solid #e2e8f0;
            padding: 8px 12px;
            text-align: left;
        }}
        .audit-table th {{
            background: #f8fafc;
            font-weight: 600;
            color: #334155;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
        }}
        .badge-rose {{ background: #ffe4e6; color: #e11d48; }}
        .badge-emerald {{ background: #d1fae5; color: #059669; }}
        .report-box {{
            border: 1px solid #e2e8f0;
            padding: 12px 16px;
            margin-bottom: 16px;
            border-radius: 6px;
        }}
        .meta-line {{ font-size: 12px; color: #64748b; margin-bottom: 8px; }}
        @media print {{
            body {{ max-width: 100%; margin: 10mm; font-size: 11pt; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 20px;">
        <button onclick="window.print()" style="padding: 8px 16px; background: #0f172a; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 500;">
            Print / Save to PDF (Ctrl+P)
        </button>
    </div>

    <h1>{meta.platform_name}</h1>
    <div class="header-meta">
        <strong>Audit Package ID:</strong> {meta.audit_id}<br>
        <strong>Generated Timestamp:</strong> {meta.export_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
        <strong>Deterministic Engine Version:</strong> <code>{meta.engine_version}</code><br>
        <strong>Regulatory Framework:</strong> {meta.regulatory_framework}
    </div>

    <div class="disclaimer-box">
        <strong>Mandatory Statutory Notice:</strong><br>
        {meta.mandatory_disclaimer}
    </div>

    <h2>1. Registered Financial Profile & Calibrated Risk Tier</h2>
    {profile_html}

    <h2>2. Deterministic Portfolio Projections (Closed-Form Engine)</h2>
    {sims_html}

    <h2>3. Autonomous Research Provenance & Citation Trails</h2>
    {research_html}

    <h2>4. AI Tutor Semantic Guardrail & Advisory Refusal Log (§69)</h2>
    {tutor_html}

    <h2>5. Cryptographic Integrity Digest</h2>
    <div class="digest-box">
        <strong>SHA-256 Substantive Content Digest:</strong> <code>{meta.sha256_digest or 'Pending'}</code>
        <div style="font-size: 11px; color: #64748b; margin-top: 6px;">
            Canonical digest computed over substantive user profile, closed-form simulations, research provenance, and AI tutor guardrail logs. Excludes transient export envelopes (audit_id and export timestamp) to guarantee deterministic cryptographic re-verification for regulatory reviewers.
        </div>
    </div>
</body>
</html>
"""
