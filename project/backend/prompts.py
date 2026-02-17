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


def build_query_prompt(
    query: str,
    results: List[Dict[str, Any]],
    course_name: str = "Sigma Web Development",
) -> str:
    """
    Build a prompt for the LLM with context chunks and few-shot examples.
    Converts timestamps to human-readable format.
    """
    # Format chunks with readable timestamps
    formatted_chunks = []
    for r in results:
        start_ts = seconds_to_timestamp(r["start"])
        end_ts = seconds_to_timestamp(r["end"])
        formatted_chunks.append(
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

    import json
    chunks_json = json.dumps(formatted_chunks, indent=2)

    prompt = f"""You are an AI teaching assistant for the {course_name} course. 
You help students find specific content in video lectures and answer their questions.

INSTRUCTIONS:
- ONLY answer based on the provided video chunks below. Do NOT make up information.
- If the answer is not in the provided chunks, say "I couldn't find information about that in the course videos."
- Always mention the specific video number, title, and timestamp (in MM:SS format).
- Be friendly, concise, and guide the student to the right video and timestamp.
- Format timestamps as MM:SS for easy navigation.
- If multiple videos cover the topic, mention all of them.

{FEW_SHOT_EXAMPLES}

RELEVANT VIDEO CHUNKS:
{chunks_json}

---------------------------------
Student Question: "{query}"

Answer (remember: only use information from the chunks above, mention video numbers and timestamps in MM:SS format):"""

    return prompt


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
