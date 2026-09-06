"""Resume os relatórios do pytest num quadro legível.

Lê `report/junit.xml` (resultado dos testes) e `coverage.xml` (cobertura) e imprime
um resumo em Markdown. Na CI o resultado é anexado ao *step summary* do GitHub
Actions; localmente serve como conferência rápida após `pytest`.

Uso:
    python scripts/test_report_summary.py [--junit report/junit.xml] [--coverage coverage.xml]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

COVERAGE_GATE = 90.0


def _read_junit(path: Path) -> dict[str, float]:
    root = ET.parse(path).getroot()
    # O pytest emite <testsuites><testsuite>; versões antigas emitem <testsuite> direto.
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        raise ValueError(f"nenhum <testsuite> encontrado em {path}")

    total = int(suite.get("tests", 0))
    failures = int(suite.get("failures", 0))
    errors = int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    return {
        "total": total,
        "passed": total - failures - errors - skipped,
        "failed": failures + errors,
        "skipped": skipped,
        "duration": float(suite.get("time", 0.0)),
    }


def _read_coverage(path: Path) -> dict[str, float]:
    root = ET.parse(path).getroot()
    return {
        "lines": float(root.get("line-rate", 0.0)) * 100,
        "branches": float(root.get("branch-rate", 0.0)) * 100,
    }


def _render(tests: dict[str, float], coverage: dict[str, float]) -> str:
    status = "aprovado" if tests["failed"] == 0 else "reprovado"
    gate = "atingido" if coverage["lines"] >= COVERAGE_GATE else "abaixo do mínimo"
    return "\n".join(
        [
            "## Testes automatizados",
            "",
            "| Métrica | Valor |",
            "| :--- | ---: |",
            f"| Testes executados | {int(tests['total'])} |",
            f"| Aprovados | {int(tests['passed'])} |",
            f"| Falhas | {int(tests['failed'])} |",
            f"| Ignorados | {int(tests['skipped'])} |",
            f"| Cobertura de linhas | {coverage['lines']:.2f}% |",
            f"| Gate de cobertura | {COVERAGE_GATE:.0f}% ({gate}) |",
            f"| Duração | {tests['duration']:.1f}s |",
            "",
            f"Resultado: **{status}**.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", type=Path, default=Path("report/junit.xml"))
    parser.add_argument("--coverage", type=Path, default=Path("coverage.xml"))
    args = parser.parse_args(argv)

    for path in (args.junit, args.coverage):
        if not path.exists():
            print(f"Relatório não encontrado: {path}. Rode `pytest` primeiro.", file=sys.stderr)
            return 1

    print(_render(_read_junit(args.junit), _read_coverage(args.coverage)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
