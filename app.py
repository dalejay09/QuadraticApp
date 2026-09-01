import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import random
import time
import io
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages

def fmt_a(a):
    if a == 1: return ""
    if a == -1: return "-"
    return str(int(a)) if a == int(a) else str(a)

def fmt_num(n):
    return int(n) if n == int(n) else n

# --- Core Math Engine (Shared by UI and PDF) ---
def generate_math_data():
    forms = ['vertex', 'intercept', 'standard', 'equal_both', 'trick_y_vertex']
    weights = [6, 6, 6, 1, 1]
    form = random.choices(forms, weights=weights, k=1)[0]
    direction = random.choice([1, -1])
    
    a = random.choice([0.5, 1, 1.5, 2]) if direction == 1 else random.choice([-0.5, -1, -1.5, -2])
    points = []
    
    if form == 'vertex':
        h, k = random.randint(-4, 4), random.randint(-5, 5)
        f = lambda x: a * (x - h)**2 + k
        points.extend([(h, k), (h + 2, f(h + 2))])
        
        a_str = fmt_a(a)
        x_part = "x^2" if h == 0 else f"(x - {h})^2" if h > 0 else f"(x + {abs(h)})^2"
        k_part = "" if k == 0 else f" + {k}" if k > 0 else f" - {abs(k)}"
        eq = f"y = {a_str}{x_part}{k_part}"
        
        px, py = fmt_num(points[1][0]), fmt_num(points[1][1])
        steps = (f"**Vertex Form**\n\n1. Vertex $(h,k) = ({h}, {k})$. Anchor: $({px}, {py})$.\n"
                 f"2. $y = a(x - h)^2 + k$\n$\\quad \\Rightarrow {py} = a({px} - ({h}))^2 + ({k})$\n"
                 f"3. ${fmt_num(py - k)} = a({fmt_num((px - h)**2)}) \\Rightarrow a = {fmt_num(a)}$\n\n**${eq}$**")
        correct = ['Vertex']

    elif form == 'intercept':
        r1, r2 = random.sample([-4, -3, -2, -1, 1, 2, 3, 4], 2)
        while r1 == -r2: r1, r2 = random.sample([-4, -3, -2, -1, 1, 2, 3, 4], 2)
        f = lambda x: a * (x - r1) * (x - r2)
        points.extend([(r1, 0), (r2, 0), (0, f(0))])
        
        a_str = fmt_a(a)
        fmt_root = lambda r: "x" if r == 0 else f"(x - {r})" if r > 0 else f"(x + {abs(r)})"
        eq = f"y = {a_str}{fmt_root(r1)}{fmt_root(r2)}"
        
        py = fmt_num(points[2][1])
        steps = (f"**Intercept Form**\n\n1. Roots $p={r1}, q={r2}$. Y-Int: $(0, {py})$.\n"
                 f"2. $y = a(x - p)(x - q)$\n$\\quad \\Rightarrow {py} = a(0 - ({r1}))(0 - ({r2}))$\n"
                 f"3. ${py} = {fmt_num((-r1)*(-r2))}a \\Rightarrow a = {fmt_num(a)}$\n\n**${eq}$**")
        correct = ['Intercept']

    elif form == 'standard':
        px1 = random.choice([2, -2, 3, -3])
        px2 = -1 if px1 > 0 else 1
        
        b = random.choice([-3, -2, -1, 1, 2, 3]) 
        c = random.randint(-4, 4)
        f = lambda x: a * x**2 + b * x + c
        
        while f(px1) == 0 and f(px2) == 0:
            b = random.choice([-3, -2, -1, 1, 2, 3])
            c = random.randint(-4, 4)
            f = lambda x: a * x**2 + b * x + c
            
        points.extend([(0, c), (px1, f(px1)), (px2, f(px2))])
        
        a_str = fmt_a(a)
        t2 = "" if b == 0 else " + x" if b == 1 else " - x" if b == -1 else f" + {b}x" if b > 0 else f" - {abs(b)}x"
        t3 = "" if c == 0 else f" + {c}" if c > 0 else f" - {abs(c)}"
        eq_str = f"{a_str}x^2{t2}{t3}"
        eq = f"y = {eq_str[3:] if eq_str.startswith(' + ') else eq_str}"
        
        px1_val, py1_val = px1, fmt_num(f(px1))
        px2_val, py2_val = px2, fmt_num(f(px2))
        
        Y1 = py1_val - c
        Y2 = py2_val - c
        M = abs(px1)
        
        Y2_scaled = M * Y2
        sum_Y = Y1 + Y2_scaled
        sign_Y2_scaled = f"+ {fmt_num(Y2_scaled)}" if Y2_scaled >= 0 else f"- {fmt_num(abs(Y2_scaled))}"
        
        a_coef_1 = px1**2
        b_coef_1 = px1
        a_coef_scaled = M
        b_cancel_str = f"({b_coef_1}b - {abs(b_coef_1)}b)" if b_coef_1 > 0 else f"(-{abs(b_coef_1)}b + {abs(b_coef_1)}b)"
        a_sum = a_coef_1 + a_coef_scaled
        
        steps = (f"**Standard Form**\n\n"
                 f"1. Y-Int $(0, {c}) \\Rightarrow c = {c}$.\n"
                 f"2. Sub $({px1_val}, {py1_val})$: ${py1_val} = a({px1_val})^2 + b({px1_val}) + {c}$\n"
                 f"$\\quad \\Rightarrow {a_coef_1}a {'+' if b_coef_1 > 0 else '-'} {abs(b_coef_1)}b = {fmt_num(Y1)}$ *(Eq. 1)*\n"
                 f"3. Sub $({px2_val}, {py2_val})$: ${py2_val} = a({px2_val})^2 + b({px2_val}) + {c}$\n"
                 f"$\\quad \\Rightarrow a {'+' if px2 > 0 else '-'} b = {fmt_num(Y2)}$ *(Eq. 2)*\n"
                 f"4. Multiply Eq. 2 by {M}: ${a_coef_scaled}a {'-' if px2 < 0 else '+'} {M}b = {fmt_num(Y2_scaled)}$ *(Eq. 3)*\n"
                 f"5. Add Eq. 1 and Eq. 3 to eliminate $b$:\n"
                 f"$\\quad ({a_coef_1}a + {a_coef_scaled}a) + {b_cancel_str} = {fmt_num(Y1)} {sign_Y2_scaled}$\n"
                 f"$\\quad {a_sum}a = {fmt_num(sum_Y)} \\Rightarrow a = {fmt_num(a)}$\n"
                 f"6. Substitute $a = {fmt_num(a)}$ back into Eq. 2:\n"
                 f"$\\quad {fmt_num(a)} {'+' if px2 > 0 else '-'} b = {fmt_num(Y2)} \\Rightarrow b = {b}$\n\n"
                 f"**${eq}$**")
        correct = ['Standard']

    elif form == 'equal_both':
        h = random.randint(-3, 3)
        d = random.choice([1, 2, 3])
        r1, r2, k = h - d, h + d, -a * (d**2)
        f = lambda x: a * (x - h)**2 + k
        points.extend([(h, k), (r1, 0), (r2, 0)])
        
        eq_v = f"y = {fmt_a(a)}{'x^2' if h==0 else f'(x - {h})^2' if h>0 else f'(x + {abs(h)})^2'}{'' if k==0 else f' + {fmt_num(k)}' if k>0 else f' - {fmt_num(abs(k))}'}"
        fmt_root = lambda r: "x" if r == 0 else f"(x - {r})" if r > 0 else f"(x + {abs(r)})"
        eq_i = f"y = {fmt_a(a)}{fmt_root(r1)}{fmt_root(r2)}"
        eq = f"{eq_v}$\nOR ${eq_i}"
        
        steps = (f"**Both forms are equally efficient!**\n\n"
                 f"- **Vertex:** $(h,k)=({h},{fmt_num(k)})$, sub $({r2},0)$\n$\\quad \\Rightarrow {eq_v}$\n"
                 f"- **Intercept:** $p={r1}, q={r2}$, sub $({h},{fmt_num(k)})$\n$\\quad \\Rightarrow {eq_i}$")
        correct = ['Vertex', 'Intercept']

    elif form == 'trick_y_vertex':
        k = random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
        f = lambda x: a * x**2 + k
        points.extend([(0, k), (2, f(2))])
        eq = f"y = {fmt_a(a)}x^2{' + ' + str(k) if k > 0 else ' - ' + str(abs(k))}"
        
        py = fmt_num(f(2))
        steps = (f"**Vertex Form (Y-Axis Shortcut)**\n\n1. Note: Y-intercept $(0, {k})$ IS the vertex.\n"
                 f"2. $y = ax^2 + {k}$\n$\\quad \\Rightarrow {py} = a(2)^2 + ({k})$\n"
                 f"3. ${fmt_num(py - k)} = 4a \\Rightarrow a = {fmt_num(a)}$\n\n**${eq}$**")
        correct = ['Vertex']

    # Dynamic Scaling
    all_x, all_y = [p[0] for p in points] + [0], [p[1] for p in points] + [0]
    if form in ['intercept', 'equal_both']:
        vx = (r1 + r2) / 2 if form == 'intercept' else h
        all_x.append(vx); all_y.append(f(vx))
    elif form == 'standard':
        vx = -b / (2 * a)
        all_x.append(vx); all_y.append(f(vx))
        
    x_pad, y_pad = max(1.5, (max(all_x) - min(all_x)) * 0.2), max(1.5, (max(all_y) - min(all_y)) * 0.2)
    x_vals = np.linspace(min(all_x) - x_pad - 5, max(all_x) + x_pad + 5, 400)
    
    return points, f, all_x, all_y, x_pad, y_pad, x_vals, correct, steps, eq

def generate_problem():
    points, f, all_x, all_y, x_pad, y_pad, x_vals, correct, steps, eq = generate_math_data()
    
    def create_fig(show_labels_val):
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.plot(x_vals, f(x_vals), color='darkgreen', linewidth=2)
        for px, py in points:
            ax.plot(px, py, 'o', color='darkgreen', markersize=6)
            if show_labels_val:
                ax.annotate(f'({fmt_num(px)}, {fmt_num(py)})', (px, py),
                            textcoords="offset points", xytext=(4, 4),
                            ha='left', va='bottom', fontsize=10,
                            bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
            
        ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
        ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlim(min(all_x) - x_pad, max(all_x) + x_pad)
        ax.set_ylim(min(all_y) - y_pad, max(all_y) + y_pad)
        return fig

    return create_fig(False), create_fig(True), correct, steps

def create_pdf_bytes():
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        problems = [generate_math_data() for _ in range(20)]
        
        generic_forms = {
            'Vertex': r"Vertex: $y = a(x-h)^2 + k$",
            'Intercept': r"Intercept: $y = a(x-p)(x-q)$",
            'Standard': r"Standard: $y = ax^2 + bx + c$"
        }
        
        # --- Page 1: Unlabelled Graphs ---
        fig, axes = plt.subplots(5, 4, figsize=(8.27, 11.69))
        fig.subplots_adjust(wspace=0.1, hspace=0.55, top=0.92, bottom=0.05, left=0.05, right=0.95)
        fig.suptitle("Worksheet: Identify the Form", fontsize=16, fontweight='bold')
        
        for i, ax in enumerate(axes.flatten()):
            points, f, all_x, all_y, x_pad, y_pad, x_vals, correct, steps, eq = problems[i]
            
            ax.plot(x_vals, f(x_vals), color='darkgreen', linewidth=1.5)
            for px, py in points:
                ax.plot(px, py, 'o', color='darkgreen', markersize=3)
            
            ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
            ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_xlim(min(all_x) - x_pad, max(all_x) + x_pad)
            ax.set_ylim(min(all_y) - y_pad, max(all_y) + y_pad)
            ax.set_title(f"Q{i+1}", loc='left', fontsize=9, fontweight='bold', pad=3)
            ax.text(0.5, -0.15, "y = _________________", transform=ax.transAxes, ha='center', fontsize=10)
            
        pdf.savefig(fig)
        plt.close(fig)
        
        # --- Page 2: Answer Key 1 (Forms) ---
        fig_ans1, ax_ans1 = plt.subplots(figsize=(8.27, 11.69))
        ax_ans1.axis('off')
        ax_ans1.text(0.5, 0.95, "Answer Key: Equation Forms", fontsize=16, fontweight='bold', ha='center')
        
        for i in range(10):
            ans_left = "\nOR ".join([generic_forms[ans] for ans in problems[i][7]])
            ans_right = "\nOR ".join([generic_forms[ans] for ans in problems[i+10][7]])
            
            ax_ans1.text(0.05, 0.88 - (i*0.08), f"Q{i+1}: {ans_left}", fontsize=11, va='top')
            ax_ans1.text(0.55, 0.88 - (i*0.08), f"Q{i+11}: {ans_right}", fontsize=11, va='top')
            
        pdf.savefig(fig_ans1)
        plt.close(fig_ans1)

        # --- Page 3: Labeled Graphs ---
        fig2, axes2 = plt.subplots(5, 4, figsize=(8.27, 11.69))
        fig2.subplots_adjust(wspace=0.1, hspace=0.55, top=0.92, bottom=0.05, left=0.05, right=0.95)
        fig2.suptitle("Worksheet: Labeled Coordinates", fontsize=16, fontweight='bold')
        
        for i, ax in enumerate(axes2.flatten()):
            points, f, all_x, all_y, x_pad, y_pad, x_vals, correct, steps, eq = problems[i]
            
            ax.plot(x_vals, f(x_vals), color='darkgreen', linewidth=1.5)
            for px, py in points:
                ax.plot(px, py, 'o', color='darkgreen', markersize=3)
                ax.annotate(f'({fmt_num(px)}, {fmt_num(py)})', (px, py),
                            textcoords="offset points", xytext=(3, 3),
                            ha='left', va='bottom', fontsize=5,
                            bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.7))
                
            ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
            ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_xlim(min(all_x) - x_pad, max(all_x) + x_pad)
            ax.set_ylim(min(all_y) - y_pad, max(all_y) + y_pad)
            ax.set_title(f"Q{i+1}", loc='left', fontsize=9, fontweight='bold', pad=3)
            ax.text(0.5, -0.15, "y = _________________", transform=ax.transAxes, ha='center', fontsize=10)
            
        pdf.savefig(fig2)
        plt.close(fig2)

        # --- Page 4: Answer Key 2 (Equations) ---
        fig_ans2, ax_ans2 = plt.subplots(figsize=(8.27, 11.69))
        ax_ans2.axis('off')
        ax_ans2.text(0.5, 0.95, "Answer Key: Solved Equations", fontsize=16, fontweight='bold', ha='center')
        
        for i in range(10):
            ax_ans2.text(0.05, 0.88 - (i*0.08), f"Q{i+1}: ${problems[i][9]}$", fontsize=11, va='top')
            ax_ans2.text(0.55, 0.88 - (i*0.08), f"Q{i+11}: ${problems[i+10][9]}$", fontsize=11, va='top')
            
        pdf.savefig(fig_ans2)
        plt.close(fig_ans2)

        # --- Appendix: Dynamic Pagination Layout ---
        app_pages = []
        current_page_items = []
        current_col = 0
        current_slot = 0
        
        for i, prob in enumerate(problems):
            is_standard = 'Standard' in prob[7]
            slots_needed = 2 if is_standard else 1
            
            if current_slot + slots_needed > 4:
                current_col += 1
                current_slot = 0
                
            if current_col > 1:
                app_pages.append(current_page_items)
                current_page_items = []
                current_col = 0
                current_slot = 0
                
            current_page_items.append({'idx': i, 'prob': prob, 'col': current_col, 'slot': current_slot})
            current_slot += slots_needed
            
        if current_page_items:
            app_pages.append(current_page_items)
            
        total_app_pages = len(app_pages)
        
        for page_idx, page_items in enumerate(app_pages):
            fig_app, ax_app = plt.subplots(figsize=(8.27, 11.69))
            ax_app.axis('off')
            ax_app.text(0.5, 0.96, f"Appendix: Step-by-Step Solutions (Page {page_idx+1}/{total_app_pages})", fontsize=14, fontweight='bold', ha='center')
            
            for item in page_items:
                q_num = item['idx']
                prob_data = item['prob']
                col = item['col']
                slot = item['slot']
                
                x_pos = 0.04 if col == 0 else 0.52
                y_pos = 0.88 - (slot * 0.22)
                
                steps_clean = prob_data[8].replace("**", "")
                
                ax_app.text(x_pos, y_pos, f"Q{q_num+1}:\n{steps_clean}", fontsize=8.5, va='top')
                
            pdf.savefig(fig_app)
            plt.close(fig_app)
        
    return buffer.getvalue()

# --- Streamlit UI ---

# 1. PDF Controls
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None
    
if st.session_state.pdf_bytes is None:
    if st.button("📄 Prepare PDF Worksheet", use_container_width=True):
        with st.spinner("Compiling dynamic master PDF... (~10s)"):
            st.session_state.pdf_bytes = create_pdf_bytes()
        st.rerun()
else:
    col_dl, col_rs = st.columns(2)
    with col_dl:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="⬇️ Download Worksheet",
            data=st.session_state.pdf_bytes,
            file_name=f"Quadratic_Master_Worksheet_{current_time}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    with col_rs:
        if st.button("Reset PDF", use_container_width=True):
            st.session_state.pdf_bytes = None
            st.rerun()

# 2. Main App Content
st.title("Quadratic Form Finder")
st.write("Which general form is most efficient for this graph?")
st.latex(r"") 

if 'generating' not in st.session_state:
    st.session_state.generating = True

col_toggle1, col_toggle2 = st.columns(2)
with col_toggle1:
    show_labels = st.toggle("Show Coordinate Labels", value=False)
with col_toggle2:
    show_equations = st.toggle("Show General Equations", value=False)

if st.session_state.generating:
    st.info("Drawing next parabola... please wait.")
    st.session_state.fig_unlab, st.session_state.fig_lab, st.session_state.correct, st.session_state.steps = generate_problem()
    st.session_state.answered = False
    st.session_state.feedback = ""
    st.session_state.generating = False
    st.rerun()
    
else:
    if show_labels:
        st.pyplot(st.session_state.fig_lab)
    else:
        st.pyplot(st.session_state.fig_unlab)

    if not st.session_state.answered:
        c1, c2, c3 = st.columns(3)
        
        def check_ans(guess):
            if guess in st.session_state.correct:
                st.session_state.answered = True
                st.session_state.feedback = "✅ Correct!"
            else:
                st.session_state.feedback = "❌ Try again! Look closely at the points."

        btn_vertex = "y = a(x - h)² + k" if show_equations else "Vertex"
        btn_intercept = "y = a(x - p)(x - q)" if show_equations else "Intercept"
        btn_standard = "y = ax² + bx + c" if show_equations else "Standard"

        c1.button(btn_vertex, on_click=check_ans, args=("Vertex",), use_container_width=True)
        c2.button(btn_intercept, on_click=check_ans, args=("Intercept",), use_container_width=True)
        c3.button(btn_standard, on_click=check_ans, args=("Standard",), use_container_width=True)

    if st.session_state.feedback:
        if "Correct" in st.session_state.feedback: 
            st.success(st.session_state.feedback)
        else: 
            st.error(st.session_state.feedback)

    if st.session_state.answered:
        st.info(st.session_state.steps)
        if st.button("Next Parabola", use_container_width=True):
            st.session_state.generating = True
            st.rerun()
