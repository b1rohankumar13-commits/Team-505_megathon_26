# ML modules

All ML modules stay together here because they use sibling imports.
From the repository root, run:

```powershell
python -m pip install -r requirements-ml.txt
python run_all.py --check-data
python run_all.py
```

See `../../START_HERE.md` for the current setup and validation limitations.
Inputs are in `../../data/`; model artifacts and reports go to the root
`artifacts/` and `results/` directories regardless of the shell working directory.
The root runner delegates to this directory's runner without duplicating its logic.

The required compatibility fixes have already been applied. `config-review.md`
is a historical review and its old `data/prepared` instructions are superseded.
