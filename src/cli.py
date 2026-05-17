import argparse
from src.orchestrator import (
    SUPPORTED_SMELLS,
    DEFAULT_ALL_SMELLS,
    DIRTY_WATERS_ALL_SMELLS,
    run_analysis,
)


def run() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze a React/npm project for selected supply chain smells."
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Path to the React/npm project.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all default local/fast smells (excluding Dirty-Waters smells).",
    )
    parser.add_argument(
        "--dirty-waters-all",
        action="store_true",
        help="Run all Dirty-Waters-based smells.",
    )
    parser.add_argument(
        "--smell",
        action="append",
        help="Run one or more specific smells. Repeat the argument to add more than one.",
    )
    parser.add_argument(
        "--repo",
        help="GitHub repository identifier for Dirty-Waters checks, e.g. owner/repo",
    )
    parser.add_argument(
        "--dirty-waters-backend",
        choices=["disabled", "wsl"],
        default="disabled",
        help="How to run Dirty-Waters.",
    )
    parser.add_argument(
        "--wsl-distro",
        default="Ubuntu",
        help="WSL distro name to use for Dirty-Waters.",
    )
    parser.add_argument(
        "--dirty-waters-root",
        default="/home/parafita/dirty-waters",
        help="Path to the Dirty-Waters clone inside WSL.",
    )

    args = parser.parse_args()

    selected_modes = sum(
        [
            bool(args.all),
            bool(args.dirty_waters_all),
            bool(args.smell),
        ]
    )

    if selected_modes == 0:
        parser.error("Use --all, --dirty-waters-all, or at least one --smell.")

    if selected_modes > 1:
        parser.error("Use only one of: --all, --dirty-waters-all, or --smell.")

    if args.all:
        selected_smells = DEFAULT_ALL_SMELLS
    elif args.dirty_waters_all:
        selected_smells = DIRTY_WATERS_ALL_SMELLS
    else:
        selected_smells = []
        for smell in args.smell:
            if smell not in SUPPORTED_SMELLS:
                parser.error(
                    f"Unsupported smell: {smell}. Supported smells: {sorted(SUPPORTED_SMELLS)}"
                )
            selected_smells.append(smell)

    output_dir = run_analysis(
        args.project,
        selected_smells,
        repo_name=args.repo,
        dirty_waters_backend=args.dirty_waters_backend,
        wsl_distro=args.wsl_distro,
        dirty_waters_root=args.dirty_waters_root,
    )

    print("Analysis completed.")
    print(f"Output directory: {output_dir}")
    print(f"Executed smells: {', '.join(selected_smells)}")