# Entity-Relationship Diagram — URL Shortener Data Model

> REQ references: REQ-SHORT-001, REQ-SHORT-002, REQ-SHORT-003, REQ-SHORT-004

```mermaid
erDiagram
    SHORTENED_URLS {
        INTEGER id PK "Auto-increment primary key"
        VARCHAR short_code UK "6-char [a-zA-Z0-9], indexed"
        TEXT original_url "The destination URL (max 2048 chars)"
        VARCHAR url_hash UK "SHA-256 of original_url — fast duplicate detection"
        INTEGER click_count "Total redirect count, default 0 (REQ-SHORT-003)"
        DATETIME last_accessed "UTC timestamp of last redirect, nullable (REQ-SHORT-003)"
        TEXT referrer "HTTP Referer header from last redirect, nullable (REQ-SHORT-003)"
        DATETIME expires_at "Optional expiry in UTC (REQ-SHORT-004), nullable"
        DATETIME created_at "Record creation time, UTC, NOT NULL"
        BOOLEAN is_active "Soft-delete flag, default TRUE"
    }

    BLOCKLIST {
        INTEGER id PK
        VARCHAR domain UK "Blocked domain (e.g. malware.example.com) — REQ-SHORT-005"
        TEXT reason "Human-readable block reason"
        DATETIME added_at "When the domain was blocklisted"
        BOOLEAN is_active "Allows temporary disabling without deletion"
    }

    AUDIT_LOG {
        INTEGER id PK
        VARCHAR event_type "CREATE | REDIRECT | DELETE | BLOCKED | EXPIRED | RATE_LIMITED"
        VARCHAR short_code FK "References SHORTENED_URLS.short_code, nullable"
        TEXT url_preview "First 100 chars of submitted URL"
        VARCHAR client_ip "Client IP address"
        INTEGER response_code "HTTP status code returned"
        DATETIME occurred_at "UTC event timestamp"
    }

    SHORTENED_URLS ||--o{ AUDIT_LOG : "generates"
    BLOCKLIST ||--o{ AUDIT_LOG : "triggers"
```

## Field Design Notes

| Field | Design Decision |
|-------|----------------|
| `url_hash` | SHA-256 of normalized URL enables O(1) duplicate detection without full-text scan. Satisfies REQ-SHORT-005 idempotency. |
| `short_code` | 6-char base-62 = 62^6 ≈ 56 billion possible codes. Collision-resistant at any realistic scale. |
| `expires_at` | Evaluated at redirect time, not stored as a flag. This means expiry is always accurate to the clock without a background job. |
| `is_active` | Soft delete preserves audit trail while preventing redirects. |
| `referrer` | Stores only the last referrer for simplicity. Full referrer history would require a separate click_events table. |
