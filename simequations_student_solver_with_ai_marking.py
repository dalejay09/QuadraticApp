import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import random
import string
import math
import io
import re
import base64
from PIL import Image
from google import genai
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

# --- Configuration ---
st.set_page_config(page_title="Algebra 101", page_icon="🧮", layout="centered")
PEN_COLORS = ["#1E90FF", "#FF2400", "#32CD32", "#9400D3", "#FF8C00"]
COLOR_NAMES = ["BLUE", "RED", "GREEN", "PURPLE", "ORANGE"]

# --- Custom CSS ---
st.markdown("""
    <style>
    /* Custom Styling for Primary Buttons */
    button[kind="primary"] {
        background-color: #007AFF !important;
        border-color: #007AFF !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background-color: #0056b3 !important;
        border-color: #0056b3 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Math Engine: ALGEBRA ---
def get_valid_vars(count):
    # Exclude constants and confusing letters
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

def generate_algebra_problem():
    var_count = st.session_state.get('var_count', 1)
    vars = get_valid_vars(var_count)
    
    if var_count == 1:
        v = vars[0]
        ans = random.randint(-10, 10)
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
        return [eq_str], {v: ans}, vars, 450

    elif var_count == 2:
        v1, v2 = vars
        ans1, ans2 = random.randint(-6, 6), random.randint(-6, 6)
        
        while True:
            a1, b1 = random.randint(-4, 4), random.randint(-4, 4)
            a2, b2 = random.randint(-4, 4), random.randint(-4, 4)
            if a1 == 0 and b1 == 0: continue
            if a2 == 0 and b2 == 0: continue
            if a1 * b2 - a2 * b1 != 0: break # Determinant != 0 ensures unique solution
            
        c1 = a1 * ans1 + b1 * ans2
        c2 = a2 * ans1 + b2 * ans2
        
        eq1 = f"{fmt_expr([a1, b1], vars)} = {c1}"
        eq2 = f"{fmt_expr([a2, b2], vars)} = {c2}"
        return [eq1, eq2], {v1: ans1, v2: ans2}, vars, 650

    elif var_count == 3:
        v1, v2, v3 = vars
        ans1, ans2, ans3 = random.randint(-4, 4), random.randint(-4, 4), random.randint(-4, 4)
        
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
        
        return [eq1, eq2, eq3], {v1: ans1, v2: ans2, v3: ans3}, vars, 800

# --- Visual Engine: BACKEND MATPLOTLIB ---
def draw_equations(eqs, height_px):
    width_px = 350
    fig, ax = plt.subplots(figsize=(width_px/100, height_px/100), dpi=100) 
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    font_size = 20 if len(eqs) <= 2 else 16
    y_start = 0.90
    y_step = 0.08 if height_px <= 450 else 0.06
    
    for i, eq in enumerate(eqs):
        ax.text(0.5, y_start - i * y_step, f"${eq}$", fontsize=font_size, ha='center', va='top')
    
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
if 'input_mode' not in st.session_state: st.session_state.input_mode = "🖌️ Digital Canvas"
if 'color_index' not in st.session_state: st.session_state.color_index = 0
if 'stroke_history' not in st.session_state: st.session_state.stroke_history = [[]]
if 'active_initial_drawing' not in st.session_state: st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
if 'is_correct' not in st.session_state: st.session_state.is_correct = False

def handle_settings_change():
    st.session_state.generating = True

col1, col2 = st.columns([5, 1])
with col1:
    st.title("Algebra 101")
with col2:
    with st.popover("⚙️", use_container_width=True):
        st.radio("Variables", [1, 2, 3], key="var_count", on_change=handle_settings_change)

if st.session_state.generating:
    with st.spinner("Generating equations..."):
        eqs, solutions, vars_list, canvas_height = generate_algebra_problem()
        st.session_state.math_data = (eqs, solutions, vars_list, canvas_height)
        st.session_state.bg_image = draw_equations(eqs, canvas_height)
        
        st.session_state.ai_feedback = ""
        st.session_state.color_index = 0 
        st.session_state.is_correct = False
        st.session_state.stroke_history = [[]]
        st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
        st.session_state.canvas_key += 1 
        st.session_state.generating = False
        st.rerun()

else:
    eqs, solutions, vars_list, canvas_height = st.session_state.math_data
    sol_str = ", ".join([f"{k} = {v}" for k, v in solutions.items()])
    
    st.radio("Input Method:", ["🖌️ Digital Canvas", "📸 Paper & Camera"], key="input_mode", horizontal=True)

    if st.session_state.input_mode == "🖌️ Digital Canvas":
        current_color_hex = PEN_COLORS[st.session_state.color_index]
        current_color_name = COLOR_NAMES[st.session_state.color_index]
        st.write(f"Solve for **{', '.join(vars_list)}**! Current pen: **{current_color_name}**")

        tool = st.radio("Tool", ["🖌️ Pen", "🧽 Tap-Eraser"], horizontal=True, label_visibility="collapsed")
        active_stroke_color = current_color_hex if tool == "🖌️ Pen" else "#FFFFFE"
        active_stroke_width = 3 if tool == "🖌️ Pen" else 15

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

        col_u, col_c = st.columns(2)
        with col_u:
            if st.button("↩️ Undo", use_container_width=True):
                if len(st.session_state.stroke_history) > 1:
                    st.session_state.stroke_history.pop()
                    last_valid = st.session_state.stroke_history[-1]
                    st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": last_valid}
                    st.session_state.canvas_key += 1
                    st.rerun()
        with col_c:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.stroke_history = [[]]
                st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
                st.session_state.color_index = 0
                st.session_state.canvas_key += 1
                st.rerun()

        current_objects = canvas_result.json_data.get("objects", []) if canvas_result.json_data else []
        last_saved_objects = st.session_state.stroke_history[-1]

        if len(current_objects) > len(last_saved_objects):
            new_stroke = current_objects[-1]
            if new_stroke.get("stroke", "").upper() == "#FFFFFE":
                e_obj = new_stroke
                ew = e_obj.get("width", 0) * e_obj.get("scaleX", 1)
                eh = e_obj.get("height", 0) * e_obj.get("scaleY", 1)
                e_left = e_obj.get("left", 0)
                e_top = e_obj.get("top", 0)
                
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

        st.write("---")
        
        if st.button("Check My Answer!", type="primary", use_container_width=True):
            if canvas_result.image_data is not None:
                with st.spinner("The AI Tutor is reviewing your algebra..."):
                    try:
                        ink_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        bg = st.session_state.bg_image.convert("RGBA")
                        if ink_img.size != bg.size:
                            ink_img = ink_img.resize(bg.size, Image.Resampling.LANCZOS)
                        final_canvas = Image.alpha_composite(bg, ink_img).convert("RGB")
                        
                        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                        prompt = f"""
                        You are a gentle, encouraging math tutor grading an algebra problem.
                        The equations provided to the student are: {', '.join(eqs)}
                        The mathematically correct final solutions are: {sol_str}.
                        
                        The student is writing in {current_color_name} ink on a digital canvas. Treat other colors as older mistakes.
                        1. Look at their step-by-step algebra.
                        2. If their {current_color_name} final answer is completely correct and explicitly states the final values, reply EXACTLY with "CORRECT:" on the first line, followed by a brief congratulatory message.
                        3. If their {current_color_name} working is incorrect or incomplete, reply EXACTLY with "INCORRECT:" on the first line. Briefly explain where they went wrong, but do not give them the final answer.
                        """
                        
                        response = client.models.generate_content(model='gemini-3.6-flash', contents=[prompt, final_canvas])
                        resp_text = response.text.strip()
                        
                        if resp_text.upper().startswith("CORRECT"):
                            st.session_state.is_correct = True
                            st.session_state.ai_feedback = re.sub(r'(?i)^CORRECT:?\s*', '', resp_text)
                        else:
                            st.session_state.is_correct = False
                            st.session_state.ai_feedback = re.sub(r'(?i)^INCORRECT:?\s*', '', resp_text)
                            st.session_state.color_index = (st.session_state.color_index + 1) % len(PEN_COLORS)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Oops! The tutor had a glitch: {e}")

    else:
        # Camera Mode UI
        st.write(f"Solve for **{', '.join(vars_list)}** on paper, then snap a photo!")
        for eq in eqs:
            st.latex(eq)
            
        picture = st.file_uploader("Upload or take a photo of your working:", type=['png', 'jpg', 'jpeg'])
        
        if picture:
            if st.button("Check My Answer!", type="primary", use_container_width=True):
                with st.spinner("The AI Tutor is reading your paper..."):
                    try:
                        img = Image.open(picture).convert('RGB')
                        img.thumbnail((1024, 1024))
                        
                        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                        prompt = f"""
                        You are a gentle, encouraging math tutor grading an algebra problem.
                        The equations provided to the student are: {', '.join(eqs)}
                        The mathematically correct final solutions are: {sol_str}.
                        
                        The student has uploaded a photo of their handwritten working.
                        1. Look at their step-by-step algebra.
                        2. If their final answer is completely correct and explicitly states the final values, reply EXACTLY with "CORRECT:" on the first line, followed by a brief congratulatory message.
                        3. If their working is incorrect or incomplete, reply EXACTLY with "INCORRECT:" on the first line. Briefly explain where they went wrong, but do not give them the final answer.
                        """
                        
                        response = client.models.generate_content(model='gemini-3.6-flash', contents=[prompt, img])
                        resp_text = response.text.strip()
                        
                        if resp_text.upper().startswith("CORRECT"):
                            st.session_state.is_correct = True
                            st.session_state.ai_feedback = re.sub(r'(?i)^CORRECT:?\s*', '', resp_text)
                        else:
                            st.session_state.is_correct = False
                            st.session_state.ai_feedback = re.sub(r'(?i)^INCORRECT:?\s*', '', resp_text)
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
        st.rerun()