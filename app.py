import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import random
import time

def fmt_a(a):
    if a == 1: return ""
    if a == -1: return "-"
    return str(int(a)) if a == int(a) else str(a)

def fmt_num(n):
    return int(n) if n == int(n) else n

def generate_problem():
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
                 f"2. $y = a(x - h)^2 + k \\Rightarrow {py} = a({px} - ({h}))^2 + ({k})$\n"
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
                 f"2. $y = a(x - p)(x - q) \\Rightarrow {py} = a(0 - ({r1}))(0 - ({r2}))$\n"
                 f"3. ${py} = {fmt_num((-r1)*(-r2))}a \\Rightarrow a = {fmt_num(a)}$\n\n**${eq}$**")
        correct = ['Intercept']

    elif form == 'standard':
        # Select from our curated pairs to keep elimination clean
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
                 f"2. Sub $({px1_val}, {py1_val})$: ${py1_val} = a({px1_val})^2 + b({px1_val}) + {c} \\Rightarrow {a_coef_1}a {'+' if b_coef_1 > 0 else '-'} {abs(b_coef_1)}b = {fmt_num(Y1)}$ *(Eq. 1)*\n"
                 f"3. Sub $({px2_val}, {py2_val})$: ${py2_val} = a({px2_val})^2 + b({px2_val}) + {c} \\Rightarrow a {'+' if px2 > 0 else '-'} b = {fmt_num(Y2)}$ *(Eq. 2)*\n"
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
        
        steps = (f"**Both forms are equally efficient!**\n\n"
                 f"- **Vertex:** $(h,k)=({h},{fmt_num(k)})$, sub $({r2},0) \\Rightarrow {eq_v}$\n"
                 f"- **Intercept:** $p={r1}, q={r2}$, sub $({h},{fmt_num(k)}) \\Rightarrow {eq_i}$")
        correct = ['Vertex', 'Intercept']

    elif form == 'trick_y_vertex':
        k = random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
        f = lambda x: a * x**2 + k
        points.extend([(0, k), (2, f(2))])
        eq = f"y = {fmt_a(a)}x^2{' + ' + str(k) if k > 0 else ' - ' + str(abs(k))}"
        
        py = fmt_num(f(2))
        steps = (f"**Vertex Form (Y-Axis Shortcut)**\n\n1. Note: Y-intercept $(0, {k})$ IS the vertex.\n"
                 f"2. $y = ax^2 + {k} \\Rightarrow {py} = a(2)^2 + ({k})$\n"
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


# --- Streamlit UI ---
st.title("Quadratic Form Finder")
st.write("Which general form is most efficient for this graph?")
st.latex(r"") # Preloads KaTeX engine

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
