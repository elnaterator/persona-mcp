"""FastAPI route handlers for the Persona REST API."""

from typing import Any

from fastapi import APIRouter, HTTPException

from persona.resume_service import ALL_SECTIONS, SECTION_LIST, ResumeService


def create_router(service: ResumeService) -> APIRouter:
    """Create an APIRouter with all resume endpoints bound to the given service."""
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/api/resume")
    def get_resume() -> dict[str, Any]:
        resume = service.get_resume()
        return resume.model_dump()

    @router.get("/api/resume/{section}")
    def get_section(section: str) -> Any:
        if section not in ALL_SECTIONS:
            raise HTTPException(
                status_code=404,
                detail=f"Invalid section: '{section}'. "
                f"Must be one of: {', '.join(ALL_SECTIONS)}",
            )
        return service.get_section(section)

    @router.put("/api/resume/contact")
    def update_contact(data: dict[str, Any]) -> dict[str, str]:
        try:
            msg = service.update_section("contact", data)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @router.put("/api/resume/summary")
    def update_summary(data: dict[str, Any]) -> dict[str, str]:
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
    def add_entry(section: str, data: dict[str, Any]) -> dict[str, str]:
        if section not in SECTION_LIST:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid section for entries: '{section}'. "
                f"Must be one of: {', '.join(SECTION_LIST)}",
            )
        try:
            msg = service.add_entry(section, data)
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=422, detail=str(e))
        return {"message": msg}

    @router.put("/api/resume/{section}/entries/{index}")
    def update_entry(section: str, index: int, data: dict[str, Any]) -> dict[str, str]:
        if section not in SECTION_LIST:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid section for entries: '{section}'. "
                f"Must be one of: {', '.join(SECTION_LIST)}",
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
    def remove_entry(section: str, index: int) -> dict[str, str]:
        if section not in SECTION_LIST:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid section for entries: '{section}'. "
                f"Must be one of: {', '.join(SECTION_LIST)}",
            )
        try:
            msg = service.remove_entry(section, index)
        except ValueError as e:
            detail = str(e)
            if "out of range" in detail:
                raise HTTPException(status_code=404, detail=detail)
            raise HTTPException(status_code=422, detail=detail)
        return {"message": msg}

    return router
