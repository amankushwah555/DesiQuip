"""VideoRenderer adapter: renders the 'Short' composition in remotion/ via the Remotion CLI."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def stage_assets(public_dir: Path, job_id: str, props: dict[str, Any],
                 assets: dict[str, Path]) -> dict[str, Any]:
    """Copy job assets into remotion/public/jobs/<id>/ and point props at them (staticFile paths)."""
    dest = public_dir / "jobs" / job_id
    dest.mkdir(parents=True, exist_ok=True)
    for name, src in assets.items():
        (dest / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest / name)

    prefix = f"jobs/{job_id}/"
    staged = copy.deepcopy(props)
    for key in ("audio", "characterImage"):
        if staged.get(key):
            staged[key] = prefix + staged[key]
    for scene in staged.get("scenes", []):
        if scene.get("asset"):
            scene["asset"] = prefix + scene["asset"]
    return staged


CLI_JS = Path("node_modules/@remotion/cli/remotion-cli.js")


def build_render_cmd(node: str, props_file: Path, out: Path, concurrency: str = "100%") -> list[str]:
    return [node, str(CLI_JS), "render", "src/index.ts", "Short", str(out),
            f"--props={props_file}", "--codec=h264", "--log=warn", f"--concurrency={concurrency}"]


def build_still_cmd(node: str, props_file: Path, out: Path) -> list[str]:
    return [node, str(CLI_JS), "still", "src/index.ts", "Thumbnail", str(out), f"--props={props_file}", "--log=warn"]


class RemotionRenderer:
    def __init__(self, project_dir: Path, concurrency: str = "100%") -> None:
        self.project_dir = Path(project_dir)
        self.concurrency = concurrency
        node = shutil.which("node")
        if not node:
            raise RuntimeError("'node' not found on PATH. Install Node.js 22 LTS (setup.ps1).")
        if not (self.project_dir / CLI_JS).is_file():
            raise RuntimeError("Remotion not installed. Run: cd remotion; npm ci")
        self.node = node

    def render(self, job_id: str, props: dict[str, Any], assets: dict[str, Path], out: Path) -> None:
        self._run(job_id, props, assets, lambda pf: build_render_cmd(self.node, pf, out.resolve(), self.concurrency))

    def still(self, job_id: str, props: dict[str, Any], assets: dict[str, Path], out: Path) -> None:
        self._run(job_id, props, assets, lambda pf: build_still_cmd(self.node, pf, out.resolve()))

    def _run(self, job_id: str, props: dict[str, Any], assets: dict[str, Path], make_cmd) -> None:
        staged = stage_assets(self.project_dir / "public", job_id, props, assets)
        props_file = self.project_dir / "out" / f"props-{job_id}.json"
        props_file.parent.mkdir(exist_ok=True)
        props_file.write_text(json.dumps(staged, ensure_ascii=False), encoding="utf-8")
        try:
            subprocess.run(make_cmd(props_file.resolve()), cwd=self.project_dir, check=True)
        finally:
            shutil.rmtree(self.project_dir / "public" / "jobs" / job_id, ignore_errors=True)
