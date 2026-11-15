#!/usr/bin/env python3
"""Check retained audit evidence without participant data or third-party imports.

This verifies byte identity, claim completeness and aggregate agreement only.
It does not certify source truth or independently reproduce a model result.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "eligibility", "identity", "related_study", "phenotype", "panel",
    "permutation", "calibration", "subgroups", "interpretation",
}


def read_evidence(root, relative):
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or '..' in path.parts or str(path) != relative:
        raise ValueError('Unsafe evidence path')
    local = root
    for part in path.parts:
        local = local / part
        if local.is_symlink():
            raise ValueError('Symlink evidence is not accepted')
    return local.read_bytes()


def lookup(record, pointer):
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        raise ValueError('Aggregate reference needs an absolute JSON pointer')
    for key in pointer[1:].split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        record = record[int(key)] if isinstance(record, list) else record[key]
    return record


def verify(root, ledger):
    if ledger.get('schema_version') != 1:
        raise ValueError('Unsupported ledger schema')
    if ledger.get('scope') != 'retained evidence; no isolated correction effects':
        raise ValueError('Unsupported audit claim scope')
    evidence = ledger.get('evidence', {})
    if not evidence:
        raise ValueError('No evidence')
    raw = {}
    for name, digest in evidence.items():
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('Invalid evidence digest: ' + name)
        value = read_evidence(root, name)
        if hashlib.sha256(value).hexdigest() != digest:
            raise ValueError('Changed evidence: ' + name)
        raw[name] = value
    claims = ledger.get('claims', [])
    if len(claims) != len(REQUIRED) or {c.get('id') for c in claims} != REQUIRED:
        raise ValueError('Missing or duplicate audit claim')
    assertions = 0
    for claim in claims:
        for key in ('observed', 'mechanism', 'correction', 'supported', 'remaining_limit'):
            if not isinstance(claim.get(key), str) or not claim[key].strip():
                raise ValueError('Incomplete claim: ' + claim['id'])
        if claim.get('effect_isolated') is not False:
            raise ValueError('Isolated correction effect is not established: ' + claim['id'])
        if claim.get('evidence_kind') not in ('documentary', 'aggregate', 'documentary_and_aggregate'):
            raise ValueError('Evidence kind missing: ' + claim['id'])
        refs = claim.get('evidence', [])
        if not refs or not set(refs).issubset(raw):
            raise ValueError('Unknown claim evidence: ' + claim['id'])
        checks = claim.get('assertions', [])
        if claim['evidence_kind'] != 'documentary' and not checks:
            raise ValueError('Aggregate claim has no assertions: ' + claim['id'])
        for check in checks:
            if check['file'] not in refs:
                raise ValueError('Assertion is not linked to claim evidence')
            actual = lookup(json.loads(raw[check['file']]), check['pointer'])
            expected = check['equals']
            if type(actual) is not type(expected) or actual != expected:
                raise ValueError('Aggregate disagreement: ' + claim['id'] + ' ' + check['pointer'])
            assertions += 1
    return {'status': 'pass', 'scope': ledger['scope'], 'claims': len(claims),
            'evidence_files': len(evidence), 'aggregate_assertions': assertions,
            'model_rerun': False, 'source_truth_verified': False,
            'limitations': 'Identity and consistency only; not consent, participant independence, clinical validation or causal effects.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        ledger = json.loads((args.root / 'docs/Audit_Evidence.json').read_text())
        result = verify(args.root, ledger)
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        print(json.dumps({'status': 'fail', 'cause': str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
