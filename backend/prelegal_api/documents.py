import html
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import markdown

from .schemas import DOCUMENTS, FIELD_LABELS, DocumentConfig

VARIABLE_CLASSES = {
    "coverpage_link",
    "keyterms_link",
    "orderform_link",
    "sow_link",
    "businessterms_link",
}
SPAN_PATTERN = re.compile(r"<span\b([^>]*)>(.*?)</span>", re.DOTALL | re.IGNORECASE)
CLASS_PATTERN = re.compile(r'\bclass=["\']([^"\']+)["\']', re.IGNORECASE)
TAG_PATTERN = re.compile(r"<[^>]+>")
FIELD_ALIASES = {
    "customer_s": "customer",
    "provider_s": "provider",
    "company_s": "company",
    "partner_s": "partner",
    "party_1_s": "party_1",
    "party_2_s": "party_2",
    "customer_covered_claim": "customer_covered_claims",
    "provider_covered_claim": "provider_covered_claims",
}


def field_id(label: str) -> str:
    label = label.replace("�", "'").replace("’", "'")
    label = re.sub(r"'s\b", "", label, flags=re.IGNORECASE)
    normalized = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return FIELD_ALIASES.get(normalized, normalized)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"p", "div", "h1", "h2", "h3", "h4", "li", "tr", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "h1", "h2", "h3", "h4", "li", "tr", "table"}:
            self.parts.append("\n")


class DocumentLibrary:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.catalog = self._load_catalog()
        self.by_id = {item["id"]: item for item in self.catalog}

    def _load_catalog(self) -> list[dict[str, Any]]:
        import json

        entries = json.loads((self.project_root / "catalog.json").read_text(encoding="utf-8"))
        result = []
        by_filename = {entry["filename"]: entry for entry in entries}
        for config in DOCUMENTS:
            source_entries = [by_filename[name] for name in config.filenames]
            result.append(
                {
                    "id": config.document_id,
                    "title": "Mutual Non-Disclosure Agreement"
                    if config.document_id == "mutual-nda"
                    else source_entries[0]["name"],
                    "description": " ".join(dict.fromkeys(entry["description"] for entry in source_entries)),
                    "files": list(config.filenames),
                    "missing_companions": list(config.missing_companions),
                    "config": config,
                }
            )
        return result

    def list_documents(self) -> list[dict[str, Any]]:
        documents = []
        for item in self.catalog:
            variables = self._variables(item["config"])
            documents.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "description": item["description"],
                    "files": item["files"],
                    "fields": variables,
                    "missing_companions": item["missing_companions"],
                }
            )
        return documents

    def _source(self, config: DocumentConfig) -> str:
        return "\n\n".join(
            (self.project_root / "templates" / filename).read_text(encoding="utf-8")
            for filename in config.filenames
        )

    def _variables(self, config: DocumentConfig) -> list[dict[str, Any]]:
        variables: dict[str, dict[str, Any]] = {}
        source = self._source(config)
        for match in SPAN_PATTERN.finditer(source):
            classes = CLASS_PATTERN.search(match.group(1))
            if not classes:
                continue
            class_names = set(classes.group(1).split())
            variable_class = next((name for name in class_names if name in VARIABLE_CLASSES), None)
            if not variable_class:
                continue
            label = html.unescape(TAG_PATTERN.sub("", match.group(2))).strip()
            key = field_id(label)
            if not key or key in {"agreement", "dpa"}:
                continue
            variables.setdefault(
                key,
                {
                    "id": key,
                    "label": FIELD_LABELS.get(key, label),
                    "required": key in config.required_fields,
                    "source_label": label,
                },
            )

        if config.document_id == "mutual-nda":
            for key in ("party_1", "party_2", "purpose", "effective_date", "governing_law", "jurisdiction", "mnda_term", "term_of_confidentiality"):
                variables.setdefault(
                    key,
                    {
                        "id": key,
                        "label": FIELD_LABELS.get(key, key.replace("_", " ").title()),
                        "required": key in config.required_fields,
                        "source_label": key,
                    },
                )
        return list(variables.values())

    def chat_context(self, document_id: str | None) -> dict[str, Any]:
        document = self.by_id.get(document_id) if document_id else None
        return {
            "catalog": [
                {"id": item["id"], "title": item["title"], "description": item["description"]}
                for item in self.catalog
            ],
            "selected_document": (
                {
                    "id": document["id"],
                    "title": document["title"],
                    "fields": self._variables(document["config"]),
                    "required_fields": list(document["config"].required_fields),
                    "missing_companions": document["missing_companions"],
                }
                if document
                else None
            ),
        }

    def render(self, document_id: str, values: dict[str, str]) -> dict[str, Any]:
        document = self.by_id.get(document_id)
        if not document:
            raise KeyError(document_id)

        config: DocumentConfig = document["config"]
        fields = self._variables(config)
        allowed = {field["id"] for field in fields}
        safe_values = {key: value.strip() for key, value in values.items() if key in allowed and value.strip()}
        source = self._source(config)

        def replace_span(match: re.Match[str]) -> str:
            attributes, content = match.group(1), match.group(2)
            classes = CLASS_PATTERN.search(attributes)
            if not classes or not (set(classes.group(1).split()) & VARIABLE_CLASSES):
                return match.group(0)
            label = html.unescape(TAG_PATTERN.sub("", content)).strip()
            value = safe_values.get(field_id(label))
            return html.escape(value, quote=False) if value else match.group(0)

        source = SPAN_PATTERN.sub(replace_span, source)
        if document_id == "mutual-nda":
            source = self._render_nda_cover(source, safe_values)

        unresolved = [field for field in fields if field["required"] and field["id"] not in safe_values]
        rendered_html = markdown.markdown(source, extensions=["tables", "sane_lists"])
        rendered_html = re.sub(
            r"<h([1-5])([^>]*)>(.*?)</h\1>",
            lambda match: (
                f"<h{int(match.group(1)) + 1}{match.group(2)}>{match.group(3)}"
                f"</h{int(match.group(1)) + 1}>"
            ),
            rendered_html,
            flags=re.DOTALL,
        )
        rendered_html = re.sub(
            r"<th([^>]*)>\s*</th>",
            lambda match: f'<th{match.group(1)} aria-label="Agreement field"></th>',
            rendered_html,
        )
        text_extractor = _TextExtractor()
        text_extractor.feed(rendered_html)
        return {
            "document_id": document_id,
            "title": document["title"],
            "html": rendered_html,
            "text": "\n".join(part for part in text_extractor.parts if part.strip()),
            "missing_required": [field["label"] for field in unresolved],
            "missing_variables": [
                field["label"] for field in fields if field["id"] not in safe_values
            ],
            "missing_companions": document["missing_companions"],
        }

    @staticmethod
    def _render_nda_cover(source: str, values: dict[str, str]) -> str:
        replacements = {
            "[Evaluating whether to enter into a business relationship with the other party.]": values.get("purpose"),
            "[Today’s date]": values.get("effective_date"),
            "Expires [1 year(s)]": f"Expires {values.get('mnda_term')}" if values.get("mnda_term") else None,
            "[1 year(s)] from Effective Date, but in the case of trade secrets": (
                f"{values.get('term_of_confidentiality')} from Effective Date, but in the case of trade secrets"
                if values.get("term_of_confidentiality")
                else None
            ),
            "[Fill in state]": values.get("governing_law"),
            "[Fill in city or county and state, i.e. “courts located in New Castle, DE”]": values.get("jurisdiction"),
        }
        for source_text, value in replacements.items():
            if value:
                source = source.replace(source_text, html.escape(value, quote=False))
        if values.get("party_1") or values.get("party_2"):
            party_1 = html.escape(values.get("party_1", ""), quote=False)
            party_2 = html.escape(values.get("party_2", ""), quote=False)
            source = source.replace("| Company | | |", f"| Company | {party_1} | {party_2} |", 1)
        return source
