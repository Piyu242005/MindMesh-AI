"""Prompt templates for the RAG pipeline with few-shot examples."""

from typing import List, Dict, Any
from .utils import seconds_to_timestamp


FEW_SHOT_EXAMPLES = """
Example 1:
User: "How do I create a table in HTML?"
Answer: Great question! Tables in HTML are covered in **Video 5: "Image, Lists, and Tables in HTML"**. 
You can find the table tutorial starting at **05:30** (timestamp: 330 seconds). The instructor walks you 
through the `<table>`, `<tr>`, `<td>`, and `<th>` tags with practical examples. Head over to Video 5 
at the 05:30 mark to learn all about it!

Example 2:
User: "What is the CSS Box Model?"
Answer: The CSS Box Model is explained in detail in **Video 18: "CSS Box Model - Margin, Padding & Borders"**. 
The concept is introduced right at the beginning at **00:10** and the instructor covers:
- **Margin** - space outside the border (at 02:15)
- **Padding** - space between content and border (at 05:40)  
- **Borders** - the border around the element (at 08:20)
I recommend watching the full video from the start for a complete understanding!
"""

FEW_SHOT_QA = """
Example 1:
Q: "What HTML tag is used for a hyperlink?"
A: The `<a>` tag (anchor) creates hyperlinks. It is introduced in **Video 4: "Heading, Paragraphs and Links"** at **03:10**.

Example 2:
Q: "What is the difference between margin and padding?"
A: **Margin** is the space *outside* the element border; **Padding** is the space *inside* the border (between the content and the border). Covered in **Video 18** at **02:15** (margin) and **05:40** (padding).
"""

FEW_SHOT_CODING = """
Example 1:
User: "Show me how to create a button in HTML"
Answer:
Based on the course content, here is how you create a button:

```html
<button type="button" onclick="alert('Clicked!')">Click Me</button>
```

This is covered in **Video 7: "Forms and input tags in HTML"** at **04:20**. The `type="button"` prevents form submission, and `onclick` adds an action.

Example 2:
User: "Write CSS for centering a div"
Answer:
The preferred modern approach shown in the course uses Flexbox:

```css
.container {
    display: flex;
    justify-content: center;
    align-items: center;
}
```

This technique is discussed in **Video 14: "Introduction to CSS"** at **07:45**.
"""


def _format_chunks(results: List[Dict[str, Any]]) -> str:
    """Convert result chunks to a formatted JSON string with human-readable timestamps."""
    import json
    formatted = []
    for r in results:
        start_ts = seconds_to_timestamp(r["start"])
        end_ts = seconds_to_timestamp(r["end"])
        formatted.append(
            {
                "title": r["title"],
                "video_number": r["number"],
                "start_time": start_ts,
                "start_seconds": r["start"],
                "end_time": end_ts,
                "end_seconds": r["end"],
                "text": r["text"],
            }
        )
    return json.dumps(formatted, indent=2)


def build_query_prompt(
    query: str,
    results: List[Dict[str, Any]],
    course_name: str = "Sigma Web Development",
    mode: str = "chat",
) -> str:
    """
    Build a mode-aware prompt for the LLM with context chunks and few-shot examples.
    Modes: 'chat' | 'qa' | 'coding'
    """
    chunks_json = _format_chunks(results)

    if mode == "qa":
        return _build_qa_prompt(query, chunks_json, course_name)
    elif mode == "coding":
        return _build_coding_prompt(query, chunks_json, course_name)
    else:
        return _build_chat_prompt(query, chunks_json, course_name)


def _build_chat_prompt(query: str, chunks_json: str, course_name: str) -> str:
    """Conversational teaching-assistant prompt."""
    return f"""You are a friendly AI teaching assistant for the {course_name} course.
You help students understand concepts and find specific content in video lectures.

INSTRUCTIONS:
- ONLY answer based on the provided video chunks below. Do NOT make up information.
- If the answer is not in the provided chunks, say "I couldn't find information about that in the course videos."
- Always mention the specific video number, title, and timestamp (in MM:SS format).
- Be warm, encouraging, and conversational in tone.
- If multiple videos cover the topic, mention all of them.

{FEW_SHOT_EXAMPLES}

RELEVANT VIDEO CHUNKS:
{chunks_json}

---------------------------------
Student: "{query}"

Answer (friendly, mention video numbers and timestamps):"""


def _build_qa_prompt(query: str, chunks_json: str, course_name: str) -> str:
    """Direct Q&A prompt — factual, concise, reference-heavy."""
    return f"""You are a precise Q&A assistant for the {course_name} course.
Answer the question directly and factually using ONLY the provided video chunks.

INSTRUCTIONS:
- Give a short, direct answer first, then cite the source.
- If the answer is not in the provided chunks, respond: "Not covered in the available course material."
- Always include: Video number, Video title, and Timestamp (MM:SS).
- Use bullet points for multi-part answers.
- Do NOT add filler phrases or extra commentary beyond what is needed.

{FEW_SHOT_QA}

RELEVANT VIDEO CHUNKS:
{chunks_json}

---------------------------------
Question: "{query}"

Answer (direct, factual, with video + timestamp references):"""


def _build_coding_prompt(query: str, chunks_json: str, course_name: str) -> str:
    """Coding-focused prompt — provides code examples with explanations."""
    return f"""You are a coding assistant for the {course_name} course.
Help the student write, understand, or debug code based on the course video content.

INSTRUCTIONS:
- Provide working code examples using ONLY concepts covered in the provided video chunks.
- Always wrap code in proper markdown fenced code blocks with the correct language tag (e.g. ```html, ```css, ```javascript).
- After each code block, briefly explain what each key part does.
- Reference the exact video number, title, and timestamp (MM:SS) where the concept is taught.
- If the request is not covered in the chunks, say "This coding topic isn't covered in the available course material."
- Prefer complete, runnable snippets over partial fragments.
- Include comments inside code where helpful.

{FEW_SHOT_CODING}

RELEVANT VIDEO CHUNKS:
{chunks_json}

---------------------------------
Student coding request: "{query}"

Response (provide code with explanation and video/timestamp references):"""


def build_summary_prompt(chunks: List[Dict[str, Any]], video_title: str) -> str:
    """Build a prompt to generate a video summary."""
    texts = [c["text"] for c in chunks]
    combined = " ".join(texts)

    return f"""Summarize the following video lecture transcript concisely.
Include the main topics covered and key takeaways.

Video Title: {video_title}
Transcript: {combined}

Summary:"""


def build_quiz_prompt(chunks: List[Dict[str, Any]], topic: str) -> str:
    """Build a prompt to generate quiz questions from content."""
    texts = [c["text"] for c in chunks]
    combined = " ".join(texts)

    return f"""Based on the following course content about "{topic}", generate 5 multiple-choice quiz questions.
Each question should have 4 options (A, B, C, D) with one correct answer.
Format each question clearly.

Content: {combined}

Quiz Questions:"""
