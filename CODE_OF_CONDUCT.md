# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone, regardless of age, body size, visible or invisible disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming, diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment for our community include:

* Demonstrating empathy and kindness toward other people
* Being respectful of differing opinions, viewpoints, and experiences
* Giving and gracefully accepting constructive feedback
* Accepting responsibility and apologizing to those affected by our mistakes, and learning from the experience
* Focusing on what is best not just for us as individuals, but for the overall community

Examples of unacceptable behavior include:

* The use of sexualized language or imagery, and sexual attention or advances of any kind
* Trolling, insulting or derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or email address, without their explicit permission
* Other conduct which could reasonably be considered inappropriate in a professional setting

## Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards of acceptable behavior and will take appropriate and fair corrective action in response to any behavior that they deem inappropriate, threatening, offensive, or harmful.

Community leaders have the right and responsibility to remove, edit, or reject comments, commits, code, wiki edits, issues, and other contributions that are not aligned to this Code of Conduct, and will communicate reasons for moderation decisions when appropriate.

## Scope

This Code of Conduct applies within all community spaces, and also applies when an individual is officially representing the community in public spaces. Examples of representing our community include using an official e-mail address, posting via an official social media account, or acting as an appointed representative at an online or offline event.

## Enforcement Guidelines

Community leaders will follow these Community Impact Guidelines in determining the consequences for any action they deem in violation of this Code of Conduct:

### 1. Correction
**Community Impact**: Use of inappropriate language or other behavior deemed unprofessional or unwelcome in the community.
**Consequence**: A private, written warning from community leaders, providing clarity around the nature of the violation and an explanation of why the behavior was inappropriate. A public apology may be requested.

### 2. Warning
**Community Impact**: A violation through a single incident or series of actions.
**Consequence**: A warning with consequences for continued behavior. No interaction with the people involved, including unsolicited interaction with those enforcing the Code of Conduct, for a specified period of time.

### 3. Temporary Ban
**Community Impact**: A serious violation of community standards, including sustained inappropriate behavior.
**Consequence**: A temporary ban from any sort of interaction or public communication with the community for a specified period of time. No public or private interaction with the people involved, including unsolicited interaction with those enforcing the Code of Conduct, is allowed during this period.

### 4. Permanent Ban
**Community Impact**: Demonstrating a pattern of violation of community standards, including sustained inappropriate behavior, harassment of an individual, or aggression toward or disparagement of classes of individuals.
**Consequence**: A permanent ban from any sort of public interaction within the community.

## Enforcement Process

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the community leaders responsible for enforcement by opening a private issue or contacting the maintainer. All complaints will be reviewed and investigated promptly and fairly.

All community leaders are obligated to respect the privacy and security of the reporter of any incident.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 2.1, available at [https://www.contributor-covenant.org/version/2/1/code_of_conduct.html][v2.1].

[homepage]: https://www.contributor-covenant.org
[v2.1]: https://www.contributor-covenant.org/version/2/1/code_of_conduct.html

---

## MindMesh AI Tech Stack & Architecture Context

When contributing to this project, it is helpful to understand the flow of data and the core technologies we rely on to maintain high performance and accuracy:

```text
Video Upload
      ↓
FFmpeg
      ↓
Faster-Whisper
      ↓
JSON Chunks
      ↓
SentenceTransformer
      ↓
Qdrant Cloud
      ↓
Semantic Search
      ↓
Gemini / Groq
      ↓
Streamlit
```

### Explanation of the Tech Stack

1. **Video Upload & FFmpeg**: The user uploads video courses. To save massive amounts of compute and memory, FFmpeg is used to instantly strip away the video stream, extracting only the raw audio (`.wav`) for processing.
2. **Faster-Whisper**: This highly optimized, local transcription model converts the audio into text. It provides timestamps which we use to chop the transcript into logical overlapping **JSON Chunks**.
3. **SentenceTransformer (`BAAI/bge-small-en-v1.5`)**: These text chunks are passed into a local embedding model that converts the semantic meaning of the text into high-dimensional numerical vectors (384 dimensions).
4. **Qdrant Cloud (Vector Database)**: We use **Qdrant Cloud** as our highly scalable Vector Database. It stores both the 384-dimensional vectors and the JSON payload (timestamps, titles). Qdrant is optimized for blazing-fast Approximate Nearest Neighbor (ANN) search, meaning it can instantly find the chunks most relevant to a user's question by calculating cosine distance.
5. **Semantic Search & LLM (Gemini/Groq)**: When a user asks a question, it is vectorized and sent to Qdrant. The top matching chunks are retrieved and injected into a prompt. This prompt is sent to an advanced LLM (like Google Gemini 2.5 Flash or Groq Llama 3) to generate a conversational, accurate answer grounded *only* in the retrieved course data.
6. **Streamlit**: The entire application, from the Upload Center to the AI Chat, is unified under a clean, responsive Streamlit frontend.
