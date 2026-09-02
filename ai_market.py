import streamlit as st
from google import genai
from PIL import Image
import io

st.set_page_config(page_title="AI Math Marker", page_icon="📸")

st.title("📸 AI Math Marker")
st.write("Handwrite a quadratic equation and solve it on paper. Snap a photo below, and let Gemini check your work!")

# 1. The Camera Widget
picture = st.camera_input("Take a photo of your working")

if picture:
    # Show the photo they just took
    st.image(picture, caption="Your Submitted Working")
    
    if st.button("Mark My Answer", use_container_width=True, type="primary"):
        with st.spinner("Gemini is reading your handwriting..."):
            try:
                # 2. Convert the photo into an image format Gemini understands
                img = Image.open(picture)
                
                # 3. Connect to Google's GenAI Client
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                
                # 4. The Secret Instructions
                prompt = """
                You are a supportive, encouraging high school math teacher. 
                The user has submitted a photo of their handwritten math working.
                
                Please do the following:
                1. Read their handwriting and write out the equation they are trying to solve.
                2. Check their algebra step-by-step.
                3. If they are correct, congratulate them!
                4. If they made a mistake, gently explain exactly where they went wrong, but do not just give them the final answer immediately—guide them on what to do next.
                """
                
                # 5. Send the prompt AND the image to Gemini 2.5 Flash
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[prompt, img]
                )
                
                # 6. Display the feedback
                st.success("Marking Complete!")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"Oops! Something went wrong: {e}")
