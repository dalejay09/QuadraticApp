import streamlit as st
import random
import math
import re
from PIL import Image
from google import genai
from streamlit_drawable_canvas import st_canvas

# --- Math Engine: FRACTIONS ---
def generate_fraction_problem():
    while True:
        denoms = random.sample(range(2, 11), 3)
        lcm = math.lcm(math.lcm(denoms[0], denoms[1]), denoms[2])
        
        if lcm <= 100:
            n1 = random.randint(1, denoms[0] - 1)
            n2 = random.randint(1, denoms[1] - 1)
            n3 = random.randint(1, denoms[2] - 1)
            
            op1 = random.choice(['+', '-'])
            op2 = random.choice(['+', '-'])
            
            v1 = n1 / denoms[0]
            v2 = n2 / denoms[1] if op1 == '+' else -n2 / denoms[1]
            v3 = n3 / denoms[2] if op2 == '+' else -n3 / denoms[2]
            
            if v1 + v2 + v3 > 0:
                break
                
    eq_str = f"{n1}/{denoms[0]} {op1} {n2}/{denoms[1]} {op2} {n3}/{denoms[2]}"
    return n1, denoms[0], op1, n2, denoms[1], op2, n3, denoms[2], eq_str, lcm

# --- Visual Engine: NATIVE DIGITAL TEXT ---
# No images used here, which means the browser will never block our export!
def generate_fabric_json(n1, d1, op1, n2, d2, op2, n3, d3):
    objects = []
    y = 100 
    
    def add_fraction(n, d, x):
        objects.extend([
            {"type": "text", "text": str(n), "left": x, "top": y - 26, "fontSize": 28, "fontFamily": "sans-serif", "fill": "black", "originX": "center", "originY": "center", "selectable": False, "evented": False},
            {"type": "line", "x1": x - 15, "y1": y, "x2": x + 15, "y2": y, "stroke": "black", "strokeWidth": 3, "selectable": False, "evented": False},
            {"type": "text", "text": str(d), "left": x, "top": y + 26, "fontSize": 28, "fontFamily": "sans-serif", "fill": "black", "originX": "center", "originY": "center", "selectable": False, "evented": False}
        ])
        
    def add_text(text, x):
        objects.append({"type": "text", "text": text, "left": x, "top": y, "fontSize": 28, "fontFamily": "sans-serif", "fill": "black", "originX": "center", "originY": "center", "selectable": False, "evented": False})
        
    add_fraction(n1, d1, 35)
    add_text(op1, 80.5)
    add_fraction(n2, d2, 126)
    add_text(op2, 171.5)
    add_fraction(n3, d3, 217)
    add_text("=", 262.5)
    
    objects.append({"type": "line", "x1": 285, "y1": y, "x2": 330, "y2": y, "stroke": "black", "strokeWidth": 3, "selectable": False, "evented": False})
    
    return {"version": "4.4.0", "objects": objects}

# --- State Management ---
if 'generating' not in st.session_state:
    st.session_state.generating = True
if 'ai_feedback' not in st.session_state:
    st.session_state.ai_feedback = ""
if 'canvas_key' not in st.session_state:
    st.session_state.canvas_key = 0 

st.title("Fraction Master!")
st.write("Write right over the text to cross out denominators, then put your answer at the end!")

if st.session_state.generating:
    with st.spinner("Generating problem..."):
        n1, d1, op1, n2, d2, op2, n3, d3, eq_str, lcm = generate_fraction_problem()
        st.session_state.math_data = (eq_str, lcm)
        st.session_state.fabric_state = generate_fabric_json(n1, d1, op1, n2, d2, op2, n3, d3)
        st.session_state.ai_feedback = ""
        st.session_state.canvas_key += 1 
        st.session_state.generating = False
        st.rerun()

else:
    eq_str, lcm = st.session_state.math_data
    
    # Notice: No background_image! We are using a pure white background with native text on top.
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", 
        stroke_width=3, 
        stroke_color="#1E90FF",
        background_color="#ffffff", 
        initial_drawing=st.session_state.fabric_state,
        update_streamlit=True,
        height=200,
        width=350,
        drawing_mode="freedraw",
        key=f"canvas_{st.session_state.canvas_key}",
    )

    if st.button("Check My Answer!", type="primary", use_container_width=True):
        
        # We are back to the "Photograph" method. It grabs the exact visual state of the canvas!
        if canvas_result.image_data is not None:
            with st.spinner("The AI Tutor is checking your work..."):
                try:
                    # The image_data array natively contains both our black text and your blue ink
                    final_canvas = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    
                    # Ensure it has a crisp white background before sending to AI
                    white_bg = Image.new("RGBA", final_canvas.size, "WHITE")
                    final_canvas = Image.alpha_composite(white_bg, final_canvas).convert("RGB")
                    
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