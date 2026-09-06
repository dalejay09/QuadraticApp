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
    return n1, d1, op1, n2, d2, op2, n3, d3, eq_str, lcm

# --- Visual Engine: BACKEND MATPLOTLIB ---
def draw_fraction_equation(n1, d1, op1, n2, d2, op2, n3, d3):
    fig, ax = plt.subplots(figsize=(3.5, 2.0), dpi=100) 
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    fontsize = 28
    
    ax.text(0.10, 0.5, rf"$\frac{{{n1}}}{{{d1}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.23, 0.5, op1, fontsize=fontsize, ha='center', va='center')
    ax.text(0.36, 0.5, rf"$\frac{{{n2}}}{{{d2}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.49, 0.5, op2, fontsize=fontsize, ha='center', va='center')
    ax.text(0.62, 0.5, rf"$\frac{{{n3}}}{{{d3}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.75, 0.5, "=", fontsize=fontsize, ha='center', va='center')
    
    ax.plot([0.814, 0.942], [0.5, 0.5], color='black', lw=2)
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    
    return Image.open(buf).convert('RGBA').copy()

# --- State Management ---
if 'generating' not in st.session_state:
    st.session_state.generating = True
if 'ai_feedback' not in st.session_state:
    st.session_state.ai_feedback = ""
if 'canvas_key' not in st.session_state:
    st.session_state.canvas_key = 0 
if 'max_lcm' not in st.session_state:
    st.session_state.max_lcm = 100
if 'current_ink' not in st.session_state:
    st.session_state.current_ink = None

def handle_settings_change():
    st.session_state.generating = True

col1, col2 = st.columns([5, 1])
with col1:
    st.title("Fraction Master!")
with col2:
    with st.popover("⚙️", use_container_width=True):
        st.radio("Max LCM Limit", [50, 100, 200], key="max_lcm", on_change=handle_settings_change)

st.write("Write right over the text to cross out denominators, then put your answer at the end!")

if st.session_state.generating:
    with st.spinner("Generating problem..."):
        n1, d1, op1, n2, d2, op2, n3, d3, eq_str, lcm = generate_fraction_problem()
        st.session_state.math_data = (eq_str, lcm)
        st.session_state.bg_image = draw_fraction_equation(n1, d1, op1, n2, d2, op2, n3, d3)
        st.session_state.ai_feedback = ""
        st.session_state.current_ink = None # Wipe the slate clean for the new problem
        st.session_state.canvas_key += 1 
        st.session_state.generating = False
        st.rerun()

else:
    eq_str, lcm = st.session_state.math_data
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", 
        stroke_width=3, 
        stroke_color="#1E90FF",
        background_image=st.session_state.bg_image,
        update_streamlit=True,
        height=200,
        width=350,
        drawing_mode="freedraw",
        return_image_data=True, 
        initial_drawing=st.session_state.get('current_ink', None),
        key=f"canvas_{st.session_state.canvas_key}",
    )

    # Automatically save ink state as they draw
    if canvas_result.json_data is not None:
        st.session_state.current_ink = canvas_result.json_data

    # --- CANVAS CONTROLS ---
    col_undo, col_clear = st.columns(2)
    with col_undo:
        if st.button("↩️ Undo Last", use_container_width=True):
            if st.session_state.current_ink and "objects" in st.session_state.current_ink and len(st.session_state.current_ink["objects"]) > 0:
                st.session_state.current_ink["objects"].pop()
                st.session_state.canvas_key += 1
                st.rerun()
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.current_ink = None
            st.session_state.canvas_key += 1
            st.rerun()

    st.write("---")

    if st.button("Check My Answer!", type="primary", use_container_width=True):
        
        has_ink = st.session_state.current_ink and "objects" in st.session_state.current_ink and len(st.session_state.current_ink["objects"]) > 0
        
        if has_ink and canvas_result.image_data is not None:
            with st.spinner("The AI Tutor is checking your work..."):
                try:
                    ink_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    bg = st.session_state.bg_image.convert("RGBA")
                    
                    if ink_img.size != bg.size:
                        ink_img = ink_img.resize(bg.size, Image.Resampling.LANCZOS)
                        
                    final_canvas = Image.alpha_composite(bg, ink_img).convert("RGB")
                    
                    st.image(final_canvas, caption="Sending this image to the AI Tutor...", use_container_width=True)
                    
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    prompt = f"""
                    You are a gentle, encouraging math tutor helping a 9-year-old learn to add and subtract fractions.
                    The problem they are solving is: {eq_str}. 
                    The Lowest Common Multiple for the denominators is {lcm}.
                    
                    I am sending you a single image of their digital workspace. 
                    The black printed fractions are the original problem. The BLUE ink is their handwriting.
                    The student is writing in blue ink directly over the top of the black fractions to cross out denominators and write new equivalent fractions.
                    Their final answer is written in blue ink on the far right, over the black horizontal line.
                    
                    IMPORTANT GRADING RULES:
                    1. First, silently calculate the correct final numerator and denominator yourself.
                    2. Read their blue ink to see if they converted the original fractions correctly.
                    3. SPECIAL RULE: If a fraction already has the lowest common denominator, the student may leave it completely unmarked. This is correct logic! Do not tell them they missed a step or forgot to mark it.
                    4. Check their final answer on the right. It does not need to be simplified.
                    
                    If their final math is correct, reply EXACTLY with the word "CORRECT:" on the first line, followed by a warm, enthusiastic message praising them.
                    If they made a mistake, reply EXACTLY with the word "INCORRECT:" on the first line. Gently point out where they went wrong without giving them the final answer. Keep your tone highly supportive.
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[prompt, final_canvas]
                    )
                    
                    resp_text = response.text.strip()
                    if resp_text.upper().startswith("CORRECT"):
                        st.session_state.ai_feedback = re.sub(r'(?i)^CORRECT:?\s*', '🌟 **Awesome job!** ', resp_text)
                    else:
                        st.session_state.ai_feedback = re.sub(r'(?i)^INCORRECT:?\s*', '💡 **Almost there!** ', resp_text)
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Oops! The tutor had a glitch: {e}")
        else:
            st.error("Please draw your working on the canvas before checking your answer!")

    if st.session_state.ai_feedback:
        st.info(st.session_state.ai_feedback)

    if st.button("Give me a new problem!", use_container_width=True):
        st.session_state.generating = True
        st.rerun()