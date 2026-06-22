class AnalyticsStore:
    users_today = 0
    queries_today = 0
    videos_uploaded = 0
    gemini_requests = 0
    groq_requests = 0
    
    course_searches = 0
    web_searches = 0
    hybrid_searches = 0
    
    total_response_time = 0.0

    @classmethod
    def reset(cls):
        cls.users_today = 0
        cls.queries_today = 0
        cls.videos_uploaded = 0
        cls.gemini_requests = 0
        cls.groq_requests = 0
        cls.course_searches = 0
        cls.web_searches = 0
        cls.hybrid_searches = 0
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
    def add_course_search(cls):
        cls.course_searches += 1

    @classmethod
    def add_web_search(cls):
        cls.web_searches += 1

    @classmethod
    def add_hybrid_search(cls):
        cls.hybrid_searches += 1

    # Keep old add_search for backwards compatibility if needed
    @classmethod
    def add_search(cls):
        pass
        
    @classmethod
    def generate_report(cls) -> str:
        avg_time = (cls.total_response_time / cls.queries_today) if cls.queries_today > 0 else 0
        msg = f"""📊 <b>MindMesh Daily Report</b>

Users Today: {cls.users_today}
Queries: {cls.queries_today}
Videos Uploaded: {cls.videos_uploaded}

Gemini Requests: {cls.gemini_requests}
Groq Requests: {cls.groq_requests}

📚 Course Searches: {cls.course_searches}
🌐 Web Searches: {cls.web_searches}
🔀 Hybrid Searches: {cls.hybrid_searches}

Average Response Time: {avg_time:.2f}s"""
        return msg
