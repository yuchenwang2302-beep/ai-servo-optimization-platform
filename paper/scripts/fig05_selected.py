"""Two replayed archive controllers: complete response and transient detail."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import FormatStrFormatter
from common import DATA, OUTPUT
from figure_export import save_paper_figure

check=json.loads((DATA/'results.json').read_text(encoding='utf-8'))['archive_pair']
assert check['passed']
z=np.genfromtxt(DATA/'multiobjective_responses.csv',delimiter=',',names=True)
t=z['time_s'];r=z['reference_pu'];low=z['low_overshoot'];fast=z['fast_settling']
assert len(t)==len(r)==len(low)==len(fast)==10001
BLUE='#28628a'; ORANGE='#ba7135'
plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],'font.size':9,
 'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':7.5,'pdf.fonttype':42,
 'svg.fonttype':'path','axes.linewidth':.65,'lines.linewidth':1.15,'path.simplify':False})
zoom_x=(.59,.80);zoom_y=(.485,.506)
fig,axes=plt.subplots(2,1,figsize=(3.42,3.45),layout='constrained')
for ax in axes:
    ax.plot(t,r,color='black',linestyle='--',label='Reference',zorder=3)
    ax.plot(t,low,color=BLUE,label='Low overshoot',zorder=4)
    ax.plot(t,fast,color=ORANGE,linestyle='-.',label='Fast settling',zorder=4)
    ax.set(xlabel='Time (s)',ylabel='Position (p.u.)');ax.grid(alpha=.25,linewidth=.5);ax.set_axisbelow(True)
axes[0].set(xlim=(0,1),ylim=(-.025,.56))
axes[0].set_xticks(np.arange(0,1.01,.2));axes[0].set_yticks([0,.2,.4])
axes[0].legend(frameon=False,loc='upper left',handlelength=2,labelspacing=.3)
axes[0].add_patch(Rectangle((zoom_x[0],zoom_y[0]),zoom_x[1]-zoom_x[0],zoom_y[1]-zoom_y[0],fill=False,edgecolor='#626b75',linewidth=.75,linestyle=(0,(2.5,2)),zorder=5))
axes[1].set(xlim=zoom_x,ylim=zoom_y)
axes[1].set_xticks([.60,.65,.70,.75,.80]);axes[1].set_yticks([.485,.490,.495,.500,.505])
axes[1].xaxis.set_major_formatter(FormatStrFormatter('%.2f'));axes[1].yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
axes[1].axhspan(.495,.505,facecolor='#dfe5e9',alpha=.28,zorder=0)
axes[1].axhline(.495,color='#909ba3',ls=':',lw=.6,zorder=1)
axes[1].axhline(.505,color='#909ba3',ls=':',lw=.6,zorder=1)
for name,y,color,xytext in [('low_overshoot',low,BLUE,(.735,.4975)),('fast_settling',fast,ORANGE,(.745,.5036))]:
    metric=check['cases'][name]['replay_objectives'][1]
    peak=int(np.argmax(y))
    axes[1].annotate(f'{metric:.2f}% overshoot',xy=(t[peak],y[peak]),xytext=xytext,fontsize=7.1,color=color,
      ha='center',va='center',arrowprops={'arrowstyle':'-','color':color,'lw':.55})
for label,ax in zip(('(a)','(b)'),axes):
    ax.text(.96,.10,label,transform=ax.transAxes,ha='right',va='bottom')
save_paper_figure(fig,OUTPUT/'selected_response',svg=True)
plt.close(fig)
