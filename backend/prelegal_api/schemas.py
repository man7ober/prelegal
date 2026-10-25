from dataclasses import dataclass


# KAN-9 intentionally limits the current chat and render API to Mutual NDA.
# Other schemas and source templates remain available for future issues.
SUPPORTED_CHAT_DOCUMENT_IDS = frozenset({"mutual-nda"})


@dataclass(frozen=True)
class DocumentConfig:
    document_id: str
    filenames: tuple[str, ...]
    required_fields: tuple[str, ...]
    missing_companions: tuple[str, ...] = ()


# Required fields are the minimum facts needed for a useful draft. Other linked
# variables remain visible and are reported for review instead of being guessed.
DOCUMENTS = (
    DocumentConfig(
        "mutual-nda",
        ("Mutual-NDA-coverpage.md", "Mutual-NDA.md"),
        ("party_1", "party_2", "purpose", "effective_date", "governing_law", "jurisdiction"),
    ),
    DocumentConfig(
        "cloud-service-agreement",
        ("CSA.md",),
        ("customer", "provider", "effective_date", "governing_law"),
        ("Order Form",),
    ),
    DocumentConfig(
        "service-level-agreement",
        ("sla.md",),
        ("customer", "provider", "target_uptime", "target_response_time"),
        ("Order Form", "Cloud Service Agreement"),
    ),
    DocumentConfig(
        "data-processing-agreement",
        ("DPA.md",),
        ("customer", "provider", "categories_of_personal_data", "categories_of_data_subjects"),
        ("Cover Page",),
    ),
    DocumentConfig(
        "design-partner-agreement",
        ("design-partner-agreement.md",),
        ("partner", "provider", "program", "term", "effective_date"),
        ("Key Terms",),
    ),
    DocumentConfig(
        "professional-services-agreement",
        ("psa.md",),
        ("customer", "provider", "fees", "deliverables", "effective_date"),
        ("Key Terms", "Statement of Work"),
    ),
    DocumentConfig(
        "partnership-agreement",
        ("Partnership-Agreement.md",),
        ("company", "partner", "territory", "obligations", "effective_date"),
        ("Business Terms",),
    ),
    DocumentConfig(
        "business-associate-agreement",
        ("BAA.md",),
        ("company", "provider", "baa_effective_date", "breach_notification_period"),
        ("Cover Page",),
    ),
    DocumentConfig(
        "software-license-agreement",
        ("Software-License-Agreement.md",),
        ("customer", "provider", "permitted_uses", "subscription_period", "effective_date"),
        ("Order Form",),
    ),
    DocumentConfig(
        "pilot-agreement",
        ("Pilot-Agreement.md",),
        ("customer", "provider", "pilot_period", "effective_date"),
        ("Order Form",),
    ),
    DocumentConfig(
        "ai-addendum",
        ("AI-Addendum.md",),
        ("customer", "provider", "training_purposes", "training_restrictions"),
        ("Cover Page", "Underlying Agreement"),
    ),
)


FIELD_LABELS = {
    "party_1": "First party legal name",
    "party_2": "Second party legal name",
    "customer": "Customer legal name",
    "provider": "Provider legal name",
    "company": "Company legal name",
    "partner": "Partner legal name",
    "purpose": "Purpose",
    "effective_date": "Effective date",
    "governing_law": "Governing law",
    "jurisdiction": "Court jurisdiction",
    "target_uptime": "Target uptime",
    "target_response_time": "Target response time",
    "categories_of_personal_data": "Categories of personal data",
    "categories_of_data_subjects": "Categories of data subjects",
    "program": "Design partner program",
    "term": "Agreement term",
    "fees": "Fees and payment terms",
    "deliverables": "Services and deliverables",
    "territory": "Partnership territory",
    "obligations": "Partner obligations",
    "baa_effective_date": "BAA effective date",
    "breach_notification_period": "Breach notification period",
    "permitted_uses": "Permitted software uses",
    "subscription_period": "Subscription period",
    "evaluation_purposes": "Evaluation purposes",
    "pilot_period": "Pilot period",
    "training_purposes": "Training purposes",
    "training_restrictions": "Training restrictions",
}
