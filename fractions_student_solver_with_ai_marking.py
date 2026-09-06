import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import random
import math
import io
import re
from PIL import Image, ImageDraw
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

# --- Visual Engine: BACKEND MATPLOTLIB (For the AI) ---
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

# --- Visual Engine: FRONTEND NATIVE TEXT (For the User) ---
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

# --- THE BULLETPROOF STROKE RENDERER ---
def render_strokes_on_image(bg_image, json_data):
    img = bg_image.copy()
    draw = ImageDraw.Draw(img)
    
    if not json_data or "objects" not in json_data:
        return img.convert("RGB")
        
    for obj in json_data["objects"]:
        # Scan for ANY object that contains a path array, completely ignoring Streamlit's arbitrary type labels
        if "path" in obj and isinstance(obj["path"], list):
            path = obj["path"]
            stroke_color = obj.get("stroke", "#1E90FF")
            stroke_width = int(obj.get("strokeWidth", 3))
            
            left = obj.get("left", 0)
            top = obj.get("top", 0)
            width = obj.get("width", 0)
            height = obj.get("height", 0)
            path_offset_x = obj.get("pathOffset", {}).get("x", 0)
            path_offset_y = obj.get("pathOffset", {}).get("y", 0)
            
            center_x = left if obj.get("originX") == "center" else left + width / 2
            center_y = top if obj.get("originY") == "center" else top + height / 2
            
            points = []
            for cmd in path:
                nums = [val for val in cmd if isinstance(val, (int, float))]
                if len(nums) >= 2:
                    x = center_x + (nums[-2] - path_offset_x)
                    y = center_y + (nums[-1] - path_offset_y)
                    points.append((x, y))
                    
            if len(points) > 1:
                draw.line(points, fill=stroke_color, width=stroke_width, joint="curve")
                
    return img.convert("RGB")

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
        st.session_state.bg_image = draw_fraction_equation(n1, d1, op1, n2, d2, op2, n3, d3)
        st.session_state.fabric_state = generate_fabric_json(n1, d1, op1, n2, d2, op2, n3, d3)
        st.session_state.ai_feedback = ""
        st.session_state.canvas_key += 1 
        st.session_state.generating = False
        st.rerun()

else:
    eq_str, lcm = st.session_state.math_data
    
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
        
        # Absolute bypass. It skips all validation and goes directly to grading.
        with st.spinner("The AI Tutor is checking your work..."):
            try:
                json_data = canvas_result.json_data if canvas_result else None
                final_canvas = render_strokes_on_image(st.session_state.bg_image, json_data)
                
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

    if st.session_state.ai_feedback:
        st.info(st.session_state.ai_feedback)

    if st.button("Give me a new problem!", use_container_width=True):
        st.session_state.generating = True
        st.rerun()