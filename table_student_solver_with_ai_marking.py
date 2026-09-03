import streamlit as st
import matplotlib
matplotlib.use('Agg') # CRITICAL: Forces Matplotlib to draw on headless servers
import matplotlib.pyplot as plt
import numpy as np
import random
import io
import re
import base64
from PIL import Image
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
from google import genai

# --- THE MONKEY PATCH ---
# We must patch Streamlit's missing URL function BEFORE importing the canvas component
import streamlit.elements.image as st_image
if not hasattr(st_image, "image_to_url"):
    def patched_image_to_url(image, *args, **kwargs):
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    st_image.image_to_url = patched_image_to_url
# ------------------------

from streamlit_drawable_canvas import st_canvas

# --- Formatting Helpers ---
def fmt_num(n):
    return int(n) if n == int(n) else n

# --- Core Math Engine: TABLES ---
def generate_table_data():
    func_type = random.choice(['Linear', 'Quadratic', 'Exponential'])
    x_vals = np.array([0, 1, 2, 3, 4])
    
    if func_type == 'Linear':
        m = random.choice([2, 3, 4, 5, -2, -3, -4])
        c = random.randint(-5, 10)
        y_vals = m * x_vals + c
        
        eq = f"y = {m}x {'+' if c >= 0 else '-'} {abs(c)}"
        steps = (f"**Linear Table Steps**\n\n"
                 f"1. Check the 1st differences: As x increases by 1, y changes by **{m}** every time.\n"
                 f"2. Constant 1st difference = Linear ($y = mx + c$).\n"
                 f"3. The gradient $m = {m}$.\n"
                 f"4. The y-intercept $c$ is the y-value when $x=0$, which is **{c}**.\n\n"
                 f"**${eq}$**")
        
    elif func_type == 'Quadratic':
        a = random.choice([1, 2, 0.5, -1, -2])
        b = random.randint(-3, 3)
        c = random.randint(-5, 5)
        y_vals = a * (x_vals**2) + b * x_vals + c
        
        a_str = "" if a == 1 else "-" if a == -1 else str(fmt_num(a))
        b_str = "" if b == 0 else f" + x" if b == 1 else f" - x" if b == -1 else f" + {b}x" if b > 0 else f" - {abs(b)}x"
        c_str = "" if c == 0 else f" + {c}" if c > 0 else f" - {abs(c)}"
        eq_str = f"{a_str}x^2{b_str}{c_str}"
        eq = f"y = {eq_str}"
        
        sec_diff = a * 2
        steps = (f"**Quadratic Table Steps**\n\n"
                 f"1. Check 1st differences: They are changing.\n"
                 f"2. Check 2nd differences: They are constant at **{fmt_num(sec_diff)}**.\n"
                 f"3. Constant 2nd difference = Quadratic ($y = ax^2 + bx + c$).\n"
                 f"4. The $a$ value is half the 2nd difference: $a = {fmt_num(sec_diff)} \\div 2 = {fmt_num(a)}$.\n"
                 f"5. The y-intercept $c$ is the y-value when $x=0$, which is **{c}**.\n"
                 f"6. Substitute a known point (e.g., $x=1, y={fmt_num(y_vals[1])}$) to find $b$.\n\n"
                 f"**${eq}$**")
                 
    elif func_type == 'Exponential':
        r = random.choice([2, 3, 4])
        a = random.choice([1, 2, 3, 5])
        y_vals = a * (r**x_vals)
        
        eq = f"y = {a} \\cdot {r}^x"
        steps = (f"**Exponential Table Steps**\n\n"
                 f"1. Check differences: Neither 1st nor 2nd are constant.\n"
                 f"2. Check for a multiplier (common ratio): As x increases by 1, y is multiplied by **{r}**.\n"
                 f"3. Constant multiplier = Exponential ($y = a \\cdot r^x$).\n"
                 f"4. The base (multiplier) $r = {r}$.\n"
                 f"5. The initial value $a$ is the y-value when $x=0$, which is **{a}**.\n\n"
                 f"**${eq}$**")

    return func_type, list(x_vals), list(y_vals), steps, eq

# --- Dynamic Plotting Engine: TABLE IMAGE (For Web App Canvas) ---
def draw_table_image(x_vals, y_vals):
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    ax.text(0.1, 0.9, "x", fontsize=20, fontweight='bold', ha='center')
    ax.text(0.3, 0.9, "y", fontsize=20, fontweight='bold', ha='center')
    ax.plot([0.0, 0.4], [0.85, 0.85], color='black', lw=2)
    
    y_pos = 0.75
    for x, y in zip(x_vals, y_vals):
        ax.text(0.1, y_pos, str(fmt_num(x)), fontsize=16, ha='center', va='center')
        ax.text(0.3, y_pos, str(fmt_num(y)), fontsize=16, ha='center', va='center')
        y_pos -= 0.15
        
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)
    
    img = Image.open(buf).convert('RGBA').copy()
    return img
    
# --- Dynamic Plotting Engine: PDF TABLE MAKER (With Markup Capabilities) ---
def draw_pdf_table(ax, x_vals, y_vals, func_type=None, show_markup=False):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    ax.text(0.15, 0.9, "x", fontsize=11, fontweight='bold', ha='center')
    ax.text(0.35, 0.9, "y", fontsize=11, fontweight='bold', ha='center')
    ax.plot([0.05, 0.45], [0.82, 0.82], color='black', lw=1.5)
    
    y_pos = [0.7, 0.55, 0.4, 0.25, 0.1]
    for i, (x, y) in enumerate(zip(x_vals, y_vals)):
        ax.text(0.15, y_pos[i], str(fmt_num(x)), fontsize=10, ha='center', va='center')
        ax.text(0.35, y_pos[i], str(fmt_num(y)), fontsize=10, ha='center', va='center')
        
    if show_markup:
        diff1 = [y_vals[i+1] - y_vals[i] for i in range(4)]
        
        for i in range(4):
            ys, ye = y_pos[i], y_pos[i+1]
            ymid = (ys + ye) / 2
            ax.annotate("", xy=(0.45, ye), xytext=(0.45, ys),
                        arrowprops=dict(arrowstyle="-", connectionstyle="arc3,rad=-0.4", color='#1E90FF', lw=1.5))
            
            if func_type == 'Linear':
                lbl = f"+{fmt_num(diff1[i])}" if diff1[i] >= 0 else str(fmt_num(diff1[i]))
                ax.text(0.65, ymid, lbl, color='#1E90FF', fontsize=10, va='center', fontweight='bold')
            elif func_type == 'Quadratic':
                lbl = f"+{fmt_num(diff1[i])}" if diff1[i] >= 0 else str(fmt_num(diff1[i]))
                ax.text(0.55, ymid, lbl, color='#1E90FF', fontsize=8, va='center')
            elif func_type == 'Exponential':
                ratio = y_vals[i+1] / y_vals[i]
                ax.text(0.65, ymid, f"×{fmt_num(ratio)}", color='#1E90FF', fontsize=10, va='center', fontweight='bold')

        if func_type == 'Quadratic':
            diff2 = [diff1[i+1] - diff1[i] for i in range(3)]
            for i in range(3):
                ys = (y_pos[i] + y_pos[i+1]) / 2
                ye = (y_pos[i+1] + y_pos[i+2]) / 2
                ymid = (ys + ye) / 2
                ax.annotate("", xy=(0.65, ye), xytext=(0.65, ys),
                            arrowprops=dict(arrowstyle="-", connectionstyle="arc3,rad=-0.4", color='#FF4500', lw=1.5))
                lbl = f"+{fmt_num(diff2[i])}" if diff2[i] >= 0 else str(fmt_num(diff2[i]))
                ax.text(0.85, ymid, lbl, color='#FF4500', fontsize=10, va='center', fontweight='bold')

# --- Unified PDF Generation Engine ---
def create_pdf_bytes():
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        problems = [generate_table_data() for _ in range(20)]
        
        # --- PAGE 1: Blank Worksheet ---
        fig, axes = plt.subplots(5, 4, figsize=(8.27, 11.69))
        fig.subplots_adjust(wspace=0.3, hspace=0.4, top=0.92, bottom=0.05, left=0.05, right=0.95)
        fig.suptitle("Worksheet: Identify the Function Family", fontsize=16, fontweight='bold')
        for i, ax in enumerate(axes.flatten()):
            func_type, x_vals, y_vals, steps, target_eq = problems[i]
            draw_pdf_table(ax, x_vals, y_vals, show_markup=False)
            ax.set_title(f"Q{i+1}", loc='left', fontsize=10, fontweight='bold', pad=2)
        pdf.savefig(fig); plt.close(fig)
        
        # --- PAGE 2: Visual Markup Answer Key ---
        fig2, axes2 = plt.subplots(5, 4, figsize=(8.27, 11.69))
        fig2.subplots_adjust(wspace=0.3, hspace=0.6, top=0.92, bottom=0.05, left=0.05, right=0.95)
        fig2.suptitle("Answer Key: Differentials & Ratios", fontsize=16, fontweight='bold')
        for i, ax in enumerate(axes2.flatten()):
            func_type, x_vals, y_vals, steps, target_eq = problems[i]
            draw_pdf_table(ax, x_vals, y_vals, func_type=func_type, show_markup=True)
            ax.set_title(f"Q{i+1}: {func_type}\n${target_eq}$", loc='left', fontsize=8, pad=2)
        pdf.savefig(fig2); plt.close(fig2)
        
        # --- PAGE 3+: Appendix (Step-by-Step Logic) ---
        app_pages = []
        current_page_items = []; current_col = 0; current_slot = 0
        
        for i, prob in enumerate(problems):
            if current_slot >= 4:
                current_col += 1; current_slot = 0
            if current_col > 1:
                app_pages.append(current_page_items)
                current_page_items = []; current_col = 0; current_slot = 0
            current_page_items.append({'idx': i, 'prob': prob, 'col': current_col, 'slot': current_slot})
            current_slot += 1
            
        if current_page_items: app_pages.append(current_page_items)
        total_app_pages = len(app_pages)
        
        for page_idx, page_items in enumerate(app_pages):
            fig_app, ax_app = plt.subplots(figsize=(8.27, 11.69))
            ax_app.axis('off')
            ax_app.text(0.5, 0.96, f"Appendix: Step-by-Step Solutions (Page {page_idx+1}/{total_app_pages})", fontsize=14, fontweight='bold', ha='center')
            for item in page_items:
                q_num = item['idx']; prob_data = item['prob']; col = item['col']; slot = item['slot']
                x_pos = 0.04 if col == 0 else 0.52
                y_pos = 0.88 - (slot * 0.22)
                steps_clean = prob_data[3].replace("**", "")
                ax_app.text(x_pos, y_pos, f"Q{q_num+1}:\n{steps_clean}", fontsize=9, va='top')
            pdf.savefig(fig_app); plt.close(fig_app)
            
    return buffer.getvalue()


# --- Streamlit UI Initializations ---
if 'initialized_study_mode' not in st.session_state:
    st.session_state.study_mode = "Solve"
    st.session_state.mark_working = True
    st.session_state.show_equations = True
    st.session_state.initialized_study_mode = True
    st.session_state.canvas_key = 0 
    
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None

def apply_study_mode():
    st.session_state.generating = True
    st.session_state.pdf_bytes = None
    sm = st.session_state.study_mode
    if sm == "Recognise":
        st.session_state.mark_working = False
    elif sm == "Solve":
        st.session_state.mark_working = True
        st.session_state.show_equations = True

def handle_settings_change():
    st.session_state.pdf_bytes = None
    st.session_state.generating = True

if 'generating' not in st.session_state:
    st.session_state.generating = True
if 'identified_correctly' not in st.session_state:
    st.session_state.identified_correctly = False
if 'ai_feedback' not in st.session_state:
    st.session_state.ai_feedback = ""
if 'ai_is_correct' not in st.session_state:
    st.session_state.ai_is_correct = False
if 'show_camera' not in st.session_state:
    st.session_state.show_camera = False

st.title("Student Table Solver")

# Custom CSS for friendly buttons
st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        background-color: #1E90FF;
        color: white;
        border: none;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #0073e6;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to render identical settings cog
def render_settings_cog():
    with st.popover("⚙️ Settings", use_container_width=True):
        st.radio("Study Mode", ["Recognise", "Solve"], key="study_mode", on_change=apply_study_mode)
        st.toggle("Mark My Working", key="mark_working")
        st.toggle("Equation Buttons", key="show_equations", on_change=handle_settings_change)
        st.radio("Camera Mode", ["App", "Native"], key="camera_mode", horizontal=True)

# PDF Controls & Settings Layout
if st.session_state.pdf_bytes is None:
    col_pdf, col_set = st.columns([5, 1])
    with col_pdf:
        if st.button("📄 Prepare Worksheet", use_container_width=True):
            with st.spinner("Compiling Master PDF..."):
                st.session_state.pdf_bytes = create_pdf_bytes()
            st.rerun()
    with col_set:
        render_settings_cog()
else:
    col_dl, col_rs, col_set = st.columns([3, 3, 1])
    with col_dl:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="⬇️ Download",
            data=st.session_state.pdf_bytes,
            file_name=f"Math_Table_Worksheet_{current_time}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    with col_rs:
        if st.button("Reset PDF", use_container_width=True):
            st.session_state.pdf_bytes = None
            st.rerun()
    with col_set:
        render_settings_cog()

st.latex(r"") 

# Generate New Math Data
if st.session_state.generating:
    st.info("Drawing next table... please wait.")
    st.session_state.math_data = generate_table_data()
    st.session_state.bg_image = draw_table_image(st.session_state.math_data[1], st.session_state.math_data[2])
    
    st.session_state.identified_correctly = False
    st.session_state.feedback = ""
    st.session_state.ai_feedback = ""
    st.session_state.ai_is_correct = False
    st.session_state.show_camera = False
    st.session_state.canvas_key += 1 
    st.session_state.generating = False
    st.rerun()
    
else:
    func_type, x_vals, y_vals, steps, target_eq = st.session_state.math_data
    show_equations_state = st.session_state.get('show_equations', True)
    
    st.write("Mark up the table below (using your finger/mouse) to find the differences or multiplier.")
    
    # --- The Digital Canvas ---
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", 
        stroke_width=3,
        stroke_color="#1E90FF",
        background_image=st.session_state.bg_image,
        update_streamlit=True,
        height=400,
        width=600,
        drawing_mode="freedraw",
        key=f"canvas_{st.session_state.canvas_key}",
    )

    # STAGE 1: Identifying Function Family
    if not st.session_state.identified_correctly:
        st.write("**What family does this function belong to?**")
        c1, c2, c3 = st.columns(3)
        
        def check_feat(guess):
            if guess == func_type:
                st.session_state.identified_correctly = True
                st.session_state.feedback = f"✅ Correct! It's {guess}."
            else:
                st.session_state.feedback = "❌ Try again! Check your differences carefully."

        btn_l = "y = mx + c" if show_equations_state else "Linear"
        btn_q = "y = ax² + bx + c" if show_equations_state else "Quadratic"
        btn_e = "y = a·rˣ" if show_equations_state else "Exponential"
        
        c1.button(btn_l, on_click=check_feat, args=("Linear",), use_container_width=True)
        c2.button(btn_q, on_click=check_feat, args=("Quadratic",), use_container_width=True)
        c3.button(btn_e, on_click=check_feat, args=("Exponential",), use_container_width=True)

        if st.session_state.feedback:
            if "Correct" not in st.session_state.feedback: 
                st.error(st.session_state.feedback)

    # STAGE 2: Correct Feature Identified
    else:
        st.success(st.session_state.feedback)
        
        if not st.session_state.get('mark_working', False):
            st.info(steps)
            if st.button("Next Table", use_container_width=True):
                st.session_state.generating = True
                st.rerun()
                
        else:
            if st.session_state.ai_is_correct:
                if st.session_state.ai_feedback:
                    st.success(f"🎉 **AI Marker:** {st.session_state.ai_feedback}")
                st.info(steps)
                if st.button("Next Table", use_container_width=True):
                    st.session_state.generating = True
                    st.rerun()
                    
            else:
                if not st.session_state.show_camera:
                    st.write("Ready to solve it? Work out the final equation on paper.")
                    col_mk, col_sk = st.columns(2)
                    with col_mk:
                        if st.button("📸 Mark My Working", use_container_width=True, type="primary"):
                            st.session_state.show_camera = True
                            st.rerun()
                    with col_sk:
                        if st.button("Skip to Solution", use_container_width=True):
                            st.session_state.ai_is_correct = True
                            st.session_state.ai_feedback = ""
                            st.rerun()
                else:
                    cam_mode = st.session_state.get('camera_mode', 'App')
                    if cam_mode == 'App':
                        paper_pic = st.camera_input("Snap a photo of your algebraic working:")
                    else:
                        paper_pic = st.file_uploader("Upload a photo of your working:", type=['png', 'jpg', 'jpeg'])
                    
                    if paper_pic:
                        if st.button("Submit Working for AI Marking", use_container_width=True, type="primary"):
                            with st.spinner("Gemini is checking your markup and algebra..."):
                                try:
                                    # Image 1: The Paper
                                    paper_img = Image.open(paper_pic)
                                    paper_img.thumbnail((1024, 1024))
                                    
                                    # Image 2: The Digital Canvas
                                    canvas_img = None
                                    if canvas_result.image_data is not None:
                                        canvas_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                                        bg = st.session_state.bg_image.convert("RGBA")
                                        canvas_img = Image.alpha_composite(bg, canvas_img).convert("RGB")
                                    
                                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                                    prompt = f"""
                                    You are a supportive high school math teacher grading a {func_type} function table problem.
                                    The CORRECT final equation they must reach is: {target_eq}
                                    
                                    I am providing you with two images:
                                    1. A digital screenshot of how they marked up the data table to find their differences/ratios.
                                    2. A photograph of their handwritten algebra to find the final equation.
                                    
                                    Please verify their logic across both images. 
                                    If their working is mathematically sound and reaches the correct equation, reply EXACTLY with the word "CORRECT:" on the first line, followed by a brief congratulatory message praising a specific step they did well.
                                    If they made a mistake in either their table markup OR their algebra, reply EXACTLY with the word "INCORRECT:" on the first line. Gently explain where they went wrong and guide them on what to do next without giving away the final answer.
                                    """
                                    
                                    contents = [prompt, paper_img]
                                    if canvas_img: contents.insert(1, canvas_img)
                                        
                                    response = client.models.generate_content(
                                        model='gemini-3.6-flash',
                                        contents=contents
                                    )
                                    
                                    resp_text = response.text.strip()
                                    if resp_text.upper().startswith("CORRECT"):
                                        st.session_state.ai_is_correct = True
                                        st.session_state.ai_feedback = re.sub(r'(?i)^CORRECT:?\s*', '', resp_text)
                                        st.rerun()
                                    else:
                                        st.session_state.ai_is_correct = False
                                        st.session_state.ai_feedback = re.sub(r'(?i)^INCORRECT:?\s*', '', resp_text)
                                        st.rerun()
                                        
                                except Exception as e:
                                    st.error(f"Oops! Something went wrong with the AI: {e}")
                                    
                    if st.session_state.ai_feedback and not st.session_state.ai_is_correct:
                        st.warning(f"**AI Marker Feedback:**\n\n{st.session_state.ai_feedback}")
                        
                    st.write("---")
                    col_retry, col_skip = st.columns(2)
                    with col_retry:
                        if st.button("Cancel Marker", use_container_width=True):
                            st.session_state.show_camera = False
                            st.session_state.ai_feedback = ""
                            st.rerun()
                    with col_skip:
                        if st.button("Skip & Show Solution", use_container_width=True):
                            st.session_state.ai_is_correct = True
                            st.session_state.ai_feedback = ""
                            st.rerun()
