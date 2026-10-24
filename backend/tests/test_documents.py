from pathlib import Path

from prelegal_api.documents import DocumentLibrary


def library() -> DocumentLibrary:
    return DocumentLibrary(Path(__file__).resolve().parents[2])


def test_catalog_groups_mutual_nda_files_and_exposes_all_types() -> None:
    documents = library().list_documents()

    assert len(documents) == 11
    nda = next(document for document in documents if document["id"] == "mutual-nda")
    assert nda["files"] == ["Mutual-NDA-coverpage.md", "Mutual-NDA.md"]
    assert "First party legal name" in {field["label"] for field in nda["fields"]}
    assert "Second party legal name" in {field["label"] for field in nda["fields"]}


def test_renderer_substitutes_values_and_keeps_legal_terms() -> None:
    rendered = library().render(
        "cloud-service-agreement",
        {"customer": "Acme & Co", "provider": "Prelegal Services", "effective_date": "2026-10-24", "governing_law": "California"},
    )

    assert "Acme &amp; Co" in rendered["html"]
    assert "Provider" in rendered["text"]
    assert "will provide" in rendered["text"]
    assert "Order Form" in rendered["missing_companions"]
    assert rendered["missing_required"] == []


def test_renderer_escapes_user_values_before_inserting_html() -> None:
    rendered = library().render(
        "pilot-agreement",
        {"customer": "<script>alert(1)</script>"},
    )

    assert "<script>" not in rendered["html"]
    assert "&lt;script&gt;" in rendered["html"]


def test_every_schema_required_field_exists_in_template_registry() -> None:
    document_library = library()
    for document in document_library.list_documents():
        fields = {field["id"] for field in document["fields"]}
        assert fields
        required = set(document_library.by_id[document["id"]]["config"].required_fields)
        assert required <= fields
