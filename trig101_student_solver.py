import streamlit as st
import random
import math
import io
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image
from datetime import datetime
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

    base_a, base_b = random.randint(4, 12), random.randint(4, 12)
    hyp_real = math.hypot(base_a, base_b)
    angle_rad = math.atan2(base_a, base_b)
    angle_deg = round(math.degrees(angle_rad))
    
    opp_val = round(base_a, 1) if base_a % 1 != 0 else base_a
    adj_val = round(base_b, 1) if base_b % 1 != 0 else base_b
    hyp_val = round(hyp_real, 1) if hyp_real % 1 != 0 else int(hyp_real)

    side_var = random.choice(['x', 'y', 'z', 'a', 'b', 'c', 'h', 'p', 'q'])
    angle_var = random.choice([r'\theta', r'\alpha', r'\beta', r'\gamma', r'\phi', 'x', 'y'])

    labels = {'opp': '', 'adj': '', 'hyp': '', 'angle': ''}
    ans = 0
    text_desc = ""
    target_var = ""
    rule_key = ""

    if topic == "Pythagoras":
        rule_key = "Pythagoras"
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
        base_rule = random.choice(["Sine", "Cosine", "Tangent"])
        find_angle = random.choice([True, False])
        
        if find_angle:
            rule_key = f"{base_rule} Inverse"
        else:
            rule_key = base_rule
            
        if base_rule == "Sine":
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
                    
        elif base_rule == "Cosine":
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
                    
        elif base_rule == "Tangent":
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

    return labels, rule_key, ans, text_desc, (opp_val, adj_val), target_var

# --- Visual Engine: DYNAMIC MATPLOTLIB GEOMETRY ---
def draw_triangle_image(problem_data, height_px=220, width_px=220):
    labels, rule_key, ans, text_desc, (a, b), target_var = problem_data
    
    fig, ax = plt.subplots(figsize=(width_px/100, height_px/100), dpi=100)
    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    ax.set_aspect('equal', adjustable='box')
    
    C = np.array([0, 0])
    A = np.array([b, 0])
    B = np.array([0, a])
    
    theta = random.uniform(0, 2 * np.pi)
    R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    C_rot, A_rot, B_rot = R.dot(C), R.dot(A), R.dot(B)
    
    pts = np.vstack([C_rot, A_rot, B_rot])
    min_pt, max_pt = pts.min(axis=0), pts.max(axis=0)
    center = (min_pt + max_pt) / 2
    scale = 0.55 / max(max_pt - min_pt)
    
    Cf = (C_rot - center) * scale + [0.5, 0.5]
    Af = (A_rot - center) * scale + [0.5, 0.5]
    Bf = (B_rot - center) * scale + [0.5, 0.5]
    
    triangle = plt.Polygon([Cf, Af, Bf], fill=False, edgecolor='black', linewidth=1.5)
    ax.add_patch(triangle)
    
    vCA = (Af - Cf) / np.linalg.norm(Af - Cf) * 0.04
    vCB = (Bf - Cf) / np.linalg.norm(Bf - Cf) * 0.04
    sq_pts = [Cf + vCA, Cf + vCA + vCB, Cf + vCB]
    ax.plot([Cf[0]+vCA[0], sq_pts[1][0], sq_pts[2][0]], [Cf[1]+vCA[1], sq_pts[1][1], sq_pts[2][1]], color='black', lw=1)
    
    if labels['angle']:
        vAC = Cf - Af
        vAB = Bf - Af
        ang1 = np.degrees(np.arctan2(vAC[1], vAC[0]))
        ang2 = np.degrees(np.arctan2(vAB[1], vAB[0]))
        min_ang, max_ang = min(ang1, ang2), max(ang1, ang2)
        if max_ang - min_ang > 180:
            min_ang, max_ang = max_ang, min_ang + 360
            
        arc = patches.Arc(Af, 0.12, 0.12, angle=0.0, theta1=min_ang, theta2=max_ang, color='black', linewidth=1)
        ax.add_patch(arc)
        
        mid_rad = np.radians((min_ang + max_ang) / 2)
        txt_pos = Af + 0.09 * np.array([np.cos(mid_rad), np.sin(mid_rad)])
        ax.text(txt_pos[0], txt_pos[1], f"${labels['angle']}$", fontsize=12, ha='center', va='center')

    def place_label(p1, p2, text):
        if not text: return
        mid = (p1 + p2) / 2
        vec = p2 - p1
        normal = np.array([-vec[1], vec[0]]) 
        normal = normal / np.linalg.norm(normal)
        if np.dot(normal, mid - np.array([0.5, 0.5])) < 0: normal = -normal
        pos = mid + normal * 0.06
        
        # Calculate side gradient alignment and prevent upside-down text
        angle_deg = np.degrees(np.arctan2(vec[1], vec[0]))
        if angle_deg > 90:
            angle_deg -= 180
        elif angle_deg < -90:
            angle_deg += 180

        ax.text(pos[0], pos[1], f"${text}$", fontsize=12, ha='center', va='center', rotation=angle_deg, rotation_mode='anchor')

    place_label(Cf, Bf, labels['opp']) 
    place_label(Cf, Af, labels['adj']) 
    place_label(Af, Bf, labels['hyp']) 

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGBA').copy()

# --- Worksheet PDF Generator (5 rows of 4 images layout) ---
def create_pdf_bytes(topic_setting):
    from google import genai
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        problems = [generate_trig_problem(topic_setting) for _ in range(20)]
        ai_steps = {}
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            payload = "".join([f"Q{i+1}: {p[3]} | Ans: {p[2]}\n" for i, p in enumerate(problems)])
            prompt = f"Write very brief, space-saving step solutions using shorthand notation (e.g., opp., adj., hyp., pythag.). Plain text.\nData:\n{payload}"
            response = client.models.generate_content(
                model='gemini-3.6-flash', contents=[prompt],
                config=dict(response_mime_type="application/json", response_schema=AIWorksheetSolutions, temperature=0.1)
            )
            for item in json.loads(response.text).get("solutions", []):
                ai_steps[item["q_num"]] = item["steps"].replace("**", "")
        except Exception as e:
            pass
        
        # Page 1: Worksheet Grid (5 rows x 4 cols of triangle images)
        fig_ws, axes = plt.subplots(5, 4, figsize=(8.27, 11.69))
        fig_ws.subplots_adjust(left=0.05, right=0.95, top=0.90, bottom=0.05, wspace=0.2, hspace=0.3)
        fig_ws.suptitle("Trigonometry 101 Worksheet", fontsize=16, fontweight='bold', ha='center')
        
        for idx, p_data in enumerate(problems):
            row, col = divmod(idx, 4)
            ax = axes[row, col]
            ax.axis('off')
            img_buf = draw_triangle_image(p_data, height_px=180, width_px=180)
            ax.imshow(img_buf)
            ax.set_title(f"Q{idx+1}", fontsize=10, fontweight='bold', pad=2)
            
        pdf.savefig(fig_ws); plt.close(fig_ws)

        # Page 2: Answer Key with compact text wrapping
        fig_ans, ax_ans = plt.subplots(figsize=(8.27, 11.69))
        ax_ans.axis('off')
        ax_ans.text(0.5, 0.95, "Answer Key & Steps", fontsize=16, fontweight='bold', ha='center')
        for i in range(10):
            left_idx = i
            right_idx = i + 10
            txt_l = f"Q{left_idx+1}: Ans: {problems[left_idx][2]} | {ai_steps.get(left_idx+1, '')}"
            txt_r = f"Q{right_idx+1}: Ans: {problems[right_idx][2]} | {ai_steps.get(right_idx+1, '')}"
            ax_ans.text(0.05, 0.88 - (i*0.08), txt_l, fontsize=8, va='top', wrap=True)
            ax_ans.text(0.52, 0.88 - (i*0.08), txt_r, fontsize=8, va='top', wrap=True)
        pdf.savefig(fig_ans); plt.close(fig_ans)

    return buffer.getvalue()

# --- State Management ---
if 'generating' not in st.session_state: st.session_state.generating = True
if 'trig_topic' not in st.session_state: st.session_state.trig_topic = "Both"
if 'interaction_mode' not in st.session_state: st.session_state.interaction_mode = "Solve"
if 'solution_req' not in st.session_state: st.session_state.solution_req = "demonstrated"
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
        st.markdown("**1. Create a physical worksheet**")
        if st.session_state.pdf_bytes is None:
            if st.button("⚙️ Generate Worksheet PDF", use_container_width=True):
                with st.spinner("Compiling Master PDF Grid..."):
                    st.session_state.pdf_bytes = create_pdf_bytes(st.session_state.trig_topic)
                st.rerun()
        else:
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
            st.download_button("⬇️ Download Worksheet", data=st.session_state.pdf_bytes, file_name=f"Trigonometry_101_{timestamp_str}.pdf", mime="application/pdf", use_container_width=True, type="primary")
            if st.button("🗑️ Clear / Reset PDF", use_container_width=True):
                st.session_state.pdf_bytes = None
                st.rerun()
        st.markdown("---")
        st.markdown("**2. Grade student workings**")
        if "WORKSHEET_MARKER_APP_URL" in st.secrets:
            st.link_button("🤖 Mark My Worksheet", st.secrets["WORKSHEET_MARKER_APP_URL"], use_container_width=True)

with col_set:
    with st.popover("⚙️", use_container_width=True):
        st.write("**Settings**")
        st.radio("Problem Type", ["Pythagoras", "Trigonometry", "Both"], key="trig_topic", on_change=handle_settings_change)
        st.radio("Interaction Mode", ["Identification", "Solve"], key="interaction_mode", on_change=handle_settings_change)
        st.radio("Solution Required", ["demonstrated", "numeric"], key="solution_req", on_change=handle_settings_change)
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
    labels, rule_key, ans, text_desc, sides, target_var = st.session_state.trig_problem_data
    bg_image = st.session_state.problem_image_context

    st.write(f"**Find the missing value (${target_var}$)!**")

    if st.session_state.interaction_mode == "Identification":
        st.image(bg_image, use_column_width=True)
        st.write("Which mathematical rule is required to solve this problem?")
        
        all_rules = ["Pythagoras", "Sine", "Cosine", "Tangent", "Sine Inverse", "Cosine Inverse", "Tangent Inverse"]
        display_names = {
            "Pythagoras": "Pythagoras",
            "Sine": "sin",
            "Cosine": "cos",
            "Tangent": "tan",
            "Sine Inverse": "sin⁻¹",
            "Cosine Inverse": "cos⁻¹",
            "Tangent Inverse": "tan⁻¹"
        }
        
        if 'id_options' not in st.session_state or st.session_state.get('last_refresh_id') != st.session_state.problem_suite_refresh_id:
            incorrect_pool = [r for r in all_rules if r != rule_key]
            chosen_incorrect = random.sample(incorrect_pool, 2)
            options = chosen_incorrect + [rule_key]
            random.shuffle(options)
            st.session_state.id_options = options
            st.session_state.last_refresh_id = st.session_state.problem_suite_refresh_id

        c1, c2, c3 = st.columns(3)
        def check_rule(guess):
            if guess == rule_key: st.session_state.id_feedback = f"Correct! Use **{display_names[rule_key]}**."
            else: st.session_state.id_feedback = f"Not quite. Try again!"
            
        for idx, opt in enumerate(st.session_state.id_options):
            col = [c1, c2, c3][idx]
            if col.button(display_names[opt], use_container_width=True):
                check_rule(opt)
        
        if st.session_state.id_feedback:
            if "Correct" in st.session_state.id_feedback: st.success(f"🌟 {st.session_state.id_feedback}")
            else: st.warning(f"🤖 {st.session_state.id_feedback}")
            
    else:
        ai_marking_component.render_grading_suite(
            bg_image=bg_image,
            height_px=450,
            key_prefix=f"trig_suite_{st.session_state.problem_suite_refresh_id}",
            solution_requirement=st.session_state.get('solution_req', 'demonstrated')
        )

    st.write("---")
    if st.button("Give me a new problem!", use_container_width=True):
        handle_settings_change()
        st.rerun()