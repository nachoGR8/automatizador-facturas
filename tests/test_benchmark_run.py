from benchmark.metrics import build_report
from benchmark.run import Result, format_report, run
from factories import make_fields


def test_run_processes_every_invoice_with_the_real_adapters():
    result = run(count=6, seed=1)

    assert result.report.invoices == 6
    assert result.seconds > 0


def test_the_report_lists_every_field_and_the_totals():
    report = build_report([make_fields()], [make_fields(supplier=None)])

    text = format_report(Result(report, seconds=2.0))

    assert "Facturas procesadas: 1" in text
    assert "2.00 s" in text
    assert "supplier" in text
    assert "total" in text
    assert "Precisión global: 85.7%" in text
    assert "0/1" in text
