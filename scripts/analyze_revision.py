"""Recompute revision results from public observations only (Python 3.10+)."""
import csv
import itertools
import json
import math
import statistics as st
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'


def stats(values):
    values = list(values)
    assert values and all(math.isfinite(v) for v in values)
    return dict(n=len(values), mean=st.mean(values), median=st.median(values),
                sd=st.stdev(values) if len(values) > 1 else None, min=min(values), max=max(values))


def paired(a, b):
    """Matched b-a, exploratory Student interval and exact sign-flip test."""
    assert len(a) == len(b) and len(a) > 1
    delta = [y-x for x, y in zip(a, b)]
    critical = {2: 12.706204736, 3: 4.30265273, 5: 2.776445105, 9: 2.306004135, 10: 2.262157163}
    margin = critical[len(delta)] * st.stdev(delta) / math.sqrt(len(delta))
    extreme = sum(abs(sum(s*d for s, d in zip(signs, delta))) >= abs(sum(delta))-1e-9
                  for signs in itertools.product((-1, 1), repeat=len(delta)))
    return dict(difference=stats(delta), mean95t=[st.mean(delta)-margin, st.mean(delta)+margin],
                exactSignflipP=extreme/2**len(delta), reductionPercent=100*(1-st.mean(a)/st.mean(b)))


def indexed(rows, fields):
    result = {tuple(r[f] for f in fields): r for r in rows}
    assert len(result) == len(rows), 'Duplicate cohort-local key'
    return result


def contrast(rows, key, arm, a, b, field):
    ix = indexed(rows, (key, arm))
    keys = sorted({r[key] for r in rows})
    assert all((k, a) in ix and (k, b) in ix for k in keys)
    return paired([ix[k, a][field] for k in keys], [ix[k, b][field] for k in keys])


def db_summary(rows, key, prediction):
    ix = indexed(rows, (key, 'mode'))
    keys = sorted({r[key] for r in rows})
    assert len(ix) == 2*len(keys)
    d, q = ([ix[k, mode]['seconds'] for k in keys] for mode in ('D', 'Q'))
    return dict(pairs=len(keys), D=stats(d), Q=stats(q), reductionPercent=100*(1-st.mean(d)/st.mean(q)),
                directMAPEPercent=100*st.mean(abs(v-prediction)/v for v in d),
                directFaster=sum(x<y for x, y in zip(d, q)))


def analyze():
    data = json.loads((DATA / 'revision/observations.json').read_text())
    t = data['supplementary']
    expected = {'M1': 10, 'S6a': 15, 'S6aStages': 31, 'D1r': 12, 'V1r': 12, 'P1': 12, 'P1Choices': 5}
    assert {k: len(v) for k, v in t.items()} == expected
    result = {}
    frozen = json.loads((DATA/'revision/frozen-model.json').read_text())
    calibration = frozen['calibration']
    assert len(calibration)==3 and frozen['calibrationLineages']==1
    assert frozen['modelFrozen'] and frozen['heldoutPredictionsFrozen'] and not frozen['heldoutResultsUsed']
    result['frozenPredictions'] = {}
    for workload, features in frozen['heldoutFeatures'].items():
        v = features['inputs']
        for k in ('Bstg','Bout','Bp','Tconv','Tdir_ctl','Tstg_ctl'):
            assert math.isclose(v[k],st.mean(r['measured'][k] for r in calibration))
        for k in ('Ds','Dt'):
            assert math.isclose(v[k],v['Dr']*st.mean(r['measured'][k]/r['measured']['Dr'] for r in calibration))
        calculated = {'direct':v['Dr']/v['Bp']+v['Tconv']+v['Tdir_ctl'],
                      'staged':v['Ds']/v['Bstg']+v['Dt']/v['Bout']+v['Tstg_ctl']}
        for mode, key in [('D','direct'),('Q','staged')]:
            assert math.isclose(calculated[key],features['predictedSeconds'][key])
            assert all(math.isclose(r['predicted'],calculated[key]) for r in t['P1'] if r['workload']==workload and r['mode']==mode)
        result['frozenPredictions'][workload] = calculated
    legacy = data['earlySupplementary']
    result['pathAndAblation'] = {c+a: stats(r['wallSeconds'] for r in legacy if r['cohort']==c and r['arm']==a)
                              for c, a in [('S1','D'), ('S1','Q'), ('R1','A'), ('R1','B'), ('R1','C')]}
    s1 = [r for r in legacy if r['cohort']=='S1']
    r1 = [r for r in legacy if r['cohort']=='R1']
    result['S1paired'] = contrast(s1, 'block', 'arm', 'D', 'Q', 'wallSeconds')
    result['R1_C_minus_A'] = contrast(r1, 'block', 'arm', 'A', 'C', 'wallSeconds')
    result['R1_C_minus_A_precleanup'] = contrast(r1, 'block', 'arm', 'A', 'C', 'beforeCleanupSeconds')
    result['R1omitFirstBlockSensitivity'] = contrast([r for r in r1 if r['block']!=1], 'block', 'arm', 'A', 'C', 'wallSeconds')
    result['M1'] = {tool: {field: stats(r[field] for r in t['M1'] if r['tool']==tool)
                         for field in ('migrationSeconds', 'firstbootFromCreationSeconds')} for tool in ('m','z')}
    assert all(r['passed'] and not r['assisted'] for r in t['M1'])
    result['M1paired'] = contrast(t['M1'], 'pair', 'tool', 'z', 'm', 'migrationSeconds')
    result['M1firstbootPaired'] = contrast(t['M1'], 'pair', 'tool', 'z', 'm', 'firstbootFromCreationSeconds')
    single = {r['repeat']: r['seconds'] for r in t['S6a'] if r['width']==1 and r['success']}
    indexed(t['S6a'], ('repeat','width'))
    result['concurrency'] = {}
    for width in (1,2,4):
        attempts = [r for r in t['S6a'] if r['width']==width]
        ok = [r for r in attempts if r['success']]
        assert all(r['overlap']>=width for r in ok)
        assert all(r['seconds'] is None for r in attempts if not r['success'])
        ratios = [width*single[r['repeat']]/r['seconds'] for r in ok]
        assert all(math.isclose(v,r['pairedThroughputSpeedup']) for v,r in zip(ratios,ok))
        result['concurrency'][str(width)] = dict(complete=len(ok), attempted=len(attempts),
                                               seconds=stats(r['seconds'] for r in ok), pairedRatios=ratios,
                                               meanPairedRatio=st.mean(ratios))
    result['services'] = {}
    for os in ('centos7','win2016'):
        rows = [r for r in t['D1r'] if r['os']==os]
        ix = indexed([r for r in rows if r['success']], ('repeat','mode'))
        keys = sorted(k for k,m in ix if m=='low' and (k,'cold') in ix)
        result['services'][os] = dict(
            attempted=len(rows), completed=len(ix), pairedBlocks=keys,
            byMode={m: stats(r['sqlGapSeconds'] for r in rows if r['success'] and r['mode']==m) for m in ('cold','low')},
            matchedReductionPercent=100*(1-st.mean(ix[k,'low']['sqlGapSeconds'] for k in keys)/
                                          st.mean(ix[k,'cold']['sqlGapSeconds'] for k in keys)))
    result['verification'] = {}
    for disks in (1,5):
        for policy in ('full','sampled'):
            rows = [r for r in t['V1r'] if r['diskCount']==disks and r['policy']==policy]
            assert len(rows)==3
            for r in rows:
                assert math.isclose(r['uniqueVerifiedBytes']/r['logicalDiskBytes'], r['uniqueCoverageFraction'])
                assert r['sourceReadBytes']==r['targetReadBytes']==r['uniqueVerifiedBytes']
            result['verification'][f'{disks}-{policy}'] = dict(seconds=stats(r['verifierWallSeconds'] for r in rows),
                coveragePercent=100*rows[0]['uniqueCoverageFraction'],
                digestWallFractions=[(r['sourceDigestSeconds']+r['targetDigestSeconds'])/r['verifierWallSeconds'] for r in rows])
    formal = [r for r in t['P1'] if r['formal'] and not r['assisted']]
    result['model'] = {}
    for w in ('heldout_db','heldout_scale'):
        for m in ('D','Q'):
            rows = [r for r in formal if r['workload']==w and r['mode']==m]
            errors = [abs(r['seconds']-r['predicted'])/r['seconds'] for r in rows]
            assert all(math.isclose(e,r['ape']) for e,r in zip(errors,rows))
            result['model'][w+'-'+m] = dict(seconds=stats(r['seconds'] for r in rows),
                                          predicted=rows[0]['predicted'], MAPEPercent=100*st.mean(errors))
    choices = []
    ix = indexed(formal, ('workload','repeat','mode'))
    for (w, repeat, mode), r in ix.items():
        if mode!='D': continue
        q = ix[w,repeat,'Q']
        predicted_choice = 'D' if r['predicted']<q['predicted'] else 'Q'
        assert predicted_choice=='D'
        choices.append(dict(workload=w, repeat=repeat, predictedChoice=predicted_choice,
                            actualChoice='D' if r['seconds']<q['seconds'] else 'Q',
                            regretSeconds=max(0,r['seconds']-q['seconds']), D=r['seconds'], Q=q['seconds']))
    assert sorted(choices,key=lambda r:(r['workload'],r['repeat'])) == sorted(t['P1Choices'],key=lambda r:(r['workload'],r['repeat']))
    result['selection'] = dict(pairs=len(choices), correct=sum(r['actualChoice']=='D' for r in choices),
                               regretSeconds=sum(r['regretSeconds'] for r in choices), equalsAlwaysDirect=True)
    diagnosis = data['diagnosis']
    result['diagnosisPaired'] = contrast(diagnosis, 'pair', 'mode', 'D', 'Q', 'seconds')
    for r in diagnosis:
        if r['mode']=='D':
            assert sum(x['sourceReadBytes'] for x in r['directDiskOperations'])==r['sourceReadBytes']
        else:
            assert sum(x['readBytes'] for x in r['stagingMeasurement']['sourceDisks'])==r['sourceReadBytes']
    pred = data['confirmation'][0]['predicted']
    db = [r for r in formal if r['workload']=='heldout_db']
    result['confirmationSensitivity'] = {
        'originalAll': db_summary(db,'repeat',pred),
        'originalOmitPair2': db_summary([r for r in db if r['repeat']!=2],'repeat',pred),
        'diagnosisAll': db_summary(diagnosis,'pair',pred),
        'diagnosisOmitPair1': db_summary([r for r in diagnosis if r['pair']!=1],'pair',pred),
        'confirmation': db_summary([dict(r,pair=1) for r in data['confirmation']],'pair',pred)}
    with (DATA/'master_analysis.csv').open() as handle:
        historical = list(csv.DictReader(handle))
    current = {r['record_id']:r for r in historical if r['current_workset']=='1'}
    phases = data['currentWorksetPhases']
    assert set(current) == {r['record_id'] for r in phases} and len(phases)==7
    result['currentWorksetTargetPhase'] = {}
    for group, expected_count in [('staging',3),('direct',3),('adjacent_direct_control',1)]:
        selected = [r for r in phases if r['group']==group]
        assert len(selected)==expected_count
        for r in selected:
            original = current[r['record_id']]
            assert (original['mode']=='coldQcow2') == (group=='staging')
            residual = float(original['wall_seconds'])-float(original['measured_stage_seconds'])
            assert 0 <= r['targetTransferPublicationSeconds'] <= residual
        result['currentWorksetTargetPhase'][group] = stats(r['targetTransferPublicationSeconds'] for r in selected)
    flags = ['historical_primary','historical_sensitivity','controlled_trial','strict_matrix',
             'current_workset','sparse_policy_trial','final_core']
    result['historicalIntersections'] = {a:{b:sum(r[a]=='1' and r[b]=='1' for r in historical) for b in flags} for a in flags}
    result['archivedOutcomes'] = json.loads((DATA/'revision/outcomes.json').read_text())
    return result


if __name__ == '__main__':
    print(json.dumps(analyze(), indent=2, allow_nan=False))
