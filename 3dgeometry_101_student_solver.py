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
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from PIL import Image
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field

# --- Import our Universal AI Marking Suite ---
import ai_marking_component

st.set_page_config(page_title="Geometry 101", page_icon="🧊", layout="centered")

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

# --- Math Engine: 3D GEOMETRY ---
def generate_geom_problem(target_metric="Volume", num_shapes=1):
    shapes_pool = ["Cylinder", "Cone", "Box", "Hemisphere", "Pyramid", "Triangular Prism"]
    if target_metric == "Surface Area":
        # Keep it restricted to simpler composites for SA to avoid complex internal face subtractions
        shapes_pool = ["Cylinder", "Box"] 
        
    stack = []
    base_radius = random.randint(3, 10)
    base_width = base_radius * 2
    
    total_val = 0
    formula_parts = []
    
    for i in range(num_shapes):
        is_top_layer = (i == num_shapes - 1)
        
        # Enforce physical stability: supporting layers must have flat tops
        if is_top_layer:
            shape = random.choice(shapes_pool)
        else:
            shape = random.choice(["Cylinder", "Box"])
            
        if shape == "Hemisphere" and target_metric == "Surface Area": 
            shape = "Cylinder"
            
        h = random.randint(4, 12)
        r = base_radius
        w = base_width
        
        if shape == "Cylinder":
            v = math.pi * (r**2) * h
            sa = (2 * math.pi * r**2) + (2 * math.pi * r * h)
            formula_parts.append("\pi r^2 h" if target_metric == "Volume" else "(2\pi r^2 + 2\pi rh)")
            stack.append({"type": shape, "r": r, "h": h})
            total_val += v if target_metric == "Volume" else sa
            
        elif shape == "Cone":
            v = (1/3) * math.pi * (r**2) * h
            s = math.hypot(r, h)
            sa = (math.pi * r**2) + (math.pi * r * s)
            formula_parts.append("\\frac{1}{3}\pi r^2 h" if target_metric == "Volume" else "(\pi r^2 + \pi rs)")
            stack.append({"type": shape, "r": r, "h": h})
            total_val += v if target_metric == "Volume" else sa
            
        elif shape == "Box":
            l = base_width
            v = l * w * h
            sa = 2*(l*w) + 2*(l*h) + 2*(w*h)
            formula_parts.append("lwh" if target_metric == "Volume" else "2(lw + lh + wh)")
            stack.append({"type": shape, "w": w, "l": l, "h": h})
            total_val += v if target_metric == "Volume" else sa
            
        elif shape == "Hemisphere":
            v = (2/3) * math.pi * (r**3)
            sa = 3 * math.pi * (r**2)
            formula_parts.append("\\frac{2}{3}\pi r^3" if target_metric == "Volume" else "3\pi r^2")
            stack.append({"type": shape, "r": r, "h": r}) 
            total_val += v if target_metric == "Volume" else sa

        elif shape == "Pyramid":
            # Square based pyramid
            l = w
            v = (1/3) * (w**2) * h
            s = math.hypot(w/2, h)
            sa = w**2 + (2 * w * s)
            formula_parts.append("\\frac{1}{3}w^2 h" if target_metric == "Volume" else "(w^2 + 2ws)")
            stack.append({"type": shape, "w": w, "h": h})
            total_val += v if target_metric == "Volume" else sa

        elif shape == "Triangular Prism":
            l = w
            v = (1/2) * w * h * l
            s = math.hypot(w/2, h)
            sa = (w * l) + (w * h) + (2 * l * s)
            formula_parts.append("\\frac{1}{2}whl" if target_metric == "Volume" else "(wl + wh + 2ls)")
            stack.append({"type": shape, "w": w, "l": l, "h": h})
            total_val += v if target_metric == "Volume" else sa

    # Correct formula string
    correct_formula_str = f"{'V' if target_metric == 'Volume' else 'SA'} = " + " + ".join(formula_parts)
    
    target_var = "Volume" if target_metric == "Volume" else "Surface Area"
    ans = round(total_val, 1)
    
    return stack, correct_formula_str, ans, target_var, target_metric

# --- Equations Generator (Identification Distractors) ---
def build_geom_equations(correct_formula, target_metric, num_shapes):
    distractor_pool_v = ["\pi r^2 h", "\\frac{1}{3}\pi r^2 h", "\\frac{4}{3}\pi r^3", "lwh", "\\frac{1}{3}w^2 h", "\\frac{1}{2}whl"]
    distractor_pool_sa = ["2\pi r^2 + 2\pi rh", "\pi r^2 + \pi rs", "4\pi r^2", "2(lw + lh + wh)"]
    
    pool = distractor_pool_v if target_metric == "Volume" else distractor_pool_sa
    
    dist1_parts = [random.choice(pool) for _ in range(num_shapes)]
    dist2_parts = [random.choice(pool) for _ in range(num_shapes)]
    
    prefix = 'V' if target_metric == 'Volume' else 'SA'
    d1 = f"{prefix} = " + " + ".join(dist1_parts)
    d2 = f"{prefix} = " + " + ".join(dist2_parts)
    
    if d1 == correct_formula: d1 = f"{prefix} = " + " + ".join([random.choice(pool)])
    if d2 == correct_formula or d2 == d1: d2 = f"{prefix} = " + " + ".join([random.choice(pool)])
        
    return correct_formula, d1, d2

# --- Visual Engine: 3D STACKED MATPLOTLIB GENERATOR ---
def draw_geometry_image(stack, size_px=380):
    fig = plt.figure(figsize=(size_px/100, size_px/100), dpi=100)
    ax = fig.add_subplot(111, projection='3d')
    ax.axis('off')
    
    current_z = 0
    max_w = 0
    
    for obj in stack:
        shape = obj['type']
        h = obj['h']
        
        if shape in ["Cylinder", "Cone", "Hemisphere"]:
            r = obj['r']
            max_w = max(max_w, r*2)
            z_grid = np.linspace(current_z, current_z + h, 30)
            theta_grid = np.linspace(0, 2*np.pi, 30)
            Theta, Z = np.meshgrid(theta_grid, z_grid)
            
            if shape == "Cylinder":
                X = r * np.cos(Theta)
                Y = r * np.sin(Theta)
            elif shape == "Cone":
                R = r * (1 - (Z - current_z) / h)
                X = R * np.cos(Theta)
                Y = R * np.sin(Theta)
            elif shape == "Hemisphere":
                phi = np.linspace(0, np.pi/2, 30) 
                Phi, Theta = np.meshgrid(phi, theta_grid)
                X = r * np.sin(Phi) * np.cos(Theta)
                Y = r * np.sin(Phi) * np.sin(Theta)
                Z = current_z + r * np.cos(Phi)
                
            ax.plot_wireframe(X, Y, Z, color='black', linewidth=0.5, alpha=0.5)
            
            if shape == "Cylinder":
                ax.text(0, r*1.2, current_z + h/2, f"h={h}", color='red', fontsize=10)
                ax.text(r/2, 0, current_z, f"r={r}", color='blue', fontsize=10)
            elif shape == "Cone":
                ax.text(0, r*1.2, current_z + h/3, f"h={h}", color='red', fontsize=10)
            elif shape == "Hemisphere":
                ax.text(0, r*1.2, current_z + r/2, f"r={r}", color='blue', fontsize=10)
                
        elif shape == "Box":
            w, l = obj['w'], obj['l']
            max_w = max(max_w, w, l)
            xx, yy = np.meshgrid([-w/2, w/2], [-l/2, l/2])
            ax.plot_surface(xx, yy, np.full_like(xx, current_z), color='gray', alpha=0.1, edgecolor='black')
            ax.plot_surface(xx, yy, np.full_like(xx, current_z + h), color='gray', alpha=0.1, edgecolor='black')
            for x_edge in [-w/2, w/2]:
                ax.plot_surface(np.full_like(xx, x_edge), yy, np.array([[current_z, current_z], [current_z+h, current_z+h]]), color='gray', alpha=0.1, edgecolor='black')
            for y_edge in [-l/2, l/2]:
                ax.plot_surface(xx, np.full_like(yy, y_edge), np.array([[current_z, current_z], [current_z+h, current_z+h]]), color='gray', alpha=0.1, edgecolor='black')
                
            ax.text(-w/2, -l/2 - 2, current_z, f"w={w}", color='blue', fontsize=10)
            ax.text(w/2 + 2, 0, current_z, f"l={l}", color='green', fontsize=10)
            ax.text(-w/2 - 2, -l/2, current_z + h/2, f"h={h}", color='red', fontsize=10)

        elif shape == "Pyramid":
            w = obj['w']
            max_w = max(max_w, w)
            bx = [-w/2, w/2, w/2, -w/2, -w/2]
            by = [-w/2, -w/2, w/2, w/2, -w/2]
            bz = [current_z] * 5
            ax.plot(bx, by, bz, color='black', linewidth=0.5, alpha=0.5)
            for i in range(4):
                ax.plot([bx[i], 0], [by[i], 0], [current_z, current_z + h], color='black', linewidth=0.5, alpha=0.5)
                
            ax.text(-w/2, -w/2 - 2, current_z, f"w={w}", color='blue', fontsize=10)
            ax.text(0, 0, current_z + h/2, f"h={h}", color='red', fontsize=10)

        elif shape == "Triangular Prism":
            w, l = obj['w'], obj['l']
            max_w = max(max_w, w, l)
            ax.plot([-w/2, w/2, 0, -w/2], [-l/2, -l/2, -l/2, -l/2], [current_z, current_z, current_z + h, current_z], color='black', linewidth=0.5, alpha=0.5)
            ax.plot([-w/2, w/2, 0, -w/2], [l/2, l/2, l/2, l/2], [current_z, current_z, current_z + h, current_z], color='black', linewidth=0.5, alpha=0.5)
            ax.plot([-w/2, -w/2], [-l/2, l/2], [current_z, current_z], color='black', linewidth=0.5, alpha=0.5)
            ax.plot([w/2, w/2], [-l/2, l/2], [current_z, current_z], color='black', linewidth=0.5, alpha=0.5)
            ax.plot([0, 0], [-l/2, l/2], [current_z + h, current_z + h], color='black', linewidth=0.5, alpha=0.5)
            
            ax.text(-w/2, -l/2 - 2, current_z, f"w={w}", color='blue', fontsize=10)
            ax.text(w/2 + 2, 0, current_z, f"l={l}", color='green', fontsize=10)
            ax.text(-w/4, -l/2, current_z + h/2, f"h={h}", color='red', fontsize=10)

        current_z += h

    ax.set_box_aspect([1, 1, current_z/max_w if max_w > 0 else 1]) 

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGBA').copy()


# --- Word Problem Engine ---
def generate_geom_word_problem(level, target_metric, num_shapes):
    from google import genai
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    if level == "1":
        prompt_choices = [
            f"Act as an NCEA Level 1 Mathematics assessment writer. Generate a single 3D shape word problem calculating the {target_metric} of a real-world object (e.g., a silo, an ice cream cone, a swimming pool, or a basketball). Give clear dimensions.",
            f"Act as an NCEA Level 1 Mathematics assessment writer. Generate a word problem where the student must calculate the capacity in Litres of a single {target_metric} shape (remembering 1 cubic meter = 1000 Litres)."
        ]
    else:
        prompt_choices = [
            f"Act as an NCEA Level 1 Mathematics Excellence assessment writer. Generate a word problem where the {target_metric} is KNOWN, and the student must algebraically work backwards to find a missing height or radius.",
            f"Act as an NCEA Level 1 Mathematics Merit assessment writer. Generate a composite 3D shape word problem (combining a cylinder and a cone, or a box and a pyramid) calculating the {target_metric}. Provide context like a house roof or a rocket.",
            f"Act as an NCEA Level 1 Mathematics Excellence assessment writer. Generate a complex {target_metric} word problem requiring a subtraction (e.g., the volume of a pipe with a hollow center, or painting the outside of a shed but NOT the floor)."
        ]
        
    prompt = random.choice(prompt_choices)
    prompt += " Output a JSON object containing: 1) problem_text: The word problem text, 2) target_variable: The target unknown variable (e.g., 'Total Volume', 'Missing Height')."
    
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[prompt],
            config=dict(response_mime_type="application/json", response_schema=WordProblemOutput, temperature=0.7)
        )
        return json.loads(response.text)
    except Exception:
        return {
            "problem_text": "A cylindrical water tank has a radius of 4m and a height of 10m. Calculate its total Volume.",
            "target_variable": "Volume"
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
def create_pdf_bytes(target_metric, num_shapes):
    from google import genai
    buffer = io.BytesIO()
    try:
        with PdfPages(buffer) as pdf:
            problems = [generate_geom_problem(target_metric, num_shapes) for _ in range(20)]
            ai_steps = {}
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                payload = "".join([f"Q{i+1}: Shapes: {[s['type'] for s in p[0]]} | Ans: {p[2]}\n" for i, p in enumerate(problems)])
                prompt = (
                    "Write concise step-by-step solutions using valid LaTeX math expressions enclosed in single dollar signs. "
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
            fig_ws.suptitle("Geometry 101 Worksheet", fontsize=16, fontweight='bold', ha='center')
            
            for idx, p_data in enumerate(problems):
                row, col = divmod(idx, 4)
                ax = axes[row, col]
                ax.axis('off')
                img_buf = draw_geometry_image(p_data[0], size_px=220)
                ax.imshow(img_buf)
                ax.set_title(f"Q{idx+1}: Find {p_data[4]}", fontsize=10, fontweight='bold', pad=1)
                
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
        st.error(f"PDF Generation Error: {e}")
        raise e

    buffer.seek(0)
    return buffer.getvalue()

# --- State Management ---
if 'generating' not in st.session_state: st.session_state.generating = True
if 'question_type' not in st.session_state: st.session_state.question_type = "Graphical"
if 'geom_metric' not in st.session_state: st.session_state.geom_metric = "Volume"
if 'num_shapes' not in st.session_state: st.session_state.num_shapes = 1
if 'level' not in st.session_state: st.session_state.level = "1"
if 'interaction_mode' not in st.session_state: st.session_state.interaction_mode = "Solve"
if 'solution_req' not in st.session_state: st.session_state.solution_req = "demonstrated"
if 'camera_mode' not in st.session_state: st.session_state.camera_mode = "App"
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
st.title("Geometry 101 🧊")

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
                        st.session_state.pdf_bytes = create_pdf_bytes(st.session_state.geom_metric, st.session_state.num_shapes)
                    except Exception:
                        st.session_state.pdf_bytes = None
                st.rerun()
        else:
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
            st.download_button("⬇️ Download Worksheet", data=st.session_state.pdf_bytes, file_name=f"Geometry_101_{timestamp_str}.pdf", mime="application/pdf", use_container_width=True, type="primary")
            if st.button("🗑️ Clear / Reset PDF", use_container_width=True):
                st.session_state.pdf_bytes = None
                st.rerun()

with col_set:
    with st.popover("⚙️", use_container_width=True):
        st.write("**Settings**")
        st.radio("Question Type", ["Graphical", "Word Problem"], key="question_type", horizontal=True, on_change=handle_settings_change)
        
        if st.session_state.question_type == "Graphical":
            st.slider("Composite Shapes", 1, 3, key="num_shapes", on_change=handle_settings_change)
        else:
            st.radio("Level", ["1", "2"], key="level", horizontal=True, on_change=handle_settings_change)
            
        st.radio("Target Metric", ["Volume", "Surface Area"], key="geom_metric", horizontal=True, on_change=handle_settings_change)
        st.radio("Interaction Mode", ["Identification", "Solve"], key="interaction_mode", on_change=handle_settings_change)
        st.radio("Solution Required", ["demonstrated", "numeric"], key="solution_req", on_change=handle_settings_change)

# --- Master App Logic ---
if st.session_state.generating:
    with st.spinner("Generating 3D problem..."):
        if st.session_state.question_type == "Graphical":
            p_data = generate_geom_problem(st.session_state.geom_metric, st.session_state.num_shapes)
            st.session_state.geom_problem_data = p_data
            st.session_state.problem_image_context = draw_geometry_image(p_data[0], size_px=380)
        else:
            wp_data = generate_geom_word_problem(st.session_state.level, st.session_state.geom_metric, st.session_state.num_shapes)
            st.session_state.geom_problem_data = wp_data
            st.session_state.problem_image_context = draw_word_problem_image(wp_data.get('problem_text', ''), width_px=380, height_px=760)
            
        st.session_state.generating = False
        st.rerun()

else:
    bg_image = st.session_state.problem_image_context
    
    if st.session_state.question_type == "Graphical":
        stack, correct_formula, ans, target_var, target_metric = st.session_state.geom_problem_data
    else:
        target_var = st.session_state.geom_problem_data.get('target_variable', 'x')

    st.write(f"**Find the {target_var}!**")

    if st.session_state.interaction_mode == "Identification":
        if st.session_state.question_type == "Word Problem":
            st.image(bg_image, use_container_width=True)
            st.info("💡 **Identification Mode** is optimized for graphical problems. Switch to **'Solve'** mode to use the canvas!")
        else:
            st.image(bg_image, use_container_width=True)
            st.write("Which geometric formula is required to solve this composite shape?")
            
            correct_eq, dist1, dist2 = build_geom_equations(correct_formula, target_metric, st.session_state.num_shapes)
            
            if 'id_eq_options' not in st.session_state or st.session_state.get('last_refresh_id') != st.session_state.problem_suite_refresh_id:
                options = [f"${correct_eq}$", f"${dist1}$", f"${dist2}$"]
                random.shuffle(options)
                st.session_state.id_eq_options = options
                st.session_state.last_refresh_id = st.session_state.problem_suite_refresh_id

            c1, c2, c3 = st.columns(3)
            def check_eq(guess):
                if guess == f"${correct_eq}$": st.session_state.id_feedback = f"Correct! This formula combines the right base solids."
                else: st.session_state.id_feedback = f"Not quite. Check the shapes involved and try again!"

            for idx, opt in enumerate(st.session_state.id_eq_options):
                col = [c1, c2, c3][idx]
                if col.button(opt, use_container_width=True, key=f"eq_btn_{idx}"):
                    check_eq(opt)
            
            if st.session_state.id_feedback:
                if "Correct" in st.session_state.id_feedback: st.success(f"🌟 {st.session_state.id_feedback}")
                else: st.warning(f"🤖 {st.session_state.id_feedback}")
            
    else:
        canvas_height = 380 if st.session_state.question_type == "Graphical" else 760
        
        # We hook into the exact same ai_marking_component!
        ai_marking_component.render_grading_suite(
            bg_image=bg_image,
            height_px=canvas_height,
            key_prefix=f"geom_suite_{st.session_state.problem_suite_refresh_id}",
            solution_requirement=st.session_state.get('solution_req', 'demonstrated')
        )

    st.write("---")
    if st.button("Give me a new geometry problem!", use_container_width=True):
        handle_settings_change()
        st.rerun()