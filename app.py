
import os
import json
import re
import streamlit as st
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="MindMap AI",
    page_icon="🧠",
    layout="wide"
)

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_client():
    if not API_KEY:
        raise ValueError(
            "Gemini API key is missing. Add it to your .env file."
        )
    return genai.Client(api_key=API_KEY)


def parse_response(response_text):
    """Convert Gemini's JSON response into Python data."""
    text = response_text.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)

    data = json.loads(text)

    required = [
        "topic", "overview", "branches",
        "learning_plan", "quiz", "resources"
    ]

    for key in required:
        if key not in data:
            raise ValueError(f"Missing section: {key}")

    return data


def generate_mindmap(topic, level, goal, days):
    """Generate a personalized learning map using Gemini."""

    client = get_client()

    prompt = f"""
You are MindMap AI, an intelligent learning assistant.

Create a personalized learning plan.

Topic: {topic}
Student Level: {level}
Learning Goal: {goal}
Duration: {days} days

Return only valid JSON in this format:

{{
 "topic": "Topic name",
 "overview": "Topic explanation",
 "branches": [
  {{
   "name": "Main concept",
   "description": "Explanation",
   "subtopics": ["Concept 1", "Concept 2"]
  }}
 ],
 "learning_plan": [
  {{
   "day": 1,
   "focus": "Topic to study",
   "activities": ["Activity 1", "Activity 2"],
   "outcome": "Expected result"
  }}
 ],
 "quiz": [
  {{
   "question": "Question",
   "options": [
    "A. Option 1",
    "B. Option 2",
    "C. Option 3",
    "D. Option 4"
   ],
   "answer": "A",
   "explanation": "Answer explanation"
  }}
 ],
 "resources": [
  {{
   "title": "Resource name",
   "purpose": "How it helps"
  }}
 ]
}}

Requirements:
- Generate 5 to 7 concept branches.
- Generate exactly {days} study-plan days.
- Generate 5 multiple-choice questions.
- Include four options per question.
- Use simple language.
- Do not invent website URLs.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )

    return parse_response(response.text or "")


def display_mindmap(data):
    st.header("🧠 " + data["topic"])
    st.info(data["overview"])

    branches = data["branches"]

    for start in range(0, len(branches), 2):
        columns = st.columns(2)

        for column, branch in zip(
            columns, branches[start:start + 2]
        ):
            with column:
                with st.container(border=True):
                    st.subheader("🌿 " + branch["name"])
                    st.write(branch["description"])

                    for subtopic in branch["subtopics"]:
                        st.markdown("- " + subtopic)


def display_study_plan(data):
    st.subheader("📅 Personalized Study Plan")

    for day in data["learning_plan"]:
        with st.expander(
            f"Day {day['day']}: {day['focus']}"
        ):
            for activity in day["activities"]:
                st.markdown("- " + activity)

            st.success("Outcome: " + day["outcome"])


def display_quiz(data):
    st.subheader("📝 Practice Quiz")

    questions = data["quiz"]

    with st.form("quiz_form"):
        answers = {}

        for index, question in enumerate(questions):
            st.markdown(
                f"**{index + 1}. {question['question']}**"
            )

            answers[index] = st.radio(
                "Select your answer",
                question["options"],
                key=f"question_{index}",
                label_visibility="collapsed"
            )

        submitted = st.form_submit_button(
            "Submit Answers",
            type="primary"
        )

    if submitted:
        score = 0

        for index, question in enumerate(questions):
            selected = answers[index][0].upper()
            correct = question["answer"][0].upper()

            if selected == correct:
                score += 1
                st.success(f"Question {index + 1}: Correct!")
            else:
                st.error(
                    f"Question {index + 1}: "
                    f"Correct answer is {correct}"
                )

            st.caption(question["explanation"])

        st.metric("Your Score", f"{score}/{len(questions)}")


# ---------------- MAIN APPLICATION ----------------

st.title("🧠 MindMap AI")
st.subheader("Turn any topic into an intelligent learning path")

st.write(
    "MindMap AI converts topics into concept maps, "
    "personalized study plans and practice quizzes."
)

# Sidebar input
with st.sidebar:
    st.header("Create Your MindMap")

    with st.form("input_form"):

        topic = st.text_input(
            "Enter Topic",
            placeholder="Example: Python Programming"
        )

        level = st.selectbox(
            "Select Your Level",
            ["Beginner", "Intermediate", "Advanced"]
        )

        goal = st.text_area(
            "Your Learning Goal",
            placeholder="What do you want to learn?"
        )

        days = st.slider(
            "Study Duration",
            min_value=3,
            max_value=14,
            value=7
        )

        submit = st.form_submit_button(
            "Generate MindMap",
            type="primary",
            use_container_width=True
        )


if submit:

    if not topic.strip():
        st.warning("Please enter a topic.")

    else:
        with st.spinner("Generating your MindMap..."):

            try:
                result = generate_mindmap(
                    topic,
                    level,
                    goal or "Understand the topic",
                    days
                )

                st.session_state["mindmap"] = result

                st.success("MindMap generated successfully!")

            except Exception as error:
                st.error(f"Error: {error}")


# Display generated content
if "mindmap" in st.session_state:

    data = st.session_state["mindmap"]

    tab1, tab2, tab3, tab4 = st.tabs([
        "🌿 Concept Map",
        "📅 Study Plan",
        "📝 Quiz",
        "📚 Resources"
    ])

    with tab1:
        display_mindmap(data)

    with tab2:
        display_study_plan(data)

    with tab3:
        display_quiz(data)

    with tab4:
        st.subheader("Suggested Learning Resources")

        for resource in data["resources"]:
            st.markdown("**" + resource["title"] + "**")
            st.write(resource["purpose"])

    # Download learning plan
    st.download_button(
        label="Download MindMap JSON",
        data=json.dumps(data, indent=4),
        file_name="mindmap_learning_plan.json",
        mime="application/json"
    )

else:
    st.info("Enter a topic in the sidebar to get started.")

    st.markdown("### Example Topics")
    st.write("""
    - Python Programming
    - Machine Learning
    - Cloud Computing
    - Data Structures
    - Database Management Systems
    """)
