"""Final archive and two fixed preference selections (paper Fig. 4)."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import DATA, OUTPUT
from figure_export import save_paper_figure

record=json.loads((DATA/'multiobjective_history.json').read_text(encoding='utf-8'))
check=json.loads((DATA/'results.json').read_text(encoding='utf-8'))['archive_pair']
assert check['passed']
archive=np.asarray(record['archive_objectives'][-1])
low=check['cases']['low_overshoot']['archive_index_zero_based']
fast=check['cases']['fast_settling']['archive_index_zero_based']
BLUE='#28628a'; ORANGE='#ba7135'
plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],'font.size':9,
 'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':7.5,'pdf.fonttype':42,
 'svg.fonttype':'path','axes.linewidth':.65,'lines.linewidth':1.2})
fig,axes=plt.subplots(3,1,figsize=(3.42,4.9),layout='constrained')
labels=['Steady-state error (p.u.)','Overshoot (%)','Settling measure (s)']
others=np.ones(len(archive),dtype=bool);others[[low,fast]]=False
for ax,(i,j) in zip(axes,[(0,1),(0,2),(1,2)]):
    ax.scatter(archive[others,i],archive[others,j],s=20,c='#929da5',label='Other archive members',zorder=3)
    ax.scatter(archive[low,i],archive[low,j],s=100,c=BLUE,marker='*',edgecolors='#172a38',linewidths=.4,label='Low overshoot',zorder=5)
    ax.scatter(archive[fast,i],archive[fast,j],s=36,c=ORANGE,marker='D',edgecolors='#59381d',linewidths=.4,label='Fast settling',zorder=5)
    ax.set(xlabel=labels[i],ylabel=labels[j]);ax.grid(alpha=.25,lw=.5);ax.set_axisbelow(True)
    if i==0: ax.ticklabel_format(axis='x',style='sci',scilimits=(-2,2),useMathText=True)
axes[0].legend(frameon=False,loc='upper right',handlelength=1.3,labelspacing=.3,borderpad=.2)
save_paper_figure(fig,OUTPUT/'final_archive')
plt.close(fig)
