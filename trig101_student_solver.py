import streamlit as st
import random
import math
import io
import json
import os
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
import streamlit.components.v1 as components
from pydantic import BaseModel, Field

# --- Import our Universal AI Marking Suite ---
import ai_marking_component

st.set_page_config(page_title="Trigonometry 101", page_icon="📐", layout="centered")

if 'PEN_COLORS' not in st.session_state:
    st.session_state.PEN_COLORS = ["#1E90FF", "#FF2400", "#32CD32", "#9400D3", "#FF8C00"]
    st.session_state.COLOR_NAMES = ["BLUE", "RED", "GREEN", "PURPLE", "ORANGE"]

st.markdown("""
    <style>
    button[kind="primary"] { background-color: #007AFF !important; border-color: #007AFF !important; color: white !important; }
    button[kind="primary"]:hover { background-color: #0056b3 !important; border-color: #0056b3 !important; }
    .stRadio > div { gap: 0rem; }
    [data-testid="stHorizontalBlock"] { gap: 0.5rem; align-items: center; }
    div[data-testid="stToolbar"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# --- AI Output Schemas ---
class SolutionRow(BaseModel):
    q_num: int = Field(description="The question number (1 to 20)")
    steps: str = Field(description="Step-by-step solving method using valid LaTeX formatting")

class AIWorksheetSolutions(BaseModel):
    solutions: list[SolutionRow]

class WordProblemOutput(BaseModel):
    problem_text: str = Field(description="The problem statement text")
    target_variable: str = Field(description="The target variable name")

# --- Math Engine: TRIGONOMETRY (Graphical) ---
def generate_trig_problem(topic_setting, level="1"):
    if topic_setting == "Both":
        topic = random.choice(["Pythagoras", "Trigonometry"])
    else:
        topic = topic_setting

    base_a, base_b = random.randint(4, 12), random.randint(4, 12)
    hyp_real = math.hypot(base_a, base_b)
    angle_rad = math.atan2(base_a, base_b)
    angle_deg = round(math.degrees(angle_rad))
    
    opp_val = round(base_a, 1) if base_a % 1 != 0 else base_a
    adj_val = round(base_b, 1) if base_b % 1 != 0 else base_b
    hyp_val = round(hyp_real, 1) if hyp_real % 1 != 0 else int(hyp_real)

    side_var = random.choice(['x', 'y', 'z', 'a', 'b', 'c', 'h', 'p', 'q'])
    angle_var = random.choice([r'\theta', r'\alpha', r'\beta', r'\gamma', r'\phi', 'x', 'y'])

    labels = {'opp': '', 'adj': '', 'hyp': '', 'angle': ''}
    ans = 0
    text_desc = ""
    target_var = ""
    rule_key = ""
    sub_type = ""

    if topic == "Pythagoras":
        rule_key = "Pythagoras"
        target = random.choice(['hyp', 'leg1', 'leg2'])
        target_var = side_var
        if target == 'hyp':
            sub_type = "hyp"
            labels['opp'], labels['adj'], labels['hyp'] = opp_val, adj_val, side_var
            ans, text_desc = hyp_val, f"Legs {opp_val}, {adj_val}. Find hyp {side_var}."
        elif target == 'leg1':
            sub_type = "leg"
            labels['opp'], labels['adj'], labels['hyp'] = side_var, adj_val, hyp_val
            ans, text_desc = opp_val, f"Hyp {hyp_val}, Leg {adj_val}. Find leg {side_var}."
        else:
            sub_type = "leg"
            labels['opp'], labels['adj'], labels['hyp'] = opp_val, side_var, hyp_val
            ans, text_desc = adj_val, f"Hyp {hyp_val}, Leg {opp_val}. Find leg {side_var}."
    else:
        base_rule = random.choice(["Sine", "Cosine", "Tangent"])
        find_angle = random.choice([True, False])
        
        if find_angle:
            rule_key = f"{base_rule} Inverse"
            sub_type = "angle"
        else:
            rule_key = base_rule
            sub_type = random.choice(["side_opp", "side_hyp"])
            
        if base_rule == "Sine":
            if find_angle:
                target_var = angle_var
                labels['opp'], labels['hyp'], labels['angle'] = opp_val, hyp_val, angle_var
                ans, text_desc = angle_deg, f"Opp {opp_val}, Hyp {hyp_val}. Find angle {angle_var}."
            else:
                target_var = side_var
                if random.choice([True, False]):
                    labels['opp'], labels['hyp'], labels['angle'] = side_var, hyp_val, f"{angle_deg}^\\circ"
                    ans, text_desc = opp_val, f"Angle {angle_deg}, Hyp {hyp_val}. Find Opp {side_var}."
                else:
                    labels['opp'], labels['hyp'], labels['angle'] = opp_val, side_var, f"{angle_deg}^\\circ"
                    ans, text_desc = hyp_val, f"Angle {angle_deg}, Opp {opp_val}. Find Hyp {side_var}."
        elif base_rule == "Cosine":
            if find_angle:
                target_var = angle_var
                labels['adj'], labels['hyp'], labels['angle'] = adj_val, hyp_val, angle_var
                ans, text_desc = angle_deg, f"Adj {adj_val}, Hyp {hyp_val}. Find angle {angle_var}."
            else:
                target_var = side_var
                if random.choice([True, False]):
                    labels['adj'], labels['hyp'], labels['angle'] = side_var, hyp_val, f"{angle_deg}^\\circ"
                    ans, text_desc = adj_val, f"Angle {angle_deg}, Hyp {hyp_val}. Find Adj {side_var}."
                else:
                    labels['adj'], labels['hyp'], labels['angle'] = adj_val, side_var, f"{angle_deg}^\\circ"
                    ans, text_desc = hyp_val, f"Angle {angle_deg}, Adj {adj_val}. Find Hyp {side_var}."
        elif base_rule == "Tangent":
            if find_angle:
                target_var = angle_var
                labels['opp'], labels['adj'], labels['angle'] = opp_val, adj_val, angle_var
                ans, text_desc = angle_deg, f"Opp {opp_val}, Adj {adj_val}. Find angle {angle_var}."
            else:
                target_var = side_var
                if random.choice([True, False]):
                    labels['opp'], labels['adj'], labels['angle'] = side_var, adj_val, f"{angle_deg}^\\circ"
                    ans, text_desc = opp_val, f"Angle {angle_deg}, Adj {adj_val}. Find Opp {side_var}."
                else:
                    labels['opp'], labels['adj'], labels['angle'] = adj_val, side_var, f"{angle_deg}^\\circ"
                    ans, text_desc = adj_val, f"Angle {angle_deg}, Opp {opp_val}. Find Adj {side_var}."

    l2_type = None
    l2_label = ""
    if level == "2" and topic != "Pythagoras":
        if find_angle:
            l2_type = random.choice(['parallel_Z', 'vertical_opp'])
            l2_label = f"{angle_var}"
        else:
            l2_type = random.choice(['complement', 'supplementary', 'parallel_Z', 'vertical_opp'])
            if l2_type == 'complement':
                l2_label = f"{90 - angle_deg}^\\circ"
            elif l2_type == 'supplementary':
                l2_label = f"{180 - angle_deg}^\\circ"
            elif l2_type == 'parallel_Z':
                l2_label = f"{angle_deg}^\\circ"
            elif l2_type == 'vertical_opp':
                l2_label = f"{angle_deg}^\\circ"
        labels['angle'] = ""

    return labels, rule_key, ans, text_desc, (opp_val, adj_val), target_var, sub_type, hyp_real, angle_deg, l2_type, l2_label

# --- Equations Generator ---
def build_equations(problem_data, topic_setting):
    labels, rule_key, ans, text_desc, (opp_val, adj_val), target_var, sub_type, hyp_real, angle_deg, l2_type, l2_label = problem_data
    hyp_val = round(hyp_real, 1) if hyp_real % 1 != 0 else int(hyp_real)
    t_disp = target_var.replace(r'\theta', 'θ').replace(r'\alpha', 'α').replace(r'\beta', 'β').replace(r'\gamma', 'γ').replace(r'\phi', 'ϕ')

    if rule_key == "Pythagoras":
        if sub_type == "hyp":
            correct = f"{t_disp} = √({opp_val}² + {adj_val}²)"
            distractor1 = f"{t_disp} = √({opp_val}² - {adj_val}²)"
            if topic_setting == "Both":
                trig_fn = random.choice(["sin", "cos", "tan"])
                distractor2 = f"{t_disp} = {opp_val} / {trig_fn}({angle_deg}°)"
            else:
                distractor2 = f"{t_disp} = {opp_val}² + {adj_val}²"
        else:
            other_side = adj_val if labels['opp'] == target_var else opp_val
            correct = f"{t_disp} = √({hyp_val}² - {other_side}²)"
            distractor1 = f"{t_disp} = √({hyp_val}² + {other_side}²)"
            if topic_setting == "Both":
                trig_fn = random.choice(["sin", "cos", "tan"])
                distractor2 = f"{t_disp} = {other_side} × {trig_fn}({angle_deg}°)"
            else:
                distractor2 = f"{t_disp} = {hyp_val}² - {other_side}²"
    else:
        base = rule_key.replace(" Inverse", "")
        fn = "sin" if base == "Sine" else ("cos" if base == "Cosine" else "tan")
        wrong_fn_map = {"sin": "cos", "cos": "tan", "tan": "sin"}
        w_fn = wrong_fn_map[fn]
        
        if "Inverse" in rule_key:
            num = opp_val if base == "Sine" else (adj_val if base == "Cosine" else opp_val)
            den = hyp_val if base != "Tangent" else adj_val
            inv_fn = "sin⁻¹" if fn == "sin" else ("cos⁻¹" if fn == "cos" else "tan⁻¹")
            w_inv_fn = "sin⁻¹" if w_fn == "sin" else ("cos⁻¹" if w_fn == "cos" else "tan⁻¹")
            correct = f"{t_disp} = {inv_fn}({num} / {den})"
            distractor1 = f"{t_disp} = {w_inv_fn}({num} / {den})"
            distractor2 = f"{t_disp} = {inv_fn}({den} / {num})"
        else:
            if labels['opp'] == target_var or labels['adj'] == target_var:
                known_side = hyp_val if base != "Tangent" else (adj_val if base == "Sine" else opp_val)
                correct = f"{t_disp} = {known_side} × {fn}({angle_deg}°)"
                distractor1 = f"{t_disp} = {known_side} × {w_fn}({angle_deg}°)"
                distractor2 = f"{t_disp} = {known_side} / {fn}({angle_deg}°)"
            else:
                known_side = opp_val if base == "Sine" else (adj_val if base == "Cosine" else opp_val)
                correct = f"{t_disp} = {known_side} / {fn}({angle_deg}°)"
                distractor1 = f"{t_disp} = {known_side} / {w_fn}({angle_deg}°)"
                distractor2 = f"{t_disp} = {known_side} × {fn}({angle_deg}°)"

    return correct, distractor1, distractor2

# --- Word Problem Engine ---
def generate_word_problem(level):
    from google import genai
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    if level == "1":
        prompt_choices = [
            "Act as an NCEA Level 1 Mathematics assessment writer. Generate a single right-angled triangle word problem involving either an angle of elevation, an angle of depression, or a leaning ladder. Randomize the real-world context, side lengths, and angle values.",
            "Act as an NCEA Level 1 Mathematics assessment writer. Generate a 'Shared Wall' back-to-back right-angled triangle word problem (e.g., a surveyor measuring angles to two separate towers from a central point, or a roof truss split by a central support pillar). Randomize dimensions and angles."
        ]
    else:
        prompt_choices = [
            "Act as an NCEA Level 1 Mathematics assessment writer. Generate an embedded/overlapping right-angled triangle word problem (e.g., a boat sailing toward a cliff/lighthouse and measuring two angles of elevation/depression at different points). Randomize distances and angles.",
            "Act as an NCEA Level 1 Mathematics assessment writer. Generate a 3D trigonometry word problem (e.g., finding the slant height or angle of a square-based pyramid, or the internal room diagonal of a rectangular prism). Randomize dimensions.",
            "Act as an NCEA Level 1 Mathematics assessment writer. Generate a True Bearings navigation word problem where an object (ship, tramper, or plane) travels along specific compass headings, turns, and requires parallel-line rules (alternate/co-interior angles) to establish internal triangle properties before solving. Randomize bearings and distances.",
            "Act as an NCEA Level 1 Mathematics assessment writer. Generate an isosceles triangle word problem (e.g., the pitch of a symmetrical roof, an A-frame house, or a stepladder). The student must realize they need to drop a perpendicular line to halve the base and create a right-angled triangle before solving. Randomize dimensions.",
            "Act as an NCEA Level 1 Mathematics assessment writer. Generate a trigonometry word problem integrated with kinematics. The student is given the speed of an object (e.g., ship or plane) and the time traveled, rather than direct distances. They must calculate the distances first before using SOH CAH TOA or Pythagoras.",
            "Act as an NCEA Level 1 Mathematics assessment writer. Generate a circle geometry crossover word problem where a tangent meets a radius (e.g., line of sight to the horizon, or a point outside a circular tank). The student must deduce the 90-degree angle at the tangent point to use right-angled trigonometry. Randomize dimensions."
        ]
        
    prompt = random.choice(prompt_choices)
    prompt += " Output a JSON object containing: 1) problem_text: The problem statement text, 2) target_variable: The target variable name (e.g., 'x', 'height', 'distance')."
    
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[prompt],
            config=dict(response_mime_type="application/json", response_schema=WordProblemOutput, temperature=0.7)
        )
        return json.loads(response.text)
    except Exception as e:
        return {
            "problem_text": "A ladder is leaning against a vertical wall. The ladder is 5.2 meters long and the base of the ladder is 2.1 meters away from the wall. Calculate the height the ladder reaches up the wall.",
            "target_variable": "height"
        }

# --- Visual Engine: UNIVERSAL MATPLOTLIB GEOMETRY ---
def draw_triangle_image(problem_data, size_px=380, label_padding=0.14):
    labels, rule_key, ans, text_desc, (a, b), target_var, sub_type, hyp_real, angle_deg, l2_type, l2_label = problem_data
    fig, ax = plt.subplots(figsize=(size_px/100, size_px/100), dpi=100)
    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_aspect('equal', adjustable='box')
    
    C = np.array([0.0, 0.0])
    A = np.array([b, 0.0])
    B = np.array([0.0, a])
    theta = random.uniform(0, 2 * np.pi)
    R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    
    def transform(pt): return R.dot(pt)
        
    extra_lines = []
    extra_arcs = []
    
    if labels['angle']: extra_arcs.append((A, C, B, labels['angle'], 0.28, 0.21))
    pts_to_fit = [transform(C), transform(A), transform(B)]
    
    if l2_type == 'complement':
        extra_arcs.append((A, C, B, l2_label, 0.28, 0.21))
    elif l2_type == 'supplementary':
        A_ext = A + (A - C) * 0.7
        extra_lines.append((A, A_ext, '-'))
        extra_arcs.append((A, B, A_ext, l2_label, 0.36, 0.28))
        pts_to_fit.append(transform(A_ext))
    elif l2_type == 'vertical_opp':
        A_ext1 = A + (A - C) * 0.7
        A_ext2 = A + (A - B) * 0.7
        extra_lines.append((A, A_ext1, '-'))
        extra_lines.append((A, A_ext2, '-'))
        extra_arcs.append((A, A_ext1, A_ext2, l2_label, 0.36, 0.28))
        pts_to_fit.append(transform(A_ext1))
        pts_to_fit.append(transform(A_ext2))
    elif l2_type == 'parallel_Z':
        A_ext1 = A + (C - B) * 0.7
        A_ext2 = A + (B - C) * 0.7
        extra_lines.append((A_ext1, A_ext2, '--'))
        extra_arcs.append((A, A_ext2, B, l2_label, 0.36, 0.28))
        pts_to_fit.append(transform(A_ext1))
        pts_to_fit.append(transform(A_ext2))
        
    pts = np.vstack(pts_to_fit)
    min_pt, max_pt = pts.min(axis=0), pts.max(axis=0)
    center = (min_pt + max_pt) / 2
    scale = 0.60 / max(max_pt - min_pt)
    
    def final_pt(pt): return (transform(pt) - center) * scale + [0.5, 0.5]
        
    Cf, Af, Bf = final_pt(C), final_pt(A), final_pt(B)
    triangle = plt.Polygon([Cf, Af, Bf], fill=False, edgecolor='black', linewidth=1.5)
    ax.add_patch(triangle)
    
    vCA_f = (Af - Cf) / np.linalg.norm(Af - Cf) * 0.04
    vCB_f = (Bf - Cf) / np.linalg.norm(Bf - Cf) * 0.04
    sq_pts = [Cf + vCA_f, Cf + vCA_f + vCB_f, Cf + vCB_f]
    ax.plot([Cf[0]+vCA_f[0], sq_pts[1][0], sq_pts[2][0]], [Cf[1]+vCA_f[1], sq_pts[1][1], sq_pts[2][1]], color='black', lw=1)
    
    for (p1, p2, style) in extra_lines:
        p1f, p2f = final_pt(p1), final_pt(p2)
        ax.plot([p1f[0], p2f[0]], [p1f[1], p2f[1]], color='black', linestyle=style, lw=1.2)
        
    for (pt_c, pt_1, pt_2, label, r_arc, r_txt) in extra_arcs:
        cf, p1f, p2f = final_pt(pt_c), final_pt(pt_1), final_pt(pt_2)
        v1, v2 = p1f - cf, p2f - cf
        ang1, ang2 = np.degrees(np.arctan2(v1[1], v1[0])), np.degrees(np.arctan2(v2[1], v2[0]))
        min_ang, max_ang = min(ang1, ang2), max(ang1, ang2)
        if max_ang - min_ang > 180: min_ang, max_ang = max_ang, min_ang + 360
        arc = patches.Arc(cf, r_arc, r_arc, angle=0.0, theta1=min_ang, theta2=max_ang, color='black', linewidth=1)
        ax.add_patch(arc)
        mid_rad = np.radians((min_ang + max_ang) / 2)
        txt_pos = cf + r_txt * np.array([np.cos(mid_rad), np.sin(mid_rad)])
        ax.text(txt_pos[0], txt_pos[1], f"${label}$", fontsize=11, ha='center', va='center')

    def place_label(p1, p2, text):
        if not text: return
        mid = (p1 + p2) / 2
        vec = p2 - p1
        normal = np.array([-vec[1], vec[0]]) / np.linalg.norm(np.array([-vec[1], vec[0]]))
        if np.dot(normal, mid - np.array([0.5, 0.5])) < 0: normal = -normal
        pos = mid + normal * label_padding
        angle_deg_val = np.degrees(np.arctan2(vec[1], vec[0]))
        if angle_deg_val > 90: angle_deg_val -= 180
        elif angle_deg_val < -90: angle_deg_val += 180
        ax.text(pos[0], pos[1], f"${text}$", fontsize=11, ha='center', va='center', rotation=angle_deg_val, rotation_mode='anchor')

    place_label(Cf, Bf, labels['opp']); place_label(Cf, Af, labels['adj']); place_label(Af, Bf, labels['hyp']) 

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGBA').copy()

# --- Visual Engine: WORD PROBLEM MATPLOTLIB CANVAS ---
def draw_word_problem_image(text, width_px=380, height_px=760):
    fig, ax = plt.subplots(figsize=(width_px/100, height_px/100), dpi=100)
    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Top-align text to leave heavy drawing space below for the student
    wrapped_text = "\n".join(textwrap.wrap(text, width=42))
    ax.text(0.02, 0.98, wrapped_text, fontsize=12, ha='left', va='top', wrap=True, family='sans-serif', color='black')
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGBA').copy()

# --- Worksheet PDF Generator ---
def create_pdf_bytes(topic_setting, level):
    from google import genai
    buffer = io.BytesIO()
    try:
        with PdfPages(buffer) as pdf:
            problems = [generate_trig_problem(topic_setting, level) for _ in range(20)]
            ai_steps = {}
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                payload = "".join([f"Q{i+1}: {p[3]} | Ans: {p[2]}\n" for i, p in enumerate(problems)])
                prompt = (
                    "Write concise step-by-step solutions using valid LaTeX math expressions enclosed in single dollar signs. "
                    "CRITICAL: For inverse trigonometric functions, strictly use \\sin^{-1}, \\cos^{-1}, and \\tan^{-1} notation. "
                    "Use \\n to separate steps so they break into new lines cleanly. "
                    "Data:\n" + payload
                )
                response = client.models.generate_content(
                    model='gemini-3.6-flash', contents=[prompt],
                    config=dict(response_mime_type="application/json", response_schema=AIWorksheetSolutions, temperature=0.1)
                )
                for item in json.loads(response.text).get("solutions", []):
                    cleaned_step = item["steps"].replace("**", "").replace(r"\n", "\n")
                    ai_steps[item["q_num"]] = cleaned_step
            except Exception as e:
                pass
            
            fig_ws, axes = plt.subplots(5, 4, figsize=(8.27, 11.69))
            fig_ws.subplots_adjust(left=0.03, right=0.97, top=0.92, bottom=0.03, wspace=0.10, hspace=0.20)
            fig_ws.suptitle("Trigonometry 101 Worksheet", fontsize=16, fontweight='bold', ha='center')
            
            for idx, p_data in enumerate(problems):
                row, col = divmod(idx, 4)
                ax = axes[row, col]
                ax.axis('off')
                img_buf = draw_triangle_image(p_data, size_px=220, label_padding=0.16)
                ax.imshow(img_buf)
                ax.set_title(f"Q{idx+1}", fontsize=10, fontweight='bold', pad=1)
                
            pdf.savefig(fig_ws); plt.close(fig_ws)

            fig_ans, ax_ans = plt.subplots(figsize=(8.27, 11.69))
            ax_ans.axis('off')
            ax_ans.text(0.5, 0.96, "Answer Key & Steps", fontsize=16, fontweight='bold', ha='center')
            for i in range(10):
                left_idx, right_idx = i, i + 10
                txt_l = f"Q{left_idx+1}: Ans: {problems[left_idx][2]}\n{ai_steps.get(left_idx+1, '')}"
                txt_r = f"Q{right_idx+1}: Ans: {problems[right_idx][2]}\n{ai_steps.get(right_idx+1, '')}"
                y_pos = 0.90 - (i * 0.088)
                ax_ans.text(0.04, y_pos, txt_l, fontsize=7.0, va='top', wrap=True)
                ax_ans.text(0.52, y_pos, txt_r, fontsize=7.0, va='top', wrap=True)
            pdf.savefig(fig_ans); plt.close(fig_ans)
    except Exception as e:
        st.error(f"PDF Generation Error Details: {e}")
        raise e

    buffer.seek(0)
    return buffer.getvalue()

# --- State Management ---
if 'generating' not in st.session_state: st.session_state.generating = True
if 'question_type' not in st.session_state: st.session_state.question_type = os.getenv("QUESTION_TYPE", st.secrets.get("QUESTION_TYPE", "Graphical"))
if 'trig_topic' not in st.session_state: st.session_state.trig_topic = os.getenv("TRIG_TOPIC", st.secrets.get("TRIG_TOPIC", "Both"))
if 'level' not in st.session_state: st.session_state.level = os.getenv("LEVEL", st.secrets.get("LEVEL", "1"))
if 'interaction_mode' not in st.session_state: st.session_state.interaction_mode = os.getenv("INTERACTION_MODE", st.secrets.get("INTERACTION_MODE", "Solve"))
if 'solution_req' not in st.session_state: st.session_state.solution_req = os.getenv("SOLUTION_REQ", st.secrets.get("SOLUTION_REQ", "demonstrated"))
if 'id_style' not in st.session_state: st.session_state.id_style = os.getenv("ID_STYLE", st.secrets.get("ID_STYLE", "Function Names"))
if 'camera_mode' not in st.session_state: st.session_state.camera_mode = os.getenv("CAMERA_MODE", st.secrets.get("CAMERA_MODE", "App"))
if 'pdf_bytes' not in st.session_state: st.session_state.pdf_bytes = None
if 'problem_suite_refresh_id' not in st.session_state: st.session_state.problem_suite_refresh_id = 0
if 'id_feedback' not in st.session_state: st.session_state.id_feedback = ""
if 'current_marking_color_index' not in st.session_state: st.session_state.current_marking_color_index = 0

def handle_settings_change():
    st.session_state.generating = True
    st.session_state.pdf_bytes = None
    st.session_state.id_feedback = ""
    st.session_state.current_marking_color_index = 0 
    st.session_state.problem_suite_refresh_id += 1 

# --- UI Setup ---
st.title("Trigonometry 101")

col_actions, col_set = st.columns([5, 1])
with col_actions:
    with st.popover("📄 Worksheet Actions", use_container_width=True):
        st.markdown("**1. Create a physical worksheet**")
        if st.session_state.question_type == "Word Problem":
            st.info("PDF Worksheets for Word Problems are coming soon! Switch to 'Graphical' to generate a physical worksheet.")
        elif st.session_state.pdf_bytes is None:
            if st.button("⚙️ Generate Worksheet PDF", use_container_width=True):
                with st.spinner("Compiling Master PDF Grid..."):
                    try:
                        st.session_state.pdf_bytes = create_pdf_bytes(st.session_state.trig_topic, st.session_state.level)
                    except Exception:
                        st.session_state.pdf_bytes = None
                st.rerun()
        else:
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
            st.download_button("⬇️ Download Worksheet", data=st.session_state.pdf_bytes, file_name=f"Trigonometry_101_{timestamp_str}.pdf", mime="application/pdf", use_container_width=True, type="primary")
            if st.button("🗑️ Clear / Reset PDF", use_container_width=True):
                st.session_state.pdf_bytes = None
                st.rerun()
        st.markdown("---")
        st.markdown("**2. Grade student workings**")
        if "WORKSHEET_MARKER_APP_URL" in st.secrets:
            st.link_button("🤖 Mark My Worksheet", st.secrets["WORKSHEET_MARKER_APP_URL"], use_container_width=True)

with col_set:
    with st.popover("⚙️", use_container_width=True):
        st.write("**Settings**")
        st.radio("Question Type", ["Graphical", "Word Problem"], key="question_type", horizontal=True, on_change=handle_settings_change)
        st.radio("Level", ["1", "2"], key="level", horizontal=True, on_change=handle_settings_change)
        st.radio("Problem Type", ["Pythagoras", "Trigonometry", "Both"], key="trig_topic", on_change=handle_settings_change)
        st.radio("Interaction Mode", ["Identification", "Solve"], key="interaction_mode", on_change=handle_settings_change)
        st.radio("Identification Style", ["Function Names", "Equations"], key="id_style", on_change=handle_settings_change)
        st.radio("Solution Required", ["demonstrated", "numeric"], key="solution_req", on_change=handle_settings_change)
        st.radio("Camera Mode", ["App", "Native"], key="camera_mode", horizontal=True)

# --- Master App Logic ---
if st.session_state.generating:
    with st.spinner("Generating problem..."):
        if st.session_state.question_type == "Graphical":
            p_data = generate_trig_problem(st.session_state.trig_topic, st.session_state.level)
            st.session_state.trig_problem_data = p_data
            st.session_state.problem_image_context = draw_triangle_image(p_data, size_px=380, label_padding=0.14)
        else:
            wp_data = generate_word_problem(st.session_state.level)
            st.session_state.trig_problem_data = wp_data
            st.session_state.problem_image_context = draw_word_problem_image(wp_data.get('problem_text', ''), width_px=380, height_px=760)
            
        st.session_state.generating = False
        st.rerun()

else:
    bg_image = st.session_state.problem_image_context
    
    if st.session_state.question_type == "Graphical":
        labels, rule_key, ans, text_desc, sides, target_var, sub_type, hyp_real, angle_deg, l2_type, l2_label = st.session_state.trig_problem_data
    else:
        target_var = st.session_state.trig_problem_data.get('target_variable', 'x')

    st.write(f"**Find the missing value ({target_var})!**")

    if st.session_state.interaction_mode == "Identification":
        if st.session_state.question_type == "Word Problem":
            st.image(bg_image, use_container_width=True)
            st.info("💡 **Identification Mode** is optimized for graphical problems. For complex word problems, please switch the app to **'Solve'** mode in Settings so you can use the canvas to sketch your triangles and mark your workings!")
        else:
            st.image(bg_image, use_container_width=True)
            st.write("Which mathematical rule/equation is required to solve this problem?")
            
            if st.session_state.id_style == "Function Names":
                all_possible_rules = ["Pythagoras", "Sine", "Cosine", "Tangent", "Sine Inverse", "Cosine Inverse", "Tangent Inverse"]
                display_names = { "Pythagoras": "Pythagoras", "Sine": "sin", "Cosine": "cos", "Tangent": "tan", "Sine Inverse": "sin⁻¹", "Cosine Inverse": "cos⁻¹", "Tangent Inverse": "tan⁻¹" }
                correct_key = rule_key
                
                if 'id_options' not in st.session_state or st.session_state.get('last_refresh_id') != st.session_state.problem_suite_refresh_id:
                    other_rules = [r for r in all_possible_rules if r != correct_key]
                    chosen_incorrect = random.sample(other_rules, 2)
                    options = chosen_incorrect + [correct_key]
                    random.shuffle(options)
                    st.session_state.id_options = options
                    st.session_state.last_refresh_id = st.session_state.problem_suite_refresh_id

                c1, c2, c3 = st.columns(3)
                def check_rule(guess):
                    if guess == correct_key: st.session_state.id_feedback = f"Correct! Use **{display_names[correct_key]}**."
                    else: st.session_state.id_feedback = f"Not quite. Try again!"
                    
                for idx, opt in enumerate(st.session_state.id_options):
                    col = [c1, c2, c3][idx]
                    if col.button(display_names[opt], use_container_width=True, key=f"fn_btn_{idx}"):
                        check_rule(opt)
            else:
                correct_eq, dist1, dist2 = build_equations(st.session_state.trig_problem_data, st.session_state.trig_topic)
                
                if 'id_eq_options' not in st.session_state or st.session_state.get('last_refresh_id') != st.session_state.problem_suite_refresh_id:
                    options = [correct_eq, dist1, dist2]
                    random.shuffle(options)
                    st.session_state.id_eq_options = options
                    st.session_state.last_refresh_id = st.session_state.problem_suite_refresh_id

                c1, c2, c3 = st.columns(3)
                def check_eq(guess):
                    if guess == correct_eq: st.session_state.id_feedback = f"Correct! This equation sets up the problem properly."
                    else: st.session_state.id_feedback = f"Not quite. Try again!"

                for idx, opt in enumerate(st.session_state.id_eq_options):
                    col = [c1, c2, c3][idx]
                    if col.button(opt, use_container_width=True, key=f"eq_btn_{idx}"):
                        check_eq(opt)
            
            if st.session_state.id_feedback:
                if "Correct" in st.session_state.id_feedback: st.success(f"🌟 {st.session_state.id_feedback}")
                else: st.warning(f"🤖 {st.session_state.id_feedback}")
            
    else:
        # Dynamically map the height of the canvas widget depending on the question type
        canvas_height = 380 if st.session_state.question_type == "Graphical" else 760
        
        ai_marking_component.render_grading_suite(
            bg_image=bg_image,
            height_px=canvas_height,
            key_prefix=f"trig_suite_{st.session_state.problem_suite_refresh_id}",
            solution_requirement=st.session_state.get('solution_req', 'demonstrated')
        )

    st.write("---")
    if st.button("Give me a new problem!", use_container_width=True):
        handle_settings_change()
        st.rerun()