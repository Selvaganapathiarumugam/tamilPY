"""Tests for the advanced validation engine."""

from __future__ import annotations

import pytest

from tpy.http import ApiResponse
from tpy.runtime.validation import ValidationError as LegacyValidationError
from tpy.runtime.validation import Validator as LegacyValidator
from tpy.validation import ValidationException, Validator, validate


def test_required_and_email():
    with pytest.raises(ValidationException) as exc:
        validate(
            {"email": ""},
            {"email": "required|email", "name": "required"},
        )
    assert "email" in exc.value.errors
    assert "name" in exc.value.errors


def test_passes_and_validated():
    data = validate(
        {
            "email": "a@b.com",
            "age": 21,
            "password": "secret",
            "password_confirmation": "secret",
            "role": "admin",
        },
        {
            "email": "required|email",
            "age": "required|integer|min:18",
            "password": "required|confirmed",
            "role": "in:admin,user",
        },
    )
    assert data["email"] == "a@b.com"
    assert data["role"] == "admin"


def test_nullable_skips_other_rules():
    data = validate({"nickname": None}, {"nickname": "nullable|email"})
    assert data["nickname"] is None


def test_between_in_uuid_url():
    ok = Validator.make(
        {
            "score": 5,
            "kind": "a",
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "site": "https://example.com",
        },
        {
            "score": "between:1,10",
            "kind": "in:a,b",
            "id": "uuid",
            "site": "url",
        },
    )
    assert ok.passes()


def test_custom_rule_extend():
    Validator.extend(
        "odd2",
        lambda attr, value, data: int(value) % 2 == 1,
        "Value must be odd.",
    )
    assert Validator.make({"n": 3}, {"n": "odd2"}).passes()
    assert Validator.make({"n": 2}, {"n": "odd2"}).fails()


def test_custom_messages():
    v = Validator.make(
        {"email": "nope"},
        {"email": "email"},
        messages={"email.email": "Bad email."},
    )
    assert v.fails()
    assert v.first_messages()["email"] == "Bad email."


def test_api_response_validation_error():
    try:
        validate({"x": ""}, {"x": "required"})
    except ValidationException as exc:
        response = ApiResponse.validation_error(exc)
        assert response.status_code == 422


def test_legacy_fluent_still_works():
    with pytest.raises(LegacyValidationError) as exc:
        LegacyValidator({"email": "x"}).required("name").email("email").validate()
    assert "name" in exc.value.errors
    assert isinstance(exc.value.errors["name"], str)
