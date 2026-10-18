#!/usr/bin/env python3
"""CLI entrypoint to run a single process via the orchestrator.

Usage:
  python -m nexus.run_job --process visual_podcast --text "..." --run-dir ./runs/abc

Exits:
  0 -> OK
  2 -> UNKNOWN (missing tools / not possible)
  1 -> FAIL (error)

Prints JSON envelope to stdout.
"""
import argparse
import json
import sys
from pathlib import Path
from nexus import orchestrator


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--process', required=True)
    text_input = p.add_mutually_exclusive_group(required=True)
    text_input.add_argument('--text')
    text_input.add_argument('--text-file', help='Read literal UTF-8 request text from a file (Windows PowerShell 5.1)')
    p.add_argument('--run-dir', required=True)
    p.add_argument('--confidence-threshold', type=float, default=0.5)
    args = p.parse_args()

    request_text = args.text if args.text is not None else Path(args.text_file).read_text(encoding='utf-8')
    res = orchestrator.handle_request(request_text, args.run_dir, confidence_threshold=args.confidence_threshold)
    # print envelope if present
    envelope = res.get('envelope') if isinstance(res, dict) else None
    out = {'status': res.get('status') if isinstance(res, dict) else 'FAIL', 'envelope': envelope}
    print(json.dumps(out, ensure_ascii=False))

    status = res.get('status') if isinstance(res, dict) else 'FAIL'
    if status == 'OK':
        sys.exit(0)
    elif status in ('UNKNOWN', 'NEEDS_CLARIFICATION'):
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
