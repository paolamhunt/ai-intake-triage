# ai-intake-triage

## V1 Design Specification and V2 Roadmap

**Brand:** The Distracted Developer  
**Status:** Design approved; implementation not started  
**Document purpose:** Source of truth for the initial public GitHub implementation

## 1. Problem statement

Professional-service businesses receive client inquiries as unstructured text through contact forms, freelance platforms, email, and other sources. These inquiries are often incomplete, ambiguous, or inconsistent, requiring a person to manually interpret the client's underlying need, identify relevant systems and requirements, determine whether the request aligns with available services, uncover missing information, and decide what should happen next.

This manual intake process is time-consuming and prone to inconsistent classification, overlooked requirements, and premature assumptions about project scope.

`ai-intake-triage` is a reusable, business-agnostic system that converts an unstructured service inquiry into validated, structured, and reviewable project information. It assists with service classification, complexity assessment, missing-information detection, and next-action recommendations while preserving human responsibility for final classification, lead acceptance, pricing, scope commitments, and consequential client communication.

The Distracted Developer provides the example and default business configuration, but its services and rules are not hard-coded into the core intake engine.

## 2. Primary user and actors

The primary V1 user is the service-business operator who reviews incoming inquiries.

- **Business operator/reviewer:** Submits or receives an inquiry, reviews its triage result, and makes final business decisions.
- **Prospective client:** Authors the inquiry but does not directly operate the V1 system.
- **Inquiry source:** Supplies inquiry content and source metadata. In V1 this is an authenticated API caller rather than a direct platform integration.
- **LLM provider:** Interprets unstructured language and returns a structured candidate analysis.
- **Configured business:** Supplies trusted services, intake requirements, supported technologies, complexity indicators, and routing rules.

## 3. V1 use cases

The primary use case is:

> A business operator submits one unstructured service inquiry. The system analyzes it against the active business configuration and returns a validated triage result for human review.

V1 supports:

- A clear inquiry that maps to one or more configured services.
- An incomplete or ambiguous inquiry requiring clarification.
- An inquiry that does not match a configured service.
- An inquiry containing contradictory information.
- Rejection of invalid or unsafe input before AI processing.
- Controlled handling of malformed or invalid AI output.
- Controlled handling of model failures and timeouts.
- Review of successful, incomplete, unmatched, declined, and failed records.
- Manual retry of a retryable processing failure.
- Recording a human correction and business disposition.
- Permanent deletion of an inquiry and all related records.

## 4. Input contract

A V1 submission contains:

```json
{
  "inquiry_text": "I run a bookkeeping business and want to automate...",
  "customer": {
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": null
  },
  "source": {
    "channel": "website",
    "external_reference": null
  }
}
```

Rules:

- `inquiry_text` is required, trimmed, non-empty, and length-limited.
- `source.channel` is required and remains an extensible string rather than a hard-coded platform enumeration.
- At least one reply path is required: customer email, customer phone, or a source external reference.
- Customer name is optional.
- Unknown input fields are rejected.
- Contact and source data are validated and persisted deterministically.
- Contact data is not sent to the LLM.
- V1 does not automatically contact the customer.

## 5. Output contract

Each successfully triaged record includes:

- Record ID, processing state, and timestamps.
- Original inquiry plus source and contact information.
- Inquiry summary and primary pain point.
- Stated requirements and explicitly mentioned systems.
- Clearly labeled inferred capabilities and inferred systems.
- Missing information with reasons, priority, and draft clarifying questions.
- Zero or more service candidates ordered from strongest to weakest match.
- An explainable preliminary complexity assessment.
- One constrained recommended next action.
- Human-review state and review reasons.
- Human corrections and disposition after review.

### 5.1 Evidence levels

The system must preserve the distinction among:

- **Stated:** Explicitly present in the inquiry.
- **Inferred:** A reasonable interpretation that requires confirmation.
- **Missing:** Required information that cannot be established from the inquiry.

An inference cannot silently become a confirmed requirement.

### 5.2 Clarifying questions

Each confirmed information gap may include a specific, customer-friendly draft question. Questions are prioritized as required or optional and remain subject to human editing and approval. They are never sent automatically in V1.

The business configuration supplies a safe default question when the AI does not produce a usable question for a confirmed gap.

### 5.3 Service candidates

- The result may contain zero or more candidate services.
- Candidate service IDs must exist in the trusted business configuration.
- Candidates use constrained match levels such as strong, possible, or weak.
- Each candidate includes a reason and supporting evidence.
- Candidates are ordered from strongest to weakest.
- V1 does not use unsupported numeric AI confidence percentages.
- The reviewer makes the final classification.

### 5.4 Complexity

Complexity is preliminary and uses `low`, `medium`, `high`, or `unknown`.

The result includes contributing factors and unresolved information that could change the level. The AI identifies potential factors; deterministic rules assign the level from validated factors and configured rules.

### 5.5 Recommended actions

V1 uses one constrained recommended action:

- `request_more_information`
- `proceed_to_discovery`
- `manual_assessment`
- `review_service_mismatch`
- `retry_processing`

The application selects the recommendation using validated analysis, business configuration, and deterministic routing rules. The recommendation never commits the business to an action.

## 6. Business configuration

V1 loads one trusted business configuration at application startup. Another business can reuse the engine by replacing the configuration without changing core application code.

The validated YAML configuration contains:

- Business name and description.
- Services with stable IDs, display names, and descriptions.
- Typical capabilities for each service.
- Required intake information and default clarification questions.
- Supported technologies where useful.
- Complexity indicators.
- Routing rules.
- A configuration version.

Configuration is declarative data, not executable Python or embedded arbitrary expressions. Application code determines how rules are executed. Unknown fields and invalid values cause startup failure.

## 7. Responsibility boundaries

### 7.1 Deterministic software

Deterministic code is responsible for:

- Authentication and API behavior.
- Request and schema validation.
- Required reply-path validation.
- Business-configuration loading and validation.
- Record IDs, timestamps, state transitions, and persistence.
- Structured AI-output validation.
- Service and action allowlists.
- Authoritative missing-information detection.
- Service-candidate ordering.
- Complexity assignment from validated factors and rules.
- Recommended-action selection.
- Failure classification and safe error responses.
- Preventing autonomous pricing, scope commitments, and communications.

### 7.2 Probabilistic AI

The AI is responsible for:

- Summarizing the underlying need and primary pain point.
- Extracting explicitly stated requirements and systems.
- Suggesting clearly labeled inferences.
- Suggesting configured service candidates with reasons and evidence.
- Detecting possible ambiguity and contradiction.
- Identifying potential complexity factors.
- Drafting customer-friendly questions associated with possible information gaps.

AI output is candidate data until validated and processed by deterministic code.

### 7.3 Human reviewer

The human is responsible for:

- Final service classification.
- Final complexity judgment.
- Editing and approving follow-up questions.
- Selecting the actual next action.
- Accepting, declining, or closing an inquiry.
- Pricing, scope, commitments, and customer communication.

## 8. Human review

Every successful triage enters `pending_review`.

One V1 human-review record contains:

- Status: pending or completed.
- Selected configured service ID, nullable when none fits.
- Confirmed or corrected complexity.
- Approved and edited clarifying questions.
- Disposition: `request_more_information`, `proceed_to_discovery`, `declined`, or `closed`.
- Optional internal notes.
- Review and update timestamps.

The original AI-assisted triage snapshot is immutable. Human decisions and corrections are stored separately. V1 supports one review per inquiry; trustworthy reviewer identity is deferred until user accounts exist.

## 9. State model

Technical processing state and human business disposition are separate concepts.

```text
received -> processing -> pending_review
                    \-> processing_failed

processing_failed -> processing  (manual retry)
```

Declined, incomplete, or unmatched are not technical failures. A successfully processed inquiry can have any appropriate human disposition.

## 10. Failure handling

Failure is a persisted, reviewable outcome whenever the application has accepted a legitimate inquiry.

Failure categories include:

- `input_rejected`
- `processing_failed`
- `output_validation_failed`
- `configuration_error`
- `persistence_failed`

A failure stores a safe message, category, timestamp, and retryable/non-retryable indicator. Public responses and routine logs do not expose secrets, stack traces, unnecessary raw model output, or provider internals.

V1 uses explicit human-triggered retries. Every attempt is preserved, a retry does not duplicate the inquiry, and automatic retry policies are deferred.

Requests rejected at the API boundary as empty, malformed, excessively large, or malicious may retain only safe audit metadata rather than harmful raw content.

## 11. API surface

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/inquiries` | Validate, persist, and synchronously process an inquiry |
| `GET` | `/api/v1/inquiries` | List records with pagination and basic filters |
| `GET` | `/api/v1/inquiries/{inquiry_id}` | Retrieve the complete record |
| `POST` | `/api/v1/inquiries/{inquiry_id}/retry` | Retry the latest retryable failure |
| `PUT` | `/api/v1/inquiries/{inquiry_id}/review` | Create or update the human review |
| `DELETE` | `/api/v1/inquiries/{inquiry_id}` | Permanently delete the inquiry and related records |
| `GET` | `/health` | Report application health |

Creation and retry are synchronous in V1. FastAPI supplies generated OpenAPI documentation.

## 12. Persistence design

V1 uses three primary relational entities:

- **Inquiry:** Original text, contact details, source, processing state, and timestamps.
- **ProcessingAttempt:** Attempt number, attempt state, provider/model metadata, configuration version, prompt version, failure details, and validated triage snapshot.
- **HumanReview:** Corrections, approved questions, disposition, notes, and timestamps.

One inquiry has one or more processing attempts and at most one human review. Permanent inquiry deletion cascades to every related record.

Operational fields used for filtering are normal relational columns. The immutable nested triage result is stored as a validated JSON snapshot because V1 does not need cross-record queries over each extracted list item. Pydantic validates the snapshot before storage and after retrieval.

## 13. End-to-end processing

1. Authenticate the caller.
2. Validate the request and input limits.
3. Persist the legitimate inquiry.
4. Create a processing attempt and move the inquiry to `processing`.
5. Send inquiry text and the minimum required business context to the configured LLM provider; exclude contact information.
6. Validate structured AI output.
7. Apply deterministic allowlists, missing-information rules, ordering, complexity rules, question filtering/fallbacks, and routing.
8. Persist the immutable validated triage snapshot.
9. Move the inquiry to `pending_review` and return the record.
10. On downstream failure, persist a controlled failure and return a safe message plus the inquiry ID.

The ordinary success path uses one model request.

## 14. Security baseline

V1 security requirements include:

- One operator API key for every inquiry, retry, review, retrieval, listing, and deletion endpoint.
- Constant-time credential comparison.
- Secrets supplied through environment variables and never committed.
- Startup failure when required secrets are absent outside explicitly configured test mode.
- Public `/health`; interactive documentation limited to development mode.
- Strict request models, input size limits, and unknown-field rejection.
- Contact information excluded from model requests.
- No routine logging of raw inquiries, contact data, credentials, or raw model responses.
- Inquiry content treated as untrusted data, not instructions.
- No LLM tools, URL fetching, code execution, or autonomous actions.
- Structured output plus deterministic validation and allowlists.
- Safe public errors without internal stack traces or provider details.
- CORS disabled unless explicitly configured.
- Database and environment files excluded from Git.
- Locked dependencies and automated vulnerability checks.
- Security tests covering unauthorized access, malformed and oversized input, invalid credentials, unsafe model output, and record deletion.

V1 is a local/private reference backend, not a public production deployment. Any later public deployment requires HTTPS, encrypted storage, managed secrets, network-level rate limiting, backups, monitoring, and an explicit privacy/retention policy.

## 15. Architecture and technology

V1 is a modular monolith: one deployable FastAPI application with focused internal modules.

- Python and FastAPI.
- Pydantic for domain, configuration, and API validation.
- Synchronous SQLAlchemy with SQLite.
- Separate Pydantic and persistence models.
- Alembic database migrations.
- Provider-neutral LLM interface.
- One OpenAI adapter and one deterministic fake provider.
- Validated YAML business configuration.
- pytest, Ruff, and GitHub Actions.
- `uv`, `pyproject.toml`, and a committed lockfile.

Dependency inversion is used where it provides real value: the application depends on interfaces for LLM access and persistence rather than concrete provider and database implementations.

## 16. Planned repository structure

```text
ai-intake-triage/
├── .github/workflows/
├── configs/
├── docs/
├── migrations/
├── src/ai_intake_triage/
│   ├── api/
│   ├── application/
│   ├── configuration/
│   ├── domain/
│   ├── infrastructure/
│   │   ├── database/
│   │   └── llm/
│   └── main.py
├── tests/
│   ├── integration/
│   └── unit/
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── alembic.ini
├── pyproject.toml
└── uv.lock
```

Directories and files are introduced only when a working implementation change requires them. The project will not begin with a tree of empty placeholders.

## 17. V1 non-goals

V1 does not include:

- A frontend, dashboard, or client-facing form.
- Direct email, website, Fiverr, or Upwork integrations.
- Automatic customer communications.
- Autonomous lead acceptance or rejection.
- Pricing, proposals, estimates, or scope commitments.
- Attachments, OCR, or document processing.
- Multiple active business configurations or multi-tenancy.
- User registration, passwords, roles, teams, or OAuth/OIDC.
- Background workers, message queues, or scheduled automatic retries.
- Cloud deployment or infrastructure as code.
- Production-scale observability.
- A vector database, RAG pipeline, agent framework, or model training.
- A full CRM or sales pipeline.
- Claims of AI quality based on a few hand-selected examples.

## 18. V2 roadmap

V2 work should be driven by evidence from using and evaluating V1. The following items are prioritized improvements, not commitments to build everything simultaneously.

### Priority 1: Evaluation and quality measurement

Build a versioned evaluation dataset of representative, ambiguous, incomplete, unmatched, and adversarial inquiries. Measure extraction accuracy, unsupported inference rate, service-match quality, missing-information recall, and agreement with human reviews.

Why: V1 establishes safe mechanics; V2 should establish whether the AI behavior is consistently useful.

### Priority 2: Stronger identity and authorization

Replace the shared operator API key with an external identity provider using standard OAuth/OIDC flows. Add individual users, reviewer attribution, scoped permissions, and per-record authorization tests.

Why: Required before supporting multiple operators or exposing sensitive records beyond a single trusted operator.

### Priority 3: Production data protection and lifecycle management

Add an explicit retention policy, scheduled expiry, encrypted managed storage, backup/restore procedures, audit events, secret rotation, and privacy documentation.

Why: Required before using the system as a durable production repository of real customer data.

### Priority 4: Asynchronous processing and bounded retry

Move model processing behind a durable job mechanism when real latency or volume justifies it. Add idempotency keys, narrowly defined automatic retries with backoff, dead-letter handling, and operational status endpoints.

Why: Synchronous processing is intentionally simpler in V1 but is less resilient under sustained traffic or provider latency.

### Priority 5: Operational observability

Add structured redacted logs, request and correlation IDs, latency and failure metrics, provider cost/token metrics, health/readiness separation, and alerts.

Why: Operators need visibility into reliability and cost before relying on the service in production.

### Priority 6: Direct intake integrations

Add one integration at a time based on actual demand, such as a website form or email intake. Normalize each source into the existing input contract and protect public submission paths with rate limiting and abuse controls.

Why: Integrations should remain adapters around the stable intake engine rather than reshaping the domain.

### Priority 7: Human-review workflow improvements

Add reviewer attribution, immutable review history, correction reasons, follow-up state, and possibly a lightweight operator interface.

Why: V1 preserves one review; real team workflows may require accountability and revision history.

### Priority 8: Multiple business configurations

Support multiple businesses only after adding identity, authorization, data isolation, configuration ownership, and tenant-aware storage.

Why: Selecting a business ID in a request is not sufficient multi-tenancy.

### Priority 9: Provider resilience

Add another real LLM adapter, model-specific capability checks, controlled provider fallback, and provider comparison within the evaluation system.

Why: The V1 abstraction should first prove useful before adding multiple integrations.

### Priority 10: Richer inputs

Consider attachments, OCR, conversation threads, or structured form fields only when concrete inquiry sources require them. Add malware scanning, file limits, format validation, and data-handling controls first.

Why: Rich inputs substantially expand privacy and security risk.

### Features that are not automatically part of V2

The following remain requirement-driven rather than default upgrades:

- Vector databases or retrieval-augmented generation.
- Autonomous agents or tool execution.
- Automated quoting or pricing.
- Automatic consequential customer communication.
- Microservices.
- Kubernetes or other orchestration platforms.
- A full CRM.

They should be added only if a validated use case makes them necessary.

## 19. Implementation rule

Implementation proceeds one verified logical change at a time:

1. Explain the current change and why it is needed.
2. Make one file or coherent change.
3. Provide an exact verification step.
4. Stop until the change is confirmed working.
5. Troubleshoot failures before adding more work.
6. Provide an exact commit message when the change forms a meaningful checkpoint.

This specification may evolve, but architectural changes must be explicit and documented rather than introduced accidentally during implementation.
