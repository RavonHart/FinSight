from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_user_db
from app.db.models.users import User
from app.domains.compliance.schemas import FullComplianceAuditBundle
from app.domains.compliance.service import generate_compliance_audit_bundle, render_compliance_audit_html

compliance_router = APIRouter(prefix="/compliance", tags=["Compliance & Audit Packager"])


@compliance_router.get("/export", response_model=None)
async def export_compliance_audit_package(
    format: str = Query("json", description="Export format: 'json' or 'html'"),
    include_simulations: bool = Query(True),
    include_research: bool = Query(True),
    include_tutor: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
):
    """
    Exports a comprehensive regulatory and compliance audit package (§20, §32, §69).
    Includes the user's registered risk profile, closed-form deterministic simulations,
    research report citation trails with Jev evaluations, and AI Tutor advisory guardrail logs.
    """
    async for session in get_user_db(user_id=str(current_user.id), is_admin=current_user.is_admin):
        bundle = await generate_compliance_audit_bundle(
            session=session,
            user_id=current_user.id,
            include_simulations=include_simulations,
            include_research=include_research,
            include_tutor=include_tutor,
        )

        if format.lower() == "html":
            html_content = render_compliance_audit_html(bundle)
            return Response(
                content=html_content,
                media_type="text/html",
                headers={
                    "Content-Disposition": f"inline; filename=finsight-audit-{bundle.metadata.audit_id}.html",
                    "X-Compliance-Digest": bundle.metadata.sha256_digest or "",
                },
            )

        return Response(
            content=bundle.model_dump_json(indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=finsight-audit-{bundle.metadata.audit_id}.json",
                "X-Compliance-Digest": bundle.metadata.sha256_digest or "",
            },
        )
