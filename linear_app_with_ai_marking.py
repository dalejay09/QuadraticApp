import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import random
import io
import re
from PIL import Image
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
from google import genai

def fmt_m(m):
    if m == 1: return ""
    if m == -1: return "-"
    return str(int(m)) if m == int(m) else str(m)

def fmt_num(n):
    return int(n) if n == int(n) else n

# --- Core Math Engine (Linear) ---
def generate_math_data():
    scenario = random.choice(['y_int', 'x_int', 'random', 'point_grad'])
    m = random.choice([0.5, 1, 1.5, 2, 3, -0.5, -1, -1.5, -2, -3])
    
    if scenario == 'y_int':
        c = random.randint(-5, 5)
        x1, y1 = 0, c
        valid_x2 = [x for x in range(-5, 6) if x != 0 and (m * x).is_integer()]
        x2 = random.choice(valid_x2)
        y2 = m * x2 + c
        points = [(x1, y1), (x2, y2)]
        
    elif scenario == 'x_int':
        x1 = random.choice([x for x in range(-5, 6) if x != 0])
        y1 = 0
        c = -m * x1
        valid_x2 = [x for x in range(-5, 6) if x != x1 and x != 0 and (m * x + c).is_integer()]
        if not valid_x2: 
            valid_x2 = [x1 + 2 if (m * (x1 + 2)).is_integer() else x1 + 1]
        x2 = random.choice(valid_x2)
        y2 = m * x2 + c
        points = [(x1, y1), (x2, y2)]
        
    elif scenario == 'random':
        c = random.randint(-5, 5)
        valid_xs = [x for x in range(-6, 7) if x != 0 and (m * x + c) != 0 and (m * x + c).is_integer()]
        if len(valid_xs) < 2:
            x1, x2 = 2, 4
            y1, y2 = m * x1 + c, m * x2 + c
        else:
            x1, x2 = random.sample(valid_xs, 2)
        y1, y2 = m * x1 + c, m * x2 + c
        points = [(x1, y1), (x2, y2)]
        
    elif scenario == 'point_grad':
        c = random.randint(-5, 5)
        x1 = random.choice([x for x in range(-5, 6) if x != 0 and (m * x + c).is_integer()])
        y1 = m * x1 + c
        points = [(x1, y1)]

    # Sort points for visual consistency (left to right)
    if len(points) == 2 and points[0][0] > points[1][0]:
        points[0], points[1] = points[1], points[0]
        x1, y1 = points[0]
        x2, y2 = points[1]

    f = lambda x: m * x + c
    m_str = fmt_m(m)
    c_str = "" if c == 0 else f" + {fmt_num(c)}" if c > 0 else f" - {fmt_num(abs(c))}"
    eq = f"y = {m_str}x{c_str}"
    
    # Step-by-step logic
    if scenario == 'point_grad':
        steps = (f"**Straight Line Equation**\n\n"
                 f"1. Gradient $m = {fmt_num(m)}$ (given).\n"
                 f"2. Sub point $({fmt_num(x1)}, {fmt_num(y1)})$: $y = mx + c$\n"
                 f"$\\quad \\Rightarrow {fmt_num(y1)} = {fmt_num(m)}({fmt_num(x1)}) + c$\n"
                 f"3. ${fmt_num(y1)} = {fmt_num(m * x1)} + c \\Rightarrow c = {fmt_num(c)}$\n\n"
                 f"**${eq}$**")
    else:
        dy, dx = y2 - y1, x2 - x1
        steps = (f"**Straight Line Equation**\n\n"
                 f"1. Gradient $m = \\frac{{{fmt_num(y2)} - ({fmt_num(y1)})}}{{{fmt_num(x2)} - ({fmt_num(x1)})}} = \\frac{{{fmt_num(dy)}}}{{{fmt_num(dx)}}} = {fmt_num(m)}$\n"
                 f"2. Sub point $({fmt_num(x1)}, {fmt_num(y1)})$: $y = mx + c$\n"
                 f"$\\quad \\Rightarrow {fmt_num(y1)} = {fmt_num(m)}({fmt_num(x1)}) + c$\n"
                 f"3. ${fmt_num(y1)} = {fmt_num(m * x1)} + c \\Rightarrow c = {fmt_num(c)}$\n\n"
                 f"**${eq}$**")

    all_x = [p[0] for p in points] + [0]
    all_y = [p[1] for p in points] + [c]
    x_pad, y_pad = max(2.0, (max(all_x) - min(all_x)) * 0.2), max(2.0, (max(all_y) - min(all_y)) * 0.2)
    x_vals = np.linspace(min(all_x) - x_pad - 2, max(all_x) + x_pad + 2, 400)
    
    # Feature Identification Logic
    all_features = [
        "positive gradient", "negative gradient", 
        "x-intercept given", "y-intercept given", 
        "gradient given", "two points given", "only one point given"
    ]
    true_features = []
    
    if m > 0: true_features.append("positive gradient")
    if m < 0: true_features.append("negative gradient")
    
    if scenario == 'point_grad':
        true_features.extend(["gradient given", "only one point given"])
    else:
        true_features.append("two points given")
        if scenario == 'y_int': true_features.append("y-intercept given")
        if scenario == 'x_int': true_features.append("x-intercept given")
        
    false_features = [feat for feat in all_features if feat not in true_features]
    btn_choices = [random.choice(true_features)] + random.sample(false_features, 2)
    random.shuffle(btn_choices)
    
    return points, f, all_x, all_y, x_pad, y_pad, x_vals, true_features, steps, eq, btn_choices, scenario, m

# --- Dynamic Plotting Engine ---
def draw_line_fig(math_data, show_labels_val, show_grid_val):
    points, f, all_x, all_y, x_pad, y_pad, x_vals, true_features, steps, eq, btn_choices, scenario, m = math_data
    fig, ax = plt.subplots(figsize=(4, 4))
    
    if show_grid_val:
        ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.set_axisbelow(True)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.tick_params(which='both', length=0)
    else:
        ax.set_xticks([])
        ax.set_yticks([])

    ax.plot(x_vals, f(x_vals), color='darkblue', linewidth=2)
    for px, py in points:
        ax.plot(px, py, 'o', color='darkblue', markersize=6)
        if show_labels_val:
            ax.annotate(f'({fmt_num(px)}, {fmt_num(py)})', (px, py),
                        textcoords="offset points", xytext=(4, 4),
                        ha='left', va='bottom', fontsize=10,
                        bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
        
    ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
    
    x_min, x_max = min(all_x) - x_pad - 2, max(all_x) + x_pad + 2
    y_min, y_max = min(all_y) - y_pad, max(all_y) + y_pad
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    
    if scenario == 'point_grad':
        x_span, y_span = x_max - x_min, y_max - y_min
        # Since figsize is square (4x4), the visual slope maps perfectly to the spans
        visual_m = m * (x_span / y_span)
        angle = np.degrees(np.arctan(visual_m))
        x_center = (x_min + x_max) / 2
        y_center = f(x_center)
        ax.text(x_center, y_center + y_span*0.02, f"gradient = {fmt_num(m)}", 
                rotation=angle, rotation_mode='anchor', ha='center', va='bottom', 
                color='darkblue', fontsize=10, 
                bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))

    return fig

# --- PDF Generation Engine (Streamlined) ---
def create_pdf_bytes():
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        problems = [generate_math_data() for _ in range(20)]
        show_grid_pdf = st.session_state.get("show_grid", False)
        
        # --- Page 1: Labeled Graphs ---
        fig, axes = plt.subplots(5, 4, figsize=(8.27, 11.69))
        fig.subplots_adjust(wspace=0.1, hspace=0.55, top=0.92, bottom=0.05, left=0.05, right=0.95)
        fig.suptitle("Worksheet: Find the Linear Equation", fontsize=16, fontweight='bold')
        
        for i, ax in enumerate(axes.flatten()):
            points, f, all_x, all_y, x_pad, y_pad, x_vals, true_features, steps, eq, btn_choices, scenario, m_val = problems[i]
            
            if show_grid_pdf:
                ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
                ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
                ax.grid(True, linestyle=':', alpha=0.6)
                ax.set_axisbelow(True)
                ax.set_xticklabels([]); ax.set_yticklabels([])
                ax.tick_params(which='both', length=0)
            else:
                ax.set_xticks([]); ax.set_yticks([])

            ax.plot(x_vals, f(x_vals), color='darkblue', linewidth=1.5)
            for px, py in points:
                ax.plot(px, py, 'o', color='darkblue', markersize=3)
                ax.annotate(f'({fmt_num(px)}, {fmt_num(py)})', (px, py),
                            textcoords="offset points", xytext=(3, 3),
                            ha='left', va='bottom', fontsize=5,
                            bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.7))
                
            ax.spines['left'].set_position('zero'); ax.spines['bottom'].set_position('zero')
            ax.spines['right'].set_color('none'); ax.spines['top'].set_color('none')
            
            x_min, x_max = min(all_x) - x_pad - 2, max(all_x) + x_pad + 2
            y_min, y_max = min(all_y) - y_pad, max(all_y) + y_pad
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            
            if scenario == 'point_grad':
                x_span, y_span = x_max - x_min, y_max - y_min
                # Subplot cell aspect ratio is roughly 1.13 in this 5x4 layout on A4
                visual_m = m_val * (x_span / y_span) * 1.13
                angle = np.degrees(np.arctan(visual_m))
                x_center = (x_min + x_max) / 2
                y_center = f(x_center)
                ax.text(x_center, y_center + y_span*0.02, f"m = {fmt_num(m_val)}", 
                        rotation=angle, rotation_mode='anchor', ha='center', va='bottom', 
                        color='darkblue', fontsize=7, 
                        bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.85))

            ax.set_title(f"Q{i+1}", loc='left', fontsize=9, fontweight='bold', pad=3)
            ax.text(0.5, -0.15, "y = _________________", transform=ax.transAxes, ha='center', fontsize=10)
            
        pdf.savefig(fig)
        plt.close(fig)

        # --- Appendix: Step-by-Step Solutions ---
        app_pages = []
        current_page_items = []
        current_col = 0
        current_slot = 0
        
        for i, prob in enumerate(problems):
            if current_slot >= 4:
                current_col += 1
                current_slot = 0
                
            if current_col > 1:
                app_pages.append(current_page_items)
                current_page_items = []
                current_col = 0
                current_slot = 0
                
            current_page_items.append({'idx': i, 'prob': prob, 'col': current_col, 'slot': current_slot})
            current_slot += 1
            
        if current_page_items:
            app_pages.append(current_page_items)
            
        total_app_pages = len(app_pages)
        
        for page_idx, page_items in enumerate(app_pages):
            fig_app, ax_app = plt.subplots(figsize=(8.27, 11.69))
            ax_app.axis('off')
            ax_app.text(0.5, 0.96, f"Appendix: Solutions (Page {page_idx+1}/{total_app_pages})", fontsize=14, fontweight='bold', ha='center')
            
            for item in page_items:
                q_num = item['idx']
                prob_data = item['prob']
                col, slot = item['col'], item['slot']
                
                x_pos = 0.04 if col == 0 else 0.52
                y_pos = 0.88 - (slot * 0.22)
                steps_clean = prob_data[8].replace("**", "")
                ax_app.text(x_pos, y_pos, f"Q{q_num+1}:\n{steps_clean}", fontsize=9, va='top')
                
            pdf.savefig(fig_app)
            plt.close(fig_app)
        
    return buffer.getvalue()


# --- Streamlit UI Initializations ---
if 'generating' not in st.session_state:
    st.session_state.generating = True
if 'identified_feature_correctly' not in st.session_state:
    st.session_state.identified_feature_correctly = False
if 'ai_feedback' not in st.session_state:
    st.session_state.ai_feedback = ""
if 'ai_is_correct' not in st.session_state:
    st.session_state.ai_is_correct = False
if 'show_camera' not in st.session_state:
    st.session_state.show_camera = False

st.title("Linear Equation Finder")

# 1. Flattened PDF Controls & Settings 
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None
    
if st.session_state.pdf_bytes is None:
    col_pdf, col_set = st.columns([5, 1])
    with col_pdf:
        if st.button("📄 Prepare Worksheet", use_container_width=True):
            with st.spinner("Compiling PDF... (~5s)"):
                st.session_state.pdf_bytes = create_pdf_bytes()
            st.rerun()
    with col_set:
        with st.popover("⚙️", use_container_width=True):
            st.write("**Settings**")
            st.toggle("Show Grid Lines", key="show_grid")
            st.toggle("Mark My Working", key="mark_working")
else:
    col_dl, col_rs, col_set = st.columns([3, 3, 1])
    with col_dl:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="⬇️ Download",
            data=st.session_state.pdf_bytes,
            file_name=f"Linear_Worksheet_{current_time}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    with col_rs:
        if st.button("Reset", use_container_width=True):
            st.session_state.pdf_bytes = None
            st.rerun()
    with col_set:
        with st.popover("⚙️", use_container_width=True):
            st.write("**Settings**")
            st.toggle("Show Grid Lines", key="show_grid")
            st.toggle("Mark My Working", key="mark_working")

# 2. Main App Content 
col_toggle1, col_toggle2 = st.columns(2)
with col_toggle1:
    show_labels = st.toggle("Coordinates", value=False)
with col_toggle2:
    show_equations = st.toggle("Equation Buttons", value=False) 

st.write("Find the linear equation $y = mx + c$ for this graph.")
st.latex(r"") 

if st.session_state.generating:
    st.info("Drawing next line... please wait.")
    st.session_state.math_data = generate_math_data()
    st.session_state.identified_feature_correctly = False
    st.session_state.feedback = ""
    st.session_state.ai_feedback = ""
    st.session_state.ai_is_correct = False
    st.session_state.show_camera = False
    st.session_state.generating = False
    st.rerun()
    
else:
    fig = draw_line_fig(st.session_state.math_data, show_labels, st.session_state.get("show_grid", False))
    st.pyplot(fig)

    correct_features = st.session_state.math_data[7]
    steps = st.session_state.math_data[8]
    btn_choices = st.session_state.math_data[10]

    # STAGE 1: Identifying Graph Features
    if not st.session_state.identified_feature_correctly:
        st.write("**Which of these features applies to the graph?**")
        c1, c2, c3 = st.columns(3)
        
        def check_feat(guess):
            if guess in correct_features:
                st.session_state.identified_feature_correctly = True
                st.session_state.feedback = f"✅ Correct! ({guess})"
            else:
                st.session_state.feedback = "❌ Try again! Look closely at the graph."

        c1.button(btn_choices[0], on_click=check_feat, args=(btn_choices[0],), use_container_width=True)
        c2.button(btn_choices[1], on_click=check_feat, args=(btn_choices[1],), use_container_width=True)
        c3.button(btn_choices[2], on_click=check_feat, args=(btn_choices[2],), use_container_width=True)

        if st.session_state.feedback:
            if "Correct" not in st.session_state.feedback: 
                st.error(st.session_state.feedback)

    # STAGE 2: Correct Feature Identified
    else:
        st.success(st.session_state.feedback)
        
        # AI marking turned off
        if not st.session_state.get('mark_working', False):
            st.info(steps)
            if st.button("Next Line", use_container_width=True):
                st.session_state.generating = True
                st.rerun()
                
        # AI marking turned ON
        else:
            if st.session_state.ai_is_correct:
                if st.session_state.ai_feedback:
                    st.success(f"🎉 **AI Marker:** {st.session_state.ai_feedback}")
                st.info(steps)
                if st.button("Next Line", use_container_width=True):
                    st.session_state.generating = True
                    st.rerun()
                    
            else:
                if not st.session_state.show_camera:
                    st.write("Ready to solve it? Work it out on paper first.")
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
                    picture = st.camera_input("Snap a photo of your working:")
                    
                    if picture:
                        if st.button("Submit Working for AI Marking", use_container_width=True, type="primary"):
                            with st.spinner("Gemini is checking your algebra..."):
                                try:
                                    img = Image.open(picture)
                                    img.thumbnail((1024, 1024))
                                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                                    
                                    target_eq = st.session_state.math_data[9]
                                    prompt = f"""
                                    You are a supportive, encouraging high school math teacher. 
                                    The user is solving for a straight line graph. 
                                    The CORRECT final equation they must reach is: {target_eq}
                                    
                                    Please read their handwritten working from the photo.
                                    1. Check their algebra step-by-step.
                                    2. If their working is mathematically sound and reaches the correct equation, reply EXACTLY with the word "CORRECT:" on the first line, followed by a brief congratulatory message.
                                    3. If they made a mistake, reply EXACTLY with the word "INCORRECT:" on the first line. Then gently explain exactly where they went wrong, but do not give them the final answer immediately—guide them on what to do next.
                                    """
                                    
                                    response = client.models.generate_content(
                                        model='gemini-3.6-flash',
                                        contents=[prompt, img]
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
