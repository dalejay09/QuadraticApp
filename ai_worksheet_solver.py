import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import io
import json
import re
from PIL import Image
from datetime import datetime
from google import genai
from pydantic import BaseModel, Field

# --- AI Output Schemas ---
class SolutionRow(BaseModel):
    question_id: str = Field(description="The question number or identifier (e.g., 'Q1', '1a')")
    original_problem: str = Field(description="The math equation or problem exactly as written")
    steps: str = Field(description="A concise step-by-step breakdown of the solution")
    final_answer: str = Field(description="The final computed answer")

class WorksheetSolutions(BaseModel):
    solutions: list[SolutionRow]

# --- PDF Generation ---
def create_solutions_pdf(solutions):
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis('off')
        
        ax.text(0.5, 0.95, "Worksheet Solutions", fontsize=16, fontweight='bold', ha='center')
        y_pos = 0.88
        
        for sol in solutions:
            # Handle dictionary vs pydantic object for PDF generation
            if isinstance(sol, dict):
                q_id = str(sol.get("question_id", ""))
                prob = str(sol.get("original_problem", ""))
                steps = str(sol.get("steps", ""))
                ans = str(sol.get("final_answer", ""))
            else:
                q_id = str(getattr(sol, "question_id", ""))
                prob = str(getattr(sol, "original_problem", ""))
                steps = str(getattr(sol, "steps", ""))
                ans = str(getattr(sol, "final_answer", ""))

            # Create a new page if we run out of vertical space
            if y_pos < 0.15:
                pdf.savefig(fig)
                plt.close(fig)
                fig, ax = plt.subplots(figsize=(8.27, 11.69))
                ax.axis('off')
                y_pos = 0.95
            
            # Format the text block
            block = (
                f"**{q_id}**: {prob}\n"
                f"Steps: {steps}\n"
                f"Answer: {ans}"
            )
            
            # Clean up Markdown bolding for Matplotlib (which doesn't natively support MD)
            block_clean = block.replace("**", "")
            
            ax.text(0.05, y_pos, block_clean, fontsize=10, va='top', wrap=True)
            y_pos -= 0.18  # Step down for the next problem
            
        pdf.savefig(fig)
        plt.close(fig)
    return buffer.getvalue()

# --- Main App UI ---
st.set_page_config(page_title="Solve My Worksheet", page_icon="📝", layout="centered")

st.title("📝 Solve My Worksheet")
st.write("Upload or snap a photo of a math worksheet, and the AI will extract, solve, and format every question.")

if 'solutions_data' not in st.session_state:
    st.session_state.solutions_data = None
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None

input_mode = st.radio("Input Method", ["📸 Camera", "📂 Upload File"], horizontal=True)

if input_mode == "📸 Camera":
    worksheet_file = st.camera_input("Snap a photo of the worksheet")
else:
    worksheet_file = st.file_uploader("Upload a worksheet image", type=['png', 'jpg', 'jpeg'])

if worksheet_file:
    if st.button("Solve Worksheet", type="primary", use_container_width=True):
        with st.spinner("Analyzing and solving questions..."):
            try:
                # 1. Compress Image
                img = Image.open(worksheet_file).convert('RGB')
                img.thumbnail((1024, 1024))
                
                # 2. Call Gemini with Structured Output
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                
                prompt = """
                You are an expert math solver. Look at the provided image of a worksheet.
                Extract every distinct math problem you can find. 
                For each problem, solve it step-by-step.
                Please provide concise mathematical notation. 
                For algebra solutions label equations Eq1, Eq2 etc if they are used in workings.
                Use shortcut notation like "sub z into Eq2" and "Eq1 + 2xEq2" for combinations and eliminations.
                Use newlines to aid in layout.
                Return the output STRICTLY adhering to the provided JSON schema.
                """
                
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[prompt, img],
                    config=dict(
                        response_mime_type="application/json",
                        response_schema=WorksheetSolutions,
                        temperature=0.1
                    )
                )
                
                # 3. Parse Data
                parsed_data = json.loads(response.text)
                st.session_state.solutions_data = parsed_data.get("solutions", [])
                st.session_state.pdf_bytes = create_solutions_pdf(st.session_state.solutions_data)
                
            except Exception as e:
                st.error(f"Failed to process worksheet: {e}")

# --- Results Rendering ---
if st.session_state.solutions_data:
    st.success("✅ Solutions generated successfully!")
    
    # Render as an HTML Table for clean web display
    html_table = """
    <table style="width:100%; border-collapse: collapse; font-family: sans-serif;">
        <tr style="background-color: #f0f2f6; border-bottom: 2px solid #d1d5db;">
            <th style="padding: 10px; text-align: left;">Q#</th>
            <th style="padding: 10px; text-align: left;">Problem</th>
            <th style="padding: 10px; text-align: left;">Steps</th>
            <th style="padding: 10px; text-align: left;">Final Answer</th>
        </tr>
    """
    
    for row in st.session_state.solutions_data:
        # 1. Safely extract data whether the SDK returned a Dictionary or a Pydantic Object
        if isinstance(row, dict):
            q_id = str(row.get("question_id", ""))
            prob = str(row.get("original_problem", ""))
            steps = str(row.get("steps", ""))
            ans = str(row.get("final_answer", ""))
        else:
            q_id = str(getattr(row, "question_id", ""))
            prob = str(getattr(row, "original_problem", ""))
            steps = str(getattr(row, "steps", ""))
            ans = str(getattr(row, "final_answer", ""))
            
        # 2. Apply superscripts now that we guarantee everything is a clean string
        steps_html = re.sub(r'\^(\d+)', r'<sup>\1</sup>', steps)
        ans_html = re.sub(r'\^(\d+)', r'<sup>\1</sup>', ans)
        
        # 3. Flatten the HTML to a single line to avoid Streamlit Markdown code blocks
        html_table += f"<tr style='border-bottom: 1px solid #e5e7eb;'><td style='padding: 10px;'><b>{q_id}</b></td><td style='padding: 10px;'>{prob}</td><td style='padding: 10px;'>{steps_html}</td><td style='padding: 10px; font-weight: bold; color: #007AFF;'>{ans_html}</td></tr>"
        
    html_table += "</table>"
    
    st.markdown(html_table, unsafe_allow_html=True)
    st.write("---")
    
    # PDF Download Button
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="⬇️ Download Solutions as PDF",
        data=st.session_state.pdf_bytes,
        file_name=f"Solved_Worksheet_{current_time}.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )
