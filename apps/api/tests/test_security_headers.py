from starlette.responses import Response

from app.security.headers import API_CONTENT_SECURITY_POLICY, apply_api_security_headers


def test_api_security_headers_fail_closed() -> None:
    response = Response()

    apply_api_security_headers(response, production=False)

    assert response.headers["Content-Security-Policy"] == API_CONTENT_SECURITY_POLICY
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"
    assert "Strict-Transport-Security" not in response.headers


def test_api_hsts_is_production_only_and_preserves_explicit_cache_policy() -> None:
    response = Response(headers={"Cache-Control": "public, max-age=300"})

    apply_api_security_headers(response, production=True)

    assert response.headers["Strict-Transport-Security"] == ("max-age=31536000; includeSubDomains")
    assert response.headers["Cache-Control"] == "public, max-age=300"
