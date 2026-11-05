# Assessment 3: Data Analysis with Python

Section III of the ADY201m brief: explore the cardiovascular dataset, clean
blood-pressure outliers, test associations and evaluate classification models.

Open the [executed notebook](03_Data_Analysis.ipynb), or download the
[HTML report](03_Data_Analysis.html).

## Methods

- Validate the 70,000-record SQL export and derive age in years.
- Examine descriptive statistics, missing values, correlations, histograms,
  pairwise trends and blood-pressure box plots.
- Clip pressure outliers using 1.5-IQR limits; standardize numeric predictors
  and one-hot encode categorical predictors within training pipelines.
- Test cholesterol, age, weight and alcohol associations using ANOVA, Welch's
  t-test, Pearson correlation and chi-square, with Holm-adjusted p-values.
- Fit the requested OLS explanatory model with HC3 standard errors.
- Compare Ridge, random forest, gradient boosting, AdaBoost, bagging, extra
  trees and stacking, followed by three additional gradient-boosting settings.

## Evaluation

The stratified split reserves 21,000 records for the final test. Model selection
uses 39,200 fitting records and 9,800 validation records; the selected estimator
is then refitted on all 49,000 non-test records. The random seed is 42.

Selected model: gradient boosting, 160 trees, depth 3, learning rate 0.05.

| Held-out metric | Result |
| --- | --- |
| Accuracy | 73.20% |
| 95% accuracy interval | 72.60%-73.80% |
| Precision | 74.83% |
| Recall | 69.89% |
| F1 | 0.723 |
| ROC AUC | 0.799 |
| Majority-class baseline accuracy | 50.03% |

The findings describe associations within this dataset. Clipping does not
recover true clinical measurements, and this model has no external validation.
The notebook discusses sampling, identical predictor patterns and the limits
of a single held-out split.

## Reproduce

Download the complete repository. The source is the root
`data/CARDIO_TRAIN_export.csv`; Assessment 3 shares it with the database work.
Install the root `requirements.txt`, open this notebook from its own folder and
choose **Run All**. The functions called by the notebook are in `analysis.py`.

Check the saved results without retraining:

```text
python verify_results.py
```

`results/` contains the data audit, statistical tests, OLS results, validation
comparison, all split assignments, per-record test predictions, selected model
parameters, environment versions and six figures.

Execution is local. The Watson Studio rerun specified by the brief has not been
performed.
