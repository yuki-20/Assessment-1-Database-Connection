"""Cardiovascular data exploration, statistical tests and classification."""
from pathlib import Path
import hashlib
import json
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (AdaBoostClassifier, BaggingClassifier, ExtraTreesClassifier,
                              GradientBoostingClassifier, RandomForestClassifier, StackingClassifier)
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
                             classification_report, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'data' / 'CARDIO_TRAIN_export.csv'
RESULTS = ROOT / 'results'
FIGURES = RESULTS / 'figures'
NUMERIC = ['AGE_YEARS', 'HEIGHT', 'WEIGHT', 'AP_HI', 'AP_LO']
CATEGORICAL = ['GENDER', 'CHOLESTEROL', 'GLUC', 'SMOKE', 'ALCO', 'ACTIVE']
FEATURES = NUMERIC + CATEGORICAL
SEED = 42


def save_json(name, value):
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / name).write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


class BloodPressureClipper(TransformerMixin, BaseEstimator):
    """Learn the 1.5-IQR limits from the current training partition."""
    def fit(self, X, y=None):
        quartiles = X[['AP_HI', 'AP_LO']].quantile([0.25, 0.75])
        width = quartiles.loc[0.75] - quartiles.loc[0.25]
        self.lower_ = quartiles.loc[0.25] - 1.5 * width
        self.upper_ = quartiles.loc[0.75] + 1.5 * width
        return self

    def transform(self, X):
        check_is_fitted(self, 'lower_')
        result = X.copy()
        result[['AP_HI', 'AP_LO']] = result[['AP_HI', 'AP_LO']].clip(
            self.lower_, self.upper_, axis=1)
        return result


def model_pipeline(estimator):
    return Pipeline([
        ('blood_pressure', BloodPressureClipper()),
        ('features', ColumnTransformer([
            ('numeric', StandardScaler(), NUMERIC),
            ('categorical', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL),
        ])),
        ('model', estimator),
    ])


def load_data():
    frame = pd.read_csv(SOURCE)
    expected = ['ID', 'AGE', 'GENDER', 'HEIGHT', 'WEIGHT', 'AP_HI', 'AP_LO',
                'CHOLESTEROL', 'GLUC', 'SMOKE', 'ALCO', 'ACTIVE', 'CARDIO']
    if list(frame.columns) != expected or frame.empty:
        raise ValueError('The SQL export must contain the original 13 columns and at least one record.')
    if frame.isna().any().any() or not np.isfinite(frame.to_numpy()).all():
        raise ValueError('Missing or non-finite source values require review before analysis.')
    if not frame.ID.is_unique:
        raise ValueError('Patient IDs must be unique.')
    for name, allowed in {'GENDER': {1, 2}, 'CHOLESTEROL': {1, 2, 3}, 'GLUC': {1, 2, 3},
                          'SMOKE': {0, 1}, 'ALCO': {0, 1}, 'ACTIVE': {0, 1}, 'CARDIO': {0, 1}}.items():
        if not set(frame[name]).issubset(allowed):
            raise ValueError(f'Unexpected category in {name}.')
    frame['AGE_YEARS'] = frame.AGE / 365.25
    audit = {'records': len(frame), 'original_columns': 13,
             'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'missing_values': int(frame.isna().sum().sum()),
             'duplicate_ids': int(frame.ID.duplicated().sum()),
             'identical_non_id_records': int(frame.drop(columns='ID').duplicated().sum()),
             'disease_cases': int(frame.CARDIO.sum()),
             'disease_fraction': float(frame.CARDIO.mean())}
    save_json('data_audit.json', audit)
    frame.describe().T.to_csv(RESULTS / 'descriptive_statistics.csv')
    return frame, audit


def exploration(frame):
    FIGURES.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.titleweight': 'bold', 'figure.facecolor': 'white'})
    correlation = frame[FEATURES + ['CARDIO']].corr()
    correlation.to_csv(RESULTS / 'correlations.csv')
    fig, ax = plt.subplots(figsize=(11, 9), layout='constrained')
    im = ax.imshow(correlation, cmap='RdBu_r', vmin=-1, vmax=1)
    ax.set_xticks(range(len(correlation)), correlation.columns, rotation=50, ha='right')
    ax.set_yticks(range(len(correlation)), correlation.index)
    for i in range(len(correlation)):
        for j in range(len(correlation)):
            v = correlation.iloc[i, j]
            ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=7,
                    color='white' if abs(v) > 0.6 else '#162433')
    ax.set_title('Raw feature correlations', pad=18)
    fig.colorbar(im, ax=ax, shrink=0.8, label='Pearson correlation')
    fig.savefig(FIGURES / 'correlation_matrix.png', dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(3, 4, figsize=(13, 9), layout='constrained')
    for ax, name in zip(axes.flat, FEATURES + ['CARDIO']):
        if name in NUMERIC:
            ax.hist(frame[name], bins=25, color='#167d8d', edgecolor='white', linewidth=0.5)
        else:
            counts = frame[name].value_counts().sort_index()
            ax.bar(counts.index, counts.values, color='#167d8d', width=0.65)
            ax.set_xticks(counts.index)
        ax.set_title(name)
        ax.set_ylabel('Records')
        if name in ('AP_HI', 'AP_LO'):
            ax.set_yscale('log')
            ax.set_ylabel('Records (log scale)')
    fig.suptitle('Distributions before cleaning', fontsize=17)
    fig.savefig(FIGURES / 'distributions.png', dpi=150)
    plt.close(fig)

    sample = frame.sample(min(3000, len(frame)), random_state=SEED)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), layout='constrained')
    for ax, (x, y) in zip(axes, [('WEIGHT', 'CARDIO'), ('AGE_YEARS', 'CARDIO'), ('AGE_YEARS', 'WEIGHT')]):
        ax.scatter(sample[x], sample[y], s=7, alpha=0.08, color='#167d8d', rasterized=True)
        fit = np.polyfit(frame[x], frame[y], 1)
        line_x = np.array([frame[x].min(), frame[x].max()])
        ax.plot(line_x, np.polyval(fit, line_x), color='#a33b20', label='Linear trend')
        ax.set(xlabel=x, ylabel=y)
        ax.legend(frameon=False)
    fig.suptitle('Pairwise relationships: descriptive trends', fontsize=16)
    fig.savefig(FIGURES / 'relationships.png', dpi=150)
    plt.close(fig)

    cleaner = BloodPressureClipper().fit(frame)
    cleaned = cleaner.transform(frame)
    bounds = pd.DataFrame({'lower': cleaner.lower_, 'upper': cleaner.upper_})
    bounds['values_clipped'] = [(frame[c] != cleaned[c]).sum() for c in bounds.index]
    bounds.to_csv(RESULTS / 'descriptive_clipping.csv')
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), layout='constrained')
    for j, name in enumerate(['AP_HI', 'AP_LO']):
        axes[0, j].boxplot(frame[name], vert=False)
        axes[0, j].set_xscale('symlog', linthresh=200)
        axes[0, j].set_title(f'{name}: raw (symmetric log scale)')
        axes[1, j].boxplot(cleaned[name], vert=False)
        axes[1, j].set_title(f'{name}: clipped to 1.5-IQR limits')
        for i in range(2):
            axes[i, j].set_yticks([])
            axes[i, j].set_xlabel('Blood pressure, mmHg')
    fig.savefig(FIGURES / 'blood_pressure_cleaning.png', dpi=150)
    plt.close(fig)
    return correlation, bounds, cleaned


def hypothesis_tests(frame):
    cholesterol = [frame.loc[frame.CHOLESTEROL == group, 'CARDIO'] for group in [1, 2, 3]]
    age_split = frame.AGE_YEARS.mean()
    younger = frame.loc[frame.AGE_YEARS < age_split, 'CARDIO']
    older = frame.loc[frame.AGE_YEARS >= age_split, 'CARDIO']
    anova = stats.f_oneway(*cholesterol)
    age = stats.ttest_ind(older, younger, equal_var=False)
    weight = stats.pearsonr(frame.WEIGHT, frame.CARDIO)
    table = pd.crosstab(frame.ALCO, frame.CARDIO)
    alcohol = stats.chi2_contingency(table, correction=True)
    tests = pd.DataFrame([
        {'variable': 'CHOLESTEROL', 'test': 'One-way ANOVA', 'statistic': anova.statistic,
         'p_value': anova.pvalue, 'effect': max(g.mean() for g in cholesterol) - min(g.mean() for g in cholesterol),
         'effect_measure': 'Range of disease proportions'},
        {'variable': 'AGE_YEARS', 'test': 'Welch t-test: older vs younger than mean',
         'statistic': age.statistic, 'p_value': age.pvalue, 'effect': older.mean() - younger.mean(),
         'effect_measure': 'Difference in disease proportions'},
        {'variable': 'WEIGHT', 'test': 'Pearson correlation', 'statistic': weight.statistic,
         'p_value': weight.pvalue, 'effect': weight.statistic, 'effect_measure': 'Pearson r'},
        {'variable': 'ALCO', 'test': 'Chi-square with Yates correction', 'statistic': alcohol.statistic,
         'p_value': alcohol.pvalue, 'effect': np.sqrt(alcohol.statistic / len(frame)),
         'effect_measure': 'Cramers V'},
    ])
    tests['p_holm'] = multipletests(tests.p_value, method='holm')[1]
    tests['reject_at_0_05'] = tests.p_holm < 0.05
    tests.to_csv(RESULTS / 'hypothesis_tests.csv', index=False)
    save_json('age_test_groups.json', {'cutoff_years': float(age_split), 'younger_n': len(younger),
              'older_n': len(older), 'younger_disease_fraction': float(younger.mean()),
              'older_disease_fraction': float(older.mean()),
              'levene_p_value': float(stats.levene(older, younger).pvalue)})
    formula = 'CARDIO ~ ' + ' + '.join(NUMERIC + [f'C({c})' for c in CATEGORICAL])
    ols = smf.ols(formula, data=frame).fit(cov_type='HC3')
    (RESULTS / 'ols_summary.txt').write_text('\n'.join(line.rstrip() for line in ols.summary().as_text().splitlines()) + '\n', encoding='utf-8')
    coefficients = pd.DataFrame({'coefficient': ols.params, 'robust_std_error': ols.bse,
                                 'p_value': ols.pvalues, 'ci_lower': ols.conf_int()[0],
                                 'ci_upper': ols.conf_int()[1]})
    coefficients.to_csv(RESULTS / 'ols_coefficients.csv')
    save_json('ols_metrics.json', {'r_squared': float(ols.rsquared),
                                  'adjusted_r_squared': float(ols.rsquared_adj), 'records': int(ols.nobs)})
    return tests, ols


def scores(estimator, X, y):
    prediction = estimator.predict(X)
    score = estimator.predict_proba(X)[:, 1] if hasattr(estimator, 'predict_proba') else estimator.decision_function(X)
    return {'accuracy': accuracy_score(y, prediction), 'balanced_accuracy': balanced_accuracy_score(y, prediction),
            'precision': precision_score(y, prediction, zero_division=0),
            'recall': recall_score(y, prediction, zero_division=0), 'f1': f1_score(y, prediction),
            'roc_auc': roc_auc_score(y, score), 'average_precision': average_precision_score(y, score)}, prediction, score


def classification(frame):
    train_ids, test_ids = train_test_split(frame.index, test_size=0.30, stratify=frame.CARDIO, random_state=SEED)
    fit_ids, validation_ids = train_test_split(train_ids, test_size=0.20,
                                               stratify=frame.loc[train_ids, 'CARDIO'], random_state=SEED + 1)
    split = pd.Series('test', index=frame.index)
    split.loc[fit_ids] = 'train'
    split.loc[validation_ids] = 'validation'
    frame[['ID', 'CARDIO']].assign(split=split).to_csv(RESULTS / 'split_assignments.csv', index=False)
    X_fit, y_fit = frame.loc[fit_ids, FEATURES], frame.loc[fit_ids, 'CARDIO']
    X_validation, y_validation = frame.loc[validation_ids, FEATURES], frame.loc[validation_ids, 'CARDIO']
    forest = RandomForestClassifier(n_estimators=100, max_depth=12, min_samples_leaf=5, random_state=SEED, n_jobs=2)
    boosting = GradientBoostingClassifier(n_estimators=100, max_depth=2, random_state=SEED)
    bagging = BaggingClassifier(estimator=RidgeClassifier(alpha=0.001), n_estimators=20,
                                max_samples=0.5, max_features=0.5, random_state=SEED, n_jobs=2)
    candidates = {
        'Ridge': model_pipeline(RidgeClassifier(alpha=0.001)),
        'Random forest': model_pipeline(forest),
        'Gradient boosting': model_pipeline(boosting),
        'AdaBoost': model_pipeline(AdaBoostClassifier(n_estimators=80, learning_rate=0.5, random_state=SEED)),
        'Bagging': model_pipeline(bagging),
        'Extra trees': model_pipeline(ExtraTreesClassifier(n_estimators=100, max_depth=12,
                                    min_samples_leaf=5, random_state=SEED, n_jobs=2)),
        'Stacking': StackingClassifier(estimators=[('ridge', model_pipeline(RidgeClassifier(alpha=0.001))),
                      ('forest', model_pipeline(clone(forest).set_params(n_estimators=60))),
                      ('boosting', model_pipeline(clone(boosting).set_params(n_estimators=60)))],
                      final_estimator=LogisticRegression(max_iter=1000),
                      cv=StratifiedKFold(3, shuffle=True, random_state=SEED), n_jobs=1),
    }
    # ponytail: three extra boosting settings bound tuning cost; expand only if validation warrants it.
    for trees, depth, rate in [(160, 2, 0.05), (160, 3, 0.05), (100, 3, 0.1)]:
        name = f'Boosting: {trees} trees, depth {depth}, rate {rate}'
        candidates[name] = model_pipeline(GradientBoostingClassifier(
            n_estimators=trees, max_depth=depth, learning_rate=rate, random_state=SEED))
    rows = []
    for name, candidate in candidates.items():
        started = time.perf_counter()
        candidate.fit(X_fit, y_fit)
        metrics, _, _ = scores(candidate, X_validation, y_validation)
        rows.append({'model': name, 'stage': 'tuned' if name.startswith('Boosting:') else 'comparison',
                     **metrics, 'fit_seconds': time.perf_counter() - started})
        pd.DataFrame(rows).to_csv(RESULTS / 'validation_comparison.csv', index=False)
        print(f"{name}: validation accuracy {metrics['accuracy']:.4f}; ROC AUC {metrics['roc_auc']:.4f}", flush=True)
    comparison = pd.DataFrame(rows).sort_values(['roc_auc', 'accuracy', 'model'], ascending=[False, False, True])
    selected_name = comparison.iloc[0]['model']
    final = clone(candidates[selected_name])
    final.fit(frame.loc[train_ids, FEATURES], frame.loc[train_ids, 'CARDIO'])
    test_metrics, labels, risk_score = scores(final, frame.loc[test_ids, FEATURES], frame.loc[test_ids, 'CARDIO'])
    test_y = frame.loc[test_ids, 'CARDIO']
    interval = proportion_confint(int((test_y == labels).sum()), len(test_y), method='wilson')
    test_metrics.update(accuracy_ci_lower=float(interval[0]), accuracy_ci_upper=float(interval[1]))
    pd.DataFrame({'ID': frame.loc[test_ids, 'ID'], 'actual': test_y,
                  'predicted': labels, 'score': risk_score}).to_csv(RESULTS / 'test_predictions.csv', index=False)
    report = classification_report(test_y, labels, output_dict=True, zero_division=0)
    save_json('classification_report.json', report)
    clipping = final.named_steps['blood_pressure'] if isinstance(final, Pipeline) else final.estimators_[0].named_steps['blood_pressure']
    save_json('model_summary.json', {'selected_model': selected_name,
              'selection_metric': 'Validation ROC AUC, then accuracy, then model name',
              'random_seed': SEED, 'fit_records': len(fit_ids), 'validation_records': len(validation_ids),
              'final_training_records': len(train_ids), 'test_records': len(test_ids), 'features': FEATURES,
              'validation_best_roc_auc': float(comparison.iloc[0].roc_auc), 'test_metrics': test_metrics,
              'majority_baseline_test_accuracy': float((test_y == frame.loc[train_ids, 'CARDIO'].mode()[0]).mean()),
              'training_bp_lower': clipping.lower_.to_dict(), 'training_bp_upper': clipping.upper_.to_dict(),
              'final_parameters': {k: v for k, v in final.get_params().items()
                                   if isinstance(v, (str, int, float, bool)) or v is None},
              'cloud_executed': False})
    fig, ax = plt.subplots(figsize=(9, 5), layout='constrained')
    ranked = comparison.sort_values('roc_auc')
    ax.barh(ranked.model, ranked.roc_auc, color=['#b15e2e' if n == selected_name else '#167d8d' for n in ranked.model])
    for index, value in enumerate(ranked.roc_auc):
        ax.text(value + 0.015, index, f'{value:.4f}', va='center', fontsize=9)
    ax.set(xlabel='Validation ROC AUC', title='Model comparison and bounded tuning', xlim=(0, 1))
    fig.savefig(FIGURES / 'model_comparison.png', dpi=150)
    plt.close(fig)
    cm = confusion_matrix(test_y, labels, labels=[0, 1])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout='constrained')
    axes[0].imshow(cm, cmap='Blues')
    for i in range(2):
        for j in range(2):
            axes[0].text(j, i, f'{cm[i, j]:,}', ha='center', va='center',
                         color='white' if cm[i, j] > cm.max() / 2 else '#162433', fontsize=14)
    axes[0].set(xticks=[0, 1], yticks=[0, 1], xlabel='Predicted class', ylabel='Actual class', title='Test confusion matrix')
    fpr, tpr, _ = roc_curve(test_y, risk_score)
    axes[1].plot(fpr, tpr, color='#167d8d', label=f"ROC AUC = {test_metrics['roc_auc']:.3f}")
    axes[1].plot([0, 1], [0, 1], '--', color='#64748b')
    axes[1].set(xlabel='False positive rate', ylabel='True positive rate', title='Held-out test ROC')
    axes[1].legend(frameon=False)
    fig.savefig(FIGURES / 'test_evaluation.png', dpi=150)
    plt.close(fig)
    return comparison, test_metrics, selected_name
