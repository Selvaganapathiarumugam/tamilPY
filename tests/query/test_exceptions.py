"""Tests for tpy.query exception hierarchy."""

from tpy.exceptions import TpyError
from tpy.query.exceptions import (
    GrammarError,
    InvalidColumnError,
    InvalidOperatorError,
    PaginationError,
    QueryError,
)


def test_query_error_is_tpy_error() -> None:
    err = QueryError("boom")
    assert isinstance(err, TpyError)
    assert str(err) == "boom"


def test_invalid_column_is_query_error() -> None:
    err = InvalidColumnError("nope")
    assert isinstance(err, QueryError)
    assert isinstance(err, TpyError)
    assert "nope" in str(err)


def test_sibling_errors_share_query_error_base() -> None:
    for cls in (InvalidOperatorError, GrammarError, PaginationError):
        err = cls("x")
        assert isinstance(err, QueryError)
