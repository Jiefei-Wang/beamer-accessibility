"""Compile isolated fixtures into their adjacent out directory; run regression checks."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests' / 'fixtures'
OUT = FIXTURES / 'out'
NEGATIVE = {
    'policy-strict-test': 'strict',
    'blank-alt-failure': 'missing',
    'table-policy-failure': 'Unannotated',
    'table-unannotated-strict-test': 'Unannotated',
    'figure-strict-missing-alt-test': 'missing',
}

def compile_fixture(source):
    expected = NEGATIVE.get(source.stem)
    for iteration in range(1 if expected or source.stem.endswith('-failure') else 2):
        result = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error',
                                 f'-output-directory={OUT}', str(source)], cwd=ROOT,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, errors='replace', timeout=180)
        if expected or source.stem.endswith('-failure'):
            if result.returncode == 0 or (expected and expected not in result.stdout.replace('\n', '').replace('\r', '')):
                raise AssertionError(f'{source.name}: expected diagnostic not produced\n{result.stdout[-3000:]}')
        elif result.returncode:
            raise AssertionError(f'{source.name}: compilation failed\n{result.stdout[-3000:]}')
    return source.name

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pattern', default='*.tex')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--compile-only', action='store_true')
    args = parser.parse_args()
    sources = sorted(FIXTURES.glob(args.pattern))
    if not sources:
        parser.error('No fixtures matched')
    OUT.mkdir(exist_ok=True)
    failures = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(compile_fixture, source) for source in sources]
        for future in as_completed(futures):
            try:
                print('[COMPILED]', future.result(), flush=True)
            except Exception as error:
                failures.append(str(error))
                print('[FAIL]', error, flush=True)
    if failures:
        return 1
    if not args.compile_only:
        for script in ('verify.py', 'verify_at.py', 'verify_regressions.py'):
            result = subprocess.run([sys.executable, "-u", str(ROOT/'tests'/script), str(OUT)], cwd=ROOT)
            if result.returncode:
                return result.returncode
    return 0

if __name__ == '__main__':
    sys.exit(main())
