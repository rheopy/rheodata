"""Command-line interface for rheodata (``rheodata`` / ``python -m rheodata``)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import rheodata


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="rheodata",
        description="Browse curated rheology datasets for training, "
                    "simulation, and benchmarking.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List every dataset (id, title, material, …).")

    s = sub.add_parser("search", help="Substring search over the registry.")
    s.add_argument("--material", default=None, help="Filter by material name.")
    s.add_argument("--experiment", default=None,
                   help="Filter by experiment type (e.g. flow_curve).")
    s.add_argument("--tag", default=None, help="Filter by tag.")
    s.add_argument("--query", default=None,
                   help="Free-text match on title/description/material.")

    i = sub.add_parser("info", help="Print a readable summary of a dataset.")
    i.add_argument("id", help="Dataset id (see `rheodata list`).")

    sk = sub.add_parser("install-skill",
                        help="Install the data-discovery AI skill.")
    sk.add_argument(
        "--target", default="vscode",
        choices=["vscode", "gemini", "cursor", "claude"],
        help="Target environment for install-skill (default: vscode).",
    )
    sk.add_argument(
        "--global-user", action="store_true",
        help="Install skill globally for the current user rather than locally.",
    )
    sk.add_argument(
        "--dest-dir", default=None,
        help="Explicit destination directory (overrides --target).",
    )
    return p.parse_args(argv)


def install_skill(
    target: str = "vscode",
    global_user: bool = False,
    dest_dir: Path | str | None = None,
) -> Path:
    """Install the packaged data-discovery AI skill into a skills directory."""
    import shutil

    try:  # works from an installed wheel
        from importlib.resources import files as _res_files
        package_skill_dir = Path(str(_res_files("rheodata") / "skills" / "data-discovery"))
    except Exception:
        package_skill_dir = Path(__file__).parent / "skills" / "data-discovery"
    if not package_skill_dir.is_dir():
        fallback = Path(__file__).parent / "skills" / "data-discovery"
        if fallback.is_dir():
            package_skill_dir = fallback
        else:
            raise RuntimeError(f"Skill directory not found at {package_skill_dir}")

    if dest_dir is not None:
        target_path = Path(dest_dir) / "data-discovery"
    elif global_user:
        target_path = Path.home() / ".agents" / "skills" / "data-discovery"
    else:
        mapping = {
            "vscode": Path(".github/skills/data-discovery"),
            "gemini": Path(".gemini/skills/data-discovery"),
            "cursor": Path(".cursor/rules/data-discovery"),
            "claude": Path(".claude/skills/data-discovery"),
        }
        target_path = mapping.get(target.lower(), Path(".github/skills/data-discovery"))

    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(package_skill_dir, target_path, dirs_exist_ok=True)
    return target_path


def _show_frame(frame) -> None:
    if frame.empty:
        print("(no datasets match)")
    else:
        with __import__("pandas").option_context(
            "display.max_columns", None, "display.width", 200,
            "display.max_colwidth", 40,
        ):
            print(frame.to_string(index=False))


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.command == "list":
            _show_frame(rheodata.list())
        elif args.command == "search":
            _show_frame(rheodata.search(
                material=args.material,
                experiment=args.experiment,
                tag=args.tag,
                query=args.query,
            ))
        elif args.command == "info":
            rheodata.info(args.id)
        elif args.command == "install-skill":
            dest = install_skill(target=args.target,
                                 global_user=args.global_user,
                                 dest_dir=args.dest_dir)
            print(f"[+] Successfully installed data-discovery skill to: {dest.resolve()}")
        return 0
    except (KeyError, ValueError, RuntimeError) as exc:
        print(f"[!] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
