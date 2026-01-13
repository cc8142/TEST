def assert_status(response, expected_status):
    actual = response.status_code
    if actual != expected_status:
        body = response.text.strip()
        snippet = body[:200] if body else "<empty>"
        raise AssertionError(
            f"Expected status {expected_status}, got {actual}. Body: {snippet}"
        )


def assert_schema(payload, schema, path="payload"):
    if isinstance(schema, dict):
        if not isinstance(payload, dict):
            raise AssertionError(f"{path} expected dict, got {type(payload).__name__}")
        for key, expected in schema.items():
            if key not in payload:
                raise AssertionError(f"{path} missing key: {key}")
            assert_schema(payload[key], expected, f"{path}.{key}")
        return

    if isinstance(schema, list):
        if not isinstance(payload, list):
            raise AssertionError(f"{path} expected list, got {type(payload).__name__}")
        if schema:
            item_schema = schema[0]
            for index, item in enumerate(payload):
                assert_schema(item, item_schema, f"{path}[{index}]")
        return

    if isinstance(schema, tuple):
        if not isinstance(payload, schema):
            expected = ", ".join(t.__name__ for t in schema)
            raise AssertionError(
                f"{path} expected one of ({expected}), got {type(payload).__name__}"
            )
        return

    if isinstance(schema, type):
        if not isinstance(payload, schema):
            raise AssertionError(
                f"{path} expected {schema.__name__}, got {type(payload).__name__}"
            )
        return

    raise TypeError(f"Unsupported schema type at {path}: {type(schema).__name__}")
