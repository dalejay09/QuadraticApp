# --- Dynamic Plotting Engine: TABLE IMAGE (For Web App Canvas) ---
def draw_table_image(x_vals, y_vals):
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    
    # CRITICAL FIX: Kill all default Matplotlib margins
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Shifted to the absolute left edge
    ax.text(0.05, 0.9, "x", fontsize=20, fontweight='bold', ha='center')
    ax.text(0.18, 0.9, "y", fontsize=20, fontweight='bold', ha='center')
    ax.plot([0.01, 0.22], [0.85, 0.85], color='black', lw=2)
    
    y_pos = 0.75
    for x, y in zip(x_vals, y_vals):
        ax.text(0.05, y_pos, str(fmt_num(x)), fontsize=16, ha='center', va='center')
        ax.text(0.18, y_pos, str(fmt_num(y)), fontsize=16, ha='center', va='center')
        y_pos -= 0.15
        
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    
    img = Image.open(buf).convert('RGBA').copy()
    return img
