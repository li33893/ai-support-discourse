"""
================================================================================
SCRIPT: 11_descriptive_figures.py
PURPOSE: Descriptive figures of the three codes by subreddit (pipeline stage XX)
================================================================================

WHAT THIS SCRIPT DOES:
    1. Draws a heatmap of usage intent × subreddit
    2. Draws two 100% stacked bar charts, one for timeframe and one for source
    3. Labels every cell and segment with both n and % within subreddit

FLOW:
    1. 03_HEAT MAP OF USAGE INTENT
       - crosstab intent × subreddit, normalised down each subreddit column
       - Rows ordered by corpus-wide intent frequency, fixed across figures
       - Each cell annotated "n · %", color encodes the column %
       -> heatmap_type_by_subreddit.png

    2. 04_STACKED BAR CHARTS FOR TIMEFRAME, SOURCE
       - crosstab subreddit × code, normalised across each subreddit row
       - Segments narrower than MIN_PCT are left unlabelled to avoid collisions
       - Label color switched by background luminance via text_color()
       -> stacked_timeframe_by_subreddit.png
       -> stacked_source_by_subreddit.png

OUTPUT FILES:
    heatmap_type_by_subreddit.png       Usage intent × subreddit, n and column %
    stacked_timeframe_by_subreddit.png  Timeframe mix within each subreddit
    stacked_source_by_subreddit.png     Source mix within each subreddit

================================================================================
"""

# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np
from matplotlib.colors import to_rgb
# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# input files
INPUT_FILE  = "posts_list_cleaned_llm_coded.csv"

# output files
TYPE_FILE      = "heatmap_type_by_subreddit.png"
TIMEFRAME_FILE = "stacked_timeframe_by_subreddit.png"
SOURCE_FILE    = "stacked_source_by_subreddit.png"

# 窄于这个百分比的段不写字，否则小段会糊成一团
MIN_PCT = 4.0

# 全局排版
plt.rcParams.update({
    "font.size": 10,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.titlesize": 12,
    "axes.titleweight": "semibold",
    "axes.titlelocation": "left",
    "axes.titlepad": 12,
    "axes.edgecolor": "#DDDDE3",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "xtick.color": "#6B6B76",
    "ytick.color": "#1F1F23",
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "legend.frameon": False,
})


# 深色底上的字改白色，否则看不清
def text_color(color):
    r, g, b = to_rgb(color)
    return "white" if (0.299 * r + 0.587 * g + 0.114 * b) < 0.55 else "#1F1F23"

# ________________________________________________________________________________

# MAIN WORKFLOW AREA

# ________________________________________________________________________________

def main():

    # 01_DIR PREPARATION
    # directories
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir    = os.path.join(current_dir, "..", "data")
    outputs_dir = os.path.join(current_dir, "..", "outputs")

    # input file paths
    input_file  = os.path.join(data_dir, INPUT_FILE)

    # output files path
    type_path      = os.path.join(outputs_dir, TYPE_FILE)
    timeframe_path = os.path.join(outputs_dir, TIMEFRAME_FILE)
    source_path    = os.path.join(outputs_dir, SOURCE_FILE)

    # 02_READ THE INPUTTED FILE
    input_df   = pd.read_csv(input_file)

    # 03_HEAT MAP OF USAGE INTENT
    counts = pd.crosstab(input_df["llm_usage_intent"], input_df["subreddit"])
    pct    = pd.crosstab(input_df["llm_usage_intent"], input_df["subreddit"], normalize="columns") * 100
    
    type_order = input_df["llm_usage_intent"].value_counts().index
    counts = counts.reindex(type_order)
    pct    = pct.reindex(type_order)

    labels = counts.astype(str) + "  ·  " + pct.round(0).astype(int).astype(str) + "%"

    fig, ax = plt.subplots(figsize=(9, 9))
    sns.heatmap(pct, annot=labels, fmt="", cmap="Purples", annot_kws={"size": 8}, ax=ax,
                linewidths=1.5, linecolor="white",
                cbar_kws={"shrink": 0.35, "aspect": 14, "label": "% within subreddit"})
    ax.set_title("Usage intent by subreddit: n (% within subreddit)")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.savefig(type_path, dpi=200, bbox_inches="tight")
    plt.close(fig)      

    # 04_STACKED BAR CHARTS FOR TIMEFRAME, SOURCE
    # timeframe
    tf_counts = pd.crosstab(
        input_df["subreddit"],
        input_df["llm_timeframe"]
    )

    tf_pct = tf_counts.div(tf_counts.sum(axis=1), axis=0) * 100

    tf_colors = ["#5F4B78", "#B07A8E", "#B8B8B8"]

    tf_ax = tf_pct.plot(
        kind="barh",
        stacked=True,
        color=tf_colors,
        width=0.68,
        edgecolor="white",
        linewidth=1.2,
        figsize=(10, 6)
    )
    
    for row, subreddit in enumerate(tf_pct.index):

        left = 0

        for col, category in enumerate(tf_pct.columns):

            p = tf_pct.loc[subreddit, category]
            n = tf_counts.loc[subreddit, category]

            if p >= MIN_PCT:

                tf_ax.text(
                    left + p / 2,
                    row,
                    f"{p:.1f}%\nn={n}",
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    color=text_color(tf_colors[col % len(tf_colors)])
                )

            left += p

    tf_ax.set_title("Timeframe by subreddit: % within subreddit")
    tf_ax.set_xlim(0, 100)
    tf_ax.set_xlabel("")
    tf_ax.set_ylabel("")
    tf_ax.invert_yaxis()

    tf_ax.legend(
        title="llm_timeframe",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5)
    )

    tf_fig = tf_ax.get_figure()

    tf_fig.savefig(
        timeframe_path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(tf_fig)

    # source
    src_counts = pd.crosstab(
        input_df["subreddit"],
        input_df["llm_source"]
    )

    src_pct = src_counts.div(src_counts.sum(axis=1), axis=0) * 100

    src_colors = [
        "#C06C84",  # rose
        "#8B5E83",  # mauve
        "#D98C6A",  # orange
        "#D8AE5E",  # mustard
        "#9DA65D",  # olive
        "#5E9B76",  # green
        "#4C9A96",  # teal
        "#4F84A6",  # blue
        "#5969A6",  # indigo
        "#8969B0",  # violet
        "#B18CB8",  # light purple
        "#8C7364",  # brown-grey
        "#B5B5B5"   # grey
    ]

    src_ax = src_pct.plot(
        kind="barh",
        stacked=True,
        color=src_colors,
        width=0.68,
        edgecolor="white",
        linewidth=1.2,
        figsize=(10, 6)
    )
    
    for row, subreddit in enumerate(src_pct.index):

        left = 0

        for col, category in enumerate(src_pct.columns):

            p = src_pct.loc[subreddit, category]
            n = src_counts.loc[subreddit, category]

            if p >= MIN_PCT:

                src_ax.text(
                    left + p / 2,
                    row,
                    f"{p:.1f}%\nn={n}",
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    color=text_color(src_colors[col % len(src_colors)])
                )

            left += p

    src_ax.set_title("Source by subreddit: % within subreddit")
    src_ax.set_xlim(0, 100)
    src_ax.set_xlabel("")
    src_ax.set_ylabel("")
    src_ax.invert_yaxis()

    src_ax.legend(
        title="llm_source",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5)
    )

    src_fig = src_ax.get_figure()

    src_fig.savefig(
        source_path,
        dpi=200,
        bbox_inches="tight"
    )


    plt.close(src_fig)
    

if __name__ == "__main__": 
    main()