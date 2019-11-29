import numpy as np

def figsize(scale, ratio=(np.sqrt(5.0)-1.0)/2.0):
    fig_width_pt = 455.8843                         # Get this from LaTeX using \the\textwidth
    inches_per_pt = 1.0/72.27                       # Convert pt to inch
    fig_width = fig_width_pt*inches_per_pt*scale    # width in inches
    fig_height = fig_width*ratio              # height in inches
    fig_size = [fig_width,fig_height]
    return fig_size
