from starlette.requests import Request

from main import _is_api_document_navigation


def _request(path: str, headers: dict[str, str] | None = None) -> Request:
    raw_headers = [
        (key.lower().encode('latin-1'), value.encode('latin-1'))
        for key, value in (headers or {}).items()
    ]
    return Request(
        {
            'type': 'http',
            'method': 'GET',
            'path': path,
            'headers': raw_headers,
            'query_string': b'',
            'server': ('testserver', 80),
            'scheme': 'http',
        }
    )


def test_api_document_navigation_is_redirected() -> None:
    request = _request('/api/library/files', {'sec-fetch-dest': 'document'})

    assert _is_api_document_navigation(request) is True


def test_list_document_navigation_is_redirected() -> None:
    request = _request('/list', {'accept': 'text/html'})

    assert _is_api_document_navigation(request) is True


def test_json_api_request_is_not_redirected() -> None:
    request = _request(
        '/api/library/files',
        {'accept': 'application/json, text/plain, */*'},
    )

    assert _is_api_document_navigation(request) is False


def test_app_route_is_not_redirected() -> None:
    request = _request('/monitor', {'sec-fetch-dest': 'document'})

    assert _is_api_document_navigation(request) is False
