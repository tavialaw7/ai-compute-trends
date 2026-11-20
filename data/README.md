# Data

**File:** `epoch_notable_ai_models.csv`, 1,011 rows and 47 columns, publication dates from 1950 to 2026.

**Source:** Epoch AI, "Data on AI models", https://epoch.ai/data/ai-models. Licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Credit Epoch AI if you reuse it.

**Provenance.** This copy comes from the public GitHub repository `spiceoogway/ai-economy-timelines` (`data/raw/epoch_notable_ai_models_raw.csv`), whose data dictionary says it retrieved the file from `https://epoch.ai/data/notable_ai_models.csv` on 2026-05-02. I could not reach epoch.ai from my build environment, so I did not compare it with Epoch's current release. The row and column counts match that repository's documentation.

**Refresh.** Download the current file from the Epoch link above, replace the CSV, and run `ai-compute-trends`. The loader reads columns by name, so a changed column name raises an error and does not silently shift data.

**Cleaning rules** (see `src/ai_compute_trends/load.py`):

- `sector`: Industry or Academia when every listed organization has that type, Collaboration when types are mixed, Other for government or research collectives.
- `country`: the first country listed for the developing organizations.
- `open_weights`: from Epoch's "Open model weights?" column, left empty when unknown.
- `frontier`: Epoch's frontier flag, meaning the model was at the top of training compute when released.
- Blank or malformed numbers and dates become NULL.
