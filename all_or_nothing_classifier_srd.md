# Cognitive Distortion Detector — Software Requirements Document (SRD)
Version: 2.0  
Owner: Jose

## 1. Purpose
Define the software requirements for a small service that performs **binary detection**:

- Given a single statement, return whether it **has** a cognitive distortion.

The service must do **only this**.

## 2. Scope
### In scope
- Accept a single `text` input (string).
- Return a single boolean output: `has_cognitive_distortion`.
- Provide a `/health` endpoint for basic operational checks.

### Out of scope
- Distortion type classification
- Scoring (severity/objectivity/subjectivity)
- Verb analysis
- Rewrite suggestions
- Storing text, user accounts, analytics, billing

## 3. Definitions
- **Statement**: One sentence or short paragraph provided as a single string.
- **Cognitive distortion**: A pattern in language that indicates distorted thinking. In v2.0, detection is implemented via deterministic heuristics.

## 4. System overview
- Stateless FastAPI service
- Deterministic classifier module
- No persistence layer

## 5. Functional requirements

### 5.1 Health check
- **Endpoint**: `GET /health`
- **Response**:

```json
{"status":"ok"}
```

### 5.2 Detect cognitive distortion
- **Endpoint**: `POST /classify`
- **Request body**:

```json
{"text":"string"}
```

- **Validation**:
  - `text` must be present and non-empty after trimming.

- **Response body**:

```json
{"has_cognitive_distortion":true}
```

## 6. Non-functional requirements
- **Deterministic**: same input always yields the same output.
- **Latency**: typical response time under 100ms locally.
- **Safety**: must not persist or log user-provided text.
- **Reliability**: return HTTP 400 for empty input.

## 7. Error handling
- Empty/whitespace-only input returns HTTP 400 with a clear message.

## 8. Testing requirements
- Unit tests must cover:
  - obvious distortion statement → `has_cognitive_distortion == true`
  - neutral/grounded statement → `has_cognitive_distortion == false`
  - empty input rejection (API-level)
