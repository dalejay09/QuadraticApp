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
PEN_COLORS = ["#1E90FF", "#FF2400", "#32CD32", "#9400D3", "#FF8C00"]
COLOR_NAMES = ["BLUE", "RED", "GREEN", "PURPLE", "ORANGE"]

# --- Math Engine: FRACTIONS ---
def generate_fraction_problem():
    max_lcm = st.session_state.get('max_lcm', 100)
    frac_count = st.session_state.get('frac_count', 3)
    
    pool = list(range(2, 11)) if max_lcm <= 100 else list(range(2, 16)) + [20, 30, 40, 50, 60, 70, 80, 90, 100]
        
    if frac_count == 1:
        # --- 1 FRACTION (SIMPLIFICATION) LOGIC ---
        while True:
            d = random.choice(pool)
            n = random.randint(1, d - 1)
            if math.gcd(n, d) == 1:
                break
        
        # Multiply both by a random factor to create a simplifiable fraction
        k = random.randint(2, max(2, 100 // d))
        n1, d1 = n * k, d * k
        eq_str = f"{n1}/{d1}"
        return n1, d1, None, None, None, None, None, None, eq_str, d1, n1, d1

    elif frac_count == 3:
        # --- 3 FRACTION LOGIC (+ and - only) ---
        rand_val = random.random()
        if rand_val < 0.4: variant = 1 
        elif rand_val < 0.6: variant = 2 
        elif rand_val < 0.8: variant = 3 
        else: variant = 4 
            
        valid_combinations = []
        if variant == 1:
            for c in combinations(pool, 3):
                L = math.lcm(math.lcm(c[0], c[1]), c[2])
                if L <= max_lcm and L not in c: valid_combinations.append(list(c))
        elif variant == 2:
            for c in combinations(pool, 3):
                L = math.lcm(math.lcm(c[0], c[1]), c[2])
                if L <= max_lcm and L in c: valid_combinations.append(list(c))
        elif variant == 3:
            for L in pool:
                if L <= max_lcm:
                    for f in pool:
                        if L != f and L % f == 0: valid_combinations.append([L, L, f])
        elif variant == 4:
            for L in pool:
                if L <= max_lcm:
                    for f in pool:
                        if L != f and L % f == 0: valid_combinations.append([L, f, f])
                            
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
            
            v1_num = n1 * (lcm // d1)
            v2_num = n2 * (lcm // d2) if op1 == '+' else -n2 * (lcm // d2)
            v3_num = n3 * (lcm // d3) if op2 == '+' else -n3 * (lcm // d3)
            
            target_num = v1_num + v2_num + v3_num
            target_den = lcm
            
            if target_num > 0:
                break
                
        eq_str = f"{n1}/{d1} {op1} {n2}/{d2} {op2} {n3}/{d3}"
        return n1, d1, op1, n2, d2, op2, n3, d3, eq_str, lcm, target_num, target_den

    else:
        # --- 2 FRACTION LOGIC (+, -, and x) ---
        while True:
            d1 = random.choice(pool)
            d2 = random.choice(pool)
            n1 = random.randint(1, d1 - 1) if d1 > 1 else 1
            n2 = random.randint(1, d2 - 1) if d2 > 1 else 1
            
            op1 = random.choice(['+', '-', 'x'])
            
            if op1 == '+':
                target_num = (n1 * d2) + (n2 * d1)
                target_den = d1 * d2
            elif op1 == '-':
                target_num = (n1 * d2) - (n2 * d1)
                target_den = d1 * d2
            else:
                target_num = n1 * n2
                target_den = d1 * d2
                
            if target_num > 0:
                break
                
        eq_str = f"{n1}/{d1} {op1} {n2}/{d2}"
        lcm = math.lcm(d1, d2)
        return n1, d1, op1, n2, d2, None, None, None, eq_str, lcm, target_num, target_den

# --- Visual Engine: BACKEND MATPLOTLIB ---
def draw_fraction_equation(n1, d1, op1, n2, d2, op2, n3, d3):
    fig, ax = plt.subplots(figsize=(3.5, 2.0), dpi=100) 
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    fontsize = 28
    
    if op1 is None and n2 is None:
        # 1 Fraction Centered Layout (Simplification Mode)
        ax.text(0.35, 0.5, rf"$\frac{{{n1}}}{{{d1}}}$", fontsize=fontsize, ha='center', va='center')
        ax.text(0.50, 0.5, "=", fontsize=fontsize, ha='center', va='center')
        ax.plot([0.564, 0.692], [0.5, 0.5], color='black', lw=2)
    elif n3 is None:
        # 2 Fractions Centered Layout
        op1_disp = r'$\times$' if op1 == 'x' else op1
        ax.text(0.25, 0.5, rf"$\frac{{{n1}}}{{{d1}}}$", fontsize=fontsize, ha='center', va='center')
        ax.text(0.40, 0.5, op1_disp, fontsize=fontsize, ha='center', va='center')
        ax.text(0.55, 0.5, rf"$\frac{{{n2}}}{{{d2}}}$", fontsize=fontsize, ha='center', va='center')
        ax.text(0.70, 0.5, "=", fontsize=fontsize, ha='center', va='center')
        ax.plot([0.764, 0.892], [0.5, 0.5], color='black', lw=2)
    else:
        # 3 Fractions Wide Layout
        op1_disp = r'$\times$' if op1 == 'x' else op1
        op2_disp = r'$\times$' if op2 == 'x' else op2
        ax.text(0.10, 0.5, rf"$\frac{{{n1}}}{{{d1}}}$", fontsize=fontsize, ha='center', va='center')
        ax.text(0.23, 0.5, op1_disp, fontsize=fontsize, ha='center', va='center')
        ax.text(0.36, 0.5, rf"$\frac{{{n2}}}{{{d2}}}$", fontsize=fontsize, ha='center', va='center')
        ax.text(0.49, 0.5, op2_disp, fontsize=fontsize, ha='center', va='center')
        ax.text(0.62, 0.5, rf"$\frac{{{n3}}}{{{d3}}}$", fontsize=fontsize, ha='center', va='center')
        ax.text(0.75, 0.5, "=", fontsize=fontsize, ha='center', va='center')
        ax.plot([0.814, 0.942], [0.5, 0.5], color='black', lw=2)
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    
    return Image.open(buf).convert('RGBA').copy()

# --- Custom CSS for Compact UI ---
st.markdown("""
    <style>
    input[type="text"] {
        text-align: center;
        font-size: 1.2rem !important;
        font-weight: bold;
    }
    div.row-widget.stRadio > div {
        flex-direction: row;
        gap: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Memory Stack Initialization ---
if 'generating' not in st.session_state: st.session_state.generating = True
if 'ai_feedback' not in st.session_state: st.session_state.ai_feedback = ""
if 'canvas_key' not in st.session_state: st.session_state.canvas_key = 0 
if 'max_lcm' not in st.session_state: st.session_state.max_lcm = 100
if 'frac_count' not in st.session_state: st.session_state.frac_count = 3
if 'simplify_answers' not in st.session_state: st.session_state.simplify_answers = "No"
if 'current_frac_count' not in st.session_state: st.session_state.current_frac_count = 3
if 'color_index' not in st.session_state: st.session_state.color_index = 0
if 'stroke_history' not in st.session_state: st.session_state.stroke_history = [[]]
if 'active_initial_drawing' not in st.session_state: st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
if 'local_checked' not in st.session_state: st.session_state.local_checked = False
if 'is_correct' not in st.session_state: st.session_state.is_correct = False
if 'user_typed_num' not in st.session_state: st.session_state.user_typed_num = 0
if 'user_typed_den' not in st.session_state: st.session_state.user_typed_den = 1
if 'user_frac_input' not in st.session_state: st.session_state.user_frac_input = ""
if 'pending_frac_update' not in st.session_state: st.session_state.pending_frac_update = None

def handle_settings_change():
    st.session_state.generating = True

def handle_frac_count_change():
    if st.session_state.frac_count == 1:
        st.session_state.simplify_answers = "Yes"
    st.session_state.generating = True

def format_fraction_input():
    raw_input = st.session_state.user_frac_input
    if raw_input:
        match = re.match(r'^\s*(-?\d+)\s*[^\d]+\s*(-?\d+)\s*$', raw_input)
        if match:
            st.session_state.user_frac_input = f"{match.group(1)}/{match.group(2)}"

# --- Synchronous Phase Transition Engine ---
def process_correct_answer(user_num, user_den):
    if st.session_state.simplify_answers == "Yes":
        if math.gcd(user_num, user_den) == 1:
            st.session_state.is_correct = True
            st.session_state.local_checked = True
            st.session_state.ai_feedback = f"🌟 **Awesome job!** Your math is absolutely perfect and fully simplified! ({user_num}/{user_den})"
            return False
        else:
            if st.session_state.current_frac_count == 1:
                st.session_state.is_correct = False
                st.session_state.local_checked = True
                st.session_state.ai_feedback = f"💡 **Almost there!** {user_num}/{user_den} is mathematically correct, but it can be simplified further! Find a common factor."
                return False
            else:
                # Direct, Synchronous Phase Transition
                n1 = user_num
                d1 = user_den
                eq_str = f"{n1}/{d1}"
                
                st.session_state.math_data = (eq_str, d1, n1, d1)
                st.session_state.current_frac_count = 1
                st.session_state.bg_image = draw_fraction_equation(n1, d1, None, None, None, None, None, None)
                
                st.session_state.ai_feedback = f"🌟 **Awesome job!** You correctly found {n1}/{d1}. Now, can you simplify it to its lowest terms?"
                st.session_state.color_index = 0
                st.session_state.local_checked = False  
                st.session_state.is_correct = False
                
                # SAFELY clear the text box via the pending router to avoid crash
                st.session_state.pending_frac_update = "" 
                
                st.session_state.stroke_history = [[]]
                st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
                st.session_state.canvas_key += 1
                return True
    else:
        st.session_state.is_correct = True
        st.session_state.local_checked = True
        st.session_state.ai_feedback = f"🌟 **Awesome job!** Your math is absolutely perfect! ({user_num}/{user_den})"
        return False

col1, col2 = st.columns([5, 1])
with col1:
    st.title("Fraction Master!")
with col2:
    with st.popover("⚙️", use_container_width=True):
        st.radio("Fractions per problem", [1, 2, 3], key="frac_count", on_change=handle_frac_count_change)
        
        disabled_simp = (st.session_state.frac_count == 1)
        st.radio("Simplify Answers", ["Yes", "No"], key="simplify_answers", on_change=handle_settings_change, disabled=disabled_simp)
        st.radio("Max LCM Limit", [50, 100, 200], key="max_lcm", on_change=handle_settings_change)

current_color_hex = PEN_COLORS[st.session_state.color_index]
current_color_name = COLOR_NAMES[st.session_state.color_index]

if st.session_state.generating:
    with st.spinner("Generating problem..."):
        st.session_state.current_frac_count = st.session_state.frac_count
        n1, d1, op1, n2, d2, op2, n3, d3, eq_str, lcm, target_num, target_den = generate_fraction_problem()
        st.session_state.math_data = (eq_str, lcm, target_num, target_den)
        st.session_state.bg_image = draw_fraction_equation(n1, d1, op1, n2, d2, op2, n3, d3)
        st.session_state.ai_feedback = ""
        st.session_state.color_index = 0 
        st.session_state.local_checked = False
        st.session_state.is_correct = False
        st.session_state.user_frac_input = "" 
        st.session_state.pending_frac_update = None
        
        st.session_state.stroke_history = [[]]
        st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
        st.session_state.canvas_key += 1 
        
        st.session_state.generating = False
        st.rerun()

else:
    eq_str, lcm, target_num, target_den = st.session_state.math_data
    
    st.write(f"Cross out the denominators! Current pen: **{current_color_name}**")

    tool = st.radio("Tool", ["🖌️ Pen", "🧽 Tap-Eraser"], horizontal=True, label_visibility="collapsed")
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

    st.write("---")
    
    # --- MAGIC UI INTERCEPT ---
    if st.session_state.pending_frac_update is not None:
        st.session_state.user_frac_input = st.session_state.pending_frac_update
        st.session_state.pending_frac_update = None
    
    st.text_input("Type your final answer:", placeholder="e.g. 35.70 or 35/70", key="user_frac_input", on_change=format_fraction_input)
    user_answer = st.session_state.user_frac_input
    
    components.html(
        """
        <script>
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        inputs.forEach(input => {
            input.setAttribute('inputmode', 'tel');
        });
        </script>
        """,
        height=0, width=0
    )

    # Boolean flag to trigger AI routing
    trigger_ai = False

    if st.button("Check My Answer!", type="primary", use_container_width=True):
        if user_answer:
            match = re.match(r'^\s*(-?\d+)\s*[^\d]+\s*(-?\d+)\s*$', user_answer)
            if match:
                user_num = int(match.group(1))
                user_den = int(match.group(2))
                
                if user_den == 0:
                    st.error("Denominator cannot be zero!")
                else:
                    if user_num * target_den == target_num * user_den:
                        # --- SMART AI ROUTING ---
                        # If they are in the simplification phase, and submit a correct but unsimplified answer,
                        # assume they simplified directly on the canvas and send it to the AI for grading.
                        if st.session_state.current_frac_count == 1 and st.session_state.simplify_answers == "Yes" and math.gcd(user_num, user_den) > 1:
                            trigger_ai = True
                        else:
                            needs_rerun = process_correct_answer(user_num, user_den)
                            if needs_rerun:
                                st.rerun()
                    else:
                        st.session_state.local_checked = True
                        st.session_state.is_correct = False
                        st.session_state.ai_feedback = ""
            else:
                st.error("Please type two numbers separated by a symbol (like 35.70 or 35/70).")
        else:
            # Box is blank: Send straight to AI Marker
            trigger_ai = True

    # --- AI DIAGNOSTICS UI (Local Check Warnings) ---
    if st.session_state.local_checked and not trigger_ai:
        if st.session_state.is_correct:
            st.success(st.session_state.ai_feedback)
        else:
            if "can be simplified further" in st.session_state.ai_feedback:
                st.warning(st.session_state.ai_feedback)
            else:
                st.warning("💡 **Almost there!** The final answer isn't quite right, or is missing.")
                
            if st.button("🤖 Ask AI Tutor to check my workings", use_container_width=True):
                trigger_ai = True

    # --- THE AI EXECUTION BLOCK ---
    if trigger_ai:
        st.session_state.local_checked = True
        st.session_state.is_correct = False
        
        if canvas_result.image_data is not None:
            with st.spinner("The AI Tutor is reviewing your handwritten workings..."):
                try:
                    ink_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    bg = st.session_state.bg_image.convert("RGBA")
                    if ink_img.size != bg.size:
                        ink_img = ink_img.resize(bg.size, Image.Resampling.LANCZOS)
                    final_canvas = Image.alpha_composite(bg, ink_img).convert("RGB")
                    
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    if st.session_state.current_frac_count == 1:
                        task_info = f"The student is asked to SIMPLIFY the fraction {eq_str} to its lowest terms. The mathematically correct final simplified answer is equivalent to {target_num}/{target_den}, but MUST have no common factors."
                        grading_3 = f"3. If their {current_color_name} handwritten final answer is mathematically CORRECT AND FULLY SIMPLIFIED (no common factors), their verdict is CORRECT."
                        grading_4 = f"4. If their handwritten answer is incorrect, missing, OR not fully simplified, figure out WHERE they went wrong. Their verdict is INCORRECT."
                    else:
                        task_info = f"The problem is: {eq_str}. The mathematically correct final answer is equivalent to {target_num}/{target_den}."
                        grading_3 = f"3. If their {current_color_name} handwritten final answer is mathematically CORRECT (equivalent to {target_num}/{target_den}), their verdict is CORRECT."
                        grading_4 = f"4. If their handwritten answer is incorrect or missing, figure out WHERE they went wrong in their {current_color_name} workings. Their verdict is INCORRECT."
                    
                    prompt = f"""
                    You are a gentle, encouraging math tutor helping a 9-year-old learn fractions.
                    {task_info}
                    
                    I am sending you an image of their digital workspace. 
                    The student is writing in ink directly over the top of the black fractions to cross out denominators and write new equivalent fractions. They may have also handwritten their final answer on the right side of the canvas over the horizontal line.
                    
                    IMPORTANT GRADING RULES:
                    1. The student may have tried this problem multiple times. Their LATEST attempt is written in {current_color_name} ink. Treat other colors as older mistakes.
                    2. Look closely at their LATEST {current_color_name} handwritten final answer on the far right. 
                    {grading_3}
                    {grading_4}
                    5. Note: If the problem is multiplication, they do not need to find a common denominator.
                    6. If their verdict is CORRECT, you MUST extract the final fraction they wrote on the canvas so the system can process it. Do not leave it as NONE if they got it right.
                    
                    YOU MUST FORMAT YOUR RESPONSE EXACTLY LIKE THIS (Three lines, no extra text):
                    VERDICT: [Write EXACTLY "CORRECT" or "INCORRECT"]
                    FOUND_FRACTION: [If they wrote a final fraction on the far right, write it here like "35/50". If they left it blank, write "NONE"]
                    MESSAGE: [Your gentle explanation or praise here]
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[prompt, final_canvas]
                    )
                    
                    resp_text = response.text.strip()
                    
                    match = re.search(r'VERDICT:\s*(CORRECT|INCORRECT)\s*\nFOUND_FRACTION:\s*(.*?)\s*\nMESSAGE:\s*(.*)', resp_text, re.IGNORECASE | re.DOTALL)
                    
                    if match:
                        verdict = match.group(1).upper()
                        found_fraction = match.group(2).strip()
                        message = match.group(3).strip()
                        
                        found_num, found_den = target_num, target_den
                        if found_fraction.upper() != "NONE" and re.match(r'^-?\d+/-?\d+$', found_fraction):
                            st.session_state.pending_frac_update = found_fraction
                            parts = found_fraction.split('/')
                            found_num, found_den = int(parts[0]), int(parts[1])
                        
                        if verdict == "CORRECT":
                            needs_rerun = process_correct_answer(found_num, found_den)
                            if needs_rerun:
                                st.rerun()
                        else:
                            st.session_state.ai_feedback = f"🤖 **Tutor says:** {message}"
                            st.session_state.color_index = (st.session_state.color_index + 1) % len(PEN_COLORS)
                    else:
                        st.session_state.ai_feedback = resp_text
                        st.session_state.color_index = (st.session_state.color_index + 1) % len(PEN_COLORS)
                        
                    # Unconditional rerun ensures the UI updates to reflect the AI's state changes
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Oops! The tutor had a glitch: {e}")
        else:
            st.error("Please draw your working on the canvas first!")

    # Display isolated AI or Phase Transition feedback safely
    if st.session_state.ai_feedback and not st.session_state.is_correct and "can be simplified further" not in st.session_state.ai_feedback:
        st.info(st.session_state.ai_feedback)

    st.write("")
    if st.button("Give me a new problem!", use_container_width=True):
        st.session_state.generating = True
        st.rerun()