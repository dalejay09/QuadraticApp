import streamlit as st
import io
import re
from PIL import Image
from google import genai
from streamlit_drawable_canvas import st_canvas

# --- REUSABLE GRADING COMPONENT (UNIVERSAL VISION ENGINE) ---
def render_grading_suite(
    bg_image, 
    height_px, 
    key_prefix="generic_marking", 
    show_experimental_toolbar=False,
    solution_requirement="demonstrated"
):
    """
    Encapsulated logic for problem canvas, markup, Undo/Clear, Photo Snap, and AI Grading.
    This component assumes the background image contains textbook-quality pre-rendered
    problems, and the student provides handwritten workings on top or via photo snap.
    """
    
    # --- Internal Key Encapsulation ---
    k = lambda part: f"_{key_prefix}_{part}"
    CANVAS_KEY = k("canvas_k")
    EXP_TOOLBAR_KEY = k("exp_tk")
    FEEDBACK_KEY = k("feedb")
    CORRECT_STATE_KEY = k("is_corr")
    TOOL_SELECTOR_KEY = k("tool_sel")
    STROKE_HIST_KEY = k("shist")
    INITIAL_DWG_KEY = k("initd")
    CAMERA_STATE_KEY = k("cam_s")

    PEN_COLORS = ["#1E90FF", "#FF2400", "#32CD32", "#9400D3", "#FF8C00"]
    COLOR_NAMES = ["BLUE", "RED", "GREEN", "PURPLE", "ORANGE"]

    if 'current_marking_color_index' not in st.session_state:
        st.session_state.current_marking_color_index = 0
        
    if k("init") not in st.session_state or st.session_state[k("init")] == False:
        st.session_state[FEEDBACK_KEY] = ""
        st.session_state[CANVAS_KEY] = 0
        st.session_state[EXP_TOOLBAR_KEY] = 0
        st.session_state[TOOL_SELECTOR_KEY] = "🖌️"
        st.session_state[STROKE_HIST_KEY] = [[]]
        st.session_state[INITIAL_DWG_KEY] = {"version": "4.4.0", "objects": []}
        st.session_state[CORRECT_STATE_KEY] = False
        st.session_state[CAMERA_STATE_KEY] = False
        st.session_state[k("init")] = True

    current_color_index = st.session_state.current_marking_color_index
    current_color_name = COLOR_NAMES[current_color_index]
    
    active_stroke_color = PEN_COLORS[current_color_index] if st.session_state[TOOL_SELECTOR_KEY] == "🖌️" else "#FFFFFE"
    active_stroke_width = 3 if st.session_state[TOOL_SELECTOR_KEY] == "🖌️" else 15

    st.write(f"Current pen: **{current_color_name}**")
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", stroke_width=active_stroke_width, stroke_color=active_stroke_color,
        background_image=bg_image, update_streamlit=True, height=height_px, width=350,
        drawing_mode="freedraw", return_image_data=True, initial_drawing=st.session_state[INITIAL_DWG_KEY], 
        key=k(f"canvas_{st.session_state[CANVAS_KEY]}")
    )

    if show_experimental_toolbar:
        st.caption("🔬 *Scribble Toolbar (Tap an icon!)*")
        icons = ["🖌️", "🧽", "↩️", "🗑️", "📸"]
        toolbar_objects = []
        baselines = {"🖌️": 20, "🧽": 90, "↩️": 160, "🗑️": 230, "📸": 300}
        for i, icon in enumerate(icons):
            toolbar_objects.append({"type": "i-text", "text": icon, "left": baselines[icon] - 12, "top": 5, "fontSize": 24, "selectable": False})
            if i < 4:
                toolbar_objects.append({"type": "line", "x1": (i+1)*70, "y1": 5, "x2": (i+1)*70, "y2": 40, "stroke": "#d1d5db", "strokeWidth": 2, "selectable": False})

        toolbar_initial = {"version": "4.4.0", "objects": toolbar_objects}

        toolbar_result = st_canvas(
            fill_color="rgba(0,0,0,0)", stroke_width=2, stroke_color="#007AFF", background_color="#f3f4f6", update_streamlit=True,
            height=45, width=350, drawing_mode="freedraw", initial_drawing=toolbar_initial,
            key=k(f"exp_toolbar_{st.session_state[EXP_TOOLBAR_KEY]}")
        )

        if toolbar_result.json_data is not None:
            objects = toolbar_result.json_data.get("objects", [])
            if len(objects) > 9:
                new_stroke = objects[-1]
                stroke_center_x = new_stroke.get("left", 0) + (new_stroke.get("width", 0) * new_stroke.get("scaleX", 1) / 2)
                
                action = None
                if 0 <= stroke_center_x < 70: action = "🖌️"
                elif 70 <= stroke_center_x < 140: action = "🧽"
                elif 140 <= stroke_center_x < 210: action = "↩️"
                elif 210 <= stroke_center_x < 280: action = "🗑️"
                elif 280 <= stroke_center_x <= 350: action = "📸"
                
                if action:
                    st.toast(f"Toolbar Tapped: {action}")
                    if action in ["🖌️", "🧽"]: st.session_state[TOOL_SELECTOR_KEY] = action
                    if action == "↩️" and len(st.session_state[STROKE_HIST_KEY]) > 1:
                        st.session_state[STROKE_HIST_KEY].pop()
                        st.session_state[INITIAL_DWG_KEY] = {"version": "4.4.0", "objects": st.session_state[STROKE_HIST_KEY][-1]}
                        st.session_state[CANVAS_KEY] += 1
                    if action == "🗑️":
                        st.session_state[STROKE_HIST_KEY], st.session_state[INITIAL_DWG_KEY] = [[]], {"version": "4.4.0", "objects": []}
                        st.session_state[CANVAS_KEY] += 1
                    if action == "📸":
                        st.session_state[CAMERA_STATE_KEY] = not st.session_state[CAMERA_STATE_KEY]
                
                st.session_state[EXP_TOOLBAR_KEY] += 1
                st.rerun()

    st.write("---")
    t_col1, t_col2, t_col3, t_col4 = st.columns([1.5, 1, 1, 1.2])
    with t_col1: st.radio("Tool", ["🖌️", "🧽"], horizontal=True, label_visibility="collapsed", key=TOOL_SELECTOR_KEY)
    with t_col2:
        if st.button("↩️", use_container_width=True, help="Undo", key=k("btn_undo")):
            if len(st.session_state[STROKE_HIST_KEY]) > 1:
                st.session_state[STROKE_HIST_KEY].pop()
                st.session_state[INITIAL_DWG_KEY], st.session_state[CANVAS_KEY] = {"version": "4.4.0", "objects": st.session_state[STROKE_HIST_KEY][-1]}, st.session_state[CANVAS_KEY] + 1
                st.rerun()
    with t_col3:
        if st.button("🗑️", use_container_width=True, help="Clear Workings", key=k("btn_clear")):
            st.session_state[STROKE_HIST_KEY], st.session_state[INITIAL_DWG_KEY], st.session_state[CANVAS_KEY] = [[]], {"version": "4.4.0", "objects": []}, st.session_state[CANVAS_KEY] + 1
            st.rerun()
    with t_col4:
        if st.button("📸 Paper", use_container_width=True, help="Snap photo of paper workings", key=k("btn_photo")):
            st.session_state[CAMERA_STATE_KEY] = not st.session_state[CAMERA_STATE_KEY]
            st.rerun()
            
    current_objects = canvas_result.json_data.get("objects", []) if canvas_result.json_data else []
    if len(current_objects) > len(st.session_state[STROKE_HIST_KEY][-1]):
        if current_objects[-1].get("stroke", "").upper() == "#FFFFFE":
            e = current_objects[-1]
            E_L, E_R, E_T, E_B = e.get("left",0)-15, e.get("left",0)+(e.get("width",0)*e.get("scaleX",1))+15, e.get("top",0)-15, e.get("top",0)+(e.get("height",0)*e.get("scaleY",1))+15
            objects_to_keep = [obj for obj in st.session_state[STROKE_HIST_KEY][-1] if not (E_R < obj.get("left",0) or E_L > obj.get("left",0)+(obj.get("width",0)*obj.get("scaleX",1)) or E_B < obj.get("top",0) or E_T > obj.get("top",0)+(obj.get("height",0)*obj.get("scaleX",1)))]
            st.session_state[STROKE_HIST_KEY].append(objects_to_keep)
            st.session_state[INITIAL_DWG_KEY], st.session_state[CANVAS_KEY] = {"version": "4.4.0", "objects": objects_to_keep}, st.session_state[CANVAS_KEY] + 1
            st.rerun()
        else:
            st.session_state[STROKE_HIST_KEY].append(current_objects.copy())

    camera_picture = None
    if st.session_state[CAMERA_STATE_KEY]:
        camera_picture = st.camera_input("Snap a photo:", key=k("cam_input")) if st.session_state.camera_mode == 'App' else st.file_uploader("Upload photo:", type=['png', 'jpg'], key=k("cam_input"))

    color_sequence_str = ", ".join(COLOR_NAMES)
    
    requirement_rule = (
        "- REQUIREMENT (NUMERIC): The student MUST calculate and provide the final evaluated numeric answer on the canvas. If they only write the setup formula without calculating the final number, mark it INCORRECT."
        if solution_requirement == "numeric"
        else "- REQUIREMENT (DEMONSTRATED): Demonstrating the correct mathematical setup/method (e.g., algebraic formula or expression ready for calculator input) is sufficient. A final calculated numeric value is optional."
    )
    
    marking_prompt = f"""
    You are an expert, encouraging math tutor grading a student's handwritten work.
    The problem to be solved is written on the provided canvas/image as Textbook printed text. Deduce the question being solved directly from the printed material on the image.
    
    The student is using a sequence of handwritten pen colors to show their progress over time. 
    The full sequence of colors they cycle through is: {color_sequence_str}.
    They are currently writing in: {current_color_name}.
    
    {requirement_rule}
    
    CRITICAL VISUAL GRADING RULE:
    - If the student solves the deduced background problem correctly using the chronology of their workings and fulfills the stated requirement above, reply EXACTLY with "CORRECT:" on the first line, followed by a brief congratulatory message.
    - If their solution or step-by-step working against the deduced background problem is incorrect or misses the required format, reply EXACTLY with "INCORRECT:" on the first line, followed by a brief hint on what to do next. Do NOT give them the final answer.
    """

    st.write("---")
    if st.button("Check My Answer!", type="primary", use_container_width=True):
        
        payload_images = []
        if canvas_result.image_data is not None and len(st.session_state[STROKE_HIST_KEY][-1]) > 0:
            ink = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').resize(bg_image.size, Image.Resampling.LANCZOS)
            payload_images.append(Image.alpha_composite(bg_image.convert("RGBA"), ink).convert("RGB"))
        if camera_picture: payload_images.append(Image.open(camera_picture).convert('RGB').resize((1024, 1024)))
            
        if not payload_images: st.error("Please draw your workings on the canvas or snap a photo first!")
        else:
            with st.spinner("Reviewing your workings..."):
                try:
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[marking_prompt] + payload_images
                    )
                    
                    response_text = response.text.strip()
                    if response_text.upper().startswith("CORRECT"):
                        st.session_state[CORRECT_STATE_KEY] = True
                        cleaned = re.sub(r'(?i)^CORRECT:?\s*', '', response_text).strip()
                        st.session_state[FEEDBACK_KEY] = cleaned if cleaned else "Perfect! You solved it correctly."
                    else:
                        st.session_state[CORRECT_STATE_KEY] = False
                        cleaned = re.sub(r'(?i)^INCORRECT:?\s*', '', response_text).strip()
                        st.session_state[FEEDBACK_KEY] = cleaned if cleaned else "Something doesn't look quite right. Give it another try!"
                        st.session_state.current_marking_color_index = (st.session_state.current_marking_color_index + 1) % len(PEN_COLORS)
                        
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    if st.session_state[FEEDBACK_KEY]:
        if st.session_state[CORRECT_STATE_KEY]:
            st.success(f"🌟 **Awesome job!** {st.session_state[FEEDBACK_KEY]}")
        else:
            st.warning(f"🤖 **Tutor says:** {st.session_state[FEEDBACK_KEY]}")