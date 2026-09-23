import streamlit as st
import random
import io
import json
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel, Field

# --- Import our Universal AI Marking Suite ---
import ai_marking_component

st.set_page_config(page_title="Numeracy 101", page_icon="🧮", layout="centered")

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

# --- AI Output Schemas ---
class SolutionRow(BaseModel):
    q_num: int = Field(description="The question number (1 to 20)")
    steps: str = Field(description="Step-by-step solving method")

class AIWorksheetSolutions(BaseModel):
    solutions: list[SolutionRow]

class WordProblemOutput(BaseModel):
    problem_text: str = Field(description="The problem statement text")
    target_variable: str = Field(description="The target unknown to find (e.g., 'Total Cost', 'Time in minutes')")

# --- Math Engine: NUMERACY WORD PROBLEM GENERATOR ---
def generate_numeracy_problem(domain):
    from google import genai
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    prompts = {
        "Financial (Money)": "Generate an everyday financial numeracy word problem. Focus on one of: calculating weekly wages with an hourly rate, finding a percentage discount on an item, calculating 15% GST, or splitting a household bill.",
        "DIY & Measurement": "Generate an everyday measurement word problem. Focus on one of: calculating the perimeter of a fence, the area of a floor for carpeting, or converting between mm, cm, and meters for a basic building task.",
        "Time & Travel": "Generate an everyday time and travel word problem. Focus on one of: calculating the duration of a bus/train journey given start and end times, or determining what time someone needs to leave home to arrive by a specific time.",
        "Data & Statistics": "Generate an everyday statistics word problem. Focus on one of: calculating the mean or median of 4-5 everyday numbers (like daily temperatures or coffee prices), or calculating a basic fraction/percentage probability.",
        "Baking & Proportions": "Generate an everyday proportions word problem. Focus on scaling a recipe up or down (e.g., a recipe makes 4 servings, how much flour is needed for 10 servings) using basic ratios or fractions."
    }
    
    base_prompt = (
        f"Act as an NCEA Numeracy (US32406) assessment writer. {prompts[domain]} "
        "Keep the numbers clean and grounded in everyday New Zealand reality. "
        "Output a JSON object containing: 1) problem_text: The word problem, 2) target_variable: What the student needs to find."
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[base_prompt],
            config=dict(response_mime_type="application/json", response_schema=WordProblemOutput, temperature=0.8)
        )
        return json.loads(response.text)
    except Exception:
        return {
            "problem_text": f"Error generating {domain} problem. Please try again.",
            "target_variable": "Unknown"
        }

# --- Visual Engine: WORD PROBLEM CANVAS RENDERER ---
def draw_word_problem_image(text, domain, width_px=380, height_px=760):
    fig, ax = plt.subplots(figsize=(width_px/100, height_px/100), dpi=100)
    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Add a domain badge at the top
    ax.text(0.5, 0.98, f"[{domain.upper()}]", fontsize=10, ha='center', va='top', fontweight='bold', color='#007AFF')
    
    wrapped_text = "\n".join(textwrap.wrap(text, width=42))
    ax.text(0.02, 0.92, wrapped_text, fontsize=12, ha='left', va='top', wrap=True, family='sans-serif', color='black')
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGBA').copy()

# --- Worksheet PDF Generator ---
def create_pdf_bytes(domain):
    from google import genai
    buffer = io.BytesIO()
    try:
        with PdfPages(buffer) as pdf:
            problems = [generate_numeracy_problem(domain) for _ in range(10)] # Limit to 10 for word-heavy grids
            ai_steps = {}
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                payload = "".join([f"Q{i+1}: {p['problem_text']}\n" for i, p in enumerate(problems)])
                prompt = (
                    "You are generating an answer key for an everyday numeracy test. "
                    "Write concise step-by-step workings and the final answer for each question. "
                    "Use \\n to separate steps so they break into new lines cleanly. "
                    "Data:\n" + payload
                )
                response = client.models.generate_content(
                    model='gemini-3.6-flash', contents=[prompt],
                    config=dict(response_mime_type="application/json", response_schema=AIWorksheetSolutions, temperature=0.1)
                )
                for item in json.loads(response.text).get("solutions", []):
                    cleaned_step = item["steps"].replace("**", "").replace(r"\n", "\n")
                    ai_steps[item["q_num"]] = cleaned_step
            except Exception:
                pass
            
            # Worksheet Page
            fig_ws, axes = plt.subplots(5, 2, figsize=(8.27, 11.69))
            fig_ws.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.03, wspace=0.10, hspace=0.30)
            fig_ws.suptitle(f"Numeracy Practice: {domain}", fontsize=16, fontweight='bold', ha='center')
            
            for idx, p_data in enumerate(problems):
                row, col = divmod(idx, 2)
                ax = axes[row, col]
                ax.axis('off')
                wrapped = "\n".join(textwrap.wrap(p_data['problem_text'], width=50))
                ax.text(0, 1, f"Q{idx+1}.", fontsize=10, fontweight='bold', va='top')
                ax.text(0.08, 1, wrapped, fontsize=9, va='top', wrap=True)
                
            pdf.savefig(fig_ws); plt.close(fig_ws)

            # Answer Key Page
            fig_ans, ax_ans = plt.subplots(figsize=(8.27, 11.69))
            ax_ans.axis('off')
            ax_ans.text(0.5, 0.96, "Answer Key & Workings", fontsize=16, fontweight='bold', ha='center')
            for i in range(5):
                left_idx, right_idx = i, i + 5
                txt_l = f"Q{left_idx+1}:\n{ai_steps.get(left_idx+1, 'Solution unavailable')}"
                txt_r = f"Q{right_idx+1}:\n{ai_steps.get(right_idx+1, 'Solution unavailable')}"
                y_pos = 0.90 - (i * 0.17)
                ax_ans.text(0.04, y_pos, txt_l, fontsize=8.0, va='top', wrap=True)
                ax_ans.text(0.52, y_pos, txt_r, fontsize=8.0, va='top', wrap=True)
            pdf.savefig(fig_ans); plt.close(fig_ans)
    except Exception as e:
        st.error(f"PDF Generation Error: {e}")
        raise e

    buffer.seek(0)
    return buffer.getvalue()

# --- State Management ---
if 'generating' not in st.session_state: st.session_state.generating = True
if 'num_domain' not in st.session_state: st.session_state.num_domain = "Financial (Money)"
if 'interaction_mode' not in st.session_state: st.session_state.interaction_mode = "Solve"
if 'camera_mode' not in st.session_state: st.session_state.camera_mode = "App"
if 'pdf_bytes' not in st.session_state: st.session_state.pdf_bytes = None
if 'problem_suite_refresh_id' not in st.session_state: st.session_state.problem_suite_refresh_id = 0

def handle_settings_change():
    st.session_state.generating = True
    st.session_state.pdf_bytes = None
    st.session_state.current_marking_color_index = 0 
    st.session_state.problem_suite_refresh_id += 1 

# --- UI Setup ---
st.title("Numeracy 101 🧮")

col_actions, col_set = st.columns([5, 1])
with col_actions:
    with st.popover("📄 Worksheet Actions", use_container_width=True):
        st.markdown(f"**Create a 10-Question {st.session_state.num_domain} Worksheet**")
        if st.session_state.pdf_bytes is None:
            if st.button("⚙️ Generate Worksheet PDF", use_container_width=True):
                with st.spinner("Compiling Numeracy Worksheet..."):
                    try:
                        st.session_state.pdf_bytes = create_pdf_bytes(st.session_state.num_domain)
                    except Exception:
                        st.session_state.pdf_bytes = None
                st.rerun()
        else:
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
            safe_name = st.session_state.num_domain.replace(' ', '_').replace('&', 'and')
            st.download_button("⬇️ Download Worksheet", data=st.session_state.pdf_bytes, file_name=f"Numeracy_{safe_name}_{timestamp_str}.pdf", mime="application/pdf", use_container_width=True, type="primary")
            if st.button("🗑️ Clear / Reset PDF", use_container_width=True):
                st.session_state.pdf_bytes = None
                st.rerun()

with col_set:
    with st.popover("⚙️", use_container_width=True):
        st.write("**Numeracy Settings**")
        domains = ["Financial (Money)", "DIY & Measurement", "Time & Travel", "Data & Statistics", "Baking & Proportions"]
        st.selectbox("Curriculum Domain", domains, key="num_domain", on_change=handle_settings_change)

# --- Master App Logic ---
if st.session_state.generating:
    with st.spinner(f"Generating {st.session_state.num_domain} scenario..."):
        wp_data = generate_numeracy_problem(st.session_state.num_domain)
        st.session_state.numeracy_problem_data = wp_data
        st.session_state.problem_image_context = draw_word_problem_image(wp_data.get('problem_text', ''), st.session_state.num_domain)
        st.session_state.generating = False
        st.rerun()

else:
    bg_image = st.session_state.problem_image_context
    target_desc = st.session_state.numeracy_problem_data.get('target_variable', 'the answer')
    
    st.write(f"**Find {target_desc}!**")
    
    problem_context = f"This is an everyday numeracy problem in the domain of {st.session_state.num_domain}. The student must use appropriate real-world math (like finding GST, scaling recipes, converting units, or calculating time). The specific problem is: {st.session_state.numeracy_problem_data.get('problem_text', '')}. Ensure they show their method clearly."

    ai_marking_component.render_grading_suite(
        bg_image=bg_image,
        height_px=760,
        key_prefix=f"num_suite_{st.session_state.problem_suite_refresh_id}",
        solution_requirement="numeric", 
        problem_context=problem_context
    )

    st.write("---")
    if st.button("Give me a new numeracy problem!", use_container_width=True):
        handle_settings_change()
        st.rerun()