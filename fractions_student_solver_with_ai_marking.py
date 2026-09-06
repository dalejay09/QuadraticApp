import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import random
import math
import io
import re
import base64
from PIL import Image
from itertools import combinations
from google import genai

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
PEN_COLORS = ["#1E90FF", "#FF2400", "#32CD32", "#9400D3", "#FF8C00"]
COLOR_NAMES = ["BLUE", "RED", "GREEN", "PURPLE", "ORANGE"]

# --- Math Engine: FRACTIONS ---
def generate_fraction_problem():
    max_lcm = st.session_state.get('max_lcm', 100)
    
    if max_lcm <= 100:
        pool = list(range(2, 11))
    else:
        pool = list(range(2, 16)) + [20, 30, 40, 50, 60, 70, 80, 90, 100]
        
    rand_val = random.random()
    if rand_val < 0.4:
        variant = 1 
    elif rand_val < 0.6:
        variant = 2 
    elif rand_val < 0.8:
        variant = 3 
    else:
        variant = 4 
        
    valid_combinations = []
    
    if variant == 1:
        for c in combinations(pool, 3):
            L = math.lcm(math.lcm(c[0], c[1]), c[2])
            if L <= max_lcm and L not in c:
                valid_combinations.append(list(c))
    elif variant == 2:
        for c in combinations(pool, 3):
            L = math.lcm(math.lcm(c[0], c[1]), c[2])
            if L <= max_lcm and L in c:
                valid_combinations.append(list(c))
    elif variant == 3:
        for L in pool:
            if L <= max_lcm:
                for f in pool:
                    if L != f and L % f == 0:
                        valid_combinations.append([L, L, f])
    elif variant == 4:
        for L in pool:
            if L <= max_lcm:
                for f in pool:
                    if L != f and L % f == 0:
                        valid_combinations.append([L, f, f])
                        
    if not valid_combinations:
        valid_combinations = [[2, 3, 4]]
        
    chosen_denoms = random.choice(valid_combinations)
    random.shuffle(chosen_denoms) 
    d1, d2, d3 = chosen_denoms
    lcm = math.lcm(math.lcm(d1, d2), d3)
    
    while True:
        n1 = random.randint(1, d1 - 1)
        n2 = random.randint(1, d2 - 1)
        n3 = random.randint(1, d3 - 1)
        
        op1 = random.choice(['+', '-'])
        op2 = random.choice(['+', '-'])
        
        v1 = n1 / d1
        v2 = n2 / d2 if op1 == '+' else -n2 / d2
        v3 = n3 / d3 if op2 == '+' else -n3 / d3
        
        if v1 + v2 + v3 > 0:
            break
            
    eq_str = f"{n1}/{d1} {op1} {n2}/{d2} {op2} {n3}/{d3}"
    
    # Calculate exact unsimplified target numerator
    target_num = int(v1 * lcm + v2 * lcm + v3 * lcm)
    
    return n1, d1, op1, n2, d2, op2, n3, d3, eq_str, lcm, target_num

# --- Visual Engine: BACKEND MATPLOTLIB ---
def draw_fraction_equation(n1, d1, op1, n2, d2, op2, n3, d3):
    fig, ax = plt.subplots(figsize=(3.5, 2.0), dpi=100) 
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    fontsize = 28
    
    ax.text(0.15, 0.5, rf"$\frac{{{n1}}}{{{d1}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.30, 0.5, op1, fontsize=fontsize, ha='center', va='center')
    ax.text(0.45, 0.5, rf"$\frac{{{n2}}}{{{d2}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.60, 0.5, op2, fontsize=fontsize, ha='center', va='center')
    ax.text(0.75, 0.5, rf"$\frac{{{n3}}}{{{d3}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.90, 0.5, "=", fontsize=fontsize, ha='center', va='center')
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    
    return Image.open(buf).convert('RGBA').copy()

# --- Memory Stack Initialization ---
if 'generating' not in st.session_state:
    st.session_state.generating = True
if 'ai_feedback' not in st.session_state:
    st.session_state.ai_feedback = ""
if 'canvas_key' not in st.session_state:
    st.session_state.canvas_key = 0 
if 'max_lcm' not in st.session_state:
    st.session_state.max_lcm = 100
if 'color_index' not in st.session_state:
    st.session_state.color_index = 0
if 'stroke_history' not in st.session_state:
    st.session_state.stroke_history = [[]]
if 'active_initial_drawing' not in st.session_state:
    st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
if 'local_checked' not in st.session_state:
    st.session_state.local_checked = False
if 'is_correct' not in st.session_state:
    st.session_state.is_correct = False

def handle_settings_change():
    st.session_state.generating = True

col1, col2 = st.columns([5, 1])
with col1:
    st.title("Fraction Master!")
with col2:
    with st.popover("⚙️", use_container_width=True):
        st.radio("Max LCM Limit", [50, 100, 200], key="max_lcm", on_change=handle_settings_change)

current_color_hex = PEN_COLORS[st.session_state.color_index]
current_color_name = COLOR_NAMES[st.session_state.color_index]

if st.session_state.generating:
    with st.spinner("Generating problem..."):
        n1, d1, op1, n2, d2, op2, n3, d3, eq_str, lcm, target_num = generate_fraction_problem()
        st.session_state.math_data = (eq_str, lcm, target_num)
        st.session_state.bg_image = draw_fraction_equation(n1, d1, op1, n2, d2, op2, n3, d3)
        st.session_state.ai_feedback = ""
        st.session_state.color_index = 0 
        st.session_state.local_checked = False
        st.session_state.is_correct = False
        
        st.session_state.stroke_history = [[]]
        st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
        st.session_state.canvas_key += 1 
        
        st.session_state.generating = False
        st.rerun()

else:
    eq_str, lcm, target_num = st.session_state.math_data
    
    st.write(f"Cross out the denominators! Current pen: **{current_color_name}**")
    
    tool = st.radio("Tool Selection", ["🖌️ Pen", "🧽 Tap-Eraser"], horizontal=True, label_visibility="collapsed")
    
    active_stroke_color = current_color_hex if tool == "🖌️ Pen" else "#FFFFFE"
    active_stroke_width = 3 if tool == "🖌️ Pen" else 15

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", 
        stroke_width=active_stroke_width, 
        stroke_color=active_stroke_color,
        background_image=st.session_state.bg_image,
        update_streamlit=True,
        height=200,
        width=350,
        drawing_mode="freedraw",
        return_image_data=True, 
        initial_drawing=st.session_state.active_initial_drawing, 
        key=f"canvas_{st.session_state.canvas_key}",
    )

    # --- THE BOUNDING BOX COLLISION ENGINE ---
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
            E_L = e_left - pad
            E_R = e_left + ew + pad
            E_T = e_top - pad
            E_B = e_top + eh + pad
            
            objects_to_keep = []
            
            for obj in last_saved_objects:
                ow = obj.get("width", 0) * obj.get("scaleX", 1)
                oh = obj.get("height", 0) * obj.get("scaleY", 1)
                o_left = obj.get("left", 0)
                o_top = obj.get("top", 0)
                
                T_L = o_left
                T_R = o_left + ow
                T_T = o_top
                T_B = o_top + oh
                
                overlap = not (E_R < T_L or E_L > T_R or E_B < T_T or E_T > T_B)
                if not overlap:
                    objects_to_keep.append(obj)
            
            st.session_state.stroke_history.append(objects_to_keep)
            st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": objects_to_keep}
            st.session_state.canvas_key += 1
            st.rerun()
            
        else:
            st.session_state.stroke_history.append(current_objects.copy())

    # --- CANVAS CONTROLS ---
    col_undo, col_clear = st.columns(2)
    with col_undo:
        if st.button("↩️ Undo Last", use_container_width=True):
            if len(st.session_state.stroke_history) > 1:
                st.session_state.stroke_history.pop()
                last_valid = st.session_state.stroke_history[-1]
                st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": last_valid}
                st.session_state.canvas_key += 1
                st.rerun()
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.stroke_history = [[]]
            st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
            st.session_state.color_index = 0
            st.session_state.canvas_key += 1
            st.rerun()

    st.write("---")
    st.write("**Final Answer:**")
    
    # --- HYBRID NATIVE INPUT ---
    col_num, col_div, col_den = st.columns([2, 1, 2])
    user_num = col_num.number_input("Numerator", step=1, value=None, label_visibility="collapsed", placeholder="Top")
    col_div.markdown("<h3 style='text-align:center; margin-top:5px;'>/</h3>", unsafe_allow_html=True)
    user_den = col_den.number_input("Denominator", step=1, value=None, label_visibility="collapsed", placeholder="Bottom")

    if st.button("Check My Answer!", type="primary", use_container_width=True):
        if user_num is not None and user_den is not None and user_den != 0:
            st.session_state.local_checked = True
            
            # Cross-multiplication checks for mathematically equivalent fractions (handles unsimplified answers perfectly)
            if user_num * lcm == target_num * user_den:
                st.session_state.is_correct = True
                st.session_state.ai_feedback = "🌟 **Awesome job!** Your math is absolutely perfect!"
            else:
                st.session_state.is_correct = False
                st.session_state.ai_feedback = ""
        else:
            st.error("Please type your final numerator and denominator!")

    if st.session_state.local_checked:
        if st.session_state.is_correct:
            st.success(st.session_state.ai_feedback)
        else:
            st.warning("💡 **Almost there!** The final fraction isn't quite right.")
            
            if st.button("🤖 Ask AI Tutor to check my working", use_container_width=True):
                if canvas_result.image_data is not None:
                    with st.spinner("The AI Tutor is reviewing your scribbles..."):
                        try:
                            ink_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                            bg = st.session_state.bg_image.convert("RGBA")
                            if ink_img.size != bg.size:
                                ink_img = ink_img.resize(bg.size, Image.Resampling.LANCZOS)
                            final_canvas = Image.alpha_composite(bg, ink_img).convert("RGB")
                            
                            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                            
                            prompt = f"""
                            You are a gentle, encouraging math tutor helping a 9-year-old learn to add and subtract fractions.
                            The problem is: {eq_str}. 
                            
                            The student typed their final answer as {user_num}/{user_den}. This is INCORRECT.
                            
                            I am sending you an image of their digital workspace. 
                            The student is writing in ink directly over the top of the black fractions to cross out denominators and write new equivalent fractions.
                            
                            IMPORTANT GRADING RULES:
                            1. Read their handwritten ink to figure out WHERE they went wrong before they typed {user_num}/{user_den}. 
                            2. Did they convert the denominators incorrectly? Did they mess up the addition/subtraction on top?
                            3. The LATEST attempt is written in {current_color_name} ink. Treat other colors as older mistakes.
                            
                            Reply EXACTLY with the word "INCORRECT:" on the first line. Gently explain where their handwritten logic went wrong to help them fix their typed answer. Keep your tone highly supportive.
                            """
                            
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=[prompt, final_canvas]
                            )
                            
                            resp_text = response.text.strip()
                            st.session_state.ai_feedback = re.sub(r'(?i)^INCORRECT:?\s*', '', resp_text)
                            st.session_state.color_index = (st.session_state.color_index + 1) % len(PEN_COLORS)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Oops! The tutor had a glitch: {e}")
                else:
                    st.error("Please draw your working on the canvas first!")

    if st.session_state.ai_feedback and not st.session_state.is_correct:
        st.info(f"**Tutor says:** {st.session_state.ai_feedback}")

    if st.button("Give me a new problem!", use_container_width=True):
        st.session_state.generating = True
        st.rerun()