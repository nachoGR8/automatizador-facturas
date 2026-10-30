import pytest

from benchmark.metrics import build_report
from factories import make_fields


def test_perfect_extraction_has_full_accuracy():
    expected = [make_fields(), make_fields(nif="A58818501")]

    report = build_report(expected, expected)

    assert report.invoices == 2
    assert all(accuracy == 1 for accuracy in report.field_accuracy.values())
    assert report.overall_accuracy == 1
    assert report.fully_correct == 2


def test_a_wrong_field_lowers_only_that_field():
    expected = [make_fields(), make_fields()]
    actual = [make_fields(), make_fields(supplier="FACTURA")]

    report = build_report(expected, actual)

    assert report.field_accuracy["supplier"] == 0.5
    assert report.field_accuracy["nif"] == 1
    assert report.fully_correct == 1
    assert report.overall_accuracy == pytest.approx(6.5 / 7)


def test_a_missing_field_counts_as_wrong():
    report = build_report([make_fields()], [make_fields(total=None)])

    assert report.field_accuracy["total"] == 0
    assert report.fully_correct == 0
