# Exoplanet Habitability Classifier

A data science project to identify potentially habitable exoplanets using unsupervised and supervised machine learning.

**Data** : NASA Exoplanet Archive — 6150 confirmed exoplanets  
**Labels** : Habitable Exoplanets Catalog (HEC) — 70 expert-identified candidates  
**Stack** : Python, pandas, scikit-learn, XGBoost

---

## Project Structure

```
exoplanet_habitability/
├── data/
│   ├── raw/                    # NASA CSV + HEC Excel files (not versioned)
├── exoplanet_guesser.ipynb     # Unsupervised exploration (KMeans, DBSCAN)
├── exoplanet_classifier.ipynb  # Supervised classification (XGBoost)
├── requirements.txt
└── README.md
```

---

## Notebooks

### 1. `exoplanet_guesser.ipynb` — Unsupervised Exploration

We explore the data without any labels and try to identify Earth-like planets through clustering.

**Pipeline**
- Download NASA Exoplanet Archive via TAP query
- Feature selection : 683 → 29 physical features
- Add Earth manually as a reference point
- Filter on habitability criteria, restrict to planets with real measurements
- KMeans clustering with physical feature weighting
- Validate against HEC

**Best result — KMeans k=2**

| Metric | Value |
|---|---|
| True Positives | 22 |
| Recall | 61% |
| F1 | 0.29 |

We found 2 out of 3 HEC planets with no labels.

---

### 2. `exoplanet_classifier.ipynb` — Supervised Classification

We use HEC membership as ground truth and train an XGBoost classifier.

**Pipeline**
- Load full NASA dataset + HEC labels
- Feature selection and median imputation
- Remove detection artifacts (radial velocity mass, parallax, proper motion...)
- Train/test split — stratified on label
- XGBoost with scale_pos_weight to handle 87:1 class imbalance
- GridSearch tuning
- Final evaluation

**Best result — XGBoost baseline**

| Metric | Value |
|---|---|
| True Positives | 11 |
| False Positives | 2 |
| Precision | 85% |
| Recall | 79% |
| F1 | 0.81 |

The tuned model (GridSearch) did not improve over the baseline.

---

## Key Decisions

**What "habitable" means**  
We don't define it ourselves. Labels come from the HEC, a catalog maintained by the University of Puerto Rico at Arecibo based on expert criteria.

**Why median imputation**  
Exoplanet distributions are heavily skewed by gas giants. The median is more representative of a typical planet than the mean.

**Why we filter before imputing**  
Imputing on the full dataset first contaminates the filtered subset with medians from non-habitable planets.

**Why we removed certain features**  
Variable like radial velocity mass (`pl_msinij`) or parallax (`sy_plx`) correlate with the HEC label for observational reasons, not physical ones. Keeping them would give the model an unfair shortcut.

---

## Setup

```bash
conda create -n astroclassif python=3.11
conda activate astroclassif
pip install -r requirements.txt
```

Then open either notebook in VS Code or Jupyter.

The NASA data will be downloaded automatically on first run (~30-60s).  
The HEC files (`habitable.xlsx`) must be placed in `data/raw/` manually.

