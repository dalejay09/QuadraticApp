import streamlit as st
import random
import math
import io
import json
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field

# --- Import our Universal AI Marking Suite ---
import ai_marking_component

st.set_page_config(page_title="Algebra Techniques 101", page_icon="✖️", layout="centered")

if 'PEN_COLORS' not in st.session_state:
    st.session_state.PEN_COLORS = ["#1E90FF", "#FF2400", "#32CD32", "#9400D3", "#FF8C00"]
    st.session_state.COLOR_NAMES = ["BLUE", "RED", "GREEN", "PURPLE", "ORANGE"]

st.markdown("""
    <style>
    button[kind="primary"] { background-color: #007AFF !important; border-color: #007AFF !important; color: white !important; }
    button[kind="primary"]:hover { background-color: #0056b3 !important; border-color: #0056b3 !important; }
    
    /* Target the exact 'Next Problem' button by stepping up to Streamlit's element container */
    div[data-testid="stElementContainer"]:has(#next-problem-btn) + div[data-testid="stElementContainer"] button {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
        color: white !important;
    }
    div[data-testid="stElementContainer"]:has(#next-problem-btn) + div[data-testid="stElementContainer"] button:hover {
        background-color: #218838 !important;
        border-color: #218838 !important;
    }
    
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

# --- Math Engine: ALGEBRA FORMATTING HELPER ---
def format_alg(expr):
    """Cleans up raw algebraic strings (e.g., '+ -3' to '- 3', removing 0x, '1x' to 'x')"""
    expr = expr.replace("+ -", "- ").replace("- -", "+ ")
    expr = re.sub(r'[+-]\s*0x\^2\b', '', expr)
    expr = re.sub(r'\b0x\^2\b', '', expr)
    expr = re.sub(r'[+-]\s*0x\b', '', expr)
    expr = re.sub(r'\b0x\b', '', expr)
    expr = re.sub(r'[+-]\s*0\b', '', expr)
    expr = re.sub(r'\b1x\^2\b', 'x^2', expr)
    expr = re.sub(r'\b1x\b', 'x', expr)
    expr = re.sub(r'\b-1x\^2\b', '-x^2', expr)
    expr = re.sub(r'\b-1x\b', '-x', expr)
    expr = " ".join(expr.split())
    if expr.startswith("+ "): expr = expr[2:]
    return expr.strip()

# --- Math Engine: CORE GENERATOR ---
def generate_algebra_problem(level="1", specific_type="All Topics (Random)"):
    types = [
        'expand_binomial', 'expand_perfect', 'factorise_single', 
        'factorise_quad', 'solve_linear', 'solve_quad', 
        'simp_mono', 'simp_dots', 'simp_quad'
    ]
    
    if specific_type != "All Topics (Random)":
        mapping = {
            "Expanding": ['expand_binomial', 'expand_perfect'],
            "Factorising": ['factorise_single', 'factorise_quad'],
            "Solving Equations": ['solve_linear', 'solve_quad'],
            "Algebraic Fractions": ['simp_mono', 'simp_dots', 'simp_quad']
        }
        p_type = random.choice(mapping[specific_type])
    else:
        p_type = random.choice(types)

    limit = 5 if level == "1" else 9
    
    instruction = "Solve:"
    q_latex = ""
    a_latex = ""
    
    def r_nonzero(low, high):
        n = 0
        while n == 0: n = random.randint(low, high)
        return n

    if p_type == 'expand_binomial':
        instruction = "Expand and simplify:"
        a = 1 if random.random() < 0.6 else random.randint(2, 4)
        c = 1 if level == "1" else random.randint(1, 4)
        b = r_nonzero(-limit, limit)
        d = r_nonzero(-limit, limit)
        
        q_latex = format_alg(f"({a}x + {b})({c}x + {d})")
        a_latex = format_alg(f"{a*c}x^2 + {a*d + b*c}x + {b*d}")
        
    elif p_type == 'expand_perfect':
        instruction = "Expand and simplify:"
        a = 1 if level == "1" else random.randint(2, 4)
        b = r_nonzero(-limit, limit)
        
        q_latex = format_alg(f"({a}x + {b})^2")
        a_latex = format_alg(f"{a**2}x^2 + {2*a*b}x + {b**2}")
        
    elif p_type == 'factorise_single':
        instruction = "Factorise completely:"
        while True:
            k = random.randint(2, limit)
            a = random.randint(1, 4)
            b = r_nonzero(-limit, limit)
            if math.gcd(a, abs(b)) == 1:
                break
                
        q_latex = format_alg(f"{k*a}x^2 + {k*b}x")
        a_latex = format_alg(f"{k}x({a}x + {b})")
        if a == 1: a_latex = format_alg(f"{k}x(x + {b})")
        
    elif p_type == 'factorise_quad':
        instruction = "Factorise completely:"
        a = 1 if random.random() < 0.7 else random.choice([2, 3])
        c = 1
        b = r_nonzero(-limit, limit)
        d = r_nonzero(-limit, limit)
        
        A = a * c
        B = a * d + b * c
        C = b * d
        q_latex = format_alg(f"{A}x^2 + {B}x + {C}")
        a_latex = format_alg(f"({a}x + {b})({c}x + {d})")
        
    elif p_type == 'solve_linear':
        instruction = "Solve:"
        a = random.randint(2, 5)
        b = 1 if level == "1" else random.randint(2, 4)
        c = r_nonzero(-limit, limit)
        d = r_nonzero(1, 5)
        
        if a * b == d: d += 1 
        
        ans_x = random.randint(-limit, limit)
        e = (a * b - d) * ans_x + a * c
        
        q_latex = format_alg(f"{a}({b}x + {c}) = {d}x + {e}")
        a_latex = f"x = {ans_x}"
        
    elif p_type == 'solve_quad':
        instruction = "Solve:"
        
        # 50% chance for a single root (perfect square) vs two distinct roots
        if random.choice([True, False]):
            r1 = r_nonzero(-limit, limit)
            B = -(2 * r1)
            C = r1**2
            a_latex = f"x = {r1}"
        else:
            r1 = r_nonzero(-limit, limit)
            r2 = r_nonzero(-limit, limit)
            while r2 == r1:
                r2 = r_nonzero(-limit, limit)
            B = -(r1 + r2)
            C = r1 * r2
            a_latex = f"x = {r1}, x = {r2}"
            
        q_latex = format_alg(f"x^2 + {B}x + {C} = 0")
        
    elif p_type == 'simp_mono':
        instruction = "Simplify fully:"
        k = random.randint(2, 6)
        x_power_top = random.choice([1, 2])
        x_power_bot = 1 if x_power_top == 2 else 2
        top_c = k * random.randint(1, 4)
        bot_c = k * random.randint(2, 5)
        
        top_str = f"{top_c}x^2" if x_power_top == 2 else f"{top_c}x"
        bot_str = f"{bot_c}x^2" if x_power_bot == 2 else f"{bot_c}x"
        q_latex = f"\\frac{{{top_str}}}{{{bot_str}}}"
        
        sim_top = int(top_c/k)
        sim_bot = int(bot_c/k)
        if x_power_top > x_power_bot:
            a_latex = f"\\frac{{{sim_top}x}}{{{sim_bot}}}" if sim_bot != 1 else f"{sim_top}x"
        else:
            a_latex = f"\\frac{{{sim_top}}}{{{sim_bot}x}}"
            
    elif p_type == 'simp_dots':
        instruction = "Simplify fully:"
        a = random.randint(2, 9)
        sign = random.choice(["+", "-"])
        q_latex = f"\\frac{{x^2 - {a**2}}}{{x {sign} {a}}}"
        ans_sign = "-" if sign == "+" else "+"
        a_latex = format_alg(f"x {ans_sign} {a}")
        
    elif p_type == 'simp_quad':
        instruction = "Simplify fully:"
        r1 = r_nonzero(-5, 5)
        r2 = r_nonzero(-5, 5)
        B = -(r1 + r2)
        C = r1 * r2
        
        sign_r1 = "+" if -r1 >= 0 else "-"
        bot_str = format_alg(f"x {sign_r1} {abs(-r1)}")
        top_str = format_alg(f"x^2 + {B}x + {C}")
        
        q_latex = f"\\frac{{{top_str}}}{{{bot_str}}}"
        sign_r2 = "+" if -r2 >= 0 else "-"
        a_latex = format_alg(f"x {sign_r2} {abs(-r2)}")

    return {
        "type": p_type,
        "instruction": instruction,
        "q_latex": q_latex,
        "a_latex": a_latex
    }

def generate_distractors(a_latex):
    d1 = a_latex.replace("+", "TEMP").replace("-", "+").replace("TEMP", "-")
    d2 = a_latex.replace("x^2", "x").replace("x = ", "x = -")
    if d1 == a_latex: d1 = a_latex + " + 1"
    if d2 == a_latex or d2 == d1: d2 = a_latex + " - 1"
    return a_latex, d1, d2

# --- Visual Engine: CANVAS RENDERER ---
def draw_algebra_image(problem_data, width_px=380, height_px=380):
    fig, ax = plt.subplots(figsize=(width_px/100, height_px/100), dpi=100)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    ax.text(0.05, 0.95, problem_data['instruction'], fontsize=12, fontweight='bold', va='top', ha='left')
    
    fs = 18 if "\\frac" in problem_data['q_latex'] else 16
    y_pos = 0.82 if "\\frac" in problem_data['q_latex'] else 0.86
    ax.text(0.05, y_pos, f"${problem_data['q_latex']}$", fontsize=fs, va='top', ha='left', color='black')
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGBA').copy()

# --- Worksheet PDF Generator ---
def create_pdf_bytes(level, specific_type):
    from google import genai
    buffer = io.BytesIO()
    try:
        with PdfPages(buffer) as pdf:
            problems = [generate_algebra_problem(level, specific_type) for _ in range(20)]
            ai_steps = {}
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                
                payload = "".join([f"Q{i+1}: {p['instruction']} {p['q_latex']} | Final Ans: {p['a_latex']}\n" for i, p in enumerate(problems)])
                    
                prompt = (
                    "Write concise step-by-step algebra solutions using valid LaTeX math expressions enclosed in single dollar signs. "
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
            except Exception:
                pass
            
            fig_ws, axes = plt.subplots(5, 4, figsize=(8.27, 11.69))
            fig_ws.subplots_adjust(left=0.03, right=0.97, top=0.92, bottom=0.03, wspace=0.15, hspace=0.25)
            fig_ws.suptitle(f"Algebra 101 Worksheet", fontsize=16, fontweight='bold', ha='center')
            
            for idx, p_data in enumerate(problems):
                row, col = divmod(idx, 4)
                ax = axes[row, col]
                ax.axis('off')
                ax.text(0.05, 0.95, f"Q{idx+1}: {p_data['instruction']}", fontsize=8, fontweight='bold', va='top')
                fs = 14 if "\\frac" in p_data['q_latex'] else 11
                ax.text(0.05, 0.75, f"${p_data['q_latex']}$", fontsize=fs, va='top')
                
            pdf.savefig(fig_ws); plt.close(fig_ws)

            fig_ans, ax_ans = plt.subplots(figsize=(8.27, 11.69))
            ax_ans.axis('off')
            ax_ans.text(0.5, 0.96, "Answer Key & Steps", fontsize=16, fontweight='bold', ha='center')
            for i in range(10):
                left_idx, right_idx = i, i + 10
                txt_l = f"Q{left_idx+1}: ${problems[left_idx]['a_latex']}$\n{ai_steps.get(left_idx+1, '')}"
                txt_r = f"Q{right_idx+1}: ${problems[right_idx]['a_latex']}$\n{ai_steps.get(right_idx+1, '')}"
                
                y_pos = 0.90 - (i * 0.088)
                ax_ans.text(0.04, y_pos, txt_l, fontsize=7.0, va='top', wrap=True)
                ax_ans.text(0.52, y_pos, txt_r, fontsize=7.0, va='top', wrap=True)
            pdf.savefig(fig_ans); plt.close(fig_ans)
    except Exception as e:
        st.error(f"PDF Generation Error: {e}")
        raise e

    buffer.seek(0)
    return buffer.getvalue()

# --- State Management ---
if 'generating' not in st.session_state: st.session_state.generating = True
if 'alg_topic' not in st.session_state: st.session_state.alg_topic = "All Topics (Random)"
if 'level' not in st.session_state: st.session_state.level = "1"
if 'interaction_mode' not in st.session_state: st.session_state.interaction_mode = "Solve"
if 'solution_req' not in st.session_state: st.session_state.solution_req = "demonstrated"
if 'camera_mode' not in st.session_state: st.session_state.camera_mode = "None"
if 'show_controls' not in st.session_state: st.session_state.show_controls = False
if 'pdf_bytes' not in st.session_state: st.session_state.pdf_bytes = None
if 'problem_suite_refresh_id' not in st.session_state: st.session_state.problem_suite_refresh_id = 0
if 'id_feedback' not in st.session_state: st.session_state.id_feedback = ""

def handle_settings_change():
    st.session_state.generating = True
    st.session_state.pdf_bytes = None
    st.session_state.id_feedback = ""
    st.session_state.current_marking_color_index = 0 
    st.session_state.problem_suite_refresh_id += 1 

# --- UI Setup ---
st.title("Algebra Techniques 101 ✖️")

col_actions, col_set = st.columns([5, 1])
with col_actions:
    with st.popover("📄 Worksheet Actions", use_container_width=True):
        st.markdown("**1. Create a physical worksheet**")
        if st.session_state.pdf_bytes is None:
            if st.button("⚙️ Generate Worksheet PDF", use_container_width=True):
                with st.spinner("Compiling Master PDF Grid..."):
                    try:
                        st.session_state.pdf_bytes = create_pdf_bytes(st.session_state.level, st.session_state.alg_topic)
                    except Exception:
                        st.session_state.pdf_bytes = None
                st.rerun()
        else:
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
            st.download_button("⬇️ Download Worksheet", data=st.session_state.pdf_bytes, file_name=f"Algebra_101_{timestamp_str}.pdf", mime="application/pdf", use_container_width=True, type="primary")
            if st.button("🗑️ Clear / Reset PDF", use_container_width=True):
                st.session_state.pdf_bytes = None
                st.rerun()

with col_set:
    with st.popover("⚙️", use_container_width=True):
        st.write("**Settings**")
        topics = ["All Topics (Random)", "Expanding", "Factorising", "Solving Equations", "Algebraic Fractions"]
        st.selectbox("Filter Topic", topics, key="alg_topic", on_change=handle_settings_change)
        st.radio("Level", ["1", "2"], key="level", horizontal=True, on_change=handle_settings_change)
        st.radio("Interaction Mode", ["Identification", "Solve"], key="interaction_mode", on_change=handle_settings_change)
        st.radio("Solution Required", ["demonstrated", "numeric"], key="solution_req", on_change=handle_settings_change)
        st.radio("Camera Mode", ["None", "App", "Native"], key="camera_mode", horizontal=True, on_change=handle_settings_change)
        st.toggle("Canvas Controls", key="show_controls", on_change=handle_settings_change)

# --- Master App Logic ---
if st.session_state.generating:
    with st.spinner("Generating algebra problem..."):
        p_data = generate_algebra_problem(st.session_state.level, st.session_state.alg_topic)
        st.session_state.alg_problem_data = p_data
        st.session_state.problem_image_context = draw_algebra_image(p_data, width_px=380, height_px=380)
        st.session_state.generating = False
        st.rerun()

else:
    bg_image = st.session_state.problem_image_context
    p_data = st.session_state.alg_problem_data
    
    st.write(f"**{p_data['instruction']}**")
    st.latex(p_data['q_latex'])

    if st.session_state.interaction_mode == "Identification":
        st.image(bg_image, use_container_width=True)
        st.write("Which of the following is the correct mathematical conclusion?")
        
        correct_opt, dist1, dist2 = generate_distractors(p_data['a_latex'])
        
        if 'id_eq_options' not in st.session_state or st.session_state.get('last_refresh_id') != st.session_state.problem_suite_refresh_id:
            options = [f"${correct_opt}$", f"${dist1}$", f"${dist2}$"]
            random.shuffle(options)
            st.session_state.id_eq_options = options
            st.session_state.last_refresh_id = st.session_state.problem_suite_refresh_id

        c1, c2, c3 = st.columns(3)
        def check_eq(guess):
            if guess == f"${correct_opt}$": st.session_state.id_feedback = "Correct! Spot on algebra."
            else: st.session_state.id_feedback = "Not quite. Check your positive and negative signs!"

        for idx, opt in enumerate(st.session_state.id_eq_options):
            col = [c1, c2, c3][idx]
            if col.button(opt, use_container_width=True, key=f"eq_btn_{idx}"):
                check_eq(opt)
        
        f_msg = st.session_state.get('id_feedback', '')
        if f_msg:
            if "Correct" in f_msg: st.success(f"🌟 {f_msg}")
            else: st.warning(f"🤖 {f_msg}")
            
    else:
        canvas_height = 380
        
        problem_context = f"This is an algebra problem. Instruction: {p_data['instruction']}. Question expression: {p_data['q_latex']}. The exact correct final algebraic answer is: {p_data['a_latex']}."

        ai_marking_component.render_grading_suite(
            bg_image=bg_image,
            height_px=canvas_height,
            key_prefix=f"alg_suite_{st.session_state.problem_suite_refresh_id}",
            solution_requirement=st.session_state.get('solution_req', 'demonstrated'),
            problem_context=problem_context,
            show_controls=st.session_state.show_controls,
            camera_mode=st.session_state.camera_mode
        )

    st.markdown("<hr style='margin: 0.5em 0px; border-color: #444;'>", unsafe_allow_html=True)
    st.markdown('<div id="next-problem-btn"></div>', unsafe_allow_html=True)
    if st.button("Give me a new algebra problem!", use_container_width=True):
        handle_settings_change()
        st.rerun()