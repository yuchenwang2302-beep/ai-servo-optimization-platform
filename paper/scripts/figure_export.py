"""Save paper figures without optional software/author/time metadata."""
from pathlib import Path

def save_paper_figure(fig, stem, svg=False):
    stem=Path(stem)
    fig.savefig(stem.with_suffix('.pdf'),metadata={k:None for k in
        ('Title','Author','Subject','Keywords','Creator','Producer','CreationDate','ModDate','Trapped')})
    fig.savefig(stem.with_suffix('.png'),dpi=400,metadata={'Software':None})
    if svg:
        fig.savefig(stem.with_suffix('.svg'),metadata={'Creator':None,'Date':None})
