import streamlit as st
import random
import os

# Page configuration
st.set_page_config(page_title="Driving Test Flashcards", page_icon="🚗")

# The 16 unique questions from the driving test screenshots
questions = [
    {
        "question": "If you have a learner licence can you carry passengers?",
        "options": [
            "Yes, provided your supervisor agrees and is sitting in the front passenger seat",
            "No, you can only drive with a supervisor",
            "Yes, you can carry family members only"
        ],
        "answer": "Yes, provided your supervisor agrees and is sitting in the front passenger seat"
    },
    {
        "question": "Does the driver of the blue car have to give way?",
        "image": "intersection_q28.jpg",
        "options": ["Yes", "No"],
        "answer": "No"
    },
    {
        "question": "What is the maximum legal speed for a car towing a trailer on the open road?",
        "options": ["80 km/h", "90 km/h", "100 km/h"],
        "answer": "90 km/h"
    },
    {
        "question": "When coming up to a Stop sign, where should you stop?",
        "options": [
            "Where you can see all vehicles coming from all directions",
            "With your front bumper on the yellow lines",
            "Two metres before the Stop sign"
        ],
        "answer": "Where you can see all vehicles coming from all directions"
    },
    {
        "question": "You are the driver of the blue car. Who must you give way to?",
        "image": "intersection_q9.jpg",
        "options": ["Car C only", "Car A only", "Cars A and C"],
        "answer": "Cars A and C"
    },
    {
        "question": "You have a restricted licence. A condition for driving at night without a supervisor is that you MUST NOT drive between what hours?",
        "options": ["11.00pm to 7.00am", "10.00pm to 5.00am", "9.00pm to 6.00am"],
        "answer": "10.00pm to 5.00am"
    },
    {
        "question": "What must you do when you see two red lights flashing outside a fire station?",
        "options": [
            "Slow down to 20 km/h",
            "Stop until the lights stop flashing",
            "Speed up to pass quickly"
        ],
        "answer": "Stop until the lights stop flashing"
    },
    {
        "question": "If you are under 20 the legal alcohol limit is zero. What does this mean?",
        "options": [
            "You could be fined $150 if your alcohol level is higher than 150 micrograms",
            "You could be disqualified from driving, given demerit points, fined or imprisoned"
        ],
        "answer": "You could be disqualified from driving, given demerit points, fined or imprisoned"
    },
    {
        "question": "Your vehicle has a current warrant of fitness but a rear red stop light is not working. What should you do?",
        "options": [
            "Get it fixed with 60 days",
            "Fix it quickly, you could get a fine",
            "Wait until the next warrant of fitness inspection"
        ],
        "answer": "Fix it quickly, you could get a fine"
    },
    {
        "question": "You're driving along a road with an 80km/h speed limit. There's a 60km/h speed limit sign ahead. When must you be going 60km/h?",
        "options": [
            "Exactly when your front wheels pass the 60 km/h sign",
            "Before you reach the 60 km/h speed limit sign",
            "Within 50 metres after passing the sign"
        ],
        "answer": "Before you reach the 60 km/h speed limit sign"
    },
    {
        "question": "If you have a restricted licence when can you carry passengers?",
        "options": [
            "Between the hours of 10 pm and 5 am",
            "When a supervisor, who holds the appropriate licence, is in the front seat next to you",
            "At any time as long as they are family members"
        ],
        "answer": "When a supervisor, who holds the appropriate licence, is in the front seat next to you"
    },
    {
        "question": "If you are a driver involved in a crash, what is the FIRST action you should take?",
        "options": [
            "Tell a police officer immediately",
            "Stop and check to see if anyone is injured",
            "Move your vehicle off the road"
        ],
        "answer": "Stop and check to see if anyone is injured"
    },
    {
        "question": "What do these road markings mean?",
        "image": "road_markings_q1.jpg",
        "options": [
            "You should only enter the turning lane at the arrow",
            "Drive straight over all road markings and wait to turn right",
            "You must not drive over this area at all"
        ],
        "answer": "Drive straight over all road markings and wait to turn right"
    },
    {
        "question": "If you are turning left at an intersection, you must give way to vehicles coming towards you that are turning right. True or False?",
        "options": ["TRUE", "FALSE"],
        "answer": "FALSE"
    },
    {
        "question": "If you are the driver and you hurt somebody in a crash, who must you report it to?",
        "options": [
            "A Police Officer within 2 hours",
            "A Police Officer within 24 hours",
            "Your insurance company within 24 hours"
        ],
        "answer": "A Police Officer within 24 hours"
    },
    {
        "question": "For the purpose of applying the give way rule, entrance ways into public car parks should be treated as:",
        "options": ["As residential driveways", "As intersections"],
        "answer": "As intersections"
    }
]

# Initialize Session State
if 'shuffled_questions' not in st.session_state:
    # Shuffle the questions once per session
    shuffled_qs = questions.copy()
    random.shuffle(shuffled_qs)
    st.session_state.shuffled_questions = shuffled_qs
    
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.shuffled_options = []
    st.session_state.user_selection = None

def initialize_options():
    opts = st.session_state.shuffled_questions[st.session_state.current_q]['options'].copy()
    random.shuffle(opts)
    st.session_state.shuffled_options = opts

if not st.session_state.shuffled_options and st.session_state.current_q < len(st.session_state.shuffled_questions):
    initialize_options()

def next_question():
    st.session_state.current_q += 1
    st.session_state.answered = False
    st.session_state.user_selection = None
    if st.session_state.current_q < len(st.session_state.shuffled_questions):
        initialize_options()

def restart_quiz():
    shuffled_qs = questions.copy()
    random.shuffle(shuffled_qs)
    st.session_state.shuffled_questions = shuffled_qs
    
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.user_selection = None
    initialize_options()

# --- UI Layout ---
st.title("🚗 Learner Licence Flashcards")
st.write("Let's review the questions you missed!")
st.divider()

if st.session_state.current_q < len(st.session_state.shuffled_questions):
    q = st.session_state.shuffled_questions[st.session_state.current_q]
    
    # Progress and Question
    st.caption(f"Question {st.session_state.current_q + 1} of {len(st.session_state.shuffled_questions)}")
    st.subheader(q['question'])
    
    # --- Image Handling Logic (Robust Pathing) ---
    if "image" in q:
        try:
            # Get the absolute path to the directory where this script lives
            script_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(script_dir, q["image"])
            st.image(image_path)
        except Exception as e:
            st.warning(f"⚠️ Could not load image '{q['image']}'. Error details: {e}")
    
    # Keep the selected option highlighted even after the form submits
    current_index = None
    if st.session_state.user_selection in st.session_state.shuffled_options:
        current_index = st.session_state.shuffled_options.index(st.session_state.user_selection)
    
    # Form to handle selection
    with st.form(key=f"form_{st.session_state.current_q}"):
        selected = st.radio(
            "Select your answer:", 
            st.session_state.shuffled_options, 
            index=current_index,
            disabled=st.session_state.answered
        )
        
        # Submit Button
        if not st.session_state.answered:
            submit = st.form_submit_button("Check Answer")
            if submit:
                if selected is None:
                    st.warning("Please select an answer first!")
                else:
                    st.session_state.answered = True
                    st.session_state.user_selection = selected
                    if selected == q['answer']:
                        st.session_state.score += 1
                    st.rerun()
        else:
            st.form_submit_button("Check Answer", disabled=True)

    # Feedback and Next Button outside the form
    if st.session_state.answered:
        if st.session_state.user_selection == q['answer']:
            st.success("Correct! 🎉")
        else:
            st.error(f"Incorrect.\n\nYou selected: **{st.session_state.user_selection}**\nThe correct answer is: **{q['answer']}**")
            
        st.button("Next Question ➔", on_click=next_question, type="primary")

else:
    # End of Quiz Screen
    st.balloons()
    st.header("Quiz Complete! 🏁")
    st.subheader(f"Your Score: {st.session_state.score} / {len(st.session_state.shuffled_questions)}")
    
    if st.session_state.score == len(st.session_state.shuffled_questions):
        st.success("Perfect score! You're ready for the test.")
    elif st.session_state.score >= len(st.session_state.shuffled_questions) * 0.8:
        st.info("Great job! Just a little more review needed.")
    else:
        st.warning("Keep practicing, you'll get it next time!")
        
    st.button("Restart Quiz 🔄", on_click=restart_quiz, type="primary")