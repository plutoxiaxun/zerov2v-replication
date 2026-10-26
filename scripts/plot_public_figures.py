"""Render the four quantitative manuscript figures from public rows.

Requires matplotlib. Output is written to an explicitly chosen directory;
PDF bytes/font metrics can differ across matplotlib and font versions.
"""
import argparse
import csv
import json
import statistics as st
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'


def source_request_percent(row):
    capacity = float(row['allocated_capacity_gib'])
    if capacity <= 0:
        raise ValueError('Provisioned capacity must be positive')
    return 100 * float(row['source_read_gib']) / capacity


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.size':10, 'pdf.fonttype':42, 'axes.spines.top':False, 'axes.spines.right':False})
    with (DATA/'master_analysis.csv').open() as f:
        rows = list(csv.DictReader(f))
    with (DATA/'controlled_trials.csv').open() as f:
        controlled = list(csv.DictReader(f))
    batches = json.loads((DATA/'revision/observations.json').read_text())['supplementary']['S6a']
    blue, red = '#34749c', '#b24a47'

    def save(fig, name):
        fig.savefig(out/(name+'.pdf'))
        fig.savefig(out/(name+'.png'), dpi=150)
        plt.close(fig)

    fig, axes = plt.subplots(1,2,figsize=(10,3.5),layout='constrained')
    for ax, workload, title, field, flag in zip(axes, ['VM-P1','L1'],
            ['(a) P1 complete active duration','(b) L1 source-read/conversion'],
            ['active_seconds','measured_stage_seconds'], ['sparse_policy_trial','strict_matrix']):
        for i, mode in enumerate(['coldQcow2','onlineSnapshotDirectRbd']):
            chosen = [r for r in rows if r[flag]=='1' and r['workload_id']==workload and r['mode']==mode
                      and (mode=='coldQcow2' or r['conversion_engine']==('full_scan' if workload=='VM-P1' else 'virt_v2v_output'))]
            y = [float(r[field]) for r in chosen]
            assert len(y)==3
            ax.scatter([i-.06,i,i+.06],y,color=[blue,red][i],s=36)
            ax.hlines(st.mean(y),i-.20,i+.20,color='black')
        ax.set(xticks=[0,1],xticklabels=['Staged','Direct'],ylabel='Time (s)',title=title,xlim=(-.5,1.5))
        ax.grid(axis='y',alpha=.2)
    save(fig,'figure-3-controlled-paths')

    fig, ax = plt.subplots(figsize=(9,3.6),layout='constrained')
    for i, workload in enumerate(['VM-E','VM-F','VM-G','VM-H']):
        for j, engine in enumerate(['TCG','KVM']):
            vals = [float(r['downtime_s']) for r in controlled if r['group']==f'{workload} / Low-downtime {engine}']
            assert len(vals)==3
            x=i+(j-.5)*.32; mean=st.mean(vals)
            ax.bar(x,mean,width=.28,color=[blue,red][j],label=engine if i==0 else None)
            ax.errorbar(x,mean,yerr=[[mean-min(vals)],[max(vals)-mean]],color='black',capsize=3)
    ax.set(xticks=range(4),xticklabels=['VM-E','VM-F','VM-G','VM-H'],ylabel='Offline cutover (s)')
    ax.legend(); ax.grid(axis='y',alpha=.2)
    save(fig,'figure-4-controlled-cutover')

    fig, axes = plt.subplots(1,2,figsize=(10,3.6),layout='constrained')
    for i, workload in enumerate(['VM-P1','VM-P2']):
        for j, engine in enumerate(['full_scan','vddk_extents']):
            chosen = [r for r in rows if r['sparse_policy_trial']=='1' and r['workload_id']==workload and r['conversion_engine']==engine]
            assert len(chosen)==3
            vals = [float(r['measured_stage_seconds']) for r in chosen]
            reads = [source_request_percent(r) for r in chosen]
            x=i+(j-.5)*.32; mean=st.mean(vals)
            for ax, value in zip(axes,[mean,st.mean(reads)]):
                ax.bar(x,value,width=.28,color=[blue,red][j],label=['qemu-img','VDDK extents'][j] if i==0 else None)
            axes[0].errorbar(x,mean,yerr=[[mean-min(vals)],[max(vals)-mean]],color='black',capsize=3)
    for ax, ylabel in zip(axes,['Baseline transfer (s)','Source requests (% of provisioned capacity)']):
        ax.set(xticks=range(2),xticklabels=['VM-P1','VM-P2'],ylabel=ylabel)
        ax.legend(); ax.grid(axis='y',alpha=.2)
    axes[1].set_ylim(0,16)
    save(fig,'figure-5-sparse-copy')

    fig, ax = plt.subplots(figsize=(5,3.3),layout='constrained')
    for i,width in enumerate([1,2,4]):
        vals=[r['seconds'] for r in batches if r['width']==width and r['success']]
        ax.scatter([i+(k-(len(vals)-1)/2)*.045 for k in range(len(vals))],vals,color=blue,zorder=3)
        ax.errorbar(i,st.mean(vals),yerr=st.stdev(vals),color=red,fmt='_',capsize=5,zorder=2)
    ax.set(xticks=range(3),xticklabels=['1 (5/5)','2 (5/5)','4 (4/5)'],ylabel='Complete-batch duration (s)',
           xlabel='Concurrency (complete/attempted)',ylim=(0,10500))
    ax.text(2,9800,'1 incomplete',ha='center',fontsize=9); ax.grid(axis='y',alpha=.2)
    save(fig,'figure-6-concurrency')
    print('Rendered Figures 3-6; data semantics reproduced, not byte-identical PDF files.')


if __name__ == '__main__':
    main()
