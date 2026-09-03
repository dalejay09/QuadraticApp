import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import random
import io
import re
from PIL import Image
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
from google import genai

# --- Formatting Helpers ---
def fmt_a(a):
    if a == 1: return ""
    if a == -1: return "-"
    return str(int(a)) if a == int(a) else str(a)

def fmt_m(m):
    if m == 1: return ""
    if m == -1: return "-"
    return str(int(m)) if m == int(m) else str(m)

def fmt_num(n):
    return int(n) if n == int(n) else n

# --- Core Math Engine: QUADRATICS ---
def generate_quadratic_data():
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

# --- Core Math Engine: LINEAR ---
def generate_linear_data():
    scenario = random.choice(['y_int', 'x_int', 'random', 'point_grad'])
    m = random.choice([0.5, 1, 1.5, 2, 3, -0.5, -1, -1.5, -2, -3])
    
    if scenario == 'y_int':
        c = random.randint(-5, 5)
        x1, y1 = 0, c
        valid_x2 = [x for x in range(-5, 6) if x != 0 and (m * x).is_integer()]
        x2 = random.choice(valid_x2)
        y2 = m * x2 + c
        points = [(x1, y1), (x2, y2)]
        
    elif scenario == 'x_int':
        x1 = random.choice([x for x in range(-5, 6) if x != 0])
        y1 = 0
        c = -m * x1
        valid_x2 = [x for x in range(-5, 6) if x != x1 and x != 0 and (m * x + c).is_integer()]
        if not valid_x2: 
            valid_x2 = [x1 + 2 if (m * (x1 + 2)).is_integer() else x1 + 1]
        x2 = random.choice(valid_x2)
        y2 = m * x2 + c
        points = [(x1, y1), (x2, y2)]
        
    elif scenario == 'random':
        c = random.randint(-5, 5)
        valid_xs = [x for x in range(-6, 7) if x != 0 and (m * x + c) != 0 and (m * x + c).is_integer()]
        if len(valid_xs) < 2:
            x1, x2 = 2, 4
            y1, y2 = m * x1 + c, m * x2 + c
        else:
            x1, x2 = random.sample(valid_xs, 2)
        y1, y2 = m * x1 + c, m * x2 + c
        points = [(x1, y1), (x2, y2)]
        
    elif scenario == 'point_grad':
        c = random.randint(-5, 5)
        x1 = random.choice([x for x in range(-5, 6) if x != 0 and (m * x + c).is_integer()])
        y1 = m * x1 + c
        points = [(x1, y1)]

    # Sort points for visual consistency (left to right)
    if len(points) == 2 and points[0][0] > points[1][0]:
        points[0], points[1] = points[1], points[0]
        x1, y1 = points[0]
        x2, y2 = points[1]

    f = lambda x: m * x + c
    m_str = fmt_m(m)
    c_str = "" if c == 0 else f" + {fmt_num(c)}" if c > 0 else f" - {fmt_num(abs(c))}"
    eq = f"y = {m_str}x{c_str}"
    
    # Step-by-step logic
    if scenario == 'point_grad':
        steps = (f"**Straight Line Equation**\n\n"
                 f"1. Gradient $m = {fmt_num(m)}$ (given).\n"
                 f"2. Sub point $({fmt_num(x1)}, {fmt_num(y1)})$: $y = mx + c$\n"
                 f"$\\quad \\Rightarrow {fmt_num(y1)} = {fmt_num(m)}({fmt_num(x1)}) + c$\n"
                 f"3. ${fmt_num(y1)} = {fmt_num(m * x1)} + c \\Rightarrow c = {fmt_num(c)}$\n\n"
                 f"**${eq}$**")
    else:
        dy, dx = y2 - y1, x2 - x1
        steps = (f"**Straight Line Equation**\n\n"
                 f"1. Gradient $m = \\frac{{{fmt_num(y2)} - ({fmt_num(y1)})}}{{{fmt_num(x2)} - ({fmt_num(x1)})}} = \\frac{{{fmt_num(dy)}}}{{{fmt_num(dx)}}} = {fmt_num(m)}$\n"
                 f"2. Sub point $({fmt_num(x1)}, {fmt_num(y1)})$: $y = mx + c$\n"
                 f"$\\quad \\Rightarrow {fmt_num(y1)} = {fmt_num(m)}({fmt_num(x1)}) + c$\n"
                 f"3. ${fmt_num(y1)} = {fmt_num(m * x1)} + c \\Rightarrow c = {fmt_num(c)}$\n\n"
                 f"**${eq}$**")

    all_x = [p[0] for p in points] + [0]
    all_y = [p[1] for p in points] + [c]
    x_pad, y_pad = max(2.0, (max(all_x) - min(all_x)) * 0.2), max(2.0, (max(all_y) - min(all_y)) * 0.2)
    x_vals = np.linspace(min(all_x) - x_pad - 2, max(all_x) + x_pad + 2, 400)
    
    # Exhaustive Feature Identification Logic
    all_features = [
        "positive gradient", "negative gradient", 
        "x-intercept given", "y-intercept given", 
        "gradient given", "two points given", "only one point given"
    ]
    true_features = []
    
    if m > 0: true_features.append("positive gradient")
    if m < 0: true_features.append("negative gradient")
    
    if scenario == 'point_grad':
        true_features.extend(["gradient given", "only one point given"])
    else:
        true_features.append("two points given")
        
    for px, py in points:
        if px == 0 and "y-intercept given" not in true_features:
            true_features.append("y-intercept given")
        if py == 0 and "x-intercept given" not in true_features:
            true_features.append("x-intercept given")
            
    false_features = [feat for feat in all_features if feat not in true_features]
    btn_choices = [random.choice(true_features)] + random.sample(false_features, 2)
    random.shuffle(btn_choices)
    
    return points, f, all_x, all_y, x_pad, y_pad, x_vals, true_features, steps, eq, btn_choices, scenario, m

# --- Dynamic Plotting Engine: QUADRATICS ---
def draw_parabola_fig(math_data, show_labels_val, show_grid_val):
    points, f, all_x, all_y, x_pad, y_pad, x_vals, correct, steps, eq = math_data
    fig, ax = plt.subplots(figsize=(4, 4))
    
    if show_grid_val:
        ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.set_axisbelow(True)
        ax.set_xticklabels([]); ax.set_yticklabels()
        ax.tick_params(which='both', length=0)
    else:
        ax.set_xticks([]); ax.set_yticks([])

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
    ax.set_xlim(min(all_x) - x_pad, max(all_x) + x_pad)
    ax.set_ylim(min(all_y) - y_pad, max(all_y) + y_pad)
    return fig

# --- Dynamic Plotting Engine: LINEAR ---
def draw_line_fig(math_data, show_labels_val, show_grid_val):
    points, f, all_x, all_y, x_pad, y_pad, x_vals, true_features, steps, eq, btn_choices, scenario, m = math_data
    fig, ax = plt.subplots(figsize=(4, 4))
    
    x_min, x_max = min(all_x) - x_pad - 2, max(all_x) + x_pad + 2
    y_min, y_max = min(all_y) - y_pad, max(all_y) + y_pad
    
    if show_grid_val:
        ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.set_axisbelow(True)
        ax.set_xticklabels([]); ax.set_yticklabels([])
        ax.tick_params(which='both', length=0)
    else:
        ax.set_xticks([]); ax.set_yticks([])

    ax.plot(x_vals, f(x_vals), color='darkblue', linewidth=2)
    for px, py in points:
        ax.plot(px, py, 'o', color='darkblue', markersize=6)
        if show_labels_val:
            ax.annotate(f'({fmt_num(px)}, {fmt_num(py)})', (px, py),
                        textcoords="offset points", xytext=(4, 4),
                        ha='left', va='bottom', fontsize=10,
                        bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
        
    if x_min <= 0 <= x_max: ax.spines['left'].set_position('zero')
    else: ax.spines['left'].set_color('none')
    
    if y_min <= 0 <= y_max: ax.spines['bottom'].set_position('zero')
    else: ax.spines['bottom'].set_color('none')
        
    ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
    ax.set_xlim(x_min, x_max); ax.set_ylim(y_min, y_max)
    
    if scenario == 'point_grad':
        x_span, y_span = x_max - x_min, y_max - y_min
        visual_m = m * (x_span / y_span)
        angle = np.degrees(np.arctan(visual_m))
        x_center = (x_min + x_max) / 2
        y_center = f(x_center)
        ax.text(x_center, y_center + y_span*0.02, f"gradient = {fmt_num(m)}", 
                rotation=angle, rotation_mode='anchor', ha='center', va='bottom', 
                color='darkblue', fontsize=10, 
                bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))

    return fig

# --- Unified PDF Generation Engine ---
def create_pdf_bytes(mode, show_grid_pdf):
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        
        # --- QUADRATIC SECTION ---
        if mode in ["Quadratic", "Both"]:
            problems_q = [generate_quadratic_data() for _ in range(20)]
            generic_forms = {
                'Vertex': r"Vertex: $y = a(x-h)^2 + k$",
                'Intercept': r"Intercept: $y = a(x-p)(x-q)$",
                'Standard': r"Standard: $y = ax^2 + bx + c$"
            }
            
            # Page 1: Unlabelled Graphs
            fig, axes = plt.subplots(5, 4, figsize=(8.27, 11.69))
            fig.subplots_adjust(wspace=0.1, hspace=0.55, top=0.92, bottom=0.05, left=0.05, right=0.95)
            fig.suptitle("Quadratic Worksheet: Identify the Form", fontsize=16, fontweight='bold')
            for i, ax in enumerate(axes.flatten()):
                points, f, all_x, all_y, x_pad, y_pad, x_vals, correct, steps, eq = problems_q[i]
                if show_grid_pdf:
                    ax.xaxis.set_major_locator(ticker.MultipleLocator(1)); ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
                    ax.grid(True, linestyle=':', alpha=0.6); ax.set_axisbelow(True)
                    ax.set_xticklabels([]); ax.set_yticklabels([]); ax.tick_params(which='both', length=0)
                else: ax.set_xticks([]); ax.set_yticks([])
                ax.plot(x_vals, f(x_vals), color='darkgreen', linewidth=1.5)
                for px, py in points: ax.plot(px, py, 'o', color='darkgreen', markersize=3)
                ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
                ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
                ax.set_xlim(min(all_x) - x_pad, max(all_x) + x_pad); ax.set_ylim(min(all_y) - y_pad, max(all_y) + y_pad)
                ax.set_title(f"Q{i+1}", loc='left', fontsize=9, fontweight='bold', pad=3)
                ax.text(0.5, -0.15, "y = _________________", transform=ax.transAxes, ha='center', fontsize=10)
            pdf.savefig(fig); plt.close(fig)
            
            # Page 2: Answer Key 1
            fig_ans1, ax_ans1 = plt.subplots(figsize=(8.27, 11.69))
            ax_ans1.axis('off')
            ax_ans1.text(0.5, 0.95, "Quadratic Answer Key: Equation Forms", fontsize=16, fontweight='bold', ha='center')
            for i in range(10):
                ans_left = "\nOR ".join([generic_forms[ans] for ans in problems_q[i][7]])
                ans_right = "\nOR ".join([generic_forms[ans] for ans in problems_q[i+10][7]])
                ax_ans1.text(0.05, 0.88 - (i*0.08), f"Q{i+1}: {ans_left}", fontsize=11, va='top')
                ax_ans1.text(0.55, 0.88 - (i*0.08), f"Q{i+11}: {ans_right}", fontsize=11, va='top')
            pdf.savefig(fig_ans1); plt.close(fig_ans1)

            # Page 3: Labeled Graphs
            fig2, axes2 = plt.subplots(5, 4, figsize=(8.27, 11.69))
            fig2.subplots_adjust(wspace=0.1, hspace=0.55, top=0.92, bottom=0.05, left=0.05, right=0.95)
            fig2.suptitle("Quadratic Worksheet: Labeled Coordinates", fontsize=16, fontweight='bold')
            for i, ax in enumerate(axes2.flatten()):
                points, f, all_x, all_y, x_pad, y_pad, x_vals, correct, steps, eq = problems_q[i]
                if show_grid_pdf:
                    ax.xaxis.set_major_locator(ticker.MultipleLocator(1)); ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
                    ax.grid(True, linestyle=':', alpha=0.6); ax.set_axisbelow(True)
                    ax.set_xticklabels([]); ax.set_yticklabels([]); ax.tick_params(which='both', length=0)
                else: ax.set_xticks([]); ax.set_yticks([])
                ax.plot(x_vals, f(x_vals), color='darkgreen', linewidth=1.5)
                for px, py in points:
                    ax.plot(px, py, 'o', color='darkgreen', markersize=3)
                    ax.annotate(f'({fmt_num(px)}, {fmt_num(py)})', (px, py), textcoords="offset points", xytext=(3, 3), ha='left', va='bottom', fontsize=5, bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.7))
                ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
                ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
                ax.set_xlim(min(all_x) - x_pad, max(all_x) + x_pad); ax.set_ylim(min(all_y) - y_pad, max(all_y) + y_pad)
                ax.set_title(f"Q{i+1}", loc='left', fontsize=9, fontweight='bold', pad=3)
                ax.text(0.5, -0.15, "y = _________________", transform=ax.transAxes, ha='center', fontsize=10)
            pdf.savefig(fig2); plt.close(fig2)

            # Page 4: Answer Key 2
            fig_ans2, ax_ans2 = plt.subplots(figsize=(8.27, 11.69))
            ax_ans2.axis('off')
            ax_ans2.text(0.5, 0.95, "Quadratic Answer Key: Solved Equations", fontsize=16, fontweight='bold', ha='center')
            for i in range(10):
                ax_ans2.text(0.05, 0.88 - (i*0.08), f"Q{i+1}: ${problems_q[i][9]}$", fontsize=11, va='top')
                ax_ans2.text(0.55, 0.88 - (i*0.08), f"Q{i+11}: ${problems_q[i+10][9]}$", fontsize=11, va='top')
            pdf.savefig(fig_ans2); plt.close(fig_ans2)

            # Appendix Q: Dynamic Pagination Layout
            app_pages = []
            current_page_items = []; current_col = 0; current_slot = 0
            for i, prob in enumerate(problems_q):
                is_standard = 'Standard' in prob[7]
                slots_needed = 2 if is_standard else 1
                if current_slot + slots_needed > 4:
                    current_col += 1; current_slot = 0
                if current_col > 1:
                    app_pages.append(current_page_items)
                    current_page_items = []; current_col = 0; current_slot = 0
                current_page_items.append({'idx': i, 'prob': prob, 'col': current_col, 'slot': current_slot})
                current_slot += slots_needed
            if current_page_items: app_pages.append(current_page_items)
            total_app_pages = len(app_pages)
            
            for page_idx, page_items in enumerate(app_pages):
                fig_app, ax_app = plt.subplots(figsize=(8.27, 11.69))
                ax_app.axis('off')
                ax_app.text(0.5, 0.96, f"Quadratic Appendix: Step-by-Step Solutions (Page {page_idx+1}/{total_app_pages})", fontsize=14, fontweight='bold', ha='center')
                for item in page_items:
                    q_num = item['idx']; prob_data = item['prob']; col = item['col']; slot = item['slot']
                    x_pos = 0.04 if col == 0 else 0.52
                    y_pos = 0.88 - (slot * 0.22)
                    steps_clean = prob_data[8].replace("**", "")
                    ax_app.text(x_pos, y_pos, f"Q{q_num+1}:\n{steps_clean}", fontsize=8.5, va='top')
                pdf.savefig(fig_app); plt.close(fig_app)


        # --- LINEAR SECTION ---
        if mode in ["Linear", "Both"]:
            problems_l = [generate_linear_data() for _ in range(20)]
            
            # Page 1: Labeled Graphs
            fig3, axes3 = plt.subplots(5, 4, figsize=(8.27, 11.69))
            fig3.subplots_adjust(wspace=0.1, hspace=0.55, top=0.92, bottom=0.05, left=0.05, right=0.95)
            fig3.suptitle("Linear Worksheet: Find the Equation", fontsize=16, fontweight='bold')
            for i, ax in enumerate(axes3.flatten()):
                points, f, all_x, all_y, x_pad, y_pad, x_vals, true_features, steps, eq, btn_choices, scenario, m_val = problems_l[i]
                x_min, x_max = min(all_x) - x_pad - 2, max(all_x) + x_pad + 2
                y_min, y_max = min(all_y) - y_pad, max(all_y) + y_pad
                
                if show_grid_pdf:
                    ax.xaxis.set_major_locator(ticker.MultipleLocator(1)); ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
                    ax.grid(True, linestyle=':', alpha=0.6); ax.set_axisbelow(True)
                    ax.set_xticklabels([]); ax.set_yticklabels([]); ax.tick_params(which='both', length=0)
                else: ax.set_xticks([]); ax.set_yticks([])
                ax.plot(x_vals, f(x_vals), color='darkblue', linewidth=1.5)
                for px, py in points:
                    ax.plot(px, py, 'o', color='darkblue', markersize=3)
                    ax.annotate(f'({fmt_num(px)}, {fmt_num(py)})', (px, py), textcoords="offset points", xytext=(3, 3), ha='left', va='bottom', fontsize=5, bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.7))
                    
                if x_min <= 0 <= x_max: ax.spines['left'].set_position('zero')
                else: ax.spines['left'].set_color('none')
                if y_min <= 0 <= y_max: ax.spines['bottom'].set_position('zero')
                else: ax.spines['bottom'].set_color('none')
                ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
                ax.set_xlim(x_min, x_max); ax.set_ylim(y_min, y_max)
                
                if scenario == 'point_grad':
                    x_span, y_span = x_max - x_min, y_max - y_min
                    visual_m = m_val * (x_span / y_span) * 1.13
                    angle = np.degrees(np.arctan(visual_m))
                    x_center = (x_min + x_max) / 2; y_center = f(x_center)
                    ax.text(x_center, y_center + y_span*0.02, f"m = {fmt_num(m_val)}", rotation=angle, rotation_mode='anchor', ha='center', va='bottom', color='darkblue', fontsize=7, bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.85))
                ax.set_title(f"Q{i+1}", loc='left', fontsize=9, fontweight='bold', pad=3)
                ax.text(0.5, -0.15, "y = _________________", transform=ax.transAxes, ha='center', fontsize=10)
            pdf.savefig(fig3); plt.close(fig3)

            # Appendix L: Solutions
            app_pages_l = []; current_page_items_l = []; current_col_l = 0; current_slot_l = 0
            for i, prob in enumerate(problems_l):
                if current_slot_l >= 4:
                    current_col_l += 1; current_slot_l = 0
                if current_col_l > 1:
                    app_pages_l.append(current_page_items_l)
                    current_page_items_l = []; current_col_l = 0; current_slot_l = 0
                current_page_items_l.append({'idx': i, 'prob': prob, 'col': current_col_l, 'slot': current_slot_l})
                current_slot_l += 1
            if current_page_items_l: app_pages_l.append(current_page_items_l)
            total_app_pages_l = len(app_pages_l)
            
            for page_idx, page_items in enumerate(app_pages_l):
                fig_app, ax_app = plt.subplots(figsize=(8.27, 11.69))
                ax_app.axis('off')
                ax_app.text(0.5, 0.96, f"Linear Appendix: Solutions (Page {page_idx+1}/{total_app_pages_l})", fontsize=14, fontweight='bold', ha='center')
                for item in page_items:
                    q_num = item['idx']; prob_data = item['prob']; col = item['col']; slot = item['slot']
                    x_pos = 0.04 if col == 0 else 0.52
                    y_pos = 0.88 - (slot * 0.22)
                    steps_clean = prob_data[8].replace("**", "")
                    ax_app.text(x_pos, y_pos, f"Q{q_num+1}:\n{steps_clean}", fontsize=9, va='top')
                pdf.savefig(fig_app); plt.close(fig_app)
        
    return buffer.getvalue()


# --- Streamlit UI Initializations ---
def handle_settings_change():
    st.session_state.pdf_bytes = None
    st.session_state.generating = True

if 'generating' not in st.session_state:
    st.session_state.generating = True
if 'identified_correctly' not in st.session_state:
    st.session_state.identified_correctly = False
if 'ai_feedback' not in st.session_state:
    st.session_state.ai_feedback = ""
if 'ai_is_correct' not in st.session_state:
    st.session_state.ai_is_correct = False
if 'show_camera' not in st.session_state:
    st.session_state.show_camera = False

st.title("Graphing Equation Finder")

# 1. Flattened PDF Controls & Settings 
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None
    
if st.session_state.pdf_bytes is None:
    col_pdf, col_set = st.columns([5, 1])
    with col_pdf:
        if st.button("📄 Prepare Worksheet", use_container_width=True):
            with st.spinner("Compiling Master PDF..."):
                st.session_state.pdf_bytes = create_pdf_bytes(st.session_state.get('func_mode', 'Both'), st.session_state.get('show_grid', False))
            st.rerun()
    with col_set:
        with st.popover("⚙️", use_container_width=True):
            st.write("**Settings**")
            st.radio("Function Mode", ["Quadratic", "Linear", "Both"], key="func_mode", on_change=handle_settings_change)
            st.toggle("Show Grid Lines", key="show_grid", on_change=handle_settings_change)
            st.toggle("Mark My Working", key="mark_working")
else:
    col_dl, col_rs, col_set = st.columns([3, 3, 1])
    with col_dl:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="⬇️ Download",
            data=st.session_state.pdf_bytes,
            file_name=f"Math_Master_Worksheet_{current_time}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    with col_rs:
        if st.button("Reset PDF", use_container_width=True):
            st.session_state.pdf_bytes = None
            st.rerun()
    with col_set:
        with st.popover("⚙️", use_container_width=True):
            st.write("**Settings**")
            st.radio("Function Mode", ["Quadratic", "Linear", "Both"], key="func_mode", on_change=handle_settings_change)
            st.toggle("Show Grid Lines", key="show_grid", on_change=handle_settings_change)
            st.toggle("Mark My Working", key="mark_working")

# 2. Main App Content 
col_toggle1, col_toggle2 = st.columns(2)
with col_toggle1:
    show_labels = st.toggle("Coordinates", value=False)
with col_toggle2:
    show_equations = st.toggle("Equation Buttons", value=False) 

st.latex(r"") 

# Generate New Math Data
if st.session_state.generating:
    st.info("Drawing next graph... please wait.")
    
    # Mode Router
    mode = st.session_state.get('func_mode', 'Both')
    prob_type = mode
    if mode == 'Both':
        prob_type = random.choice(['Quadratic', 'Linear'])
        
    st.session_state.current_prob_type = prob_type
    
    if prob_type == 'Quadratic':
        st.session_state.math_data = generate_quadratic_data()
    else:
        st.session_state.math_data = generate_linear_data()
        
    st.session_state.identified_correctly = False
    st.session_state.feedback = ""
    st.session_state.ai_feedback = ""
    st.session_state.ai_is_correct = False
    st.session_state.show_camera = False
    st.session_state.generating = False
    st.rerun()
    
else:
    prob_type = st.session_state.current_prob_type
    
    # Dynamic Heading
    if prob_type == 'Quadratic':
        st.write("Which general form is most efficient for this parabola?")
        fig = draw_parabola_fig(st.session_state.math_data, show_labels, st.session_state.get("show_grid", False))
        correct_features = st.session_state.math_data[7]
        steps = st.session_state.math_data[8]
        target_eq = st.session_state.math_data[9]
    else:
        st.write("Find the linear equation $y = mx + c$ for this graph.")
        fig = draw_line_fig(st.session_state.math_data, show_labels, st.session_state.get("show_grid", False))
        correct_features = st.session_state.math_data[7]
        steps = st.session_state.math_data[8]
        target_eq = st.session_state.math_data[9]
        btn_choices = st.session_state.math_data[10]

    st.pyplot(fig)

    # STAGE 1: Identifying Graph Features / Form
    if not st.session_state.identified_correctly:
        c1, c2, c3 = st.columns(3)
        
        def check_feat(guess):
            if guess in correct_features:
                st.session_state.identified_correctly = True
                st.session_state.feedback = f"✅ Correct! ({guess})"
            else:
                st.session_state.feedback = "❌ Try again! Look closely at the graph."

        if prob_type == 'Quadratic':
            btn_v = "y = a(x - h)² + k" if show_equations else "Vertex"
            btn_i = "y = a(x - p)(x - q)" if show_equations else "Intercept"
            btn_s = "y = ax² + bx + c" if show_equations else "Standard"
            c1.button(btn_v, on_click=check_feat, args=("Vertex",), use_container_width=True)
            c2.button(btn_i, on_click=check_feat, args=("Intercept",), use_container_width=True)
            c3.button(btn_s, on_click=check_feat, args=("Standard",), use_container_width=True)
        else:
            st.write("**Which of these features applies to the graph?**")
            c1.button(btn_choices[0], on_click=check_feat, args=(btn_choices[0],), use_container_width=True, key="lb1")
            c2.button(btn_choices[1], on_click=check_feat, args=(btn_choices[1],), use_container_width=True, key="lb2")
            c3.button(btn_choices[2], on_click=check_feat, args=(btn_choices[2],), use_container_width=True, key="lb3")

        if st.session_state.feedback:
            if "Correct" not in st.session_state.feedback: 
                st.error(st.session_state.feedback)

    # STAGE 2: Correct Feature Identified
    else:
        st.success(st.session_state.feedback)
        
        if not st.session_state.get('mark_working', False):
            st.info(steps)
            if st.button("Next Graph", use_container_width=True):
                st.session_state.generating = True
                st.rerun()
                
        else:
            if st.session_state.ai_is_correct:
                if st.session_state.ai_feedback:
                    st.success(f"🎉 **AI Marker:** {st.session_state.ai_feedback}")
                st.info(steps)
                if st.button("Next Graph", use_container_width=True):
                    st.session_state.generating = True
                    st.rerun()
                    
            else:
                if not st.session_state.show_camera:
                    st.write("Ready to solve it? Work it out on paper first.")
                    col_mk, col_sk = st.columns(2)
                    with col_mk:
                        if st.button("📸 Mark My Working", use_container_width=True, type="primary"):
                            st.session_state.show_camera = True
                            st.rerun()
                    with col_sk:
                        if st.button("Skip to Solution", use_container_width=True):
                            st.session_state.ai_is_correct = True
                            st.session_state.ai_feedback = ""
                            st.rerun()
                else:
                    picture = st.camera_input("Snap a photo of your working:")
                    
                    if picture:
                        if st.button("Submit Working for AI Marking", use_container_width=True, type="primary"):
                            with st.spinner("Gemini is checking your algebra..."):
                                try:
                                    img = Image.open(picture)
                                    img.thumbnail((1024, 1024))
                                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                                    
                                    graph_name = "quadratic" if prob_type == "Quadratic" else "straight line"
                                    prompt = f"""
                                    You are a supportive, encouraging high school math teacher. 
                                    The user is solving for a {graph_name} graph. 
                                    The CORRECT final equation they must reach is: {target_eq}
                                    
                                    Please read their handwritten working from the photo.
                                    1. Check their algebra step-by-step.
                                    2. If their working is mathematically sound and reaches the correct equation, reply EXACTLY with the word "CORRECT:" on the first line, followed by a brief congratulatory message.
                                    3. If they made a mistake, reply EXACTLY with the word "INCORRECT:" on the first line. Then gently explain exactly where they went wrong, but do not give them the final answer immediately—guide them on what to do next.
                                    """
                                    
                                    response = client.models.generate_content(
                                        model='gemini-3.6-flash',
                                        contents=[prompt, img]
                                    )
                                    
                                    resp_text = response.text.strip()
                                    if resp_text.upper().startswith("CORRECT"):
                                        st.session_state.ai_is_correct = True
                                        st.session_state.ai_feedback = re.sub(r'(?i)^CORRECT:?\s*', '', resp_text)
                                        st.rerun()
                                    else:
                                        st.session_state.ai_is_correct = False
                                        st.session_state.ai_feedback = re.sub(r'(?i)^INCORRECT:?\s*', '', resp_text)
                                        st.rerun()
                                        
                                except Exception as e:
                                    st.error(f"Oops! Something went wrong with the AI: {e}")
                                    
                    if st.session_state.ai_feedback and not st.session_state.ai_is_correct:
                        st.warning(f"**AI Marker Feedback:**\n\n{st.session_state.ai_feedback}")
                        
                    st.write("---")
                    col_retry, col_skip = st.columns(2)
                    with col_retry:
                        if st.button("Cancel Marker", use_container_width=True):
                            st.session_state.show_camera = False
                            st.session_state.ai_feedback = ""
                            st.rerun()
                    with col_skip:
                        if st.button("Skip & Show Solution", use_container_width=True):
                            st.session_state.ai_is_correct = True
                            st.session_state.ai_feedback = ""
                            st.rerun()
