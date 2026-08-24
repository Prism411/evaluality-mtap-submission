#!/usr/bin/env python3
"""Audit signed direction alignment for the three external IQA databases.

The script deliberately never applies ``abs`` to an association.  It records
the raw SRCC, method polarity, target polarity and their signed product so that
an inversion remains negative in the screening inputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


METHOD_POLARITY = {
    "liqe": 1,
    "qualiclip": 1,
    "clipiqa_plus": 1,
    "topiq_nr": 1,
    "musiq": 1,
    "dbcnn": 1,
    "hyperiqa": 1,
    "niqe": -1,
    "brisque": -1,
    "clipiqa": 1,
    "sift_bovw": 1,
}

# All three released opinion-score fields used here are higher-is-better.
# KADID calls its field ``dmos``, but the database release explicitly defines
# larger values in its [1, 5] range as higher visual quality.
TARGET_POLARITY = {"kadid": 1, "koniq": 1, "clive": 1}

# Database that supplies the signed value reported in Main Table 2.  The audit
# intentionally reads the cached raw association for that database rather than
# reconstructing a minimum from an absolute value or a rounded manuscript cell.
TABLE_2_SOURCE_DATABASE = {
    "liqe": "kadid",
    "qualiclip": "kadid",
    "clipiqa_plus": "kadid",
    "topiq_nr": "kadid",
    "musiq": "kadid",
    "dbcnn": "kadid",
    "hyperiqa": "kadid",
    "niqe": "koniq",
    "brisque": "koniq",
    "clipiqa": "kadid",
    "sift_bovw": "koniq",
}

EXPECTED_MINIMA = {
    "liqe": 0.723,
    "qualiclip": 0.665,
    "clipiqa_plus": 0.654,
    "topiq_nr": 0.511,
    "musiq": 0.556,
    "dbcnn": 0.484,
    "hyperiqa": 0.462,
    "niqe": 0.368,
    "brisque": 0.236,
    "clipiqa": 0.501,
    "sift_bovw": -0.445,
}


def load_srcc(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text())
    return {name: float(values["srcc"]) for name, values in payload.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--opinion-metrics", type=Path, required=True)
    parser.add_argument("--clive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    opinion_payload = json.loads(args.opinion_metrics.read_text())
    raw = {
        "kadid": {
            name: float(values["srcc"])
            for name, values in opinion_payload["kadid10k"].items()
        },
        "koniq": {
            name: float(values["srcc"])
            for name, values in opinion_payload["koniq10k"].items()
        },
        "clive": load_srcc(args.clive),
    }
    methods = {}
    for method, method_sign in METHOD_POLARITY.items():
        database = TABLE_2_SOURCE_DATABASE[method]
        target_sign = TARGET_POLARITY[database]
        raw_rho = raw[database][method]
        aligned = method_sign * target_sign * raw_rho
        expected = EXPECTED_MINIMA[method]
        if abs(aligned - expected) > 5e-4:
            raise AssertionError(
                f"{method}: signed value {aligned:.6f} != Table 2 {expected:.3f}"
            )
        methods[method] = {
            "source_database": database,
            "raw_srcc": raw_rho,
            "method_polarity": method_sign,
            "target_polarity": target_sign,
            "direction_aligned_srcc": aligned,
            "table_2_value": expected,
        }

    result = {
        "definition": "rho_star = method_polarity * target_polarity * raw_srcc",
        "absolute_value_used": False,
        "target_note": (
            "KADID's released column is named dmos, but its documented [1,5] "
            "scale is higher-is-better; KonIQ and CLIVE MOS are also higher-is-better."
        ),
        "methods": methods,
        "table_2_reported_signed_values_verified": True,
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
