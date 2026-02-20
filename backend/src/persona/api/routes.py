"""FastAPI route handlers for the Persona REST API."""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from persona.accomplishment_service import AccomplishmentService
from persona.application_service import ApplicationService
from persona.auth import UserContext
from persona.models import Resume
from persona.resume_service import ALL_SECTIONS, SECTION_LIST, ResumeService


def _make_user_dep(get_current_user: Callable | None) -> Callable:
    """Return a FastAPI dependency that yields ``UserContext | None``.

    When auth is disabled (``get_current_user`` is ``None``), the returned
    dependency always yields ``None`` so route handlers don't need to know
    whether auth is configured.
    """
    if get_current_user is not None:
        return get_current_user

    async def _no_auth() -> None:
        return None

    return _no_auth


def create_router(
    service: ResumeService,
    app_service: ApplicationService | None = None,
    acc_service: AccomplishmentService | None = None,
    get_current_user: Callable | None = None,
) -> APIRouter:
    """Create an APIRouter with all endpoints.

    Args:
        service: Resume service.
        app_service: Optional application service.
        acc_service: Optional accomplishment service.
        get_current_user: Optional FastAPI dependency that validates Bearer JWTs
            and returns a ``UserContext``. When provided, all routes except
            ``GET /health`` and ``POST /api/webhooks/clerk`` require a valid
            token.
    """
    # Top-level router — only truly public endpoints land here.
    router = APIRouter()

    # All API routes are protected. When auth is disabled the dependency list
    # is empty, so existing tests keep working without any token.
    _auth_deps = [Depends(get_current_user)] if get_current_user is not None else []
    api = APIRouter(dependencies=_auth_deps)

    # Optional-user dependency: always returns UserContext | None.
    _user_dep = _make_user_dep(get_current_user)

    # ------------------------------------------------------------------
    # Public: health check (no auth required)
    # ------------------------------------------------------------------

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # ------------------------------------------------------------------
    # Resume Version Routes
    # ------------------------------------------------------------------

    @api.get("/api/resumes")
    def list_resumes(
        current_user: UserContext | None = Depends(_user_dep),
    ) -> list[dict[str, Any]]:
        uid = current_user.id if current_user is not None else None
        return service.list_resumes(user_id=uid)

    @api.post("/api/resumes", status_code=201)
    def create_resume(
        data: dict[str, Any],
        current_user: UserContext | None = Depends(_user_dep),
    ) -> dict[str, Any]:
        label = data.get("label", "")
        if not label or not label.strip():
            raise HTTPException(status_code=422, detail="Label is required")
        uid = current_user.id if current_user is not None else None
        try:
            return service.create_resume(label, user_id=uid)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @api.get("/api/resumes/default")
    def get_default_resume(
        current_user: UserContext | None = Depends(_user_dep),
    ) -> dict[str, Any]:
        uid = current_user.id if current_user is not None else None
        try:
            version = service.get_resume(None, user_id=uid)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        resume = Resume(**version["resume_data"])
        version["resume_data"] = resume.model_dump()
        return version

    @api.get("/api/resumes/{version_id}")
    def get_resume_version(
        version_id: int,
        current_user: UserContext | None = Depends(_user_dep),
    ) -> dict[str, Any]:
        uid = current_user.id if current_user is not None else None
        try:
            version = service.get_resume(version_id, user_id=uid)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        resume = Resume(**version["resume_data"])
        version["resume_data"] = resume.model_dump()
        return version

    @api.patch("/api/resumes/{version_id}")
    def update_resume_metadata(
        version_id: int,
        data: dict[str, Any],
        current_user: UserContext | None = Depends(_user_dep),
    ) -> dict[str, Any]:
        label = data.get("label", "")
        if not label or not label.strip():
            raise HTTPException(status_code=422, detail="Label is required")
        uid = current_user.id if current_user is not None else None
        try:
            version = service.update_metadata(version_id, label, user_id=uid)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        resume = Resume(**version["resume_data"])
        version["resume_data"] = resume.model_dump()
        return version

    @api.delete("/api/resumes/{version_id}")
    def delete_resume_version(
        version_id: int,
        current_user: UserContext | None = Depends(_user_dep),
    ) -> dict[str, str]:
        uid = current_user.id if current_user is not None else None
        try:
            msg = service.delete_resume(version_id, user_id=uid)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            detail = str(e)
            if "last remaining" in detail:
                raise HTTPException(status_code=409, detail=detail)
            raise HTTPException(status_code=404, detail=detail)
        return {"message": msg}

    @api.post("/api/resumes/{version_id}/default")
    def set_resume_default(
        version_id: int,
        current_user: UserContext | None = Depends(_user_dep),
    ) -> dict[str, str]:
        uid = current_user.id if current_user is not None else None
        try:
            msg = service.set_default(version_id, user_id=uid)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return {"message": msg}

    @api.get("/api/resumes/{version_id}/{section}")
    def get_resume_section(
        version_id: int,
        section: str,
        current_user: UserContext | None = Depends(_user_dep),
    ) -> Any:
        if section not in ALL_SECTIONS:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Invalid section: '{section}'. "
                    f"Must be one of: {', '.join(ALL_SECTIONS)}"
                ),
            )
        uid = current_user.id if current_user is not None else None
        try:
            version = service.get_resume(version_id, user_id=uid)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        resume = Resume(**version["resume_data"])
        return resume.model_dump()[section]

    @api.put("/api/resumes/{version_id}/contact")
    def update_resume_contact(
        version_id: int,
        data: dict[str, Any],
        current_user: UserContext | None = Depends(_user_dep),
    ) -> dict[str, str]:
        uid = current_user.id if current_user is not None else None
        try:
            msg = service.update_section("contact", data, version_id, user_id=uid)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @api.put("/api/resumes/{version_id}/summary")
    def update_resume_summary(
        version_id: int,
        data: dict[str, Any],
        current_user: UserContext | None = Depends(_user_dep),
    ) -> dict[str, str]:
        text = data.get("text", "")
        if not text:
            raise HTTPException(
                status_code=422, detail="Summary text must not be empty"
            )
        uid = current_user.id if current_user is not None else None
        try:
            msg = service.update_section("summary", data, version_id, user_id=uid)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @api.post("/api/resumes/{version_id}/{section}/entries", status_code=201)
    def add_resume_entry(
        version_id: int,
        section: str,
        data: dict[str, Any],
        current_user: UserContext | None = Depends(_user_dep),
    ) -> dict[str, str]:
        if section not in SECTION_LIST:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid section for entries: '{section}'. "
                    f"Must be one of: {', '.join(SECTION_LIST)}"
                ),
            )
        uid = current_user.id if current_user is not None else None
        try:
            msg = service.add_entry(section, data, version_id, user_id=uid)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @api.put("/api/resumes/{version_id}/{section}/entries/{index}")
    def update_resume_entry(
        version_id: int,
        section: str,
        index: int,
        data: dict[str, Any],
        current_user: UserContext | None = Depends(_user_dep),
    ) -> dict[str, str]:
        if section not in SECTION_LIST:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid section for entries: '{section}'. "
                    f"Must be one of: {', '.join(SECTION_LIST)}"
                ),
            )
        uid = current_user.id if current_user is not None else None
        try:
            msg = service.update_entry(section, index, data, version_id, user_id=uid)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            detail = str(e)
            if "out of range" in detail:
                raise HTTPException(status_code=404, detail=detail)
            raise HTTPException(status_code=422, detail=detail)
        return {"message": msg}

    @api.delete("/api/resumes/{version_id}/{section}/entries/{index}")
    def remove_resume_entry(
        version_id: int,
        section: str,
        index: int,
        current_user: UserContext | None = Depends(_user_dep),
    ) -> dict[str, str]:
        if section not in SECTION_LIST:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid section for entries: '{section}'. "
                    f"Must be one of: {', '.join(SECTION_LIST)}"
                ),
            )
        uid = current_user.id if current_user is not None else None
        try:
            msg = service.remove_entry(section, index, version_id, user_id=uid)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            detail = str(e)
            if "out of range" in detail:
                raise HTTPException(status_code=404, detail=detail)
            raise HTTPException(status_code=422, detail=detail)
        return {"message": msg}

    # --- Old /api/resume routes (backward compat for existing tests) ---

    @api.get("/api/resume")
    def get_resume_legacy() -> dict[str, Any]:
        version = service.get_resume()
        resume = Resume(**version["resume_data"])
        return resume.model_dump()

    @api.get("/api/resume/{section}")
    def get_section_legacy(section: str) -> Any:
        if section not in ALL_SECTIONS:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Invalid section: '{section}'. "
                    f"Must be one of: {', '.join(ALL_SECTIONS)}"
                ),
            )
        version = service.get_resume()
        resume = Resume(**version["resume_data"])
        return resume.model_dump()[section]

    @api.put("/api/resume/contact")
    def update_contact_legacy(data: dict[str, Any]) -> dict[str, str]:
        try:
            msg = service.update_section("contact", data)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @api.put("/api/resume/summary")
    def update_summary_legacy(data: dict[str, Any]) -> dict[str, str]:
        text = data.get("text", "")
        if not text:
            raise HTTPException(
                status_code=422, detail="Summary text must not be empty"
            )
        try:
            msg = service.update_section("summary", data)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @api.post("/api/resume/{section}/entries", status_code=201)
    def add_entry_legacy(section: str, data: dict[str, Any]) -> dict[str, str]:
        if section not in SECTION_LIST:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid section for entries: '{section}'. "
                    f"Must be one of: {', '.join(SECTION_LIST)}"
                ),
            )
        try:
            msg = service.add_entry(section, data)
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @api.put("/api/resume/{section}/entries/{index}")
    def update_entry_legacy(
        section: str, index: int, data: dict[str, Any]
    ) -> dict[str, str]:
        if section not in SECTION_LIST:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid section for entries: '{section}'. "
                    f"Must be one of: {', '.join(SECTION_LIST)}"
                ),
            )
        try:
            msg = service.update_entry(section, index, data)
        except ValueError as e:
            detail = str(e)
            if "out of range" in detail:
                raise HTTPException(status_code=404, detail=detail)
            raise HTTPException(status_code=422, detail=detail)
        return {"message": msg}

    @api.delete("/api/resume/{section}/entries/{index}")
    def remove_entry_legacy(section: str, index: int) -> dict[str, str]:
        if section not in SECTION_LIST:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid section for entries: '{section}'. "
                    f"Must be one of: {', '.join(SECTION_LIST)}"
                ),
            )
        try:
            msg = service.remove_entry(section, index)
        except ValueError as e:
            detail = str(e)
            if "out of range" in detail:
                raise HTTPException(status_code=404, detail=detail)
            raise HTTPException(status_code=422, detail=detail)
        return {"message": msg}

    # ==========================================================
    # Application Routes
    # ==========================================================

    if app_service is not None:

        @api.get("/api/applications")
        def list_applications(
            status: str | None = None,
            q: str | None = None,
            current_user: UserContext | None = Depends(_user_dep),
        ) -> list[dict[str, Any]]:
            uid = current_user.id if current_user is not None else None
            return app_service.list_applications(status=status, q=q, user_id=uid)

        @api.post("/api/applications", status_code=201)
        def create_application(
            data: dict[str, Any],
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, Any]:
            uid = current_user.id if current_user is not None else None
            try:
                return app_service.create_application(data, user_id=uid)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))

        @api.get("/api/applications/{app_id}")
        def get_application(
            app_id: int,
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, Any]:
            uid = current_user.id if current_user is not None else None
            try:
                return app_service.get_application(app_id, user_id=uid)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @api.patch("/api/applications/{app_id}")
        def update_application(
            app_id: int,
            data: dict[str, Any],
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, Any]:
            uid = current_user.id if current_user is not None else None
            try:
                return app_service.update_application(app_id, data, user_id=uid)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                detail = str(e)
                if "not found" in detail:
                    raise HTTPException(status_code=404, detail=detail)
                raise HTTPException(status_code=422, detail=detail)

        @api.delete("/api/applications/{app_id}")
        def delete_application(
            app_id: int,
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, str]:
            uid = current_user.id if current_user is not None else None
            try:
                app = app_service.delete_application(app_id, user_id=uid)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            return {
                "message": (
                    f"Deleted application '{app['position']}' at "
                    f"'{app['company']}' and all associated data"
                )
            }

        # --- Application Contacts ---

        @api.get("/api/applications/{app_id}/contacts")
        def list_contacts(
            app_id: int,
            current_user: UserContext | None = Depends(_user_dep),
        ) -> list[dict[str, Any]]:
            uid = current_user.id if current_user is not None else None
            try:
                app_service.get_application(app_id, user_id=uid)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            return app_service.list_contacts(app_id)

        @api.post("/api/applications/{app_id}/contacts", status_code=201)
        def add_contact(
            app_id: int,
            data: dict[str, Any],
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, Any]:
            uid = current_user.id if current_user is not None else None
            try:
                app_service.get_application(app_id, user_id=uid)
                return app_service.add_contact(app_id, data)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                detail = str(e)
                if "not found" in detail:
                    raise HTTPException(status_code=404, detail=detail)
                raise HTTPException(status_code=422, detail=detail)

        @api.patch("/api/applications/{app_id}/contacts/{contact_id}")
        def update_contact(
            app_id: int,
            contact_id: int,
            data: dict[str, Any],
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, Any]:
            uid = current_user.id if current_user is not None else None
            try:
                app_service.get_application(app_id, user_id=uid)
                return app_service.update_contact(contact_id, data)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @api.delete("/api/applications/{app_id}/contacts/{contact_id}")
        def delete_contact(
            app_id: int,
            contact_id: int,
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, str]:
            uid = current_user.id if current_user is not None else None
            try:
                app_service.get_application(app_id, user_id=uid)
                name = app_service.remove_contact(contact_id)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            return {"message": f"Removed contact '{name}'"}

        # --- Communications ---

        @api.get("/api/applications/{app_id}/communications")
        def list_communications(
            app_id: int,
            current_user: UserContext | None = Depends(_user_dep),
        ) -> list[dict[str, Any]]:
            uid = current_user.id if current_user is not None else None
            try:
                app_service.get_application(app_id, user_id=uid)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            return app_service.list_communications(app_id)

        @api.post(
            "/api/applications/{app_id}/communications",
            status_code=201,
        )
        def add_communication(
            app_id: int,
            data: dict[str, Any],
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, Any]:
            uid = current_user.id if current_user is not None else None
            try:
                app_service.get_application(app_id, user_id=uid)
                return app_service.add_communication(app_id, data)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                detail = str(e)
                if "not found" in detail:
                    raise HTTPException(status_code=404, detail=detail)
                raise HTTPException(status_code=422, detail=detail)

        @api.patch("/api/applications/{app_id}/communications/{comm_id}")
        def update_communication(
            app_id: int,
            comm_id: int,
            data: dict[str, Any],
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, Any]:
            uid = current_user.id if current_user is not None else None
            try:
                app_service.get_application(app_id, user_id=uid)
                return app_service.update_communication(comm_id, data)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @api.delete("/api/applications/{app_id}/communications/{comm_id}")
        def delete_communication(
            app_id: int,
            comm_id: int,
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, str]:
            uid = current_user.id if current_user is not None else None
            try:
                app_service.get_application(app_id, user_id=uid)
                subject = app_service.remove_communication(comm_id)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            return {"message": f"Removed communication '{subject}'"}

        # --- Application Context ---

        @api.get("/api/applications/{app_id}/context")
        def get_application_context(
            app_id: int,
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, Any]:
            uid = current_user.id if current_user is not None else None
            try:
                return app_service.get_application_context(app_id, user_id=uid)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

    # ==========================================================
    # Accomplishment Routes
    # ==========================================================

    if acc_service is not None:

        @api.get("/api/accomplishments")
        def list_accomplishments(
            tag: str | None = None,
            q: str | None = None,
            current_user: UserContext | None = Depends(_user_dep),
        ) -> list[dict[str, Any]]:
            uid = current_user.id if current_user is not None else None
            return acc_service.list_accomplishments(tag=tag, q=q, user_id=uid)

        @api.post("/api/accomplishments", status_code=201)
        def create_accomplishment(
            data: dict[str, Any],
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, Any]:
            uid = current_user.id if current_user is not None else None
            try:
                return acc_service.create_accomplishment(data, user_id=uid)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))

        # NOTE: /tags MUST be registered BEFORE /{acc_id} to prevent FastAPI
        # matching the literal string "tags" as an integer path parameter.
        @api.get("/api/accomplishments/tags")
        def list_accomplishment_tags() -> list[str]:
            return acc_service.list_tags()

        @api.get("/api/accomplishments/{acc_id}")
        def get_accomplishment(
            acc_id: int,
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, Any]:
            uid = current_user.id if current_user is not None else None
            try:
                return acc_service.get_accomplishment(acc_id, user_id=uid)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @api.patch("/api/accomplishments/{acc_id}")
        def update_accomplishment(
            acc_id: int,
            data: dict[str, Any],
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, Any]:
            uid = current_user.id if current_user is not None else None
            try:
                return acc_service.update_accomplishment(acc_id, data, user_id=uid)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                detail = str(e)
                if "not found" in detail:
                    raise HTTPException(status_code=404, detail=detail)
                raise HTTPException(status_code=422, detail=detail)

        @api.delete("/api/accomplishments/{acc_id}")
        def delete_accomplishment(
            acc_id: int,
            current_user: UserContext | None = Depends(_user_dep),
        ) -> dict[str, str]:
            uid = current_user.id if current_user is not None else None
            try:
                acc = acc_service.delete_accomplishment(acc_id, user_id=uid)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            return {"message": f"Deleted accomplishment '{acc['title']}'"}

    # ==========================================================
    # Webhook Routes (no auth — verified via Svix signature)
    # ==========================================================

    @router.post("/api/webhooks/clerk")
    async def clerk_webhook(request: Any) -> dict[str, str]:
        """Handle Clerk lifecycle webhooks (user.deleted, etc.)."""
        from fastapi import Request

        if not isinstance(request, Request):
            raise HTTPException(status_code=400, detail="Invalid request")
        return await _handle_clerk_webhook(request)

    # Include protected sub-router
    router.include_router(api)
    return router


async def _handle_clerk_webhook(request: Any) -> dict[str, str]:
    """Verify Svix signature and process Clerk webhook events."""
    import json
    import os

    from fastapi import HTTPException, Request
    from svix.webhooks import Webhook, WebhookVerificationError

    if not isinstance(request, Request):
        raise HTTPException(status_code=400, detail="Invalid request")

    webhook_secret = os.environ.get("CLERK_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise HTTPException(
            status_code=500, detail="CLERK_WEBHOOK_SECRET is not configured"
        )

    payload = await request.body()
    headers = dict(request.headers)

    try:
        wh = Webhook(webhook_secret)
        event = wh.verify(payload, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if isinstance(event, (str, bytes)):
        event = json.loads(event)

    event_type = event.get("type", "")
    if event_type == "user.deleted":
        user_id = event.get("data", {}).get("id")
        if user_id:
            from persona.database import delete_user

            try:
                from persona.server import _conn

                if _conn is not None:
                    delete_user(_conn, user_id)
            except ImportError:
                pass

    return {"status": "ok"}
