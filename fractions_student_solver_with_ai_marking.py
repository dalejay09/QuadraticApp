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
from google import genai

# --- THE ULTIMATE MONKEY PATCH (Kept for Cloud Stability) ---
import streamlit_drawable_canvas
def b64_image_to_url(image, *args, **kwargs):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

streamlit_drawable_canvas.image_to_url = b64_image_to_url
from streamlit_drawable_canvas import st_canvas
# -----------------------------------------------------------

# --- Math Engine: FRACTIONS ---
def generate_fraction_problem():
    while True:
        # Pick 3 unique denominators between 2 and 10
        denoms = random.sample(range(2, 11), 3)
        # Calculate Lowest Common Multiple
        lcm = math.lcm(math.lcm(denoms[0], denoms[1]), denoms[2])
        
        if lcm <= 100:
            # Pick valid numerators
            n1 = random.randint(1, denoms[0] - 1)
            n2 = random.randint(1, denoms[1] - 1)
            n3 = random.randint(1, denoms[2] - 1)
            
            op1 = random.choice(['+', '-'])
            op2 = random.choice(['+', '-'])
            
            # Ensure the final result isn't negative for a 9-year-old
            v1 = n1 / denoms[0]
            v2 = n2 / denoms[1] if op1 == '+' else -n2 / denoms[1]
            v3 = n3 / denoms[2] if op2 == '+' else -n3 / denoms[2]
            
            if v1 + v2 + v3 > 0:
                break
                
    eq_str = f"{n1}/{denoms[0]} {op1} {n2}/{denoms[1]} {op2} {n3}/{denoms[2]}"
    return n1, denoms[0], op1, n2, denoms[1], op2, n3, denoms[2], eq_str, lcm

# --- Visual Engine: HORIZONTAL EQUATION ---
def draw_fraction_equation(n1, d1, op1, n2, d2, op2, n3, d3):
    # Wider aspect ratio for horizontal layout
    fig, ax = plt.subplots(figsize=(8, 3), dpi=100) 
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    fontsize = 40
    
    # Render fractions evenly spaced using LaTeX formatting
    ax.text(0.12, 0.5, rf"$\frac{{{n1}}}{{{d1}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.26, 0.5, op1, fontsize=fontsize, ha='center', va='center')
    ax.text(0.40, 0.5, rf"$\frac{{{n2}}}{{{d2}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.54, 0.5, op2, fontsize=fontsize, ha='center', va='center')
    ax.text(0.68, 0.5, rf"$\frac{{{n3}}}{{{d3}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.82, 0.5, "=", fontsize=fontsize, ha='center', va='center')
    # The space from 0.85 to 1.0 is left entirely blank for the user's answer!
    
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

st.title("Fraction Master!")
st.write("Find the common denominator, cross out the old numbers, and write the new ones!")

# Generate New Data
if st.session_state.generating:
    with st.spinner("Generating problem..."):
        n1, d1, op1, n2, d2, op2, n3, d3, eq_str, lcm = generate_fraction_problem()
        st.session_state.math_data = (eq_str, lcm)
        st.session_state.bg_image = draw_fraction_equation(n1, d1, op1, n2, d2, op2, n3, d3)
        st.session_state.ai_feedback = ""
        st.session_state.canvas_key += 1 
        st.session_state.generating = False
        st.rerun()

else:
    eq_str, lcm = st.session_state.math_data
    
    # The Drawing Canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", 
        stroke_width=3,
        stroke_color="#1E90FF",
        background_image=st.session_state.bg_image,
        update_streamlit=True,
        height=300,
        width=800,
        drawing_mode="freedraw",
        key=f"canvas_{st.session_state.canvas_key}",
    )

    if st.button("Check My Answer!", type="primary", use_container_width=True):
        if canvas_result.image_data is not None:
            with st.spinner("The AI Tutor is checking your work..."):
                try:
                    # Flatten the ink and the background into a single image for the AI
                    ink_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    bg = st.session_state.bg_image.convert("RGBA")
                    if ink_img.size != bg.size:
                        ink_img = ink_img.resize(bg.size, Image.Resampling.LANCZOS)
                    final_canvas = Image.alpha_composite(bg, ink_img).convert("RGB")
                    
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    prompt = f"""
                    You are a gentle, encouraging math tutor helping a 9-year-old learn to add and subtract fractions.
                    The problem they are solving is: {eq_str}. 
                    The Lowest Common Multiple for the denominators is {lcm}.
                    
                    I am sending you a single image of their digital workspace. The black text is the original problem. The blue ink is their handwriting.
                    
                    Look at their blue ink. Did they find the correct common denominator? Did they convert the numerators correctly? Is their final answer correct (it does not need to be simplified)?
                    
                    If they got the final answer correct, reply EXACTLY with the word "CORRECT:" on the first line, followed by a warm, enthusiastic message praising them for finding the common denominator.
                    If they made a mistake, reply EXACTLY with the word "INCORRECT:" on the first line. Gently point out where they went wrong (e.g., "You found the right bottom number, but don't forget to multiply the top number too!") without giving them the final answer. Keep your tone highly supportive.
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
                        
                except Exception as e:
                    st.error(f"Oops! The tutor had a glitch: {e}")

    if st.session_state.ai_feedback:
        st.info(st.session_state.ai_feedback)

    if st.button("Give me a new problem!", use_container_width=True):
        st.session_state.generating = True
        st.rerun()