# Generator

Python source that produced this dataset. Requirements: Python 3.10+, `reportlab`, `Pillow`, `piexif`, and `pdftoppm` (poppler) for the scanned documents.

- `data.py` - company, policies, vehicle values, vendors, benchmarks, prior claims
- `claims.py` - the 22 claim scenarios, including each answer key (`truth`)
- `kb_text.py` - policy forms and guidelines text
- `pdfkit.py`, `docimg.py`, `photos.py` - document, image and photo rendering
- `truth.py` - output schema and eval sets
- `build.py` - run `python build.py <output_dir>`

To add a claim, append a scenario to `claims.py` (copy an existing one) and re-run the build.
