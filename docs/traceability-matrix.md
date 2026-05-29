# Traceability Matrix — URL Shortener Service

**Spec:** SPEC-SHORT-001 v1.0.0  
**Generated from:** specs/url-shortener.yaml  
**Test run date:** 2026-05-29  
**Test command:** `.venv/Scripts/python -m pytest tests/ -v`  
**Result:** 46 passed / 0 failed (100% first-run pass rate after self-critique cycle)

---

## Requirement → Code → Test Mapping

| REQ-ID | Requirement Summary | Source File(s) | Test File(s) | Test Functions | Status |
|--------|--------------------|--------------------|--------------|----------------|--------|
| REQ-SHORT-001 | Shorten valid URL → unique 6-char code | `src/utils.py` `generate_short_code()` | `tests/test_url_shortening.py` `tests/test_validation.py` | `test_shorten_valid_url_returns_201` `test_shorten_url_response_contains_all_required_fields` `test_two_different_urls_get_different_codes` `test_code_is_correct_length` `test_code_uses_only_allowed_characters` `test_codes_are_unique_across_calls` | ✅ PASS |
| REQ-SHORT-002 | Redirect `GET /{code}` → 302 to original URL | `src/routers/urls.py` `redirect_to_url()` | `tests/test_redirect.py` | `test_valid_short_code_returns_302_redirect` `test_nonexistent_code_returns_404` | ✅ PASS |
| REQ-SHORT-003 | Track click_count, last_accessed, referrer | `src/crud.py` `record_redirect()` | `tests/test_analytics.py` | `test_initial_click_count_is_zero` `test_click_count_increments_on_each_redirect` `test_last_accessed_updates_after_redirect` `test_referrer_stored_from_referer_header` `test_analytics_not_incremented_for_expired_url` `test_get_url_info_returns_all_analytics_fields` | ✅ PASS |
| REQ-SHORT-004 | Optional expiry — 410 Gone if past expires_at | `src/routers/urls.py` `redirect_to_url()` | `tests/test_expiry.py` `tests/test_redirect.py` | `test_url_without_expiry_never_expires` `test_past_expiry_returns_410_immediately` `test_future_expiry_allows_redirect` `test_info_endpoint_shows_expires_at` `test_expired_url_returns_410` | ✅ PASS |
| REQ-SHORT-005 | Validate URL — reject invalid, blocked, private-IP | `src/utils.py` `validate_url()` | `tests/test_validation.py` `tests/test_url_shortening.py` | `test_reject_invalid_url_format_returns_422` `test_reject_ftp_scheme_returns_422` `test_reject_file_scheme_returns_422` `test_reject_blocked_domain_returns_400` `test_reject_private_ip_returns_422` `test_ftp_scheme_raises_validation_error` `test_plain_text_raises_validation_error` `test_private_ip_192_168_raises_validation_error` `test_private_ip_10_x_raises_validation_error` `test_localhost_raises_validation_error` `test_blocked_domain_raises_validation_error` `test_subdomain_of_blocked_domain_also_blocked` `test_url_exceeding_max_length_raises_error` | ✅ PASS |
| REQ-SHORT-006 | RESTful API — structured errors, /docs, /api/health | `src/main.py` `src/routers/urls.py` | `tests/test_api.py` | `test_health_endpoint_returns_200` `test_delete_existing_url_returns_204` `test_delete_nonexistent_url_returns_404` `test_deleted_url_no_longer_redirects` `test_get_info_for_nonexistent_code_returns_404` `test_openapi_docs_endpoint_is_available` | ✅ PASS |

---

## Gherkin Scenario → Test Coverage

| Scenario ID | Title | Test Function | Status |
|-------------|-------|--------------|--------|
| SCN-001 | Successfully shorten a valid URL | `test_shorten_valid_url_returns_201` | ✅ PASS |
| SCN-002 | Redirect a valid short URL to original | `test_valid_short_code_returns_302_redirect` | ✅ PASS |
| SCN-003 | Analytics increment on each redirect | `test_click_count_increments_on_each_redirect` `test_last_accessed_updates_after_redirect` | ✅ PASS |
| SCN-004 | Expired URL returns 410 Gone | `test_expired_url_returns_410` `test_past_expiry_returns_410_immediately` | ✅ PASS |
| SCN-005 | Reject invalid URL format | `test_reject_invalid_url_format_returns_422` `test_plain_text_raises_validation_error` | ✅ PASS |
| SCN-006 | Reject non-HTTP scheme (ftp://) | `test_reject_ftp_scheme_returns_422` `test_ftp_scheme_raises_validation_error` `test_reject_file_scheme_returns_422` | ✅ PASS |
| SCN-007 | Reject URL on malicious domain blocklist | `test_reject_blocked_domain_returns_400` `test_blocked_domain_raises_validation_error` | ✅ PASS |
| SCN-008 | Idempotent submission returns existing code | `test_idempotent_submission_returns_200_with_same_code` | ✅ PASS |
| SCN-009 | 404 for nonexistent short code | `test_nonexistent_code_returns_404` `test_get_info_for_nonexistent_code_returns_404` | ✅ PASS |
| SCN-010 | Reject URL with private IP (SSRF prevention) | `test_reject_private_ip_returns_422` `test_private_ip_192_168_raises_validation_error` `test_private_ip_10_x_raises_validation_error` `test_localhost_raises_validation_error` | ✅ PASS |

---

## Coverage Summary

| Metric | Count |
|--------|-------|
| Requirements defined | 6 |
| Requirements with ≥1 test | 6 |
| Requirements fully covered | 6 |
| Gherkin scenarios defined | 10 |
| Scenarios with ≥1 test | 10 |
| Total test functions | 46 |
| Tests passing | 46 |
| Tests failing | 0 |
| **Coverage** | **100%** |

### Requirements Without Tests
None — all 6 requirements have at least one test.

### Tests Without Requirements
None — every test references a REQ-ID in its docstring.

### Traceability Gaps
No gaps identified. The spec-driven workflow forced alignment between requirements, code, and tests before any code was written, which eliminated the typical gap where tests are added after the fact and don't map back to formal requirements.
