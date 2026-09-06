import streamlit as st
import random
import math
import re
import numpy as np
from PIL import Image
from google import genai
from streamlit_drawable_canvas import st_canvas

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

# --- Native Canvas Engine: HORIZONTAL EQUATION ---
def generate_fabric_json(n1, d1, op1, n2, d2, op2, n3, d3):
    objects = []
    y = 150 # Center of our 300px tall canvas
    
    # Helper function to dynamically draw a fraction out of pure text & lines
    def add_fraction(n, d, x):
        objects.append({
            "type": "text", "text": str(n), "left": x, "top": y - 40,
            "fontSize": 50, "fontFamily": "sans-serif", "fill": "black",
            "originX": "center", "originY": "center", "selectable": False, "evented": False
        })
        objects.append({
            "type": "text", "text": str(d), "left": x, "top": y + 40,
            "fontSize": 50, "fontFamily": "sans-serif", "fill": "black",
            "originX": "center", "originY": "center", "selectable": False, "evented": False
        })
        objects.append({
            "type": "line", "x1": x - 35, "y1": y, "x2": x + 35, "y2": y,
            "stroke": "black", "strokeWidth": 5,
            "selectable": False, "evented": False
        })

    # Helper function for plus, minus, and equals signs
    def add_text(text, x):
        objects.append({
            "type": "text", "text": text, "left": x, "top": y,
            "fontSize": 50, "fontFamily": "sans-serif", "fill": "black",
            "originX": "center", "originY": "center", "selectable": False, "evented": False
        })
        
    add_fraction(n1, d1, 120)
    add_text(op1, 230)
    add_fraction(n2, d2, 340)
    add_text(op2, 450)
    add_fraction(n3, d3, 560)
    add_text("=", 670)
    # The space from 700 to 800 is a massive blank void for their final answer!
    
    return {
        "version": "4.4.0",
        "objects": objects
    }

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
        st.session_state.fabric_state = generate_fabric_json(n1, d1, op1, n2, d2, op2, n3, d3)
        st.session_state.ai_feedback = ""
        st.session_state.canvas_key += 1 
        st.session_state.generating = False
        st.rerun()

else:
    eq_str, lcm = st.session_state.math_data
    
    # The Drawing Canvas (NO background_image used!)
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", 
        stroke_width=3,
        stroke_color="#1E90FF",
        background_color="#ffffff", # Force a crisp white background
        initial_drawing=st.session_state.fabric_state, # Our native text objects!
        update_streamlit=True,
        height=300,
        width=800,
        drawing_mode="freedraw",
        key=f"canvas_{st.session_state.canvas_key}",
    )

    if st.button("Check My Answer!", type="primary", use_container_width=True):
        try:
            if canvas_result.image_data is not None:
                with st.spinner("The AI Tutor is checking your work..."):
                    # The canvas data inherently includes our native black text AND their blue ink on a white background!
                    final_canvas = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').convert("RGB")
                    
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
                    
                    st.rerun()
        except RuntimeError:
            st.error("Please draw something on the canvas before checking your answer!")

    if st.session_state.ai_feedback:
        st.info(st.session_state.ai_feedback)

    if st.button("Give me a new problem!", use_container_width=True):
        st.session_state.generating = True
        st.rerun()