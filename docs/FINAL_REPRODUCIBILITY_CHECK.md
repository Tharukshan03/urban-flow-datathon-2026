# Final Reproducibility Check

## Environment

- Use Python 3.11 or a compatible Python 3 release.
- Create and activate an isolated virtual environment.
- Install the pinned project dependencies from the repository root:

```text
python -m pip install -r requirements.txt
```

The requirements cover pandas, NumPy, scikit-learn, Matplotlib, joblib, Jupyter, PyArrow, OpenPyXL, Streamlit, and Plotly. The active local `.venv` used for final verification contains the notebook and model dependencies but does not currently contain Streamlit or Plotly; reinstalling from `requirements.txt` is required before launching the bonus applications in that environment.

## Primary analytical artifacts

- Final integrated notebook: `MergeConflicts_FinalNotebook.ipynb`
- Technical report source: `reports/MergeConflicts_Technical_Report.md`
- Technical report PDF: `reports/MergeConflicts_Technical_Report.pdf`
- Fare pipeline: `models/fare_pipeline.pkl`
- Duration pipeline: `models/duration_pipeline.pkl`

The serialized fare and duration pipelines contain a `preprocessor` and a `LinearRegression` model. Model loading is a structure check only; no final test data or model retraining is required.

## Application commands

Launch the Track 6 dashboard from the repository root:

```text
python -m streamlit run dashboard/app.py
```

Launch the Track 5 AI Mobility Assistant from the repository root in a separate terminal:

```text
python -m streamlit run assistant/app.py
```

Both applications use bundled reporting data. They do not require raw taxi files for the prepared demonstration.

## Dataset confidentiality

Competition raw, processed, and split datasets are intentionally excluded from public Git tracking. The required `train.parquet`, `validation.parquet`, and `test.parquet` files may be placed in the private competition submission ZIP, but they must never be added to public Git history. The `submission/` directory and final ZIP filename are ignored locally for this reason.

## Demo video status

The recording script is `docs/MergeConflicts_Demo_Script.md`. The final unlisted YouTube URL is currently pending and must replace the placeholder in `docs/DEMO_VIDEO_LINK.txt` before submission.

## Final validation checklist

- [x] Final notebook is valid notebook JSON.
- [x] Final notebook uses repository-relative paths.
- [x] Final notebook executes top-to-bottom without cell errors.
- [x] Report metrics match the source notebooks and handovers.
- [x] Report figures and architecture assets exist.
- [x] Fare and duration pipelines reload successfully.
- [x] Member 1, Member 2, and Member 3 core artifacts exist.
- [x] Track 5 and Track 6 source and bundled data exist.
- [x] Raw, processed, and split competition datasets are excluded from Git.
- [x] `requirements.txt` lists all required project packages.
- [ ] Install all pinned requirements in the environment used for the demo applications.
- [ ] Record and upload the demo as an unlisted YouTube video.
- [ ] Replace the pending demo-link placeholder with the verified URL.
- [ ] Confirm the competition platform accepts the final ZIP size.
