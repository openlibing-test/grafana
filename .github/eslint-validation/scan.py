import os
import pathlib
import subprocess
import sys

kind = sys.argv[1]
base = os.environ.get('SCAN_BASE_SHA', '')
head = os.environ.get('SCAN_HEAD_SHA', 'HEAD')
pr = bool(base)
command = ['git', 'diff', '--name-only', '--diff-filter=ACMR', '-z', base + '...' + head] if pr else ['git', 'ls-files', '-z']
files = subprocess.check_output(command).decode().split('\0')
files = [f for f in files if f and pathlib.Path(f).is_file()]
report = pathlib.Path('/tmp/pre-commit-reports')
if not pr:
    report.mkdir(parents=True, exist_ok=True)
if kind == 'eslint':
    files = [f for f in files if f.startswith(('public/', 'packages/')) and f.endswith(('.ts', '.tsx')) and not f.endswith(('.gen.ts', '_gen.ts'))]
    if not files:
        sys.exit(0)
    print(f'ESLint: {len(files)} tracked TypeScript files; mode={"PR gate" if pr else "full"}', flush=True)
    args = ['node', '.github/eslint-validation/node_modules/eslint/bin/eslint.js', '--config', '.github/eslint-validation/eslint.config.mjs']
    if not pr:
        args += ['--format', './.github/eslint-validation/node_modules/@microsoft/eslint-formatter-sarif/sarif.js', '--output-file', str(report / 'eslint.sarif')]
    sys.exit(subprocess.call(args + files))
else:
    packages = sorted({'./' + str(pathlib.PurePosixPath(f).parent) for f in files if f.endswith('.go')}) if pr else ['./...']
    if not packages:
        sys.exit(0)
    print(f'gosec: {len(packages)} package targets; mode={"PR gate" if pr else "root module full"}', flush=True)
    args = ['.github/bin/gosec', '-conf=gosec.json', '-exclude-dir=vendor', '-exclude-generated']
    if not pr:
        args += ['-fmt=sarif', '-out=' + str(report / 'gosec.sarif')]
    sys.exit(subprocess.call(args + packages))
