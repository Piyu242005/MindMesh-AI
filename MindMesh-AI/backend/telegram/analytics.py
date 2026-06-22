class AnalyticsStore:
    users_today = 0
    queries_today = 0
    videos_uploaded = 0
    gemini_requests = 0
    groq_requests = 0
    qdrant_searches = 0
    total_response_time = 0.0

    @classmethod
    def reset(cls):
        cls.users_today = 0
        cls.queries_today = 0
        cls.videos_uploaded = 0
        cls.gemini_requests = 0
        cls.groq_requests = 0
        cls.qdrant_searches = 0
        cls.total_response_time = 0.0

    @classmethod
    def add_query(cls, provider: str, response_time: float):
        cls.queries_today += 1
        cls.total_response_time += response_time
        if provider == "gemini":
            cls.gemini_requests += 1
        else:
            cls.groq_requests += 1

    @classmethod
    def add_upload(cls):
        cls.videos_uploaded += 1

    @classmethod
    def add_search(cls):
        cls.qdrant_searches += 1
        
    @classmethod
    def generate_report(cls) -> str:
        avg_time = (cls.total_response_time / cls.queries_today) if cls.queries_today > 0 else 0
        msg = f"""📊 <b>MindMesh Daily Report</b>

Users Today: {cls.users_today}
Queries: {cls.queries_today}
Videos Uploaded: {cls.videos_uploaded}

Gemini Requests: {cls.gemini_requests}
Groq Requests: {cls.groq_requests}

Qdrant Searches: {cls.qdrant_searches}

Average Response Time: {avg_time:.2f}s"""
        return msg
