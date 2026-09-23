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
import numpy as np
from PIL import Image
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field

# --- Import our Universal AI Marking Suite ---
import ai_marking_component

st.set_page_config(page_title="Linear Algebra 101", page_icon="📈", layout="centered")

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
    target_variable: str = Field(description="The target unknown variable (e.g., 'cost of adult ticket')")
    is_trick: bool = Field(description="True if the generated problem is a trick question with no solution or infinite solutions.", default=False)
    trick_type: str = Field(description="'None', 'No Solution', or 'Infinite Solutions'", default="None")

# --- Math Engine: LINEAR ALGEBRA & SIMULTANEOUS EQUATIONS ---
def generate_linear_problem(level="1", include_tricks=False):
    is_trick = include_tricks and random.choice([True, False])
    method = random.choice(["Elimination", "Substitution"])
    
    if is_trick:
        trick_type = random.choice(["No Solution (Parallel)", "Infinite Solutions (Coincident)"])
        a1 = random.choice([-3, -2, 1, 2, 3, 4])
        b1 = random.choice([-2, -1, 1, 2, 3])
        if a1 == 0 and b1 == 0: a1 = 1
        c1 = random.randint(-10, 10)
        
        mult = random.choice([-2, 2, 3])
        a2 = a1 * mult
        b2 = b1 * mult
        
        if trick_type == "Infinite Solutions (Coincident)":
            c2 = c1 * mult
        else: # Parallel
            c2 = c1 * mult + random.choice([-5, -3, 3, 5])
            
        eq1_str = f"{a1}x {'+' if b1 >= 0 else '-'} {abs(b1)}y = {c1}"
        eq2_str = f"{a2}x {'+' if b2 >= 0 else '-'} {abs(b2)}y = {c2}"
        
        return {
            "a1": a1, "b1": b1, "c1": c1, "a2": a2, "b2": b2, "c2": c2,
            "ans_x": "N/A", "ans_y": "N/A",
            "eq1": eq1_str, "eq2": eq2_str,
            "method": method, "is_trick": True, "trick_type": trick_type
        }
        
    else:
        if level == "1":
            ans_x = random.randint(-3, 5)
            ans_y = random.randint(-3, 5)
        else:
            ans_x = random.randint(-6, 8)
            ans_y = random.randint(-6, 8)
        
        a1 = random.choice([-3, -2, 1, 2, 3, 4])
        b1 = random.choice([-2, -1, 1, 2, 3])
        if a1 == 0 and b1 == 0: a1 = 1
        c1 = a1 * ans_x + b1 * ans_y
        
        a2 = random.choice([-4, -2, 1, 2, 3])
        b2 = random.choice([-2, -1, 1, 2, 3])
        if a1 * b2 == b1 * a2:
            b2 += 1
        c2 = a2 * ans_x + b2 * ans_y
        
        eq1_str = f"{a1}x {'+' if b1 >= 0 else '-'} {abs(b1)}y = {c1}"
        eq2_str = f"{a2}x {'+' if b2 >= 0 else '-'} {abs(b2)}y = {c2}"
        
        return {
            "a1": a1, "b1": b1, "c1": c1, "a2": a2, "b2": b2, "c2": c2,
            "ans_x": ans_x, "ans_y": ans_y,
            "eq1": eq1_str, "eq2": eq2_str,
            "method": method, "is_trick": False, "trick_type": "None"
        }

# --- Equations Generator (Identification Distractors) ---
def build_linear_equations(problem_data):
    if problem_data.get("is_trick"):
        if "Infinite" in problem_data["trick_type"]:
            correct = r"\text{Infinite Solutions}"
            dist1 = r"\text{No Solution}"
            dist2 = f"x = 0, y = 0"
        else:
            correct = r"\text{No Solution}"
            dist1 = r"\text{Infinite Solutions}"
            dist2 = f"x = 1, y = 1"
        return correct, dist1, dist2
        
    ans_x, ans_y = problem_data["ans_x"], problem_data["ans_y"]
    correct = f"x = {ans_x}, y = {ans_y}"
    dist1 = f"x = {ans_y}, y = {ans_x}"
    dist2 = f"x = {-ans_x}, y = {-ans_y}"
    return correct, dist1, dist2

# --- Visual Engine: CARTESIAN GRID MATPLOTLIB GENERATOR ---
def draw_cartesian_grid(problem_data, size_px=380):
    fig, ax = plt.subplots(figsize=(size_px/100, (size_px * 2)/100), dpi=100)
    fig.subplots_adjust(left=0.12, right=0.88, top=0.92, bottom=0.38)
    
    a1, b1, c1 = problem_data["a1"], problem_data["b1"], problem_data["c1"]
    a2, b2, c2 = problem_data["a2"], problem_data["b2"], problem_data["c2"]
    
    if problem_data.get("is_trick"):
        lim = 10
    else:
        ans_x, ans_y = problem_data["ans_x"], problem_data["ans_y"]
        lim = max(8, abs(ans_x) + 5, abs(ans_y) + 5)
        
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.axhline(0, color='black', linewidth=1)
    ax.axvline(0, color='black', linewidth=1)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    ax.set_aspect('equal', adjustable='box')
    
    x_vals = np.linspace(-lim, lim, 100)
    
    # Line 1
    if b1 != 0:
        y1_vals = (c1 - a1 * x_vals) / b1
        ax.plot(x_vals, y1_vals, label=f"{problem_data['eq1']}", color='#1E90FF', linewidth=2)
    else:
        x_val = c1 / a1
        ax.axvline(x_val, label=f"{problem_data['eq1']}", color='#1E90FF', linewidth=2)
        
    # Line 2 (Dashed if coincident so both show)
    ls2 = '--' if problem_data.get("trick_type") == "Infinite Solutions (Coincident)" else '-'
    if b2 != 0:
        y2_vals = (c2 - a2 * x_vals) / b2
        ax.plot(x_vals, y2_vals, label=f"{problem_data['eq2']}", color='#FF2400', linewidth=2, linestyle=ls2)
    else:
        x_val = c2 / a2
        ax.axvline(x_val, label=f"{problem_data['eq2']}", color='#FF2400', linewidth=2, linestyle=ls2)
        
    ax.legend(loc='upper right', fontsize=8)
    ax.set_title("Simultaneous Linear Equations", fontsize=10, fontweight='bold', pad=10)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGBA').copy()

# --- Word Problem Engine ---
def generate_linear_word_problem(level, include_tricks=False):
    from google import genai
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    if include_tricks and random.choice([True, False]):
        prompt = (
            "Act as an NCEA Level 1 Mathematics assessment writer. "
            "Generate a TRICK simultaneous equations word problem involving two items. "
            "The two mathematical constraints provided MUST mathematically result in either parallel lines (no solution/impossible scenario) or identical proportional lines (infinite solutions/not enough info). "
            "Output a JSON object containing: 1) problem_text: The problem statement, 2) target_variable: What to find, "
            "3) is_trick: true, 4) trick_type: 'No Solution' or 'Infinite Solutions'."
        )
    else:
        prompt = (
            "Act as an NCEA Level 1 Mathematics assessment writer. "
            "Generate a standard simultaneous equations word problem involving two unknown items "
            "with a clear real-world context and two distinct linear constraints. "
            "Output a JSON object containing: 1) problem_text: The problem statement text, 2) target_variable: The target unknown variable, "
            "3) is_trick: false, 4) trick_type: 'None'."
        )
    
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[prompt],
            config=dict(response_mime_type="application/json", response_schema=WordProblemOutput, temperature=0.7)
        )
        return json.loads(response.text)
    except Exception:
        return {
            "problem_text": "At a cinema, 2 adult tickets and 3 child tickets cost $45. 4 adult tickets and 1 child ticket cost $55. Find the cost of an adult ticket.",
            "target_variable": "adult ticket cost",
            "is_trick": False,
            "trick_type": "None"
        }

def draw_word_problem_image(text, width_px=380, height_px=760):
    fig, ax = plt.subplots(figsize=(width_px/100, height_px/100), dpi=100)
    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    wrapped_text = "\n".join(textwrap.wrap(text, width=42))
    ax.text(0.02, 0.98, wrapped_text, fontsize=12, ha='left', va='top', wrap=True, family='sans-serif', color='black')
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGBA').copy()

# --- Worksheet PDF Generator ---
def create_pdf_bytes(level, include_tricks=False):
    from google import genai
    buffer = io.BytesIO()
    try:
        with PdfPages(buffer) as pdf:
            problems = [generate_linear_problem(level, include_tricks) for _ in range(20)]
            ai_steps = {}
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                
                payload = ""
                for i, p in enumerate(problems):
                    ans_str = p["trick_type"] if p.get("is_trick") else f"x={p['ans_x']}, y={p['ans_y']}"
                    payload += f"Q{i+1}: 1) {p['eq1']} 2) {p['eq2']} | Method: {p['method']} | Ans: {ans_str}\n"
                    
                prompt = (
                    "Write concise step-by-step simultaneous equation solutions using valid LaTeX math expressions enclosed in single dollar signs. "
                    "If the answer says 'No Solution' or 'Infinite Solutions', show the elimination/substitution leading to a false/true statement (e.g. 0 = 5) and state the reason. "
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
            fig_ws.subplots_adjust(left=0.03, right=0.97, top=0.92, bottom=0.03, wspace=0.10, hspace=0.20)
            fig_ws.suptitle("Linear Algebra 101 Worksheet", fontsize=16, fontweight='bold', ha='center')
            
            for idx, p_data in enumerate(problems):
                row, col = divmod(idx, 4)
                ax = axes[row, col]
                ax.axis('off')
                ax.text(0.05, 0.85, f"Q{idx+1} ({p_data['method']})", fontsize=9, fontweight='bold')
                ax.text(0.05, 0.55, f"1) ${p_data['eq1']}$", fontsize=9)
                ax.text(0.05, 0.35, f"2) ${p_data['eq2']}$", fontsize=9)
                
            pdf.savefig(fig_ws); plt.close(fig_ws)

            fig_ans, ax_ans = plt.subplots(figsize=(8.27, 11.69))
            ax_ans.axis('off')
            ax_ans.text(0.5, 0.96, "Answer Key & Steps", fontsize=16, fontweight='bold', ha='center')
            for i in range(10):
                left_idx, right_idx = i, i + 10
                
                ans_l = problems[left_idx]["trick_type"] if problems[left_idx].get("is_trick") else f"x={problems[left_idx]['ans_x']}, y={problems[left_idx]['ans_y']}"
                ans_r = problems[right_idx]["trick_type"] if problems[right_idx].get("is_trick") else f"x={problems[right_idx]['ans_x']}, y={problems[right_idx]['ans_y']}"
                
                txt_l = f"Q{left_idx+1} ({problems[left_idx]['method']}): {ans_l}\n{ai_steps.get(left_idx+1, '')}"
                txt_r = f"Q{right_idx+1} ({problems[right_idx]['method']}): {ans_r}\n{ai_steps.get(right_idx+1, '')}"
                
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
if 'question_type' not in st.session_state: st.session_state.question_type = "Graphical"
if 'level' not in st.session_state: st.session_state.level = "1"
if 'interaction_mode' not in st.session_state: st.session_state.interaction_mode = "Solve"
if 'solution_req' not in st.session_state: st.session_state.solution_req = "demonstrated"
if 'camera_mode' not in st.session_state: st.session_state.camera_mode = "App"
if 'pdf_bytes' not in st.session_state: st.session_state.pdf_bytes = None
if 'problem_suite_refresh_id' not in st.session_state: st.session_state.problem_suite_refresh_id = 0
if 'id_feedback' not in st.session_state: st.session_state.id_feedback = ""
if 'include_tricks' not in st.session_state: st.session_state.include_tricks = False

def handle_settings_change():
    st.session_state.generating = True
    st.session_state.pdf_bytes = None
    st.session_state.id_feedback = ""
    st.session_state.current_marking_color_index = 0 
    st.session_state.problem_suite_refresh_id += 1 

# --- UI Setup ---
st.title("Linear Algebra 101 📈")

col_actions, col_set = st.columns([5, 1])
with col_actions:
    with st.popover("📄 Worksheet Actions", use_container_width=True):
        st.markdown("**1. Create a physical worksheet**")
        if st.session_state.question_type == "Word Problem":
            st.info("Switch to 'Graphical' to generate a physical worksheet.")
        elif st.session_state.pdf_bytes is None:
            if st.button("⚙️ Generate Worksheet PDF", use_container_width=True):
                with st.spinner("Compiling Master PDF Grid..."):
                    try:
                        st.session_state.pdf_bytes = create_pdf_bytes(st.session_state.level, st.session_state.include_tricks)
                    except Exception:
                        st.session_state.pdf_bytes = None
                st.rerun()
        else:
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
            st.download_button("⬇️ Download Worksheet", data=st.session_state.pdf_bytes, file_name=f"Linear_Algebra_101_{timestamp_str}.pdf", mime="application/pdf", use_container_width=True, type="primary")
            if st.button("🗑️ Clear / Reset PDF", use_container_width=True):
                st.session_state.pdf_bytes = None
                st.rerun()

with col_set:
    with st.popover("⚙️", use_container_width=True):
        st.write("**Settings**")
        st.radio("Question Type", ["Graphical", "Word Problem"], key="question_type", horizontal=True, on_change=handle_settings_change)
        st.radio("Level", ["1", "2"], key="level", horizontal=True, on_change=handle_settings_change)
        st.radio("Interaction Mode", ["Identification", "Solve"], key="interaction_mode", on_change=handle_settings_change)
        st.radio("Solution Required", ["demonstrated", "numeric"], key="solution_req", on_change=handle_settings_change)
        st.toggle("Include Trick Questions", key="include_tricks", on_change=handle_settings_change)

# --- Master App Logic ---
if st.session_state.generating:
    with st.spinner("Generating simultaneous equations..."):
        if st.session_state.question_type == "Graphical":
            p_data = generate_linear_problem(st.session_state.level, st.session_state.include_tricks)
            st.session_state.linear_problem_data = p_data
            st.session_state.problem_image_context = draw_cartesian_grid(p_data, size_px=380)
        else:
            wp_data = generate_linear_word_problem(st.session_state.level, st.session_state.include_tricks)
            st.session_state.linear_problem_data = wp_data
            st.session_state.problem_image_context = draw_word_problem_image(wp_data.get('problem_text', ''), width_px=380, height_px=760)
            
        st.session_state.generating = False
        st.rerun()

else:
    bg_image = st.session_state.problem_image_context
    p_data = st.session_state.linear_problem_data
    is_trick = p_data.get('is_trick', False)
    
    if is_trick:
        st.markdown("### 🛑 TRICK QUESTION - WHY?")
        if st.session_state.question_type == "Graphical":
            st.latex(f"1)\\ {p_data['eq1']}")
            st.latex(f"2)\\ {p_data['eq2']}")
    else:
        if st.session_state.question_type == "Graphical":
            st.write(f"**Solve using {p_data['method']}:**")
            st.latex(f"1)\\ {p_data['eq1']}")
            st.latex(f"2)\\ {p_data['eq2']}")
        else:
            target_desc = p_data.get('target_variable', 'x')
            st.write(f"**Find the {target_desc}!**")

    if st.session_state.interaction_mode == "Identification":
        if st.session_state.question_type == "Word Problem":
            st.image(bg_image, use_container_width=True)
            st.info("💡 **Identification Mode** is optimized for graphical systems. Switch to **'Solve'** mode to use the canvas!")
        else:
            st.image(bg_image, use_container_width=True)
            st.write("What is the solution $(x, y)$ where these two lines intersect?")
            
            correct_opt, dist1, dist2 = build_linear_equations(p_data)
            
            if 'id_eq_options' not in st.session_state or st.session_state.get('last_refresh_id') != st.session_state.problem_suite_refresh_id:
                options = [f"${correct_opt}$", f"${dist1}$", f"${dist2}$"]
                random.shuffle(options)
                st.session_state.id_eq_options = options
                st.session_state.last_refresh_id = st.session_state.problem_suite_refresh_id

            c1, c2, c3 = st.columns(3)
            def check_eq(guess):
                if guess == f"${correct_opt}$": st.session_state.id_feedback = f"Correct! That is the proper solution state."
                else: st.session_state.id_feedback = f"Not quite. Check the intersection point on the graph and try again!"

            for idx, opt in enumerate(st.session_state.id_eq_options):
                col = [c1, c2, c3][idx]
                if col.button(opt, use_container_width=True, key=f"eq_btn_{idx}"):
                    check_eq(opt)
            
            f_msg = st.session_state.get('id_feedback', '')
            if f_msg:
                if "Correct" in f_msg: st.success(f"🌟 {f_msg}")
                else: st.warning(f"🤖 {f_msg}")
            
    else:
        canvas_height = 760
        
        if st.session_state.question_type == "Graphical":
            if is_trick:
                problem_context = f"This is a TRICK simultaneous linear equations problem. Equation 1: {p_data['eq1']}, Equation 2: {p_data['eq2']}. The correct solution is: {p_data['trick_type']}. The student MUST demonstrate workings showing the variables canceling out to an inconsistent statement (like 0 = 5) or tautology (like 0 = 0) and state why."
            else:
                problem_context = f"This is a simultaneous linear equations problem requiring the student to use the {p_data['method']} method. Equation 1: {p_data['eq1']}, Equation 2: {p_data['eq2']}. The correct solution point is x = {p_data['ans_x']}, y = {p_data['ans_y']}. The student MUST demonstrate workings using {p_data['method']}."
        else:
            if is_trick:
                problem_context = f"This is a TRICK linear algebra word problem. The system actually has {p_data['trick_type']}. The student MUST demonstrate workings leading to a cancellation (0=0 or 0=X) and explicitly note the lack of a standard solution."
            else:
                problem_context = f"This is a linear algebra word problem. Target variable: {p_data.get('target_variable', 'x')}."

        ai_marking_component.render_grading_suite(
            bg_image=bg_image,
            height_px=canvas_height,
            key_prefix=f"linear_suite_{st.session_state.problem_suite_refresh_id}",
            solution_requirement=st.session_state.get('solution_req', 'demonstrated'),
            problem_context=problem_context
        )

    st.write("---")
    if st.button("Give me a new linear algebra problem!", use_container_width=True):
        handle_settings_change()
        st.rerun()