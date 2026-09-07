import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import random
import string
import io
import json
import re
import base64
from PIL import Image
from datetime import datetime
from google import genai
from pydantic import BaseModel, Field
import streamlit.components.v1 as components

# --- THE ULTIMATE MONKEY PATCH ---
import streamlit_drawable_canvas
def b64_image_to_url(image, *args, **kwargs):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

streamlit_drawable_canvas.image_to_url = b64_image_to_url
from streamlit_drawable_canvas import st_canvas
# ---------------------------------

# --- AI Output Schemas ---
class SolutionRow(BaseModel):
    q_num: int = Field(description="The question number (1 to 20)")
    steps: str = Field(description="Step-by-step solving method (plain text, no latex blocks, use basic newlines)")

class AIWorksheetSolutions(BaseModel):
    solutions: list[SolutionRow]

# --- Configuration & CSS Layout Hacks ---
st.set_page_config(page_title="Algebra 101", page_icon="🧮", layout="centered")
PEN_COLORS = ["#1E90FF", "#FF2400", "#32CD32", "#9400D3", "#FF8C00"]
COLOR_NAMES = ["BLUE", "RED", "GREEN", "PURPLE", "ORANGE"]

st.markdown("""
    <style>
    /* Primary Button Styling */
    button[kind="primary"] {
        background-color: #007AFF !important;
        border-color: #007AFF !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background-color: #0056b3 !important;
        border-color: #0056b3 !important;
    }
    
    /* Toolbar Tightening Hacks */
    .stRadio > div { gap: 0rem; }
    [data-testid="stHorizontalBlock"] { gap: 0.5rem; align-items: center; }
    div[data-testid="stToolbar"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# --- Math Engine: ALGEBRA ---
def get_valid_vars(count):
    valid_chars = [c for c in string.ascii_lowercase if c not in 'eilo']
    return sorted(random.sample(valid_chars, count))

def fmt_expr(coefs, v_list):
    terms = []
    for c, v in zip(coefs, v_list):
        if c == 0: continue
        sign = "+" if c > 0 and len(terms) > 0 else "-" if c < 0 else ""
        sign_str = f"{sign} " if sign else ""
        val = "" if abs(c) == 1 else str(abs(c))
        terms.append(f"{sign_str}{val}{v}")
    return " ".join(terms) if terms else "0"

def build_canvas_row(coefs, v_list, rhs):
    row = []
    has_prev = False
    for c, v in zip(coefs, v_list):
        if c == 0:
            row.append("")
        else:
            val_str = "" if abs(c) == 1 else str(abs(c))
            if not has_prev:
                sign = "-" if c < 0 else ""
                row.append(f"{sign}{val_str}{v}")
                has_prev = True
            else:
                sign = "+" if c > 0 else "-"
                row.append(f"{sign}\\,{val_str}{v}") 
                
    row.append("=")
    row.append(str(rhs))
    return row

def get_nonzero_randint(a, b):
    return random.choice([x for x in range(a, b + 1) if x != 0])

def generate_algebra_problem(override_var_count=None):
    var_count = override_var_count if override_var_count is not None else st.session_state.get('var_count', 1)
    vars = get_valid_vars(var_count)
    
    if var_count == 1:
        v = vars[0]
        ans = get_nonzero_randint(-10, 10)
        a = random.choice([-5, -4, -3, -2, -1, 2, 3, 4, 5])
        c = random.choice([-5, -4, -3, -2, -1, 2, 3, 4, 5])
        while a == c: c = random.choice([-5, -4, -3, -2, -1, 2, 3, 4, 5])
        b = random.randint(-15, 15)
        d = (a * ans + b) - (c * ans)
        
        lhs = f"{fmt_expr([a], [v])}"
        if b > 0: lhs += f" + {b}"
        elif b < 0: lhs += f" - {abs(b)}"
        
        rhs = f"{fmt_expr([c], [v])}"
        if d > 0: rhs += f" + {d}"
        elif d < 0: rhs += f" - {abs(d)}"
        
        if not lhs: lhs = "0"
        if not rhs: rhs = "0"
        
        eq_str = f"{lhs} = {rhs}"
        fallback = f"1. Group terms: {a-c}{v} = {d-b}\n2. Solve: {v} = {ans}"
        canvas_eqs = [[eq_str]] 
        
        return [eq_str], {v: ans}, vars, 450, fallback, canvas_eqs

    elif var_count == 2:
        v1, v2 = vars
        ans1, ans2 = get_nonzero_randint(-6, 6), get_nonzero_randint(-6, 6)
        
        while True:
            a1, b1 = random.randint(-4, 4), random.randint(-4, 4)
            a2, b2 = random.randint(-4, 4), random.randint(-4, 4)
            if a1 == 0 and b1 == 0: continue
            if a2 == 0 and b2 == 0: continue
            if a1 * b2 - a2 * b1 != 0: break 
            
        c1 = a1 * ans1 + b1 * ans2
        c2 = a2 * ans1 + b2 * ans2
        
        eq1 = f"{fmt_expr([a1, b1], vars)} = {c1}"
        eq2 = f"{fmt_expr([a2, b2], vars)} = {c2}"
        fallback = f"Solution: {v1} = {ans1}, {v2} = {ans2}\n(Check via substitution)"
        
        canvas_eqs = [
            build_canvas_row([a1, b1], vars, c1),
            build_canvas_row([a2, b2], vars, c2)
        ]
        
        return [eq1, eq2], {v1: ans1, v2: ans2}, vars, 650, fallback, canvas_eqs

    elif var_count == 3:
        v1, v2, v3 = vars
        ans1, ans2, ans3 = get_nonzero_randint(-4, 4), get_nonzero_randint(-4, 4), get_nonzero_randint(-4, 4)
        
        def get_row():
            while True:
                r = [random.randint(-3, 3) for _ in range(3)]
                if any(c != 0 for c in r): return r
                
        while True:
            r1, r2, r3 = get_row(), get_row(), get_row()
            det = (r1[0]*(r2[1]*r3[2] - r2[2]*r3[1]) -
                   r1[1]*(r2[0]*r3[2] - r2[2]*r3[0]) +
                   r1[2]*(r2[0]*r3[1] - r2[1]*r3[0]))
            if det != 0: break
            
        c1 = r1[0]*ans1 + r1[1]*ans2 + r1[2]*ans3
        c2 = r2[0]*ans1 + r2[1]*ans2 + r2[2]*ans3
        c3 = r3[0]*ans1 + r3[1]*ans2 + r3[2]*ans3
        
        eq1 = f"{fmt_expr(r1, vars)} = {c1}"
        eq2 = f"{fmt_expr(r2, vars)} = {c2}"
        eq3 = f"{fmt_expr(r3, vars)} = {c3}"
        fallback = f"Solution: {v1}={ans1}, {v2}={ans2}, {v3}={ans3}\n(Check via substitution)"
        
        canvas_eqs = [
            build_canvas_row(r1, vars, c1),
            build_canvas_row(r2, vars, c2),
            build_canvas_row(r3, vars, c3)
        ]
        
        return [eq1, eq2, eq3], {v1: ans1, v2: ans2, v3: ans3}, vars, 800, fallback, canvas_eqs

# --- Integrated AI-PDF Generation Engine ---
def create_pdf_bytes(var_count):
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        problems = [generate_algebra_problem(var_count) for _ in range(20)]
        ai_steps = {}
        
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            
            payload = ""
            for i, p in enumerate(problems):
                eq_str = " ; ".join(p[0])
                ans_str = ", ".join([f"{k}={v}" for k,v in p[1].items()])
                payload += f"Q{i+1}: Equations: [{eq_str}] | Correct Answer: [{ans_str}]\n"
            
            prompt = f"""
            You are an expert math tutor. I generated a worksheet with {var_count}-variable algebra problems.
            I already know the equations and correct answers. 
            Write the concise, human-readable step-by-step solution method for each problem (e.g., elimination or substitution).
            Keep it very brief (under 50 words per question) so it fits on a printed page. 
            Do NOT use markdown bolding or latex formats, use plain text formatting.
            
            Data:
            {payload}
            """
            
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[prompt],
                config=dict(
                    response_mime_type="application/json",
                    response_schema=AIWorksheetSolutions,
                    temperature=0.1
                )
            )
            
            ai_data = json.loads(response.text).get("solutions", [])
            for item in ai_data:
                ai_steps[item["q_num"]] = item["steps"].replace("**", "")
                
        except Exception as e:
            print(f"Background AI Solver failed, using fallback: {e}")
        
        # Page 1: Questions
        fig, axes = plt.subplots(figsize=(8.27, 11.69))
        axes.axis('off')
        axes.text(0.5, 0.95, f"Algebra 101 Worksheet ({var_count} Variable{'s' if var_count>1 else ''})", fontsize=16, fontweight='bold', ha='center')
        
        for i in range(10):
            eq_text_L = "\n".join(problems[i][0])
            eq_text_R = "\n".join(problems[i+10][0])
            axes.text(0.05, 0.88 - (i*0.085), f"Q{i+1}:\n{eq_text_L}", fontsize=11, va='top')
            axes.text(0.55, 0.88 - (i*0.085), f"Q{i+11}:\n{eq_text_R}", fontsize=11, va='top')
        pdf.savefig(fig); plt.close(fig)

        # Page 2: Answer Key
        fig_ans, ax_ans = plt.subplots(figsize=(8.27, 11.69))
        ax_ans.axis('off')
        ax_ans.text(0.5, 0.95, "Algebra 101 Answer Key", fontsize=16, fontweight='bold', ha='center')
        for i in range(10):
            ans_L = ", ".join([f"{k} = {v}" for k, v in problems[i][1].items()])
            ans_R = ", ".join([f"{k} = {v}" for k, v in problems[i+10][1].items()])
            ax_ans.text(0.05, 0.88 - (i*0.085), f"Q{i+1}: {ans_L}", fontsize=11, va='top')
            ax_ans.text(0.55, 0.88 - (i*0.085), f"Q{i+11}: {ans_R}", fontsize=11, va='top')
        pdf.savefig(fig_ans); plt.close(fig_ans)

        # Page 3+: AI Generated Solutions Appendix
        for page_idx in range(2):
            fig_app, ax_app = plt.subplots(figsize=(8.27, 11.69))
            ax_app.axis('off')
            ax_app.text(0.5, 0.95, f"Solutions Appendix (Page {page_idx+1})", fontsize=14, fontweight='bold', ha='center')
            
            offset = page_idx * 10
            for i in range(5):
                q_id_L = offset + i + 1
                prob_L = problems[q_id_L - 1]
                step_L = ai_steps.get(q_id_L, prob_L[4]) 
                txt_L = f"Q{q_id_L}:\n" + "\n".join(prob_L[0]) + "\n\n" + step_L
                ax_app.text(0.05, 0.88 - (i*0.17), txt_L, fontsize=8, va='top', wrap=True)
                
                q_id_R = offset + i + 6
                prob_R = problems[q_id_R - 1]
                step_R = ai_steps.get(q_id_R, prob_R[4])
                txt_R = f"Q{q_id_R}:\n" + "\n".join(prob_R[0]) + "\n\n" + step_R
                ax_app.text(0.55, 0.88 - (i*0.17), txt_R, fontsize=8, va='top', wrap=True)
                
            pdf.savefig(fig_app); plt.close(fig_app)
            
    return buffer.getvalue()

# --- Visual Engine: BACKEND MATPLOTLIB ---
def draw_equations(canvas_eqs, height_px):
    width_px = 350
    fig, ax = plt.subplots(figsize=(width_px/100, height_px/100), dpi=100) 
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    num_eqs = len(canvas_eqs)
    font_size = 20 if num_eqs <= 2 else 16
    y_start = 0.90
    y_step = 0.08 if height_px <= 450 else 0.06
    
    for i, row in enumerate(canvas_eqs):
        y = y_start - i * y_step
        if len(row) == 1:
            ax.text(0.5, y, f"${row[0]}$", fontsize=font_size, ha='center', va='top')
        else:
            num_vars = len(row) - 2
            if num_vars == 2:
                x_coords = [0.38, 0.58]; x_eq = 0.65; x_rhs = 0.70            
            else:
                x_coords = [0.26, 0.46, 0.66]; x_eq = 0.72; x_rhs = 0.77            

            for j in range(num_vars):
                if row[j]: ax.text(x_coords[j], y, f"${row[j]}$", fontsize=font_size, ha='right', va='top')
            
            ax.text(x_eq, y, "$=$", fontsize=font_size, ha='center', va='top')
            ax.text(x_rhs, y, f"${row[-1]}$", fontsize=font_size, ha='left', va='top')
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGBA').copy()

# --- Memory Stack Initialization ---
if 'generating' not in st.session_state: st.session_state.generating = True
if 'ai_feedback' not in st.session_state: st.session_state.ai_feedback = ""
if 'canvas_key' not in st.session_state: st.session_state.canvas_key = 0 
if 'var_count' not in st.session_state: st.session_state.var_count = 1
if 'camera_mode' not in st.session_state: st.session_state.camera_mode = "App"
if 'color_index' not in st.session_state: st.session_state.color_index = 0
if 'stroke_history' not in st.session_state: st.session_state.stroke_history = [[]]
if 'active_initial_drawing' not in st.session_state: st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
if 'is_correct' not in st.session_state: st.session_state.is_correct = False
if 'pdf_bytes' not in st.session_state: st.session_state.pdf_bytes = None
if 'scroll_to_top' not in st.session_state: st.session_state.scroll_to_top = False
if 'show_camera_supplement' not in st.session_state: st.session_state.show_camera_supplement = False

def handle_settings_change():
    st.session_state.generating = True
    st.session_state.pdf_bytes = None

# Auto-Scroll Injector
if st.session_state.scroll_to_top:
    components.html("<script>window.parent.scrollTo(0, 0);</script>", height=0)
    st.session_state.scroll_to_top = False

# --- Top Bar UI ---
st.title("Algebra 101")

col_actions, col_set = st.columns([5, 1])
with col_actions:
    with st.popover("📄 Worksheet Actions", use_container_width=True):
        st.markdown("**1. Create a physical worksheet**")
        
        if st.session_state.pdf_bytes is None:
            if st.button("⚙️ Generate Worksheet PDF", use_container_width=True):
                with st.spinner("Compiling Master PDF & generating AI solution paths (takes ~10s)..."):
                    st.session_state.pdf_bytes = create_pdf_bytes(st.session_state.var_count)
                st.rerun()
        else:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="⬇️ Download Worksheet (PDF)",
                data=st.session_state.pdf_bytes,
                file_name=f"Algebra_101_Worksheet_{current_time}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
            if st.button("🗑️ Clear / Reset PDF", use_container_width=True):
                st.session_state.pdf_bytes = None
                st.rerun()
                
        st.markdown("---")
        st.markdown("**2. Grade student workings**")
        
        if "WORKSHEET_MARKER_APP_URL" in st.secrets:
            st.link_button("🤖 Mark My Worksheet", st.secrets["WORKSHEET_MARKER_APP_URL"], use_container_width=True)
        else:
            st.caption("⚠️ Please add WORKSHEET_MARKER_APP_URL to your Streamlit secrets to enable the marking app.")

with col_set:
    with st.popover("⚙️", use_container_width=True):
        st.write("**Settings**")
        st.radio("Variables", [1, 2, 3], key="var_count", on_change=handle_settings_change)
        st.radio("Camera Mode", ["App", "Native"], key="camera_mode", horizontal=True)

if st.session_state.generating:
    with st.spinner("Generating equations..."):
        if len(st.session_state.get("math_data", [])) == 6:
            eqs, solutions, vars_list, canvas_height, fallback, canvas_eqs = generate_algebra_problem()
        else:
            generation_output = generate_algebra_problem()
            eqs, solutions, vars_list, canvas_height, fallback, canvas_eqs = generation_output
            
        st.session_state.math_data = (eqs, solutions, vars_list, canvas_height, fallback, canvas_eqs)
        st.session_state.bg_image = draw_equations(canvas_eqs, canvas_height)
        
        st.session_state.ai_feedback = ""
        st.session_state.color_index = 0 
        st.session_state.is_correct = False
        st.session_state.show_camera_supplement = False
        st.session_state.stroke_history = [[]]
        st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
        st.session_state.canvas_key += 1 
        st.session_state.generating = False
        st.rerun()

else:
    if len(st.session_state.math_data) == 6:
        eqs, solutions, vars_list, canvas_height, fallback, canvas_eqs = st.session_state.math_data
    else:
        st.session_state.generating = True
        st.rerun()
        
    sol_str = ", ".join([f"{k} = {v}" for k, v in solutions.items()])
    current_color_hex = PEN_COLORS[st.session_state.color_index]
    current_color_name = COLOR_NAMES[st.session_state.color_index]
    
    st.write(f"Solve for **{', '.join(vars_list)}**! Current pen: **{current_color_name}**")

    # --- Tight Unified Toolbar ---
    t_col1, t_col2, t_col3, t_col4 = st.columns([1.5, 1, 1, 1.2])
    with t_col1:
        tool = st.radio("Tool", ["🖌️", "🧽"], horizontal=True, label_visibility="collapsed")
    with t_col2:
        if st.button("↩️", use_container_width=True, help="Undo"):
            if len(st.session_state.stroke_history) > 1:
                st.session_state.stroke_history.pop()
                last_valid = st.session_state.stroke_history[-1]
                st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": last_valid}
                st.session_state.canvas_key += 1
                st.rerun()
    with t_col3:
        if st.button("🗑️", use_container_width=True, help="Clear Canvas"):
            st.session_state.stroke_history = [[]]
            st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
            st.session_state.canvas_key += 1
            st.rerun()
    with t_col4:
        if st.button("📸 Paper", use_container_width=True, help="Add a photo of paper workings"):
            st.session_state.show_camera_supplement = not st.session_state.show_camera_supplement
            st.rerun()

    active_stroke_color = current_color_hex if tool == "🖌️" else "#FFFFFE"
    active_stroke_width = 3 if tool == "🖌️" else 15

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", 
        stroke_width=active_stroke_width, 
        stroke_color=active_stroke_color,
        background_image=st.session_state.bg_image,
        update_streamlit=True,
        height=canvas_height,
        width=350,
        drawing_mode="freedraw",
        return_image_data=True, 
        initial_drawing=st.session_state.active_initial_drawing, 
        key=f"canvas_{st.session_state.canvas_key}",
    )
    
    # Custom Eraser Logic
    current_objects = canvas_result.json_data.get("objects", []) if canvas_result.json_data else []
    last_saved_objects = st.session_state.stroke_history[-1]

    if len(current_objects) > len(last_saved_objects):
        new_stroke = current_objects[-1]
        if new_stroke.get("stroke", "").upper() == "#FFFFFE":
            e_obj = new_stroke
            ew = e_obj.get("width", 0) * e_obj.get("scaleX", 1)
            eh = e_obj.get("height", 0) * e_obj.get("scaleY", 1)
            e_left = e_obj.get("left", 0); e_top = e_obj.get("top", 0)
            
            pad = 15
            E_L = e_left - pad; E_R = e_left + ew + pad
            E_T = e_top - pad; E_B = e_top + eh + pad
            
            objects_to_keep = []
            for obj in last_saved_objects:
                ow = obj.get("width", 0) * obj.get("scaleX", 1)
                oh = obj.get("height", 0) * obj.get("scaleY", 1)
                o_left = obj.get("left", 0); o_top = obj.get("top", 0)
                T_L = o_left; T_R = o_left + ow
                T_T = o_top; T_B = o_top + oh
                overlap = not (E_R < T_L or E_L > T_R or E_B < T_T or E_T > T_B)
                if not overlap: objects_to_keep.append(obj)
            
            st.session_state.stroke_history.append(objects_to_keep)
            st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": objects_to_keep}
            st.session_state.canvas_key += 1
            st.rerun()
        else:
            st.session_state.stroke_history.append(current_objects.copy())

    # --- Unified AI Processing ---
    camera_picture = None
    if st.session_state.show_camera_supplement:
        cam_mode = st.session_state.get('camera_mode', 'App')
        if cam_mode == 'App':
            camera_picture = st.camera_input("Snap a photo of your working:")
        else:
            camera_picture = st.file_uploader("Upload or snap a photo of your paper workings:", type=['png', 'jpg', 'jpeg'])

    st.write("---")
    if st.button("Check My Answer!", type="primary", use_container_width=True):
        payload_images = []
        
        # 1. Grab Canvas Ink (if any exists)
        if canvas_result.image_data is not None and len(st.session_state.stroke_history[-1]) > 0:
            ink_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            bg = st.session_state.bg_image.convert("RGBA")
            if ink_img.size != bg.size:
                ink_img = ink_img.resize(bg.size, Image.Resampling.LANCZOS)
            final_canvas = Image.alpha_composite(bg, ink_img).convert("RGB")
            payload_images.append(final_canvas)
            
        # 2. Grab Paper Photo (if provided)
        if camera_picture:
            paper_img = Image.open(camera_picture).convert('RGB')
            paper_img.thumbnail((1024, 1024))
            payload_images.append(paper_img)
            
        if not payload_images:
            st.error("Please draw your workings on the canvas or snap a photo first!")
        else:
            with st.spinner("The AI Tutor is reviewing your workings..."):
                try:
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    prompt = f"""
                    You are a gentle, encouraging math tutor grading an algebra problem.
                    The equations provided to the student are: {', '.join(eqs)}
                    The mathematically correct final solutions are: {sol_str}.
                    
                    The student has provided their workings as images. This might be a digital drawing, a photo of paper, or both.
                    Please check all provided images. For the digital canvas, they are writing in {current_color_name} ink. Treat other colors as older mistakes.
                    
                    1. Look at their step-by-step algebra across all images.
                    2. If their final answer is completely correct and explicitly states the final values, reply EXACTLY with "CORRECT:" on the first line, followed by a brief congratulatory message.
                    3. If their working is incorrect or incomplete, reply EXACTLY with "INCORRECT:" on the first line. Briefly explain where they went wrong, but do not give them the final answer.
                    """
                    
                    response = client.models.generate_content(model='gemini-3.6-flash', contents=[prompt] + payload_images)
                    resp_text = response.text.strip()
                    
                    if resp_text.upper().startswith("CORRECT"):
                        st.session_state.is_correct = True
                        st.session_state.ai_feedback = re.sub(r'(?i)^CORRECT:?\s*', '', resp_text)
                    else:
                        st.session_state.is_correct = False
                        st.session_state.ai_feedback = re.sub(r'(?i)^INCORRECT:?\s*', '', resp_text)
                        st.session_state.color_index = (st.session_state.color_index + 1) % len(PEN_COLORS)
                    
                    st.session_state.scroll_to_top = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Oops! The tutor had a glitch: {e}")

    # Render Feedback
    if st.session_state.ai_feedback:
        if st.session_state.is_correct:
            st.success(f"🌟 **Awesome job!** {st.session_state.ai_feedback}")
        else:
            st.warning(f"🤖 **Tutor says:** {st.session_state.ai_feedback}")

    st.write("")
    if st.button("Give me a new problem!", use_container_width=True):
        st.session_state.generating = True
        st.session_state.scroll_to_top = True
        st.rerun()