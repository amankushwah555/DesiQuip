"""Command line entry point.

    python -m desiquip new <job_id> --topic "..."     # start from an idea (Writer agent writes the script)
    python -m desiquip new <job_id> [--from DIR]      # start from a ready script (default: examples/demo-001)
    python -m desiquip make <job_id> [--upload] [--from STEP]
    python -m desiquip write|voice|captions|render|finalize|upload <job_id>
    python -m desiquip validate <job_id>              # check script.json against the spec rules
    python -m desiquip auth                           # one-time YouTube OAuth
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# CLI step name -> Container service name, in pipeline order.
STEPS = {"write": "write", "voice": "voice", "captions": "caption", "render": "render",
         "finalize": "finalize", "upload": "publish"}
PIPELINE = ["write", "voice", "captions", "render", "finalize"]


def make_container():
    from .container import Container
    return Container.from_files(ROOT)


def _setup_logging() -> None:
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(ROOT / "logs" / "desiquip.log", encoding="utf-8")])


def run_step(container, step: str, job_id: str):
    log = logging.getLogger("desiquip")
    service = getattr(container, f"{STEPS[step]}_service")()
    log.info("== %s: %s", step, job_id)
    t0 = time.perf_counter()
    result = service.run(job_id)
    log.info("== %s done in %.1fs", step, time.perf_counter() - t0)
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="desiquip", description="DesiQuip Shorts pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)
    mk = sub.add_parser("make", help="run write -> voice -> captions -> render -> finalize")
    mk.add_argument("job_id")
    mk.add_argument("--upload", action="store_true", help="also upload (private) at the end")
    mk.add_argument("--from", dest="start", choices=PIPELINE, default=None,
                    help="resume from a step (default: write if there is no script yet, else voice)")
    for step in STEPS:
        sub.add_parser(step).add_argument("job_id")
    sub.add_parser("validate", help="check script.json against the spec rules").add_argument("job_id")
    sub.add_parser("auth", help="one-time YouTube OAuth; saves secrets/token.json")
    nw = sub.add_parser("new", help="create jobs/<job_id>/ from a topic or a template folder")
    nw.add_argument("job_id")
    src = nw.add_mutually_exclusive_group()
    src.add_argument("--topic", help="idea for the Writer agent, e.g. \"बिजली का बिल\"")
    src.add_argument("--from", dest="template", default=str(ROOT / "examples" / "demo-001"))
    nw.add_argument("--character", default="uncle_ji")
    args = p.parse_args(argv)

    _setup_logging()
    log = logging.getLogger("desiquip")
    try:
        if args.cmd == "auth":
            from .adapters.youtube import authorize
            authorize(ROOT / "secrets")
            log.info("YouTube authorised; token saved to secrets/token.json")
            return 0
        container = make_container()
        if args.cmd == "validate":
            problems = container.validate_job(args.job_id)
            for problem in problems:
                print(f"- {problem}")
            print("OK: script follows the spec rules" if not problems else f"{len(problems)} problem(s)")
            return 1 if problems else 0
        if args.cmd == "new":
            store = container.store()
            if args.topic:
                created = store.create_from_topic(args.job_id, args.topic, args.character)
            else:
                created = store.create(args.job_id, Path(args.template))
            log.info("Created %s", created)
            return 0
        if args.cmd == "make":
            start = args.start or ("voice" if container.store().has(args.job_id, "script.json") else "write")
            steps = PIPELINE[PIPELINE.index(start):] + (["upload"] if args.upload else [])
        else:
            steps = [args.cmd]
        for step in steps:
            result = run_step(container, step, args.job_id)
            log.info("   -> %s", result)
        return 0
    except Exception as e:  # noqa: BLE001 - CLI boundary: log and return an exit code
        log.error("FAILED: %s", e, exc_info=log.isEnabledFor(logging.DEBUG))
        return 1


if __name__ == "__main__":
    sys.exit(main())
