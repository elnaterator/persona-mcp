"""FastAPI route handlers for the Persona REST API."""

from typing import Any

from fastapi import APIRouter, HTTPException

from persona.application_service import ApplicationService
from persona.models import Resume
from persona.resume_service import ALL_SECTIONS, SECTION_LIST, ResumeService


def create_router(
    service: ResumeService,
    app_service: ApplicationService | None = None,
) -> APIRouter:
    """Create an APIRouter with all endpoints."""
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # ==========================================================
    # Resume Version Routes
    # ==========================================================

    @router.get("/api/resumes")
    def list_resumes() -> list[dict[str, Any]]:
        return service.list_resumes()

    @router.post("/api/resumes", status_code=201)
    def create_resume(data: dict[str, Any]) -> dict[str, Any]:
        label = data.get("label", "")
        if not label or not label.strip():
            raise HTTPException(status_code=422, detail="Label is required")
        try:
            return service.create_resume(label)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/api/resumes/default")
    def get_default_resume() -> dict[str, Any]:
        try:
            version = service.get_resume(None)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        resume = Resume(**version["resume_data"])
        version["resume_data"] = resume.model_dump()
        return version

    @router.get("/api/resumes/{version_id}")
    def get_resume_version(version_id: int) -> dict[str, Any]:
        try:
            version = service.get_resume(version_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        resume = Resume(**version["resume_data"])
        version["resume_data"] = resume.model_dump()
        return version

    @router.put("/api/resumes/{version_id}")
    def update_resume_metadata(version_id: int, data: dict[str, Any]) -> dict[str, Any]:
        label = data.get("label", "")
        if not label or not label.strip():
            raise HTTPException(status_code=422, detail="Label is required")
        try:
            version = service.update_metadata(version_id, label)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        resume = Resume(**version["resume_data"])
        version["resume_data"] = resume.model_dump()
        return version

    @router.delete("/api/resumes/{version_id}")
    def delete_resume_version(version_id: int) -> dict[str, str]:
        try:
            msg = service.delete_resume(version_id)
        except ValueError as e:
            detail = str(e)
            if "last remaining" in detail:
                raise HTTPException(status_code=409, detail=detail)
            raise HTTPException(status_code=404, detail=detail)
        return {"message": msg}

    @router.put("/api/resumes/{version_id}/default")
    def set_resume_default(version_id: int) -> dict[str, str]:
        try:
            msg = service.set_default(version_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return {"message": msg}

    @router.get("/api/resumes/{version_id}/{section}")
    def get_resume_section(version_id: int, section: str) -> Any:
        if section not in ALL_SECTIONS:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Invalid section: '{section}'. "
                    f"Must be one of: {', '.join(ALL_SECTIONS)}"
                ),
            )
        try:
            version = service.get_resume(version_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        resume = Resume(**version["resume_data"])
        return resume.model_dump()[section]

    @router.put("/api/resumes/{version_id}/contact")
    def update_resume_contact(version_id: int, data: dict[str, Any]) -> dict[str, str]:
        try:
            msg = service.update_section("contact", data, version_id)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @router.put("/api/resumes/{version_id}/summary")
    def update_resume_summary(version_id: int, data: dict[str, Any]) -> dict[str, str]:
        text = data.get("text", "")
        if not text:
            raise HTTPException(
                status_code=422, detail="Summary text must not be empty"
            )
        try:
            msg = service.update_section("summary", data, version_id)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @router.post("/api/resumes/{version_id}/{section}/entries", status_code=201)
    def add_resume_entry(
        version_id: int, section: str, data: dict[str, Any]
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
            msg = service.add_entry(section, data, version_id)
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @router.put("/api/resumes/{version_id}/{section}/entries/{index}")
    def update_resume_entry(
        version_id: int, section: str, index: int, data: dict[str, Any]
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
            msg = service.update_entry(section, index, data, version_id)
        except ValueError as e:
            detail = str(e)
            if "out of range" in detail:
                raise HTTPException(status_code=404, detail=detail)
            raise HTTPException(status_code=422, detail=detail)
        return {"message": msg}

    @router.delete("/api/resumes/{version_id}/{section}/entries/{index}")
    def remove_resume_entry(
        version_id: int, section: str, index: int
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
            msg = service.remove_entry(section, index, version_id)
        except ValueError as e:
            detail = str(e)
            if "out of range" in detail:
                raise HTTPException(status_code=404, detail=detail)
            raise HTTPException(status_code=422, detail=detail)
        return {"message": msg}

    # --- Old /api/resume routes (backward compat for existing tests) ---

    @router.get("/api/resume")
    def get_resume_legacy() -> dict[str, Any]:
        version = service.get_resume()
        resume = Resume(**version["resume_data"])
        return resume.model_dump()

    @router.get("/api/resume/{section}")
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

    @router.put("/api/resume/contact")
    def update_contact_legacy(data: dict[str, Any]) -> dict[str, str]:
        try:
            msg = service.update_section("contact", data)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @router.put("/api/resume/summary")
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

    @router.post("/api/resume/{section}/entries", status_code=201)
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

    @router.put("/api/resume/{section}/entries/{index}")
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

    @router.delete("/api/resume/{section}/entries/{index}")
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

        @router.get("/api/applications")
        def list_applications(
            status: str | None = None, q: str | None = None
        ) -> list[dict[str, Any]]:
            return app_service.list_applications(status=status, q=q)

        @router.post("/api/applications", status_code=201)
        def create_application(data: dict[str, Any]) -> dict[str, Any]:
            try:
                return app_service.create_application(data)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))

        @router.get("/api/applications/{app_id}")
        def get_application(app_id: int) -> dict[str, Any]:
            try:
                return app_service.get_application(app_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @router.put("/api/applications/{app_id}")
        def update_application(app_id: int, data: dict[str, Any]) -> dict[str, Any]:
            try:
                return app_service.update_application(app_id, data)
            except ValueError as e:
                detail = str(e)
                if "not found" in detail:
                    raise HTTPException(status_code=404, detail=detail)
                raise HTTPException(status_code=422, detail=detail)

        @router.delete("/api/applications/{app_id}")
        def delete_application(app_id: int) -> dict[str, str]:
            try:
                app = app_service.delete_application(app_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            return {
                "message": (
                    f"Deleted application '{app['position']}' at "
                    f"'{app['company']}' and all associated data"
                )
            }

        # --- Application Contacts ---

        @router.get("/api/applications/{app_id}/contacts")
        def list_contacts(app_id: int) -> list[dict[str, Any]]:
            try:
                app_service.get_application(app_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            return app_service.list_contacts(app_id)

        @router.post("/api/applications/{app_id}/contacts", status_code=201)
        def add_contact(app_id: int, data: dict[str, Any]) -> dict[str, Any]:
            try:
                return app_service.add_contact(app_id, data)
            except ValueError as e:
                detail = str(e)
                if "not found" in detail:
                    raise HTTPException(status_code=404, detail=detail)
                raise HTTPException(status_code=422, detail=detail)

        @router.put("/api/applications/{app_id}/contacts/{contact_id}")
        def update_contact(
            app_id: int, contact_id: int, data: dict[str, Any]
        ) -> dict[str, Any]:
            try:
                return app_service.update_contact(contact_id, data)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @router.delete("/api/applications/{app_id}/contacts/{contact_id}")
        def delete_contact(app_id: int, contact_id: int) -> dict[str, str]:
            try:
                name = app_service.remove_contact(contact_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            return {"message": f"Removed contact '{name}'"}

        # --- Communications ---

        @router.get("/api/applications/{app_id}/communications")
        def list_communications(app_id: int) -> list[dict[str, Any]]:
            try:
                app_service.get_application(app_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            return app_service.list_communications(app_id)

        @router.post(
            "/api/applications/{app_id}/communications",
            status_code=201,
        )
        def add_communication(app_id: int, data: dict[str, Any]) -> dict[str, Any]:
            try:
                return app_service.add_communication(app_id, data)
            except ValueError as e:
                detail = str(e)
                if "not found" in detail:
                    raise HTTPException(status_code=404, detail=detail)
                raise HTTPException(status_code=422, detail=detail)

        @router.put("/api/applications/{app_id}/communications/{comm_id}")
        def update_communication(
            app_id: int, comm_id: int, data: dict[str, Any]
        ) -> dict[str, Any]:
            try:
                return app_service.update_communication(comm_id, data)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @router.delete("/api/applications/{app_id}/communications/{comm_id}")
        def delete_communication(app_id: int, comm_id: int) -> dict[str, str]:
            try:
                subject = app_service.remove_communication(comm_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            return {"message": f"Removed communication '{subject}'"}

        # --- Application Context ---

        @router.get("/api/applications/{app_id}/context")
        def get_application_context(app_id: int) -> dict[str, Any]:
            try:
                return app_service.get_application_context(app_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

    return router
