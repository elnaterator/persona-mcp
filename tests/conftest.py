"""Shared test fixtures for persona MCP server tests."""

from pathlib import Path

import pytest

SAMPLE_RESUME_MD = """\
---
name: "Jane Doe"
email: "jane@example.com"
phone: "+1-555-0100"
location: "San Francisco, CA"
linkedin: "https://linkedin.com/in/janedoe"
website: "https://janedoe.dev"
github: "https://github.com/janedoe"
---

## Summary

Experienced software engineer with 10 years of experience.

## Experience

### Senior Software Engineer | Acme Corp
- **Start**: 2021-01
- **End**: present
- **Location**: San Francisco, CA

- Led migration of monolithic application to microservices
- Reduced deployment time by 60%

### Software Engineer | StartupCo
- **Start**: 2018-06
- **End**: 2020-12
- **Location**: New York, NY

- Built real-time data pipeline processing 1M events/day
- Mentored 3 junior engineers

## Education

### M.S. Computer Science | Stanford University
- **Start**: 2016-09
- **End**: 2018-05
- **Honors**: Dean's List

### B.S. Computer Science | UC Berkeley
- **Start**: 2012-09
- **End**: 2016-05

## Skills

### Programming Languages
- Python
- TypeScript
- Go

### Frameworks
- FastAPI
- React
- Kubernetes

### Soft Skills
- Technical Leadership
- Mentoring
"""

EMPTY_RESUME_MD = """\
---
---
"""


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory with jobs/resume/ structure."""
    resume_dir = tmp_path / "jobs" / "resume"
    resume_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def sample_resume_path(tmp_data_dir: Path) -> Path:
    """Create a sample resume.md in the tmp data directory."""
    resume_path = tmp_data_dir / "jobs" / "resume" / "resume.md"
    resume_path.write_text(SAMPLE_RESUME_MD)
    return resume_path


@pytest.fixture
def empty_resume_path(tmp_data_dir: Path) -> Path:
    """Create an empty resume.md in the tmp data directory."""
    resume_path = tmp_data_dir / "jobs" / "resume" / "resume.md"
    resume_path.write_text(EMPTY_RESUME_MD)
    return resume_path
