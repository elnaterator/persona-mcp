"""Unit tests for persona.database module (v2 schema)."""

import sqlite3
from pathlib import Path

import pytest


class TestInitDatabase:
    """Tests for init_database function."""

    def test_creates_db_file(self, tmp_path: Path) -> None:
        from persona.database import init_database

        conn = init_database(tmp_path)
        assert (tmp_path / "persona.db").exists()
        conn.close()

    def test_creates_data_dir_if_missing(self, tmp_path: Path) -> None:
        from persona.database import init_database

        data_dir = tmp_path / "nested" / "dir"
        conn = init_database(data_dir)
        assert (data_dir / "persona.db").exists()
        conn.close()

    def test_sets_wal_mode(self, tmp_path: Path) -> None:
        from persona.database import init_database

        conn = init_database(tmp_path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
        conn.close()

    def test_sets_foreign_keys_on(self, tmp_path: Path) -> None:
        from persona.database import init_database

        conn = init_database(tmp_path)
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1
        conn.close()

    def test_sets_busy_timeout(self, tmp_path: Path) -> None:
        from persona.database import init_database

        conn = init_database(tmp_path)
        timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
        assert timeout == 5000
        conn.close()

    def test_runs_migrations(self, tmp_path: Path) -> None:
        from persona.database import init_database
        from persona.migrations import SCHEMA_VERSION

        conn = init_database(tmp_path)
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == SCHEMA_VERSION
        conn.close()

    def test_returns_connection(self, tmp_path: Path) -> None:
        from persona.database import init_database

        conn = init_database(tmp_path)
        assert isinstance(conn, sqlite3.Connection)
        conn.close()


class TestCreateResumeVersion:
    """Tests for create_resume_version."""

    def test_creates_version_with_data(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_resume_version

        data = {"contact": {"name": "Alice"}, "summary": "A test."}
        result = create_resume_version(db_conn, "Test Resume", data)

        assert result["id"] is not None
        assert result["label"] == "Test Resume"
        assert result["is_default"] is False
        assert result["resume_data"] == data

    def test_returns_parsed_resume_data(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_resume_version

        data = {"skills": [{"name": "Python", "category": "Languages"}]}
        result = create_resume_version(db_conn, "Skills Resume", data)

        assert isinstance(result["resume_data"], dict)
        assert result["resume_data"]["skills"][0]["name"] == "Python"

    def test_multiple_versions_get_unique_ids(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.database import create_resume_version

        v1 = create_resume_version(db_conn, "Version A", {})
        v2 = create_resume_version(db_conn, "Version B", {})

        assert v1["id"] != v2["id"]

    def test_new_version_not_default(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_resume_version

        result = create_resume_version(db_conn, "Non-Default", {"summary": "hi"})
        assert result["is_default"] is False


class TestLoadResumeVersion:
    """Tests for load_resume_version."""

    def test_loads_version_by_id(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_resume_version, load_resume_version

        created = create_resume_version(db_conn, "My Resume", {"summary": "hello"})
        loaded = load_resume_version(db_conn, created["id"])

        assert loaded["id"] == created["id"]
        assert loaded["label"] == "My Resume"
        assert loaded["resume_data"]["summary"] == "hello"

    def test_raises_for_missing_id(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_resume_version

        with pytest.raises(ValueError, match="not found"):
            load_resume_version(db_conn, 9999)

    def test_json_round_trip(self, db_conn: sqlite3.Connection) -> None:
        """SC-001: Data written and read back must match exactly."""
        from persona.database import create_resume_version, load_resume_version

        original = {
            "contact": {"name": "Jane", "email": "jane@example.com"},
            "summary": "Experienced engineer.",
            "experience": [{"title": "Dev", "company": "Acme"}],
            "education": [],
            "skills": [{"name": "Python", "category": "Languages"}],
        }
        created = create_resume_version(db_conn, "Round Trip", original)
        loaded = load_resume_version(db_conn, created["id"])

        assert loaded["resume_data"] == original


class TestLoadResumeVersions:
    """Tests for load_resume_versions."""

    def test_returns_all_versions(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_resume_version, load_resume_versions

        create_resume_version(db_conn, "Alpha", {})
        create_resume_version(db_conn, "Beta", {})
        versions = load_resume_versions(db_conn)

        # db_conn fixture already has a default version from migration
        labels = [v["label"] for v in versions]
        assert "Alpha" in labels
        assert "Beta" in labels

    def test_includes_metadata_fields(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_resume_versions

        versions = load_resume_versions(db_conn)
        assert len(versions) >= 1
        v = versions[0]
        assert "id" in v
        assert "label" in v
        assert "is_default" in v
        assert "app_count" in v
        assert "created_at" in v
        assert "updated_at" in v

    def test_app_count_is_zero_for_new_version(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.database import create_resume_version, load_resume_versions

        create_resume_version(db_conn, "No Apps", {})
        versions = load_resume_versions(db_conn)
        no_apps = next(v for v in versions if v["label"] == "No Apps")

        assert no_apps["app_count"] == 0

    def test_returns_list(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_resume_versions

        result = load_resume_versions(db_conn)
        assert isinstance(result, list)


class TestLoadDefaultResumeVersion:
    """Tests for load_default_resume_version."""

    def test_returns_default_version(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_default_resume_version

        default = load_default_resume_version(db_conn)
        assert default["is_default"] is True

    def test_raises_when_no_default(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_default_resume_version

        db_conn.execute("UPDATE resume_version SET is_default = 0")
        db_conn.commit()

        with pytest.raises(ValueError, match="No default"):
            load_default_resume_version(db_conn)

    def test_returns_full_resume_data(
        self, db_conn_with_data: sqlite3.Connection
    ) -> None:
        from persona.database import load_default_resume_version

        default = load_default_resume_version(db_conn_with_data)
        assert default["resume_data"]["contact"]["name"] == "Jane Doe"


class TestUpdateResumeVersionMetadata:
    """Tests for update_resume_version_metadata."""

    def test_updates_label(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            load_default_resume_version,
            update_resume_version_metadata,
        )

        version = load_default_resume_version(db_conn)
        updated = update_resume_version_metadata(db_conn, version["id"], "New Label")

        assert updated["label"] == "New Label"
        assert updated["id"] == version["id"]

    def test_raises_for_missing_id(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import update_resume_version_metadata

        with pytest.raises(ValueError, match="not found"):
            update_resume_version_metadata(db_conn, 9999, "Ghost")

    def test_does_not_change_resume_data(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            load_default_resume_version,
            update_resume_version_data,
            update_resume_version_metadata,
        )

        version = load_default_resume_version(db_conn)
        original_data = {"summary": "preserved"}
        update_resume_version_data(db_conn, version["id"], original_data)

        updated = update_resume_version_metadata(db_conn, version["id"], "Renamed")
        assert updated["resume_data"] == original_data


class TestUpdateResumeVersionData:
    """Tests for update_resume_version_data."""

    def test_updates_resume_data(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            load_default_resume_version,
            load_resume_version,
            update_resume_version_data,
        )

        version = load_default_resume_version(db_conn)
        new_data = {"summary": "Updated summary", "contact": {"name": "Bob"}}
        update_resume_version_data(db_conn, version["id"], new_data)

        reloaded = load_resume_version(db_conn, version["id"])
        assert reloaded["resume_data"]["summary"] == "Updated summary"
        assert reloaded["resume_data"]["contact"]["name"] == "Bob"

    def test_raises_for_missing_id(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import update_resume_version_data

        with pytest.raises(ValueError, match="not found"):
            update_resume_version_data(db_conn, 9999, {})

    def test_json_round_trip_complex_data(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            load_default_resume_version,
            load_resume_version,
            update_resume_version_data,
        )

        version = load_default_resume_version(db_conn)
        complex_data = {
            "contact": {"name": "Alice", "email": "alice@test.com"},
            "summary": "A summary.",
            "experience": [
                {"title": "Engineer", "company": "Corp", "highlights": ["a", "b"]}
            ],
            "skills": [{"name": "Go", "category": "Languages"}],
        }
        update_resume_version_data(db_conn, version["id"], complex_data)

        reloaded = load_resume_version(db_conn, version["id"])
        assert reloaded["resume_data"] == complex_data


class TestDeleteResumeVersion:
    """Tests for delete_resume_version."""

    def test_deletes_non_default_version(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_resume_version,
            delete_resume_version,
            load_resume_versions,
        )

        created = create_resume_version(db_conn, "Temp", {})
        delete_resume_version(db_conn, created["id"])

        versions = load_resume_versions(db_conn)
        ids = [v["id"] for v in versions]
        assert created["id"] not in ids

    def test_returns_label_of_deleted_version(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.database import create_resume_version, delete_resume_version

        created = create_resume_version(db_conn, "Deletable", {})
        label = delete_resume_version(db_conn, created["id"])

        assert label == "Deletable"

    def test_raises_when_deleting_last_version(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.database import delete_resume_version, load_default_resume_version

        default = load_default_resume_version(db_conn)
        with pytest.raises(ValueError, match="last remaining"):
            delete_resume_version(db_conn, default["id"])

    def test_raises_for_missing_id(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import delete_resume_version

        with pytest.raises(ValueError, match="not found"):
            delete_resume_version(db_conn, 9999)

    def test_auto_promotes_when_deleting_default(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.database import (
            create_resume_version,
            delete_resume_version,
            load_default_resume_version,
            load_resume_versions,
        )

        other = create_resume_version(db_conn, "Other", {})
        default = load_default_resume_version(db_conn)

        delete_resume_version(db_conn, default["id"])

        new_default = load_default_resume_version(db_conn)
        assert new_default["is_default"] is True

        versions = load_resume_versions(db_conn)
        assert len(versions) == 1
        assert versions[0]["id"] == other["id"]


class TestSetDefaultResumeVersion:
    """Tests for set_default_resume_version."""

    def test_sets_new_default(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_resume_version,
            load_default_resume_version,
            set_default_resume_version,
        )

        new_version = create_resume_version(db_conn, "New Default", {})
        set_default_resume_version(db_conn, new_version["id"])

        default = load_default_resume_version(db_conn)
        assert default["id"] == new_version["id"]

    def test_unsets_previous_default(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_resume_version,
            load_resume_version,
            load_resume_versions,
            set_default_resume_version,
        )

        old_default_id = load_resume_versions(db_conn)[0]["id"]
        new_version = create_resume_version(db_conn, "New One", {})
        set_default_resume_version(db_conn, new_version["id"])

        old = load_resume_version(db_conn, old_default_id)
        assert old["is_default"] is False

    def test_returns_label(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_resume_version,
            set_default_resume_version,
        )

        v = create_resume_version(db_conn, "Promoted", {})
        label = set_default_resume_version(db_conn, v["id"])

        assert label == "Promoted"

    def test_raises_for_missing_id(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import set_default_resume_version

        with pytest.raises(ValueError, match="not found"):
            set_default_resume_version(db_conn, 9999)

    def test_only_one_default_after_set(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_resume_version,
            load_resume_versions,
            set_default_resume_version,
        )

        v1 = create_resume_version(db_conn, "V1", {})
        v2 = create_resume_version(db_conn, "V2", {})
        set_default_resume_version(db_conn, v1["id"])
        set_default_resume_version(db_conn, v2["id"])

        versions = load_resume_versions(db_conn)
        defaults = [v for v in versions if v["is_default"]]
        assert len(defaults) == 1
        assert defaults[0]["id"] == v2["id"]


# ============================================================
# Application DB operations
# ============================================================


class TestCreateApplication:
    """Tests for create_application."""

    def test_creates_with_all_fields(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, load_default_resume_version

        default = load_default_resume_version(db_conn)
        data = {
            "company": "Acme",
            "position": "Engineer",
            "description": "Do stuff",
            "status": "Applied",
            "url": "https://example.com",
            "notes": "Great company",
            "resume_version_id": default["id"],
        }
        result = create_application(db_conn, data)

        assert result["id"] is not None
        assert result["company"] == "Acme"
        assert result["position"] == "Engineer"
        assert result["status"] == "Applied"
        assert result["url"] == "https://example.com"
        assert result["resume_version_id"] == default["id"]

    def test_creates_with_minimal_fields(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application

        result = create_application(db_conn, {"company": "Corp", "position": "Dev"})

        assert result["company"] == "Corp"
        assert result["position"] == "Dev"
        assert result["status"] == "Interested"

    def test_multiple_apps_get_unique_ids(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application

        a1 = create_application(db_conn, {"company": "A", "position": "P1"})
        a2 = create_application(db_conn, {"company": "B", "position": "P2"})

        assert a1["id"] != a2["id"]

    def test_resume_version_id_fk(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, load_default_resume_version

        default = load_default_resume_version(db_conn)
        result = create_application(
            db_conn,
            {"company": "X", "position": "Y", "resume_version_id": default["id"]},
        )

        assert result["resume_version_id"] == default["id"]


class TestLoadApplication:
    """Tests for load_application."""

    def test_loads_existing_application(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, load_application

        created = create_application(db_conn, {"company": "Foo", "position": "Bar"})
        loaded = load_application(db_conn, created["id"])

        assert loaded["id"] == created["id"]
        assert loaded["company"] == "Foo"
        assert loaded["position"] == "Bar"

    def test_raises_for_nonexistent_id(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_application

        with pytest.raises(ValueError, match="not found"):
            load_application(db_conn, 9999)


class TestLoadApplications:
    """Tests for load_applications."""

    def test_returns_all_applications(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, load_applications

        create_application(db_conn, {"company": "A", "position": "P1"})
        create_application(db_conn, {"company": "B", "position": "P2"})
        results = load_applications(db_conn)

        assert len(results) == 2

    def test_filter_by_status(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, load_applications

        create_application(
            db_conn, {"company": "A", "position": "P1", "status": "Applied"}
        )
        create_application(
            db_conn, {"company": "B", "position": "P2", "status": "Interested"}
        )
        results = load_applications(db_conn, status="Applied")

        assert len(results) == 1
        assert results[0]["company"] == "A"

    def test_search_by_company(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, load_applications

        create_application(db_conn, {"company": "Acme Corp", "position": "Dev"})
        create_application(db_conn, {"company": "Other Inc", "position": "QA"})
        results = load_applications(db_conn, q="acme")

        assert len(results) == 1
        assert results[0]["company"] == "Acme Corp"

    def test_search_by_position(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, load_applications

        create_application(db_conn, {"company": "Corp", "position": "Backend Engineer"})
        create_application(db_conn, {"company": "Corp", "position": "Designer"})
        results = load_applications(db_conn, q="engineer")

        assert len(results) == 1
        assert results[0]["position"] == "Backend Engineer"

    def test_combined_filter_and_search(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, load_applications

        create_application(
            db_conn,
            {"company": "Acme", "position": "Engineer", "status": "Applied"},
        )
        create_application(
            db_conn,
            {"company": "Acme", "position": "Designer", "status": "Interested"},
        )
        results = load_applications(db_conn, status="Applied", q="acme")

        assert len(results) == 1
        assert results[0]["position"] == "Engineer"

    def test_returns_empty_list_when_no_match(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.database import create_application, load_applications

        create_application(db_conn, {"company": "Foo", "position": "Bar"})
        results = load_applications(db_conn, q="zzznomatch")

        assert results == []

    def test_returns_empty_list_on_empty_db(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import load_applications

        results = load_applications(db_conn)

        assert results == []


class TestUpdateApplication:
    """Tests for update_application."""

    def test_updates_single_field(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, update_application

        app = create_application(db_conn, {"company": "Corp", "position": "Dev"})
        updated = update_application(db_conn, app["id"], {"status": "Applied"})

        assert updated["status"] == "Applied"
        assert updated["company"] == "Corp"

    def test_updates_multiple_fields(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, update_application

        app = create_application(db_conn, {"company": "Corp", "position": "Dev"})
        updated = update_application(
            db_conn,
            app["id"],
            {"company": "NewCorp", "notes": "Great fit"},
        )

        assert updated["company"] == "NewCorp"
        assert updated["notes"] == "Great fit"

    def test_raises_for_nonexistent_id(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import update_application

        with pytest.raises(ValueError, match="not found"):
            update_application(db_conn, 9999, {"status": "Applied"})


class TestDeleteApplication:
    """Tests for delete_application."""

    def test_deletes_existing_application(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_application,
            delete_application,
            load_applications,
        )

        app = create_application(db_conn, {"company": "Corp", "position": "Dev"})
        delete_application(db_conn, app["id"])
        results = load_applications(db_conn)

        assert all(r["id"] != app["id"] for r in results)

    def test_raises_for_nonexistent_id(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import delete_application

        with pytest.raises(ValueError, match="not found"):
            delete_application(db_conn, 9999)

    def test_cascades_contacts_and_communications(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.database import (
            create_application,
            create_communication,
            create_contact,
            delete_application,
        )

        app = create_application(db_conn, {"company": "C", "position": "P"})
        create_contact(db_conn, app["id"], {"name": "Alice"})
        create_communication(
            db_conn,
            app["id"],
            {
                "type": "email",
                "direction": "sent",
                "body": "Hello",
                "date": "2024-01-01",
            },
        )

        delete_application(db_conn, app["id"])

        contact_count = db_conn.execute(
            "SELECT COUNT(*) FROM application_contact WHERE app_id = ?",
            (app["id"],),
        ).fetchone()[0]
        comm_count = db_conn.execute(
            "SELECT COUNT(*) FROM communication WHERE app_id = ?",
            (app["id"],),
        ).fetchone()[0]

        assert contact_count == 0
        assert comm_count == 0


class TestCreateContact:
    """Tests for create_contact."""

    def test_creates_with_all_fields(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, create_contact

        app = create_application(db_conn, {"company": "C", "position": "P"})
        data = {
            "name": "Bob Smith",
            "role": "Recruiter",
            "email": "bob@corp.com",
            "phone": "+1-555-0001",
            "notes": "Very helpful",
        }
        result = create_contact(db_conn, app["id"], data)

        assert result["name"] == "Bob Smith"
        assert result["role"] == "Recruiter"
        assert result["email"] == "bob@corp.com"
        assert result["app_id"] == app["id"]

    def test_creates_with_minimal_fields(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, create_contact

        app = create_application(db_conn, {"company": "C", "position": "P"})
        result = create_contact(db_conn, app["id"], {"name": "Alice"})

        assert result["name"] == "Alice"
        assert result["app_id"] == app["id"]

    def test_raises_for_nonexistent_app(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_contact

        with pytest.raises(ValueError, match="not found"):
            create_contact(db_conn, 9999, {"name": "Ghost"})


class TestLoadContacts:
    """Tests for load_contacts."""

    def test_loads_all_contacts_for_app(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, create_contact, load_contacts

        app = create_application(db_conn, {"company": "C", "position": "P"})
        create_contact(db_conn, app["id"], {"name": "Alice"})
        create_contact(db_conn, app["id"], {"name": "Bob"})
        results = load_contacts(db_conn, app["id"])

        assert len(results) == 2

    def test_returns_empty_list_when_no_contacts(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.database import create_application, load_contacts

        app = create_application(db_conn, {"company": "C", "position": "P"})
        results = load_contacts(db_conn, app["id"])

        assert results == []

    def test_ordered_by_id(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, create_contact, load_contacts

        app = create_application(db_conn, {"company": "C", "position": "P"})
        c1 = create_contact(db_conn, app["id"], {"name": "First"})
        c2 = create_contact(db_conn, app["id"], {"name": "Second"})
        results = load_contacts(db_conn, app["id"])

        assert results[0]["id"] == c1["id"]
        assert results[1]["id"] == c2["id"]


class TestUpdateContact:
    """Tests for update_contact."""

    def test_updates_fields(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, create_contact, update_contact

        app = create_application(db_conn, {"company": "C", "position": "P"})
        contact = create_contact(db_conn, app["id"], {"name": "Alice"})
        updated = update_contact(
            db_conn, contact["id"], {"email": "alice@corp.com", "role": "HR"}
        )

        assert updated["email"] == "alice@corp.com"
        assert updated["role"] == "HR"
        assert updated["name"] == "Alice"

    def test_raises_for_nonexistent_contact(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import update_contact

        with pytest.raises(ValueError, match="not found"):
            update_contact(db_conn, 9999, {"name": "Ghost"})


class TestDeleteContact:
    """Tests for delete_contact."""

    def test_deletes_existing_contact(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_application,
            create_contact,
            delete_contact,
            load_contacts,
        )

        app = create_application(db_conn, {"company": "C", "position": "P"})
        contact = create_contact(db_conn, app["id"], {"name": "Alice"})
        delete_contact(db_conn, contact["id"])

        results = load_contacts(db_conn, app["id"])
        assert all(r["id"] != contact["id"] for r in results)

    def test_returns_contact_name(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, create_contact, delete_contact

        app = create_application(db_conn, {"company": "C", "position": "P"})
        contact = create_contact(db_conn, app["id"], {"name": "Alice"})
        name = delete_contact(db_conn, contact["id"])

        assert name == "Alice"

    def test_raises_for_nonexistent_contact(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import delete_contact

        with pytest.raises(ValueError, match="not found"):
            delete_contact(db_conn, 9999)


class TestCreateCommunication:
    """Tests for create_communication."""

    def test_creates_with_contact_id_auto_populates_name(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.database import (
            create_application,
            create_communication,
            create_contact,
        )

        app = create_application(db_conn, {"company": "C", "position": "P"})
        contact = create_contact(db_conn, app["id"], {"name": "Alice"})
        result = create_communication(
            db_conn,
            app["id"],
            {
                "type": "email",
                "direction": "sent",
                "body": "Hello Alice",
                "date": "2024-01-15",
                "contact_id": contact["id"],
            },
        )

        assert result["contact_name"] == "Alice"
        assert result["contact_id"] == contact["id"]

    def test_creates_without_contact_id(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import create_application, create_communication

        app = create_application(db_conn, {"company": "C", "position": "P"})
        result = create_communication(
            db_conn,
            app["id"],
            {
                "type": "phone",
                "direction": "received",
                "body": "They called",
                "date": "2024-01-10",
            },
        )

        assert result["contact_id"] is None
        assert result["app_id"] == app["id"]
        assert result["type"] == "phone"


class TestLoadCommunications:
    """Tests for load_communications."""

    def test_loads_communications_for_app(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_application,
            create_communication,
            load_communications,
        )

        app = create_application(db_conn, {"company": "C", "position": "P"})
        create_communication(
            db_conn,
            app["id"],
            {"type": "email", "direction": "sent", "body": "A", "date": "2024-01-01"},
        )
        create_communication(
            db_conn,
            app["id"],
            {
                "type": "phone",
                "direction": "received",
                "body": "B",
                "date": "2024-02-01",
            },
        )
        results = load_communications(db_conn, app["id"])

        assert len(results) == 2

    def test_sorted_by_date_desc(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_application,
            create_communication,
            load_communications,
        )

        app = create_application(db_conn, {"company": "C", "position": "P"})
        create_communication(
            db_conn,
            app["id"],
            {"type": "email", "direction": "sent", "body": "Old", "date": "2024-01-01"},
        )
        create_communication(
            db_conn,
            app["id"],
            {"type": "email", "direction": "sent", "body": "New", "date": "2024-06-01"},
        )
        results = load_communications(db_conn, app["id"])

        assert results[0]["date"] == "2024-06-01"
        assert results[1]["date"] == "2024-01-01"


class TestUpdateCommunication:
    """Tests for update_communication."""

    def test_updates_fields(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_application,
            create_communication,
            update_communication,
        )

        app = create_application(db_conn, {"company": "C", "position": "P"})
        comm = create_communication(
            db_conn,
            app["id"],
            {
                "type": "email",
                "direction": "sent",
                "body": "Draft",
                "date": "2024-01-01",
            },
        )
        updated = update_communication(
            db_conn, comm["id"], {"subject": "Re: Interview", "status": "draft"}
        )

        assert updated["subject"] == "Re: Interview"
        assert updated["status"] == "draft"

    def test_updating_contact_id_updates_contact_name(
        self, db_conn: sqlite3.Connection
    ) -> None:
        from persona.database import (
            create_application,
            create_communication,
            create_contact,
            update_communication,
        )

        app = create_application(db_conn, {"company": "C", "position": "P"})
        contact = create_contact(db_conn, app["id"], {"name": "Bob"})
        comm = create_communication(
            db_conn,
            app["id"],
            {"type": "email", "direction": "sent", "body": "Hi", "date": "2024-01-01"},
        )
        updated = update_communication(
            db_conn, comm["id"], {"contact_id": contact["id"]}
        )

        assert updated["contact_id"] == contact["id"]
        assert updated["contact_name"] == "Bob"

    def test_raises_for_nonexistent_comm(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import update_communication

        with pytest.raises(ValueError, match="not found"):
            update_communication(db_conn, 9999, {"subject": "Ghost"})


class TestDeleteCommunication:
    """Tests for delete_communication."""

    def test_deletes_existing_communication(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_application,
            create_communication,
            delete_communication,
            load_communications,
        )

        app = create_application(db_conn, {"company": "C", "position": "P"})
        comm = create_communication(
            db_conn,
            app["id"],
            {
                "type": "email",
                "direction": "sent",
                "body": "Hello",
                "date": "2024-01-01",
                "subject": "Greetings",
            },
        )
        delete_communication(db_conn, comm["id"])

        results = load_communications(db_conn, app["id"])
        assert all(r["id"] != comm["id"] for r in results)

    def test_returns_subject(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import (
            create_application,
            create_communication,
            delete_communication,
        )

        app = create_application(db_conn, {"company": "C", "position": "P"})
        comm = create_communication(
            db_conn,
            app["id"],
            {
                "type": "email",
                "direction": "sent",
                "body": "Hello",
                "date": "2024-01-01",
                "subject": "My Subject",
            },
        )
        subject = delete_communication(db_conn, comm["id"])

        assert subject == "My Subject"

    def test_raises_for_nonexistent_comm(self, db_conn: sqlite3.Connection) -> None:
        from persona.database import delete_communication

        with pytest.raises(ValueError, match="not found"):
            delete_communication(db_conn, 9999)
