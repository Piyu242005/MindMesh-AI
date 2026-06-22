# Contributing to MindMesh AI

First off, thank you for considering contributing to MindMesh AI! It's people like you that make open-source such a great community to learn, inspire, and create.

## 🚀 Development Setup

1. **Fork** the repository and clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/MindMesh-AI.git
   cd MindMesh-AI
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your API keys (Gemini, Groq, Qdrant).

## 🌿 Branch Naming Conventions

Please create a branch for your work. Use the following prefixes to clearly indicate the intent of your branch:
- `feature/` - for new features or enhancements
- `fix/` - for bug fixes
- `docs/` - for documentation updates
- `refactor/` - for code refactoring without changing functionality
- `test/` - for adding or modifying tests

*Example*: `feature/add-chat-history` or `fix/qdrant-search`

## 📝 Commit Message Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- `feat: [description]` - A new feature
- `fix: [description]` - A bug fix
- `docs: [description]` - Documentation changes
- `style: [description]` - Formatting, missing semi-colons, etc.
- `refactor: [description]` - Code change that neither fixes a bug nor adds a feature
- `test: [description]` - Adding missing tests

*Example*: `feat: implement Faster-Whisper audio transcription`

## 🔄 Pull Request Workflow

1. Update the `README.md` or `CHANGELOG.md` with details of changes, if applicable.
2. Ensure your code follows the existing coding standards and Python best practices.
3. Submit a Pull Request targeting the `main` branch.
4. Fill out the provided Pull Request Template.
5. Wait for a maintainer to review your code. We may request some changes before merging.

## 📐 Coding Standards

- **Python**: Follow PEP 8 guidelines.
- **Type Hinting**: Use type hints wherever possible to maintain a robust codebase.
- **Docstrings**: Ensure functions and classes are documented clearly.
- **Streamlit**: Keep UI components organized inside the `pages/` directory and decoupled from backend logic.

## 🧪 Testing Requirements

Before submitting a PR, ensure that:
1. The app successfully runs locally (`streamlit run app.py`).
2. The core RAG pipeline (upload -> transcribe -> embed -> search) functions correctly without breaking existing features.
3. (Future) Run the test suite if applicable: `pytest tests/`

Thank you for contributing to MindMesh AI!
