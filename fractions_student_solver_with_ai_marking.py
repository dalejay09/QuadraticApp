import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import random
import math
import io
import re
import base64
from PIL import Image, ImageDraw
from google import genai

# --- THE ULTIMATE MONKEY PATCH ---
# Bypasses Streamlit's buggy media manager for background images
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

# --- Visual Engine: COMPRESSED PORTRAIT EQUATION ---
def draw_fraction_equation(n1, d1, op1, n2, d2, op2, n3, d3):
    # Compressed 7:4 aspect ratio tailored perfectly for mobile portrait mode
    fig, ax = plt.subplots(figsize=(7, 4), dpi=100) 
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    fontsize = 50
    
    # Tightly packed to the left so the right side is completely open for answers
    ax.text(0.10, 0.5, rf"$\frac{{{n1}}}{{{d1}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.23, 0.5, op1, fontsize=fontsize, ha='center', va='center')
    ax.text(0.36, 0.5, rf"$\frac{{{n2}}}{{{d2}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.49, 0.5, op2, fontsize=fontsize, ha='center', va='center')
    ax.text(0.62, 0.5, rf"$\frac{{{n3}}}{{{d3}}}$", fontsize=fontsize, ha='center', va='center')
    ax.text(0.75, 0.5, "=", fontsize=fontsize, ha='center', va='center')
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    
    return Image.open(buf).convert('RGBA').copy()

# --- BACKEND STROKE RENDERER ---
# This guarantees we never trigger a browser security crash!
def create_final_image(bg_image, json_data):
    # Lock the resolution to match our Streamlit Canvas dimensions exactly
    img = bg_image.resize((350, 200), Image.Resampling.LANCZOS).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    if json_data and "objects" in json_data:
        for obj in json_data["objects"]:
            if obj.get("type") == "path":
                path = obj.get("path", [])
                stroke_color = obj.get("stroke", "#1E90FF")
                stroke_width = int(obj.get("strokeWidth", 3))
                
                # Extract coordinates from the frontend path array and draw them in Python
                points = []
                for cmd in path:
                    if len(cmd) >= 3:
                        points.append((cmd[-2], cmd[-1]))
                        
                if len(points) > 1:
                    draw.line(points, fill=stroke_color, width=stroke_width, joint="curve")
                    
    return img


# --- State Management ---
if 'generating' not in st.session_state:
    st.session_state.generating = True
if 'ai_feedback' not in st.session_state:
    st.session_state.ai_feedback = ""
if 'canvas_key' not in st.session_state:
    st.session_state.canvas_key = 0 

st.title("Fraction Master!")
st.write("Write right over the text to cross out denominators, then put your answer at the end!")

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
    
    # Portrait-optimized 350x200 canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", 
        stroke_width=3,
        stroke_color="#1E90FF",
        background_image=st.session_state.bg_image,
        update_streamlit=True,
        height=200,
        width=350,
        drawing_mode="freedraw",
        key=f"canvas_{st.session_state.canvas_key}",
    )

    if st.button("Check My Answer!", type="primary", use_container_width=True):
        # We NO LONGER check image_data. We only check if they drew paths in the json_data!
        if canvas_result.json_data is not None and len(canvas_result.json_data.get("objects", [])) > 0:
            with st.spinner("The AI Tutor is checking your work..."):
                try:
                    # Construct the composite image safely on the backend
                    final_canvas = create_final_image(st.session_state.bg_image, canvas_result.json_data)
                    
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    prompt = f"""
                    You are a gentle, encouraging math tutor helping a 9-year-old learn to add and subtract fractions.
                    The problem they are solving is: {eq_str}. 
                    The Lowest Common Multiple for the denominators is {lcm}.
                    
                    I am sending you a single image of their digital workspace. The black text is the original problem. The blue ink is their handwriting.
                    Note: The student is writing directly OVER the original black text to cross out denominators and convert them to the LCM. They will write their final answer on the far right.
                    
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
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Oops! The tutor had a glitch: {e}")
        else:
            st.error("Please draw something on the canvas before checking your answer!")

    if st.session_state.ai_feedback:
        st.info(st.session_state.ai_feedback)

    if st.button("Give me a new problem!", use_container_width=True):
        st.session_state.generating = True
        st.rerun()