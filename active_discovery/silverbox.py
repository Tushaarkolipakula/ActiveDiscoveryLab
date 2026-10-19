"""Passive physical-data validation; not validation of active interventions.

Official split follows nonlinear_benchmarks.Silverbox. Only the first 50 test
outputs initialize free-running predictions. No later measured output is fed back.
"""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from scipy.io import loadmat


def fit_model(u, y, cubic, penalty):
    # Scaling is fitted only on the supplied training partition.
    scale_u, scale_y = float(np.std(u)), float(np.std(y))
    u, y = u/scale_u, y/scale_y
    columns = [y[1:-1], y[:-2], u[1:-1], u[:-2], np.ones(len(y)-2)]
    if cubic:
        columns.append(y[1:-1]**3)
    x = np.column_stack(columns)
    coef = np.linalg.solve(x.T@x/len(x)+penalty*np.eye(x.shape[1]), x.T@y[2:]/len(x))
    return {'coefficients': coef.tolist(), 'scale_u': scale_u, 'scale_y': scale_y,
            'cubic': cubic, 'penalty': penalty}


def predict(model, u, initial_y, warmup=50):
    if len(initial_y) != warmup or len(u) <= warmup:
        raise ValueError('Provide exactly the allowed initialization window.')
    u = np.asarray(u)/model['scale_u']
    y = np.empty(len(u))
    y[:warmup] = np.asarray(initial_y)/model['scale_y']
    c = model['coefficients']
    for t in range(warmup, len(u)):
        a, b = y[t-1], y[t-2]
        if not np.isfinite(a) or abs(a)>1e6:
            return None  # Report divergence; never clip or reset with test outputs.
        y[t] = c[0]*a+c[1]*b+c[2]*u[t-1]+c[3]*u[t-2]+c[4]
        if model['cubic']:
            y[t] += c[5]*a**3
    return y*model['scale_y']


def score(model, u, y):
    prediction = predict(model, u, y[:50])
    if prediction is None:
        return {'rmse_volts': None, 'nrmse': None, 'diverged': True}, None
    rmse = float(np.sqrt(np.mean((prediction[50:]-y[50:])**2)))
    return {'rmse_volts': rmse, 'nrmse': rmse/float(np.std(y[50:])), 'diverged': False}, prediction


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('data/silverbox/raw/SilverboxFiles/SNLS80mV.mat'))
    parser.add_argument('--out', type=Path, default=Path('results/silverbox-001'))
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error('Use an empty directory; preserve consumed test evidence.')
    args.out.mkdir(parents=True, exist_ok=True)
    penalties = [0., 1e-8, 1e-6, 1e-4, 1e-2]
    plan = {'created_utc': datetime.now(timezone.utc).isoformat(), 'models': ['linear_arx2', 'cubic_arx2'],
            'penalties': penalties, 'selection': 'Chronological final 20% of official train_val; free-running RMSE',
            'warmup': 50, 'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'data_sha256': hashlib.sha256(args.data.read_bytes()).hexdigest(),
            'source': 'https://sites.google.com/view/nonlinear-benchmark/benchmarks/silverbox',
            'split_reference': 'https://github.com/MaartenSchoukens/nonlinear_benchmarks/blob/master/nonlinear_benchmarks/benchmarks.py',
            'train_val_slice': [40650,101212], 'test_multisine_slice': [101212,127400],
            'test_arrow_slice': [100,40575],
            'claim_scope': 'Passive physical-data prediction baseline, not physical active discovery or a new law.'}
    (args.out/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    data = loadmat(args.data)
    u, y = data['V1'].reshape(-1), data['V2'].reshape(-1)
    train_u, train_y = u[40650:101212], y[40650:101212]
    cut = int(.8*len(train_u))
    models, validation = {}, {}
    for name, cubic in [('linear_arx2',False), ('cubic_arx2',True)]:
        trials = []
        for penalty in penalties:
            model = fit_model(train_u[:cut],train_y[:cut],cubic,penalty)
            metrics,_ = score(model,train_u[cut:],train_y[cut:])
            trials.append({'penalty': penalty, **metrics})
        finite = [t for t in trials if not t['diverged']]
        if not finite:
            raise RuntimeError(f'All {name} validation models diverged; do not evaluate test.')
        selected = min(finite,key=lambda t:t['rmse_volts'])['penalty']
        models[name] = fit_model(train_u,train_y,cubic,selected)
        validation[name] = trials
    # Freeze the selected models BEFORE evaluating the official test sets.
    (args.out/'selected_models.json').write_text(json.dumps({'models':models,'validation':validation},indent=2),encoding='utf-8')
    results = []
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2,1,figsize=(10,6))
    for ax,(split,lo,hi) in zip(axes,[('multisine',101212,127400),('arrow_full',100,40575)]):
        test_u,test_y=u[lo:hi],y[lo:hi]
        ax.plot(np.arange(50,650)/610.35,test_y[50:650],label='Measured',color='black',linewidth=1)
        for name,model in models.items():
            metrics,prediction=score(model,test_u,test_y)
            results.append({'split':split,'model':name,'scored_samples':len(test_y)-50,**metrics})
            if prediction is not None:
                ax.plot(np.arange(50,650)/610.35,prediction[50:650],label=name,alpha=.8,linewidth=.8)
        ax.set(title=f'{split}: first 600 scored samples',xlabel='Time (s)',ylabel='Output (V)')
        ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(args.out/'physical_predictions.png',dpi=160); plt.close(fig)
    (args.out/'metrics.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    lines=['# Silverbox: real measured data, passive validation','',
           'Linear and cubic autoregressive predictors were trained on the official training partition. '
           'Regularization was selected using only an internal chronological validation split. '
           'The selected models were then refitted on train_val and frozen before test evaluation.','',
           '| Test | Model | Free-running RMSE (mV) | NRMSE | Diverged |','|---|---|---:|---:|---|']
    for row in results:
        error='—' if row['diverged'] else f"{1000*row['rmse_volts']:.3f}"
        norm='—' if row['diverged'] else f"{row['nrmse']:.4f}"
        lines.append(f"| {row['split']} | {row['model']} | {error} | {norm} | {row['diverged']} |")
    lines+=['','![Measured and predicted output](physical_predictions.png)','',
            'Only the first 50 measured outputs initialize each test sequence. Predictions then run without '
            'measured-output feedback. NRMSE is normalized by the standard deviation of scored measured outputs. '
            'No test output is used to select hyperparameters. The full arrow test includes extrapolation; '
            'its overlapping no-extrapolation subset is not counted as independent evidence.','',
            'This is a simple discrete-time baseline on recordings of a physical electronic Duffing oscillator. '
            'It does not validate the simulator’s active experiment selection, establish causal discovery, '
            'or claim state-of-the-art performance. Training with noisy lagged outputs may bias coefficients. '
            'The cubic feature is informed by the published apparatus description, not newly discovered physics.','',
            'Source: https://sites.google.com/view/nonlinear-benchmark/benchmarks/silverbox',
            'Citation: T. Wigren and J. Schoukens, Three free data sets for development and benchmarking '
            'in nonlinear system identification, European Control Conference, 2013, pp. 2933–2938.']
    (args.out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()
