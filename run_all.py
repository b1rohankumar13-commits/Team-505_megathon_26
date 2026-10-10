"""Run the existing ML pipeline from the project root or check its data paths."""
from pathlib import Path
import runpy
import sys


if __name__ == "__main__":
    ml_dir = Path(__file__).resolve().parent / "src" / "ml"
    sys.path.insert(0, str(ml_dir))
    if sys.argv[1:] == ["--check-data"]:
        namespace = runpy.run_path(str(ml_dir / "run_all.py"), run_name="_preflight")
        cfg, pd = namespace["cfg"], namespace["pd"]
        with namespace["stage"]("preflight/load and validate inputs; no training"):
            paths = dict(namespace["PATHS"])
            paths.update(transaction_labels=cfg.LABELS_TXN_CSV, takeup_labels=cfg.LABELS_TAKEUP_CSV)
            for name, path in paths.items():
                if not Path(path).is_file():
                    raise FileNotFoundError(f"{name}: {path}")
                print(f"FOUND {name}: {path}", flush=True)
            tables, _ = namespace["clean_tables"]({k: pd.read_csv(v) for k, v in namespace["PATHS"].items()})
            namespace["check_sources"](tables, pd.read_csv(cfg.LABELS_TXN_CSV), pd.read_csv(cfg.LABELS_TAKEUP_CSV))
            print(f"PASS: {len(tables['customers'])} customers; all input paths and source checks passed.")
    elif sys.argv[1:]:
        raise SystemExit("Usage: python run_all.py [--check-data]")
    else:
        runpy.run_path(str(ml_dir / "run_all.py"), run_name="__main__")
