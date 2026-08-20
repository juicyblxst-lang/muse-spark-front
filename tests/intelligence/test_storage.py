from pathlib import Path

from app.storage import SQLiteStore

def test_documents_and_jobs_are_user_scoped(tmp_path: Path):
    store = SQLiteStore(tmp_path / "muse.sqlite3")
    store.create_document(document_id="doc-1", user_id="user-a", file_name="a.md", storage_path="user-a/doc-1/a.md")
    store.create_document(document_id="doc-2", user_id="user-b", file_name="b.md", storage_path="user-b/doc-2/b.md")

    assert [item["id"] for item in store.list_documents("user-a")] == ["doc-1"]
    assert store.get_document("doc-2", "user-a") is None

    store.create_job(job_id="job-1", user_id="user-a", document_id="doc-1")
    store.update_job("job-1", "user-a", {"status": "complete", "progress": 100})
    assert store.get_job("job-1", "user-a")["status"] == "complete"
    assert store.get_job("job-1", "user-b") is None
