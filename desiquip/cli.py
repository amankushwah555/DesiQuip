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
STEPS = {"write": "write", "voice": "voice", "clips": "clip", "captions": "caption", "render": "render",
         "finalize": "finalize", "qa": "qa", "package": "package", "upload": "publish"}
PIPELINE = ["write", "voice", "clips", "captions", "render", "finalize", "qa", "package"]


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


def run_daily(container, step_runner, count: int | None) -> int:
    """Spec section 9, 14:00 run: new jobs from the Trend finder, produce each, then report.
    A failed job never blocks the others."""
    log = logging.getLogger("desiquip")
    orch = container.orchestrator(step_runner)
    orch.process_approvals()
    job_ids = container.trend_service().run(count or container.daily_count())
    for job_id in job_ids:
        result = orch.produce(job_id)
        log.info("== %s -> %s", job_id, result)
    orch.send_summary()
    return 0


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
    pr = sub.add_parser("produce", help="orchestrated: run the flow with QA retries, then ask for approval")
    pr.add_argument("job_id")
    pr.add_argument("--from", dest="start", default=None)
    dl = sub.add_parser("run-daily", help="Trend finder -> N new jobs -> produce each -> approvals -> summary")
    dl.add_argument("--count", type=int, default=None)
    sub.add_parser("approvals", help="process Approve/Reject decisions (Telegram or CLI) and publish approved jobs")
    ap = sub.add_parser("approve", help="approve a job awaiting approval (publishes it)")
    ap.add_argument("job_id")
    rj = sub.add_parser("reject", help="reject a job; the note becomes a learning")
    rj.add_argument("job_id")
    rj.add_argument("--note", default="")
    sub.add_parser("status", help="list jobs and their status")
    sub.add_parser("summary", help="send the daily summary (Telegram or log)")
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
                container.rights().add(f"orig-{args.job_id}", "original", owner="DesiQuip")
            else:
                created = store.create(args.job_id, Path(args.template))
            log.info("Created %s", created)
            return 0
        step_runner = lambda step, job_id: run_step(container, step, job_id)  # noqa: E731
        if args.cmd == "status":
            for row in container.jobs().list():
                print(f"{row['job_id']:<24} {row['status']:<18} retries={row['retries']} "
                      f"{row['youtube_id'] or ''} {row['error'] or ''}")
            return 0
        if args.cmd in ("approve", "reject"):
            container.approver().decide(args.job_id, args.cmd, getattr(args, "note", ""))
            container.orchestrator(step_runner).process_approvals()
            return 0
        if args.cmd == "approvals":
            container.orchestrator(step_runner).process_approvals()
            return 0
        if args.cmd == "summary":
            container.orchestrator(step_runner).send_summary()
            return 0
        if args.cmd == "produce":
            container.jobs().create(args.job_id)
            container.orchestrator(step_runner).produce(args.job_id, args.start)
            return 0
        if args.cmd == "run-daily":
            return run_daily(container, step_runner, args.count)
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
