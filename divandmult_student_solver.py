import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import random
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
PEN_COLORS = ["#1E90FF", "#FF2400", "#32CD32", "#9400D3", "#FF8C00"]
COLOR_NAMES = ["BLUE", "RED", "GREEN", "PURPLE", "ORANGE"]

st.set_page_config(page_title="Arithmetic Master", page_icon="✏️", layout="centered")

# --- Custom CSS ---
st.markdown("""
    <style>
    input[type="text"] { text-align: center; font-size: 1.2rem !important; font-weight: bold; }
    div.row-widget.stRadio > div { flex-direction: row; gap: 15px; }
    button[kind="primary"] { background-color: #007AFF !important; border-color: #007AFF !important; color: white !important; }
    button[kind="primary"]:hover { background-color: #0056b3 !important; border-color: #0056b3 !important; }
    div[data-testid="stElementContainer"]:has(#next-problem-btn) + div[data-testid="stElementContainer"] button {
        background-color: #28a745 !important; border-color: #28a745 !important; color: white !important;
    }
    div[data-testid="stElementContainer"]:has(#next-problem-btn) + div[data-testid="stElementContainer"] button:hover {
        background-color: #218838 !important; border-color: #218838 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Math Engine ---
def generate_problem(operation, level):
    if operation == "Multiplication":
        if level == 1:
            a = random.randint(11, 99)
            b = random.randint(2, 9)
        elif level == 2:
            a = random.randint(11, 99)
            b = random.randint(11, 99)
        else:
            a = random.randint(101, 999)
            b = random.randint(11, 99)
        ans = str(a * b)
        return a, b, ans, f"{a} * {b}"
        
    else: # Division
        if level == 1:
            # 2-digit by 1-digit, no remainders
            b = random.randint(2, 9)
            ans_val = random.randint(11, 99 // b)
            a = ans_val * b
            ans = str(ans_val)
        elif level == 2:
            # 3-digit by 1-digit, possible remainders
            b = random.randint(2, 9)
            a = random.randint(101, 999)
            q, r = divmod(a, b)
            ans = f"{q} R {r}" if r else str(q)
        else:
            # 3-digit by 2-digit, possible remainders
            b = random.randint(11, 50)
            a = random.randint(101, 999)
            q, r = divmod(a, b)
            ans = f"{q} R {r}" if r else str(q)
        return b, a, ans, f"{a} / {b}"

# --- Visual Engine (Matplotlib) ---
def draw_math_setup(op, num1, num2):
    fig, ax = plt.subplots(figsize=(4.0, 4.5), dpi=100)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis('off')
    
    if op == "Multiplication":
        ax.text(0.65, 0.85, f"{num1}", fontsize=36, ha='right', va='center', fontfamily='monospace')
        ax.text(0.65, 0.72, f"{num2}", fontsize=36, ha='right', va='center', fontfamily='monospace')
        ax.text(0.35, 0.72, "x", fontsize=30, ha='center', va='center', fontfamily='monospace')
        ax.plot([0.3, 0.7], [0.62, 0.62], color='black', lw=3)
    else:
        # Long Division Bracket
        divisor, dividend = num1, num2
        ax.text(0.38, 0.85, f"{divisor}", fontsize=34, ha='right', va='center', fontfamily='monospace')
        ax.text(0.42, 0.85, ")", fontsize=34, ha='left', va='center', fontfamily='monospace')
        
        num_digits = len(str(dividend))
        line_end = 0.48 + (num_digits * 0.09)
        
        ax.plot([0.46, line_end], [0.93, 0.93], color='black', lw=3)
        ax.text(0.48, 0.85, f"{dividend}", fontsize=34, ha='left', va='center', fontfamily='monospace', letterspacing=2)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGBA').copy()

# --- State Initialization ---
if 'generating' not in st.session_state: st.session_state.generating = True
if 'ai_feedback' not in st.session_state: st.session_state.ai_feedback = ""
if 'canvas_key' not in st.session_state: st.session_state.canvas_key = 0 
if 'color_index' not in st.session_state: st.session_state.color_index = 0
if 'stroke_history' not in st.session_state: st.session_state.stroke_history = [[]]
if 'active_initial_drawing' not in st.session_state: st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
if 'is_correct' not in st.session_state: st.session_state.is_correct = False
if 'user_input' not in st.session_state: st.session_state.user_input = ""
if 'last_submitted_text' not in st.session_state: st.session_state.last_submitted_text = None
if 'last_canvas_state' not in st.session_state: st.session_state.last_canvas_state = []

def trigger_generation():
    st.session_state.generating = True

# --- UI Setup ---
col1, col2 = st.columns([4, 1])
with col1:
    st.title("Arithmetic Master! ✏️")
with col2:
    with st.popover("⚙️", use_container_width=True):
        st.radio("Operation", ["Multiplication", "Division"], key="operation", on_change=trigger_generation)
        st.radio("Level", [1, 2, 3], key="level", on_change=trigger_generation, format_func=lambda x: f"Level {x}")
        st.toggle("Canvas Controls", key="show_controls", value=True, on_change=trigger_generation)

current_color_hex = PEN_COLORS[st.session_state.color_index]
current_color_name = COLOR_NAMES[st.session_state.color_index]

if st.session_state.generating:
    with st.spinner("Preparing your math canvas..."):
        num1, num2, ans, eq_str = generate_problem(st.session_state.operation, st.session_state.level)
        st.session_state.math_data = (num1, num2, ans, eq_str)
        st.session_state.bg_image = draw_math_setup(st.session_state.operation, num1, num2)
        st.session_state.ai_feedback = ""
        st.session_state.color_index = 0 
        st.session_state.is_correct = False
        st.session_state.user_input = "" 
        st.session_state.stroke_history = [[]]
        st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
        st.session_state.last_submitted_text = None
        st.session_state.last_canvas_state = []
        st.session_state.canvas_key += 1 
        st.session_state.generating = False
        st.rerun()

else:
    num1, num2, target_ans, eq_str = st.session_state.math_data
    
    st.write(f"Show your working! Current pen: **{current_color_name}**")

    tool = st.radio("Tool", ["🖌️ Pen", "🧽 Tap-Eraser"], horizontal=True, label_visibility="collapsed")
    active_stroke_color = current_color_hex if tool == "🖌️ Pen" else "#FFFFFE"
    active_stroke_width = 3 if tool == "🖌️ Pen" else 15

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", stroke_width=active_stroke_width, stroke_color=active_stroke_color,
        background_image=st.session_state.bg_image, update_streamlit=True, height=450, width=400,
        drawing_mode="freedraw", return_image_data=True, initial_drawing=st.session_state.active_initial_drawing, 
        key=f"canvas_{st.session_state.canvas_key}",
    )

    if st.session_state.get('show_controls', True):
        col_u, col_c = st.columns(2)
        with col_u:
            if st.button("↩️ Undo", use_container_width=True):
                if len(st.session_state.stroke_history) > 1:
                    st.session_state.stroke_history.pop()
                    st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": st.session_state.stroke_history[-1]}
                    st.session_state.canvas_key += 1
                    st.rerun()
        with col_c:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.stroke_history = [[]]
                st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": []}
                st.session_state.canvas_key += 1
                st.rerun()

    # --- Canvas History Logic ---
    current_objects = canvas_result.json_data.get("objects", []) if canvas_result.json_data else []
    last_saved_objects = st.session_state.stroke_history[-1]

    if len(current_objects) > len(last_saved_objects):
        new_stroke = current_objects[-1]
        if new_stroke.get("stroke", "").upper() == "#FFFFFE":
            e_obj = new_stroke
            ew = e_obj.get("width", 0) * e_obj.get("scaleX", 1)
            eh = e_obj.get("height", 0) * e_obj.get("scaleY", 1)
            e_left, e_top = e_obj.get("left", 0), e_obj.get("top", 0)
            pad = 15
            E_L, E_R, E_T, E_B = e_left - pad, e_left + ew + pad, e_top - pad, e_top + eh + pad
            
            objects_to_keep = []
            for obj in last_saved_objects:
                ow = obj.get("width", 0) * obj.get("scaleX", 1)
                oh = obj.get("height", 0) * obj.get("scaleY", 1)
                o_left, o_top = obj.get("left", 0), obj.get("top", 0)
                T_L, T_R, T_T, T_B = o_left, o_left + ow, o_top, o_top + oh
                if (E_R < T_L or E_L > T_R or E_B < T_T or E_T > T_B):
                    objects_to_keep.append(obj)
            
            st.session_state.stroke_history.append(objects_to_keep)
            st.session_state.active_initial_drawing = {"version": "4.4.0", "objects": objects_to_keep}
            st.session_state.canvas_key += 1
            st.rerun()
        else:
            st.session_state.stroke_history.append(current_objects.copy())

    st.markdown("<hr style='margin: 0.5em 0px; border-color: #444;'>", unsafe_allow_html=True)
    
    placeholder_text = "e.g. 1035 or 14 R 2" if st.session_state.operation == "Division" else "e.g. 1035"
    user_answer = st.text_input("Type your final answer:", placeholder=placeholder_text, key="user_input").strip().lower()
    
    trigger_ai = False

    if st.button("Check My Answer!", type="primary", use_container_width=True):
        canvas_changed = (current_objects != st.session_state.last_canvas_state)
        
        if not user_answer:
            trigger_ai = True
        elif user_answer == st.session_state.last_submitted_text and canvas_changed:
            trigger_ai = True
        else:
            # Local format check
            clean_target = target_ans.lower().replace(" ", "")
            clean_user = user_answer.replace(" ", "")
            if clean_user == clean_target:
                st.session_state.is_correct = True
                st.session_state.ai_feedback = f"🌟 **Awesome job!** You correctly calculated {target_ans}!"
            else:
                trigger_ai = True
                
        st.session_state.last_submitted_text = user_answer
        st.session_state.last_canvas_state = current_objects.copy()

    # --- AI EXECUTION BLOCK ---
    if trigger_ai:
        st.session_state.is_correct = False
        
        if canvas_result.image_data is not None:
            with st.spinner("The AI Tutor is reviewing your handwritten workings..."):
                try:
                    ink_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    bg = st.session_state.bg_image.convert("RGBA")
                    if ink_img.size != bg.size: ink_img = ink_img.resize(bg.size, Image.Resampling.LANCZOS)
                    final_canvas = Image.alpha_composite(bg, ink_img).convert("RGB")
                    
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    op_name = "Long-form Multiplication" if st.session_state.operation == "Multiplication" else "Long Division"
                    
                    prompt = f"""
                    You are a gentle, encouraging math tutor helping a 10-year-old learn {op_name}.
                    The math problem is: {eq_str}. 
                    The correct final answer is: {target_ans}.
                    
                    Look at their digital workspace. They are writing in {current_color_name} ink.
                    Treat all other colors as older mistakes.
                    
                    IMPORTANT RULES:
                    1. If a student sketches a vertical line or plus sign over an existing minus sign, evaluate it as positive. Horizontal lines over plus signs evaluate as negative.
                    2. Ignore old strikethroughs from older colors. Evaluate only {current_color_name} ink.
                    3. If their {current_color_name} final answer is CORRECT ({target_ans}), reply EXACTLY with "CORRECT:" on line 1, followed by a warm, praising message on line 2.
                    4. If their answer is incorrect or missing, reply EXACTLY with "INCORRECT:" on line 1, and figure out WHERE they went wrong in their {current_color_name} workings on line 2. Gently guide them on what to do next without giving the answer away.
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[prompt, final_canvas]
                    )
                    
                    resp_text = response.text.strip()
                    
                    if resp_text.upper().startswith("CORRECT"):
                        st.session_state.is_correct = True
                        msg = re.sub(r'(?i)^CORRECT:?\s*', '', resp_text).strip()
                        st.session_state.ai_feedback = f"🌟 **Awesome job!** {msg}"
                    else:
                        st.session_state.is_correct = False
                        msg = re.sub(r'(?i)^INCORRECT:?\s*', '', resp_text).strip()
                        st.session_state.ai_feedback = f"🤖 **Tutor says:** {msg}"
                        st.session_state.color_index = (st.session_state.color_index + 1) % len(PEN_COLORS)
                        
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Oops! The tutor had a glitch: {e}")
        else:
            st.error("Please draw your working on the canvas first!")

    if st.session_state.ai_feedback:
        if st.session_state.is_correct:
            st.success(st.session_state.ai_feedback)
        else:
            st.warning(st.session_state.ai_feedback)

    st.markdown("<hr style='margin: 0.5em 0px; border-color: #444;'>", unsafe_allow_html=True)
    st.markdown('<div id="next-problem-btn"></div>', unsafe_allow_html=True)
    if st.button("Give me a new problem!", use_container_width=True):
        trigger_generation()
        st.rerun()