import streamlit as st
import random
import math
import io
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from matplotlib.backends.backend_pdf import PdfPages
import streamlit.components.v1 as components
from pydantic import BaseModel, Field

# --- Import our Universal AI Marking Suite ---
import ai_marking_component

st.set_page_config(page_title="Trigonometry 101", page_icon="📐", layout="centered")

if 'PEN_COLORS' not in st.session_state:
    st.session_state.PEN_COLORS = ["#1E90FF", "#FF2400", "#32CD32", "#9400D3", "#FF8C00"]
    st.session_state.COLOR_NAMES = ["BLUE", "RED", "GREEN", "PURPLE", "ORANGE"]

st.markdown("""
    <style>
    button[kind="primary"] { background-color: #007AFF !important; border-color: #007AFF !important; color: white !important; }
    button[kind="primary"]:hover { background-color: #0056b3 !important; border-color: #0056b3 !important; }
    .stRadio > div { gap: 0rem; }
    [data-testid="stHorizontalBlock"] { gap: 0.5rem; align-items: center; }
    div[data-testid="stToolbar"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# --- AI Output Schemas for Worksheets ---
class SolutionRow(BaseModel):
    q_num: int = Field(description="The question number (1 to 20)")
    steps: str = Field(description="Step-by-step solving method")

class AIWorksheetSolutions(BaseModel):
    solutions: list[SolutionRow]

# --- Math Engine: TRIGONOMETRY ---
def generate_trig_problem(topic_setting):
    """Generates random side/angle combinations and returns the required labels & rule."""
    if topic_setting == "Both":
        topic = random.choice(["Pythagoras", "Trigonometry"])
    else:
        topic = topic_setting

    # Base triangle generation (3,4,5 scaling to keep it visually nice)
    base_a, base_b = random.randint(4, 12), random.randint(4, 12)
    hyp_real = math.hypot(base_a, base_b)
    angle_rad = math.atan2(base_a, base_b)
    angle_deg = round(math.degrees(angle_rad))
    
    # We round sides to 1 decimal place for neatness if not whole numbers
    opp_val = round(base_a, 1) if base_a % 1 != 0 else base_a
    adj_val = round(base_b, 1) if base_b % 1 != 0 else base_b
    hyp_val = round(hyp_real, 1) if hyp_real % 1 != 0 else int(hyp_real)

    # Random variables for sides and angles
    side_var = random.choice(['x', 'y', 'z', 'a', 'b', 'c', 'h', 'p', 'q'])
    angle_var = random.choice([r'\theta', r'\alpha', r'\beta', r'\gamma', r'\phi', 'x', 'y'])

    labels = {'opp': '', 'adj': '', 'hyp': '', 'angle': ''}
    ans = 0
    text_desc = ""
    target_var = ""

    if topic == "Pythagoras":
        rule = "Pythagoras"
        target = random.choice(['hyp', 'leg1', 'leg2'])
        target_var = side_var
        if target == 'hyp':
            labels['opp'], labels['adj'], labels['hyp'] = opp_val, adj_val, side_var
            ans, text_desc = hyp_val, f"Legs {opp_val}, {adj_val}. Find hyp {side_var}."
        elif target == 'leg1':
            labels['opp'], labels['adj'], labels['hyp'] = side_var, adj_val, hyp_val
            ans, text_desc = opp_val, f"Hyp {hyp_val}, Leg {adj_val}. Find leg {side_var}."
        else:
            labels['opp'], labels['adj'], labels['hyp'] = opp_val, side_var, hyp_val
            ans, text_desc = adj_val, f"Hyp {hyp_val}, Leg {opp_val}. Find leg {side_var}."
    
    else:
        rule = random.choice(["Sine", "Cosine", "Tangent"])
        find_angle = random.choice([True, False])
        
        if rule == "Sine":
            if find_angle:
                target_var = angle_var
                labels['opp'], labels['hyp'], labels['angle'] = opp_val, hyp_val, angle_var
                ans, text_desc = angle_deg, f"Opp {opp_val}, Hyp {hyp_val}. Find angle {angle_var}."
            else:
                target_var = side_var
                if random.choice([True, False]):
                    labels['opp'], labels['hyp'], labels['angle'] = side_var, hyp_val, f"{angle_deg}^\\circ"
                    ans, text_desc = opp_val, f"Angle {angle_deg}, Hyp {hyp_val}. Find Opp {side_var}."
                else:
                    labels['opp'], labels['hyp'], labels['angle'] = opp_val, side_var, f"{angle_deg}^\\circ"
                    ans, text_desc = hyp_val, f"Angle {angle_deg}, Opp {opp_val}. Find Hyp {side_var}."
                    
        elif rule == "Cosine":
            if find_angle:
                target_var = angle_var
                labels['adj'], labels['hyp'], labels['angle'] = adj_val, hyp_val, angle_var
                ans, text_desc = angle_deg, f"Adj {adj_val}, Hyp {hyp_val}. Find angle {angle_var}."
            else:
                target_var = side_var
                if random.choice([True, False]):
                    labels['adj'], labels['hyp'], labels['angle'] = side_var, hyp_val, f"{angle_deg}^\\circ"
                    ans, text_desc = adj_val, f"Angle {angle_deg}, Hyp {hyp_val}. Find Adj {side_var}."
                else:
                    labels['adj'], labels['hyp'], labels['angle'] = adj_val, side_var, f"{angle_deg}^\\circ"
                    ans, text_desc = hyp_val, f"Angle {angle_deg}, Adj {adj_val}. Find Hyp {side_var}."
                    
        elif rule == "Tangent":
            if find_angle:
                target_var = angle_var
                labels['opp'], labels['adj'], labels['angle'] = opp_val, adj_val, angle_var
                ans, text_desc = angle_deg, f"Opp {opp_val}, Adj {adj_val}. Find angle {angle_var}."
            else:
                target_var = side_var
                if random.choice([True, False]):
                    labels['opp'], labels['adj'], labels['angle'] = side_var, adj_val, f"{angle_deg}^\\circ"
                    ans, text_desc = opp_val, f"Angle {angle_deg}, Adj {adj_val}. Find Opp {side_var}."
                else:
                    labels['opp'], labels['adj'], labels['angle'] = opp_val, side_var, f"{angle_deg}^\\circ"
                    ans, text_desc = adj_val, f"Angle {angle_deg}, Opp {opp_val}. Find Adj {side_var}."

    return labels, rule, ans, text_desc, (opp_val, adj_val), target_var

# --- Visual Engine: DYNAMIC MATPLOTLIB GEOMETRY ---
def draw_triangle_image(problem_data, height_px):
    labels, rule, ans, text_desc, (a, b), target_var = problem_data
    
    fig, ax = plt.subplots(figsize=(3.5, height_px/100), dpi=100)
    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Base Triangle Vertices: C(right angle), A(angle theta), B
    C = np.array([0, 0])
    A = np.array([b, 0])
    B = np.array([0, a])
    
    # Random Rotation
    theta = random.uniform(0, 2 * np.pi)
    R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    C_rot, A_rot, B_rot = R.dot(C), R.dot(A), R.dot(B)
    
    # Scale and center in the frame
    pts = np.vstack([C_rot, A_rot, B_rot])
    min_pt, max_pt = pts.min(axis=0), pts.max(axis=0)
    center = (min_pt + max_pt) / 2
    scale = 0.55 / max(max_pt - min_pt)
    
    Cf = (C_rot - center) * scale + [0.5, 0.5]
    Af = (A_rot - center) * scale + [0.5, 0.5]
    Bf = (B_rot - center) * scale + [0.5, 0.5]
    
    # Draw Triangle
    triangle = plt.Polygon([Cf, Af, Bf], fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(triangle)
    
    # Draw Right Angle Square at C
    vCA = (Af - Cf) / np.linalg.norm(Af - Cf) * 0.05
    vCB = (Bf - Cf) / np.linalg.norm(Bf - Cf) * 0.05
    sq_pts = [Cf + vCA, Cf + vCA + vCB, Cf + vCB]
    ax.plot([Cf[0]+vCA[0], sq_pts[1][0], sq_pts[2][0]], [Cf[1]+vCA[1], sq_pts[1][1], sq_pts[2][1]], color='black', lw=1.5)
    
    # Draw Angle Arc at A (if labeled)
    if labels['angle']:
        vAC = (Cf - Af) / np.linalg.norm(Cf - Af) * 0.1
        vAB = (Bf - Af) / np.linalg.norm(Bf - Af) * 0.1
        # Simple curve approximation for arc
        arc_x = [Af[0] + vAC[0]*0.8, Af[0] + (vAC[0]+vAB[0])*0.6, Af[0] + vAB[0]*0.8]
        arc_y = [Af[1] + vAC[1]*0.8, Af[1] + (vAC[1]+vAB[1])*0.6, Af[1] + vAB[1]*0.8]
        ax.plot(arc_x, arc_y, color='black', lw=1.5)
        # Place angle text slightly further inward
        txt_pos = Af + (vAC + vAB) * 0.8
        ax.text(txt_pos[0], txt_pos[1], f"${labels['angle']}$", fontsize=16, ha='center', va='center')

    # Helper to place text outside the line
    def place_label(p1, p2, text):
        if not text: return
        mid = (p1 + p2) / 2
        vec = p2 - p1
        # Normal vector pointing "outward" from the center of the triangle
        normal = np.array([-vec[1], vec[0]]) 
        normal = normal / np.linalg.norm(normal)
        # Ensure normal points away from the opposing vertex (center of triangle approximation)
        if np.dot(normal, mid - np.array([0.5, 0.5])) < 0: normal = -normal
        pos = mid + normal * 0.06
        ax.text(pos[0], pos[1], f"${text}$", fontsize=16, ha='center', va='center')

    place_label(Cf, Bf, labels['opp']) # Opposite to A
    place_label(Cf, Af, labels['adj']) # Adjacent to A
    place_label(Af, Bf, labels['hyp']) # Hypotenuse

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGBA').copy()

# --- Worksheet PDF Generator ---
def create_pdf_bytes(topic_setting):
    from google import genai
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        problems = [generate_trig_problem(topic_setting) for _ in range(20)]
        ai_steps = {}
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            payload = "".join([f"Q{i+1}: {p[3]} | Ans: {p[2]}\n" for i, p in enumerate(problems)])
            prompt = f"Write the concise, human-readable step-by-step solution method for each right-angled triangle problem using SOH CAH TOA or Pythagoras. Plain text.\nData:\n{payload}"
            response = client.models.generate_content(
                model='gemini-3.6-flash', contents=[prompt],
                config=dict(response_mime_type="application/json", response_schema=AIWorksheetSolutions, temperature=0.1)
            )
            for item in json.loads(response.text).get("solutions", []):
                ai_steps[item["q_num"]] = item["steps"].replace("**", "")
        except Exception as e:
            pass
        
        fig, axes = plt.subplots(figsize=(8.27, 11.69))
        axes.axis('off')
        axes.text(0.5, 0.95, f"Trigonometry 101 Worksheet", fontsize=16, fontweight='bold', ha='center')
        for i in range(10):
            axes.text(0.05, 0.88 - (i*0.085), f"Q{i+1}: {problems[i][3]}", fontsize=11, va='top')
            axes.text(0.55, 0.88 - (i*0.085), f"Q{i+11}: {problems[i+10][3]}", fontsize=11, va='top')
        pdf.savefig(fig); plt.close(fig)

        fig_ans, ax_ans = plt.subplots(figsize=(8.27, 11.69))
        ax_ans.axis('off')
        ax_ans.text(0.5, 0.95, "Answer Key & Steps", fontsize=16, fontweight='bold', ha='center')
        for i in range(10):
            ax_ans.text(0.05, 0.88 - (i*0.085), f"Q{i+1}: {problems[i][2]}\n{ai_steps.get(i+1, '')}", fontsize=8, va='top', wrap=True)
            ax_ans.text(0.55, 0.88 - (i*0.085), f"Q{i+11}: {problems[i+10][2]}\n{ai_steps.get(i+11, '')}", fontsize=8, va='top', wrap=True)
        pdf.savefig(fig_ans); plt.close(fig_ans)

    return buffer.getvalue()

# --- State Management ---
if 'generating' not in st.session_state: st.session_state.generating = True
if 'trig_topic' not in st.session_state: st.session_state.trig_topic = "Both"
if 'interaction_mode' not in st.session_state: st.session_state.interaction_mode = "Solve"
if 'camera_mode' not in st.session_state: st.session_state.camera_mode = "App"
if 'pdf_bytes' not in st.session_state: st.session_state.pdf_bytes = None
if 'problem_suite_refresh_id' not in st.session_state: st.session_state.problem_suite_refresh_id = 0
if 'id_feedback' not in st.session_state: st.session_state.id_feedback = ""
if 'current_marking_color_index' not in st.session_state: st.session_state.current_marking_color_index = 0

def handle_settings_change():
    st.session_state.generating = True
    st.session_state.pdf_bytes = None
    st.session_state.id_feedback = ""
    st.session_state.current_marking_color_index = 0 
    st.session_state.problem_suite_refresh_id += 1 

# --- UI Setup ---
st.title("Trigonometry 101")

col_actions, col_set = st.columns([5, 1])
with col_actions:
    with st.popover("📄 Worksheet Actions", use_container_width=True):
        if st.session_state.pdf_bytes is None:
            if st.button("⚙️ Generate Worksheet PDF", use_container_width=True):
                with st.spinner("Compiling Master PDF..."):
                    st.session_state.pdf_bytes = create_pdf_bytes(st.session_state.trig_topic)
                st.rerun()
        else:
            st.download_button("⬇️ Download Worksheet", data=st.session_state.pdf_bytes, file_name="Trigonometry_101.pdf", mime="application/pdf", use_container_width=True, type="primary")
            if st.button("🗑️ Clear / Reset PDF", use_container_width=True):
                st.session_state.pdf_bytes = None
                st.rerun()

with col_set:
    with st.popover("⚙️", use_container_width=True):
        st.write("**Settings**")
        st.radio("Problem Type", ["Pythagoras", "Trigonometry", "Both"], key="trig_topic", on_change=handle_settings_change)
        st.radio("Interaction Mode", ["Identification", "Solve"], key="interaction_mode", on_change=handle_settings_change)
        st.radio("Camera Mode", ["App", "Native"], key="camera_mode", horizontal=True)

# --- Master App Logic ---
if st.session_state.generating:
    with st.spinner("Drawing geometry..."):
        p_data = generate_trig_problem(st.session_state.trig_topic)
        st.session_state.trig_problem_data = p_data
        st.session_state.problem_image_context = draw_triangle_image(p_data, 450)
        st.session_state.generating = False
        st.rerun()

else:
    labels, rule, ans, text_desc, sides, target_var = st.session_state.trig_problem_data
    bg_image = st.session_state.problem_image_context

    st.write(f"**Find the missing value (${target_var}$)!**")

    if st.session_state.interaction_mode == "Identification":
        # MODE 1: IDENTIFICATION (Master App handles this purely)
        st.image(bg_image, use_container_width=True)
        st.write("Which mathematical rule is required to solve this problem?")
        
        c1, c2, c3, c4 = st.columns(4)
        def check_rule(guess):
            if guess == rule: st.session_state.id_feedback = f"Correct! We use **{rule}** here."
            else: st.session_state.id_feedback = f"Not quite. Try again!"
            
        if c1.button("Pythagoras", use_container_width=True): check_rule("Pythagoras")
        if c2.button("Sine", use_container_width=True): check_rule("Sine")
        if c3.button("Cosine", use_container_width=True): check_rule("Cosine")
        if c4.button("Tangent", use_container_width=True): check_rule("Tangent")
        
        if st.session_state.id_feedback:
            if "Correct" in st.session_state.id_feedback: st.success(f"🌟 {st.session_state.id_feedback}")
            else: st.warning(f"🤖 {st.session_state.id_feedback}")
            
    else:
        # MODE 2: SOLVE (Master App delegates to the Universal Marker Widget)
        TRIG_GRADING_HINTS = """
        CRITICAL GEOMETRY/TRIGONOMETRY VISUAL PARSING RULES:
        1. STEP 1 (OVERWRITING): Look exclusively at the current pen ink color alone. If that ink color alone shows the correct mathematical final answer (number or angle), treat it as correct and ignore the messy older ink underneath.
        2. STEP 2 (COMBINED MARKUP): If Step 1 does not yield a correct answer, evaluate the tangled messy ink as a single, combined shape. If the combined colors together form the correct final answer, treat it as correct.
        3. STEP 3 (DELETIONS): If you see distinct scribbles over old work, assume that specific messy part is deleted. Evaluate the remaining work.
        """
        
        color_sequence_str = ", ".join(st.session_state.COLOR_NAMES)
        current_color_str = st.session_state.COLOR_NAMES[st.session_state.current_marking_color_index]
        
        universal_prompt = f"""
        You are an expert math tutor grading a student's Trigonometry/Geometry work.
        The right-angled triangle problem to be solved is printed on the background image. Deduce the knowns and the unknown directly from the diagram.
        
        The student is using a sequence of pen colors: {color_sequence_str}.
        They are currently writing in: {current_color_str}.
        
        {TRIG_GRADING_HINTS}
        
        GRADING INSTRUCTIONS:
        - If Step 1 OR Step 2 OR Step 3 reveals the mathematically correct final answer for the missing side/angle, reply EXACTLY with "CORRECT:" on the first line, followed by a brief congratulatory message. Be highly forgiving of visual messiness.
        - If their working is still incorrect, incomplete, or missing the final answer after trying all steps, reply EXACTLY with "INCORRECT:" on the first line, followed by a brief, encouraging hint on what trig ratio or step to use next. Do not give the final answer.
        """

        ai_marking_component.render_grading_suite(
            bg_image=bg_image,
            height_px=450,
            grading_prompt_instructions=universal_prompt,
            suite_key=f"trig_suite_{st.session_state.problem_suite_refresh_id}"
        )

    st.write("---")
    if st.button("Give me a new problem!", use_container_width=True):
        handle_settings_change()
        st.rerun()