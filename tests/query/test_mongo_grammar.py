"""Mongo grammar compile smoke tests."""

from tpy.query.builder import QueryBuilder
from tpy.query.mongo_grammar import MongoGrammar


class _Dummy:
    PLACEHOLDER = "?"


def test_mongo_filter_eq_and_in():
    grammar = MongoGrammar()
    builder = (
        QueryBuilder(_Dummy(), "users", grammar=None)
        .where("status", "active")
        .where_in("role", [1, 2])
    )
    # Force mongo compile without SQL grammar execution
    filt = grammar.to_filter(builder)
    assert filt == {
        "$and": [
            {"status": "active"},
            {"role": {"$in": [1, 2]}},
        ]
    }
