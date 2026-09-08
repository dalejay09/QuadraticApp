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
    button[kind="primary"] {
        background-color: #007AFF !important;
        border-color: #007AFF !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background-color: #0056b3 !important;
        border-color: #0056b3 !important;
    }
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
        return [eq_str], {v: ans}, vars, 450, fallback, [[eq_str]] 

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
        canvas_eqs = [build_canvas_row([a1, b1], vars, c1), build_canvas_row([a2, b2], vars, c2)]
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
            det = (r1[0]*(r2[1]*r3[2] - r2[2]*r3[1]) - r1[1]*(r2[0]*r3[2] - r2[2]*r3[0]) + r1[2]*(r2[0]*r3[1] - r2[1]*r3[0]))
            if det != 0: break
        c1 = r1[0]*ans1 + r1[1]*ans2 + r1[2]*ans3
        c2 = r2[0]*ans1 + r2[1]*ans2 + r2[2]*ans3
        c3 = r3[0]*ans1 + r3[1]*ans2 + r3[2]*ans3
        eq1 = f"{fmt_expr(r1, vars)} = {c1}"
        eq2 = f"{fmt_expr(r2, vars)} = {c2}"
        eq3 = f"{fmt_expr(r3, vars)} = {c3}"
        fallback = f"Solution: {v1}={ans1}, {v2}={ans2}, {v3}={ans3}\n(Check via substitution)"
        canvas_eqs = [build_canvas_row(r1, vars, c1), build_canvas_row(r2, vars, c2), build_canvas_row(r3, vars, c3)]
        return [eq1, eq2, eq3], {v1: ans1, v2: ans2, v3: ans3}, vars, 800, fallback, canvas_eqs

# --- Integrated AI-PDF Generation Engine ---
def create_pdf_bytes(var_count):
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        problems = [generate_algebra_problem(var_count) for _ in range(20)]
        ai_steps = {}
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            payload = "".join([f"Q{i+1}: Eqs: [{' ; '.join(p[0])}] | Ans: [{', '.join([f'{k}={v}' for k,v in p[1].items()])}]\n" for i, p in enumerate(problems)])
            prompt = f"Write the concise, human-readable step-by-step solution method for each problem. Keep it very brief. Plain text formatting.\nData:\n{payload}"
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[prompt],
                config=dict(response_mime_type="application/json", response_schema=AIWorksheetSolutions, temperature=0.1)
            )
            for item in json.loads(response.text).get("solutions", []):
                ai_steps[item["q_num"]] = item["steps"].replace("**", "")
        except Exception as e:
            pass
        
        fig, axes = plt.subplots(figsize=(8.27, 11.69))
        axes.axis('off')
        axes.text(0.5, 0.95, f"Algebra 101 Worksheet ({var_count} Variable{'s' if var_count>1 else ''})", fontsize=16, fontweight='bold', ha='center')
        for i in range(10):
            axes.text(0.05, 0.88 - (i*0.085), f"Q{i+1}:\n{chr(10).join(problems[i][0])}", fontsize=11, va='top')
            axes.text(0.55, 0.88 - (i*0.085), f"Q{i+11}:\n{chr(10).join(problems[i+10][0])}", fontsize=11, va='top')
        pdf.savefig(fig); plt.close(fig)

        fig_ans, ax_ans = plt.subplots(figsize=(8.27, 11.69))
        ax_ans.axis('off')
        ax_ans.text(0.5, 0.95, "Algebra 101 Answer Key", fontsize=16, fontweight='bold', ha='center')
        for i in range(10):
            ax_ans.text(0.05, 0.88 - (i*0.085), f"Q{i+1}: {', '.join([f'{k} = {v}' for k, v in problems[i][1].items()])}", fontsize=11, va='top')
            ax_ans.text(0.55, 0.88 - (i*0.085), f"Q{i+11}: {', '.join([f'{k} = {v}' for k, v in problems[i+10][1].items()])}", fontsize=11, va='top')
        pdf.savefig(fig_ans); plt.close(fig_ans)

        for page_idx in range(2):
            fig_app, ax_app = plt.subplots(figsize=(8.27, 11.69))
            ax_app.axis('off')
            ax_app.text(0.5, 0.95, f"Solutions Appendix (Page {page_idx+1})", fontsize=14, fontweight='bold', ha='center')
            offset = page_idx * 10
            for i in range(5):
                txt_L = f"Q{offset+i+1}:\n{chr(10).join(problems[offset+i][0])}\n\n{ai_steps.get(offset+i+1, problems[offset+i][4])}"
                ax_app.text(0.05, 0.88 - (i*0.17), txt_L, fontsize=8, va='top', wrap=True)
                txt_R = f"Q{offset+i+6}:\n{chr(10).join(problems[offset+i+5][0])}\n\n{ai_steps.get(offset+i+6, problems[offset+i+5][4])}"
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
    
    font_size = 20 if len(canvas_eqs) <= 2 else 16
    y_start, y_step = 0.90, 0.08 if height_px <= 450 else 0.06
    
    for i, row in enumerate(canvas_eqs):
        y = y_start - i * y_step
        if len(row) == 1:
            ax.text(0.5, y, f"${row[0]}$", fontsize=font_size, ha='center', va='top')
        else:
            num_vars = len(row) - 2
            x_coords = [0.38, 0.58] if num_vars == 2 else [0.26, 0.46, 0.66]
            x_eq, x_rhs = (0.65, 0.70) if num_vars == 2 else (0.72, 0.77)
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
if 'tool_selector' not in st.session_state: st.session_state.tool_selector = "🖌️"
if 'experimental_toolbar_key' not in st.session_state: st.session_state.experimental_toolbar_key = 0

def handle_settings_change():
    st.session_state.generating = True
    st.session_state.pdf_bytes = None

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
                with st.spinner("Compiling Master PDF..."):
                    st.session_state.pdf_bytes = create_pdf_bytes(st.session_state.var_count)
                st.rerun()
        else:
            st.download_button(label="⬇️ Download Worksheet", data=st.session_state.pdf_bytes, file_name=f"Algebra_101.pdf", mime="application/pdf", use_container_width=True, type="primary")
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
        st.radio("Variables", [1, 2, 3], key="var_count", on_change=handle_settings_change)
        st.radio("Camera Mode", ["App", "Native"], key="camera_mode", horizontal=True)

if st.session_state.generating:
    with st.spinner("Generating equations..."):
        if len(st.session_state.get("math_data", [])) == 6:
            eqs, solutions, vars_list, canvas_height, fallback, canvas_eqs = generate_algebra_problem()
        else:
            eqs, solutions, vars_list, canvas_height, fallback, canvas_eqs = generate_algebra_problem()
        st.session_state.math_data = (eqs, solutions, vars_list, canvas_height, fallback, canvas_eqs)
        st.session_state.bg_image = draw_equations(canvas_eqs, canvas_height)
        st.session_state.ai_feedback, st.session_state.color_index, st.session_state.is_correct = "", 0, False
        st.session_state.stroke_history, st.session_state.active_initial_drawing = [[]], {"version": "4.4.0", "objects": []}
        st.session_state.canvas_key += 1; st.session_state.generating = False
        st.rerun()

else:
    eqs, solutions, vars_list, canvas_height, fallback, canvas_eqs = st.session_state.math_data
    sol_str = ", ".join([f"{k} = {v}" for k, v in solutions.items()])
    
    st.write(f"Solve for **{', '.join(vars_list)}**! Current pen: **{COLOR_NAMES[st.session_state.color_index]}**")

    # --- 1. Main Drawing Canvas ---
    active_stroke_color = PEN_COLORS[st.session_state.color_index] if st.session_state.tool_selector == "🖌️" else "#FFFFFE"
    active_stroke_width = 3 if st.session_state.tool_selector == "🖌️" else 15

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", stroke_width=active_stroke_width, stroke_color=active_stroke_color,
        background_image=st.session_state.bg_image, update_streamlit=True, height=canvas_height, width=350,
        drawing_mode="freedraw", return_image_data=True, initial_drawing=st.session_state.active_initial_drawing, 
        key=f"canvas_{st.session_state.canvas_key}"
    )

    # --- 2. EXPERIMENTAL Transform Canvas Toolbar ---
    st.caption("🔬 *Experimental Canvas Toolbar (Drag an icon slightly to trigger it!)*")
    
    # Baseline coordinates for the icons
    baselines = {"🖌️": 20, "🧽": 90, "↩️": 160, "🗑️": 230, "📸": 300}
    toolbar_initial = {
        "version": "4.4.0",
        "objects": [{"type": "i-text", "text": icon, "left": pos, "top": 5, "fontSize": 24, "selectable": True, "hasControls": False, "hasBorders": True} for icon, pos in baselines.items()]
    }

    # FIX: "transform" mode was physically removed from the package. Forced to fallback to "freedraw". 
    toolbar_result = st_canvas(
        fill_color="rgba(0,0,0,0)", stroke_width=0, background_color="#e5e7eb", update_streamlit=True,
        height=45, width=350, drawing_mode="freedraw", initial_drawing=toolbar_initial,
        key=f"exp_toolbar_{st.session_state.experimental_toolbar_key}"
    )

    # Process Experimental Interaction
    if toolbar_result.json_data is not None:
        for obj in toolbar_result.json_data.get("objects", []):
            text = obj.get("text", "")
            if text in baselines:
                if abs(obj.get("left", baselines[text]) - baselines[text]) > 2 or abs(obj.get("top", 5) - 5) > 2:
                    st.toast(f"Experimental Canvas Detected: {text}")
                    if text in ["🖌️", "🧽"]: st.session_state.tool_selector = text
                    if text == "↩️" and len(st.session_state.stroke_history) > 1:
                        st.session_state.stroke_history.pop()
                        st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": st.session_state.stroke_history[-1]}
                        st.session_state.canvas_key += 1
                    if text == "🗑️":
                        st.session_state.stroke_history, st.session_state.active_initial_drawing = [[]], {"version": "4.4.0", "objects": []}
                        st.session_state.canvas_key += 1
                    if text == "📸":
                        st.session_state.show_camera_supplement = not st.session_state.show_camera_supplement
                        
                    st.session_state.experimental_toolbar_key += 1
                    st.rerun()

    # --- 3. The Native Toolbar (Retained for comparison) ---
    t_col1, t_col2, t_col3, t_col4 = st.columns([1.5, 1, 1, 1.2])
    with t_col1: st.radio("Tool", ["🖌️", "🧽"], horizontal=True, label_visibility="collapsed", key="tool_selector_native")
    with t_col2:
        if st.button("↩️", use_container_width=True):
            if len(st.session_state.stroke_history) > 1:
                st.session_state.stroke_history.pop()
                st.session_state.active_initial_drawing, st.session_state.canvas_key = {"version": "4.4.0", "objects": st.session_state.stroke_history[-1]}, st.session_state.canvas_key + 1
                st.rerun()
    with t_col3:
        if st.button("🗑️", use_container_width=True):
            st.session_state.stroke_history, st.session_state.active_initial_drawing, st.session_state.canvas_key = [[]], {"version": "4.4.0", "objects": []}, st.session_state.canvas_key + 1
            st.rerun()
    with t_col4:
        if st.button("📸 Paper", use_container_width=True):
            st.session_state.show_camera_supplement = not st.session_state.show_camera_supplement
            st.rerun()
            
    # Eraser Logic
    current_objects = canvas_result.json_data.get("objects", []) if canvas_result.json_data else []
    if len(current_objects) > len(st.session_state.stroke_history[-1]):
        if current_objects[-1].get("stroke", "").upper() == "#FFFFFE":
            e = current_objects[-1]
            E_L, E_R, E_T, E_B = e.get("left",0)-15, e.get("left",0)+(e.get("width",0)*e.get("scaleX",1))+15, e.get("top",0)-15, e.get("top",0)+(e.get("height",0)*e.get("scaleY",1))+15
            objects_to_keep = [obj for obj in st.session_state.stroke_history[-1] if not (E_R < obj.get("left",0) or E_L > obj.get("left",0)+(obj.get("width",0)*obj.get("scaleX",1)) or E_B < obj.get("top",0) or E_T > obj.get("top",0)+(obj.get("height",0)*obj.get("scaleY",1)))]
            st.session_state.stroke_history.append(objects_to_keep)
            st.session_state.active_initial_drawing, st.session_state.canvas_key = {"version": "4.4.0", "objects": objects_to_keep}, st.session_state.canvas_key + 1
            st.rerun()
        else:
            st.session_state.stroke_history.append(current_objects.copy())

    # --- Unified AI Processing ---
    camera_picture = None
    if st.session_state.show_camera_supplement:
        camera_picture = st.camera_input("Snap a photo:") if st.session_state.get('camera_mode', 'App') == 'App' else st.file_uploader("Upload photo:", type=['png', 'jpg'])

    st.write("---")
    if st.button("Check My Answer!", type="primary", use_container_width=True):
        payload_images = []
        if canvas_result.image_data is not None and len(st.session_state.stroke_history[-1]) > 0:
            ink = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').resize(st.session_state.bg_image.size, Image.Resampling.LANCZOS)
            payload_images.append(Image.alpha_composite(st.session_state.bg_image.convert("RGBA"), ink).convert("RGB"))
        if camera_picture: payload_images.append(Image.open(camera_picture).convert('RGB').resize((1024, 1024)))
            
        if not payload_images: st.error("Please draw your workings on the canvas or snap a photo first!")
        else:
            with st.spinner("Reviewing your workings..."):
                try:
                    response = genai.Client(api_key=st.secrets["GEMINI_API_KEY"]).models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[f"Grade this algebra problem. Equations: {', '.join(eqs)}. Answers: {sol_str}. Current canvas ink: {COLOR_NAMES[st.session_state.color_index]}. If completely correct and states final answer, reply 'CORRECT:'. Else reply 'INCORRECT:' with a brief hint."] + payload_images
                    )
                    if response.text.strip().upper().startswith("CORRECT"):
                        st.session_state.is_correct, st.session_state.ai_feedback = True, re.sub(r'(?i)^CORRECT:?\s*', '', response.text.strip())
                    else:
                        st.session_state.is_correct, st.session_state.ai_feedback = False, re.sub(r'(?i)^INCORRECT:?\s*', '', response.text.strip())
                        st.session_state.color_index = (st.session_state.color_index + 1) % len(PEN_COLORS)
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    if st.session_state.ai_feedback:
        st.success(f"🌟 **Awesome job!** {st.session_state.ai_feedback}") if st.session_state.is_correct else st.warning(f"🤖 **Tutor says:** {st.session_state.ai_feedback}")

    st.write("")
    if st.button("Give me a new problem!", use_container_width=True):
        st.session_state.generating, st.session_state.scroll_to_top = True, True
        st.rerun()