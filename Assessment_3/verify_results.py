"""Verify saved analysis results without retraining the classifiers."""
import json
import hashlib
import math

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from analysis import BloodPressureClipper, FEATURES, RESULTS, SOURCE


def verify():
    source = pd.read_csv(SOURCE)
    audit = json.loads((RESULTS / 'data_audit.json').read_text())
    assert audit['source_sha256'] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert audit['records'] == len(source) == 70000
    split = pd.read_csv(RESULTS / 'split_assignments.csv')
    assert split.ID.is_unique and set(split.ID) == set(source.ID)
    assert split.split.value_counts().to_dict() == {'train': 39200, 'test': 21000, 'validation': 9800}
    truth = source.set_index('ID').CARDIO
    assert np.array_equal(split.CARDIO.to_numpy(), truth.loc[split.ID].to_numpy())
    predictions = pd.read_csv(RESULTS / 'test_predictions.csv')
    assert predictions.ID.is_unique
    assert set(predictions.ID) == set(split.loc[split.split == 'test', 'ID'])
    assert np.array_equal(predictions.actual.to_numpy(), truth.loc[predictions.ID].to_numpy())
    assert set(predictions.predicted).issubset({0, 1}) and np.isfinite(predictions.score).all()
    tp = int(((predictions.actual == 1) & (predictions.predicted == 1)).sum())
    tn = int(((predictions.actual == 0) & (predictions.predicted == 0)).sum())
    fp = int(((predictions.actual == 0) & (predictions.predicted == 1)).sum())
    fn = int(((predictions.actual == 1) & (predictions.predicted == 0)).sum())
    expected = {'accuracy': (tp + tn) / len(predictions), 'precision': tp / (tp + fp),
                'recall': tp / (tp + fn), 'f1': 2 * tp / (2 * tp + fp + fn),
                'balanced_accuracy': (tp / (tp + fn) + tn / (tn + fp)) / 2,
                'roc_auc': roc_auc_score(predictions.actual, predictions.score)}
    summary = json.loads((RESULTS / 'model_summary.json').read_text())
    assert summary['features'] == FEATURES and 'ID' not in FEATURES and 'CARDIO' not in FEATURES
    for metric, value in expected.items():
        assert math.isclose(value, summary['test_metrics'][metric], abs_tol=1e-12), metric
    assert summary['final_training_records'] == 49000 and summary['test_records'] == 21000
    train = source.set_index('ID').loc[split.loc[split.split != 'test', 'ID']]
    q1, q3 = train[['AP_HI', 'AP_LO']].quantile([0.25, 0.75]).to_numpy()
    assert np.allclose(q1 - 1.5 * (q3 - q1), list(summary['training_bp_lower'].values()))
    assert np.allclose(q3 + 1.5 * (q3 - q1), list(summary['training_bp_upper'].values()))
    comparison = pd.read_csv(RESULTS / 'validation_comparison.csv')
    assert len(comparison) == 10
    assert {'Ridge', 'Random forest', 'Gradient boosting', 'AdaBoost', 'Bagging', 'Extra trees', 'Stacking'}.issubset(set(comparison.model))
    selected = comparison.sort_values(['roc_auc', 'accuracy', 'model'], ascending=[False, False, True]).iloc[0].model
    assert selected == summary['selected_model']
    tests = pd.read_csv(RESULTS / 'hypothesis_tests.csv')
    assert set(tests.variable) == {'CHOLESTEROL', 'AGE_YEARS', 'WEIGHT', 'ALCO'}
    assert (tests.p_holm >= tests.p_value - 1e-14).all()
    assert (tests.reject_at_0_05 == (tests.p_holm < 0.05)).all()
    # An extreme held-out value cannot change learned training limits.
    sample = pd.DataFrame({'AP_HI': [0., 1., 2., 3.], 'AP_LO': [0., 1., 2., 3.]})
    clipper = BloodPressureClipper().fit(sample)
    assert clipper.transform(pd.DataFrame({'AP_HI': [1000.], 'AP_LO': [-1000.]})).iloc[0].tolist() == [4.5, -1.5]
    assert clipper.upper_.tolist() == [4.5, 4.5] and sample.AP_HI.tolist() == [0., 1., 2., 3.]
    notebook = json.loads((RESULTS.parent / '03_Data_Analysis.ipynb').read_text(encoding='utf-8'))
    cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
    assert [c['execution_count'] for c in cells] == list(range(1, len(cells) + 1))
    assert not any(o['output_type'] == 'error' for c in cells for o in c['outputs'])
    print('PASS: split isolation, source labels, model selection, test metrics, training limits, statistical tests and notebook outputs.')


if __name__ == '__main__':
    verify()
