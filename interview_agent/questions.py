"""Curated interview question bank, keyed by curriculum day.

Each entry provides:
  * topic      — short display label (also used for UI chips)
  * concepts   — keyword stems used by the Assessor to score answers
  * questions  — primary questions (>= 2) to rotate across candidates
  * deep_dives — harder follow-ups asked after a strong answer
  * probes     — targeted follow-ups when a specific concept was missing

The text is written to sound like a real senior interviewer, not a quiz.
"""
from __future__ import annotations

from typing import Any, Dict, List

QUESTION_BANK: Dict[int, Dict[str, Any]] = {
    1: {
        "topic": "Environment & Tooling",
        "concepts": ["python", "virtual", "venv", "environment", "vs code", "debug", "extension"],
        "questions": [
            "You set up a project virtual environment on day one. What problem does a virtual environment actually solve, and how did you know yours was working correctly?",
            "Walk me through the developer environment you ended up with after the first few days — editor, interpreter, extensions, local model. Why that stack?",
        ],
        "deep_dives": [
            "If a teammate cloned your repo and hit 'module not found', what's your debugging sequence?",
        ],
        "probes": {"virtual": "Could you explain what a virtual environment isolates, and what lives inside the .venv folder?"},
    },
    2: {
        "topic": "Local LLM Setup",
        "concepts": ["ollama", "model", "local", "copilot", "offline", "cli", "qwen"],
        "questions": [
            "You installed Ollama and pulled a local coding model. Why run a model locally at all, and what did you give up compared to a hosted model?",
            "How did you verify the local model was actually working before wiring it into your editor?",
        ],
        "deep_dives": [
            "What factors decide whether a local model or a hosted API is the right choice for a given task?",
        ],
        "probes": {"offline": "Talk me through the offline workflow you validated — what could and couldn't you do without internet?"},
    },
    3: {
        "topic": "First Full-Stack Project",
        "concepts": ["fastapi", "react", "vite", "git", "github", "api", "backend", "frontend", "endpoint"],
        "questions": [
            "Your first project wired a React frontend to a FastAPI backend. Explain the full journey of a user request from the browser to your model and back.",
            "You published the project to GitHub. Walk me through your Git workflow that first week — branching, commits, and what you'd do differently now.",
        ],
        "deep_dives": [
            "Where does the boundary between frontend and backend belong in a chat app, and how did you decide what each side handled?",
        ],
        "probes": {"api": "What exactly is an API endpoint in that architecture, and what did your first FastAPI endpoint return?"},
    },
    4: {
        "topic": "Structured Data Processing",
        "concepts": ["pandas", "sql", "sqlite", "csv", "database", "schema", "sqlalchemy", "clean"],
        "questions": [
            "You cleaned healthcare claims data with Pandas and stored it in SQLite. What cleaning problems did you actually hit, and how did you handle them?",
            "Why SQLite for this project instead of a full client-server database? Where would that choice start to hurt you?",
        ],
        "deep_dives": [
            "How did you decide which questions belonged in SQL versus which needed semantic search — what distinguishes them?",
        ],
        "probes": {"schema": "What does a good database schema for claims and plans look like, and how did you design the tables?"},
    },
    5: {
        "topic": "Unstructured Data Extraction",
        "concepts": ["pdf", "ocr", "tesseract", "scrape", "beautifulsoup", "extract", "text", "normalize"],
        "questions": [
            "You pulled text out of PDFs, scanned enrollment forms, and web pages. What made each source tricky, and how did you normalize the results into one format?",
            "When is OCR necessary versus regular PDF text extraction, and what kinds of errors does OCR introduce?",
        ],
        "deep_dives": [
            "If a scanned document came back with garbled text, how would you detect and handle that without corrupting your knowledge base?",
        ],
        "probes": {"normalize": "What did 'cleaning and normalizing' extracted text mean concretely in your pipeline?"},
    },
    6: {
        "topic": "Knowledge Base & Chunking",
        "concepts": ["chunk", "split", "metadata", "jsonl", "knowledge base", "token", "overlap"],
        "questions": [
            "You turned mixed documents into a unified knowledge base with text splitters. How did you choose your chunk size and splitting strategy?",
            "What metadata did you attach to every chunk, and why does that metadata matter later in retrieval?",
        ],
        "deep_dives": [
            "What are the failure modes of chunking — when does a bad chunk strategy break the answers your chatbot gives?",
        ],
        "probes": {"metadata": "How did you actually attach metadata like source and plan type to each chunk in the JSONL export?"},
    },
    7: {
        "topic": "Embeddings",
        "concepts": ["embedding", "vector", "semantic", "cosine", "similarity", "dimension", "pca", "cluster", "sentence"],
        "questions": [
            "Explain what an embedding is in your own words, and why a chatbot needs them rather than just keyword matching.",
            "You visualized your embeddings with PCA. What did the clusters tell you, and what would it have meant if similar healthcare concepts did NOT cluster together?",
        ],
        "deep_dives": [
            "Two sentences can be semantically similar but share no words. How does an embedding model capture that relationship?",
        ],
        "probes": {
            "dimension": "What is a vector's dimension, and what tradeoffs come with higher-dimensional embeddings?",
            "cosine": "Why is cosine similarity the default distance for embeddings rather than Euclidean distance?",
        },
    },
    8: {
        "topic": "Vector Databases",
        "concepts": ["vector database", "chroma", "pinecone", "index", "relational", "metadata", "ann", "similarity search"],
        "questions": [
            "What is a vector database and how is it different from the SQLite tables you built earlier?",
            "You compared Chroma (local) and Pinecone (managed). What were the real tradeoffs, and why did you pick what you picked for this project?",
        ],
        "deep_dives": [
            "How does an approximate nearest-neighbor index actually make a vector search fast, and what do you trade for that speed?",
        ],
        "probes": {
            "metadata": "How did metadata filtering work in your vector store, and when did you use it?",
            "index": "What is an index in a vector database, and why can't you just scan every vector on every query?",
        },
    },
    9: {
        "topic": "Populating the Vector DB",
        "concepts": ["collection", "index", "chroma", "metadata", "semantic search", "filter", "embed"],
        "questions": [
            "You loaded embeddings and documents into your vector database. How did you verify every chunk was indexed and nothing was silently lost?",
            "How did you test semantic search quality with real healthcare questions before wiring it into the chatbot?",
        ],
        "deep_dives": [
            "If a search returned irrelevant results, how would you diagnose whether the problem was the embeddings, the chunking, or the query itself?",
        ],
        "probes": {"filter": "Give me a concrete example of a query where you had to filter by metadata to get the right answer."},
    },
    10: {
        "topic": "Retrieval & Matching Engine",
        "concepts": ["router", "sql", "vector", "hybrid", "retrieval", "merge", "dedup", "relevance", "score"],
        "questions": [
            "Your retrieval engine decided between SQL, vector search, and hybrid retrieval. Walk me through how a query gets routed, with a concrete healthcare example.",
            "You merged results from multiple retrieval sources. How did you deduplicate and rank them into one coherent answer?",
        ],
        "deep_dives": [
            "What is hybrid retrieval actually combining — and when does combining them beat either one alone?",
        ],
        "probes": {
            "router": "How does your router decide 'this question is structured, so use SQL'? What signals does it use?",
            "relevance": "How did you evaluate retrieval accuracy — what did you measure, and what was failing at first?",
        },
    },
    11: {
        "topic": "RAG End-to-End",
        "concepts": ["rag", "retrieval", "context", "ground", "prompt", "pipeline", "openai", "ollama", "groq", "hallucin"],
        "questions": [
            "Explain end-to-end how a user's question becomes an answer in your RAG pipeline — from the request to the final reply.",
            "How did you force the LLM to answer only from retrieved context, and what did you do about hallucinations?",
        ],
        "deep_dives": [
            "If the retrieved context is wrong or empty, what should the system do instead of confidently making something up?",
        ],
        "probes": {
            "ground": "What did your 'grounded prompt' look like, and what instructions made the model stick to the retrieved text?",
            "context": "How much context did you pass to the model, and how did you decide when you had enough — or too much?",
        },
    },
    12: {
        "topic": "Prompt Engineering",
        "concepts": ["prompt", "zero-shot", "few-shot", "chain-of-thought", "system prompt", "template", "evaluate", "tone"],
        "questions": [
            "What's the difference between zero-shot, few-shot, and chain-of-thought prompting — and give me a healthcare example where you'd reach for each?",
            "You iterated on system prompt variations for the chatbot. How did you measure that one prompt was actually better than another?",
        ],
        "deep_dives": [
            "Chain-of-thought can improve reasoning — but it can also encourage the model to rationalize wrong answers. How do you think about that tradeoff?",
        ],
        "probes": {
            "few-shot": "What does a few-shot example look like in your prompt, and what makes a good vs. bad example?",
            "template": "Where do you keep your prompt templates, and how do you version them across releases?",
        },
    },
    13: {
        "topic": "Function Calling & Structured Outputs",
        "concepts": ["function calling", "tool", "schema", "pydantic", "structured", "validation", "json", "parameters"],
        "questions": [
            "Explain how function calling works — how does the model decide a function is needed, and how does your code actually execute it?",
            "Why did you validate structured outputs with Pydantic, and what happens when validation fails at runtime?",
        ],
        "deep_dives": [
            "When is function calling the right tool versus letting the model answer in free text? What breaks if you pick wrong?",
        ],
        "probes": {
            "schema": "Walk me through a tool schema you defined for the healthcare chatbot — what fields and why?",
            "validation": "What kinds of invalid outputs did you catch in testing, and how did you handle them gracefully?",
        },
    },
    14: {
        "topic": "Fine-Tuning Concepts",
        "concepts": ["fine-tun", "dataset", "training", "rag", "prompt", "overfit", "lora", "when to"],
        "questions": [
            "When is fine-tuning the right move versus prompt engineering or RAG — and when is it a waste of effort?",
            "You built a fine-tuning dataset. What made a training example high quality, and how did you validate the dataset before training?",
        ],
        "deep_dives": [
            "What are the risks of fine-tuning on a small, self-made dataset — and how do you detect overfitting?",
        ],
        "probes": {"dataset": "How many examples do you realistically need, and how did you split train vs. test?"},
    },
    15: {
        "topic": "LoRA & QLoRA Hands-On",
        "concepts": ["lora", "qlora", "peft", "transformers", "bitsandbytes", "quantiz", "adapter"],
        "questions": [
            "You fine-tuned with LoRA or QLoRA. Explain what LoRA actually modifies about the model and why that keeps training tractable.",
            "How did you evaluate the fine-tuned model against the base model on unseen cases — and what did you measure?",
        ],
        "deep_dives": [
            "What does quantization do to a model, and what's the practical cost/benefit of QLoRA over LoRA?",
        ],
        "probes": {"adapter": "What exactly is an adapter, and how does it keep the base weights frozen?"},
    },
    16: {
        "topic": "Chatbot Backend & API",
        "concepts": ["fastapi", "endpoint", "session", "history", "api", "retrieval", "function calling", "response"],
        "questions": [
            "Describe the architecture of your /chat endpoint — how do retrieval, function calling, and generation fit together on one request?",
            "How did you manage conversation state on the backend, and why does session-based management matter for a chatbot?",
        ],
        "deep_dives": [
            "If the same user sends ten requests in parallel, what could go wrong with your session handling?",
        ],
        "probes": {"history": "How does the backend store and reload conversation history for a returning session?"},
    },
    17: {
        "topic": "Chatbot Frontend",
        "concepts": ["streamlit", "frontend", "chat", "uuid", "session", "requests", "state"],
        "questions": [
            "How does your frontend stay in sync with the backend — what does a chat message round-trip look like from the UI's perspective?",
            "You added a plan selector and a new-conversation option. How did the frontend manage that state between interactions?",
        ],
        "deep_dives": [
            "What UX problems did you discover when a real user used the chat interface, and how did you fix them?",
        ],
        "probes": {"uuid": "Why did you generate a UUID per conversation rather than reusing one identifier?"},
    },
    18: {
        "topic": "Streaming Responses",
        "concepts": ["stream", "token", "sse", "server-sent", "incremental", "loading", "interrupt"],
        "questions": [
            "Why did you implement streaming responses instead of returning one big JSON body, and what changed in the user experience?",
            "How did you handle an interrupted or failed stream mid-generation?",
        ],
        "deep_dives": [
            "What are the real engineering costs of streaming — error handling, connection lifecycle, partial state — and how did you manage them?",
        ],
        "probes": {"sse": "What is Server-Sent Events and how does it differ from a normal HTTP request/response?"},
    },
    19: {
        "topic": "Response Formatting & Citations",
        "concepts": ["citation", "source", "pydantic", "markdown", "card", "structured", "trust", "render"],
        "questions": [
            "You added citations to chatbot responses. How did you know which retrieved chunks actually supported the answer you returned?",
            "How did you validate structured outputs like claims cards before rendering them, and why does that matter for trust?",
        ],
        "deep_dives": [
            "A citation can be wrong even when it 'looks' right. How would you audit citation quality in production?",
        ],
        "probes": {"source": "Where does the source information for a citation come from in your pipeline?"},
    },
    20: {
        "topic": "Conversation Memory & Context",
        "concepts": ["memory", "context", "history", "token", "summariz", "session", "persist", "truncat"],
        "questions": [
            "How did you keep a long conversation coherent while staying inside token limits — what was your actual strategy?",
            "The chatbot should remember user preferences across a conversation. How did you persist and reload that state?",
        ],
        "deep_dives": [
            "Summarization-based memory can silently drop important details. How do you decide what's safe to compress?",
        ],
        "probes": {"token": "How did you measure token usage and decide when to summarize or truncate history?"},
    },
    21: {
        "topic": "LangChain Agents & ReAct",
        "concepts": ["agent", "langchain", "react", "tool", "reasoning", "trace", "loop", "observation"],
        "questions": [
            "Explain the ReAct pattern — what does 'reason' and 'act' mean in an agent loop, and where does the observation come from?",
            "You converted function-calling workflows into a LangChain agent. What did the agent give you that plain function calling didn't?",
        ],
        "deep_dives": [
            "Agents can loop forever or pick the wrong tool. How did you bound and debug that behavior?",
        ],
        "probes": {
            "trace": "What does a reasoning trace look like, and how did you use it to find a wrong tool selection?",
            "tool": "How did you wrap a chatbot capability as a reusable LangChain tool — what's in a tool definition?",
        },
    },
    22: {
        "topic": "Multi-Agent Orchestration",
        "concepts": ["multi-agent", "crewai", "langgraph", "router", "specialist", "orchestrat", "delegate", "workflow"],
        "questions": [
            "How did your router agent decide which specialist should handle a request, and what did each specialist own?",
            "You compared multi-agent versus single-agent performance. When did the multi-agent approach actually win — and when was it pure overhead?",
        ],
        "deep_dives": [
            "Multi-agent systems introduce failure and latency at every handoff. How did you keep the orchestration reliable?",
        ],
        "probes": {
            "router": "What does a routing agent need to know to delegate correctly — and what happens when it delegates wrong?",
            "workflow": "Walk me through the full multi-agent workflow for one healthcare question from start to finish.",
        },
    },
    23: {
        "topic": "Model Context Protocol (MCP)",
        "concepts": ["mcp", "protocol", "server", "tool", "standard", "client", "context", "json-rpc"],
        "questions": [
            "Explain MCP to someone who has never heard of it — what problem does it solve that a plain REST API doesn't?",
            "You built an MCP server exposing healthcare tools. How did you connect it to an MCP client and verify the tools actually executed?",
        ],
        "deep_dives": [
            "What's the difference between MCP as a protocol and your earlier function-calling schemas — is MCP just reinventing that?",
        ],
        "probes": {
            "standard": "What does 'standardized tool exposure' buy you as an ecosystem — who benefits and how?",
            "client": "How does a client discover and invoke the tools your MCP server exposes?",
        },
    },
    24: {
        "topic": "Agentic Integration & Reliability",
        "concepts": ["integration", "mcp", "retry", "timeout", "error", "graceful", "reliab", "failure"],
        "questions": [
            "You integrated agents, MCP tools, retrieval, and memory into one pipeline. What was the hardest part of making that work together?",
            "How did you implement retries, timeouts, and graceful error handling — and how did you test failure cases?",
        ],
        "deep_dives": [
            "What's the difference between retrying a call and retrying the whole agent loop, and why does it matter?",
        ],
        "probes": {"failure": "Give me a failure scenario you deliberately tested and what your pipeline did about it."},
    },
    25: {
        "topic": "Evaluation & Testing",
        "concepts": ["evaluation", "benchmark", "metric", "dataset", "grounding", "accuracy", "consistency", "baseline"],
        "questions": [
            "How did you evaluate your chatbot — what did you measure, and how did you build the benchmark dataset?",
            "What were the most common failure cases you found in evaluation, and what did you change because of them?",
        ],
        "deep_dives": [
            "How do you measure 'grounding' — the answer staying faithful to the retrieved context — rather than just judging if it sounds good?",
        ],
        "probes": {"baseline": "Why establish baseline metrics before any optimization — what are you comparing against later?"},
    },
    26: {
        "topic": "Performance & Cost",
        "concepts": ["token", "latency", "cost", "cache", "benchmark", "optimiz", "tiktoken", "throughput"],
        "questions": [
            "You optimized the pipeline for latency and cost. What did you measure first, and what moved the needle most?",
            "How did you implement response caching, and what are the risks of caching LLM responses?",
        ],
        "deep_dives": [
            "Where does most of your token spend actually go — prompt, context, or output — and how would you cut it without hurting quality?",
        ],
        "probes": {"latency": "What was your end-to-end latency before and after optimization, and what contributed the most?"},
    },
    27: {
        "topic": "Security & Guardrails",
        "concepts": ["security", "auth", "validation", "prompt injection", "guardrail", "jailbreak", "sanitize", "pii"],
        "questions": [
            "How did you secure the chatbot API and protect sensitive healthcare data end to end?",
            "Explain what a prompt-injection attack looks like against a RAG chatbot, and how you defended against it.",
        ],
        "deep_dives": [
            "Why is prompt-injection defense especially hard in a RAG system where the retrieved text itself is untrusted input?",
        ],
        "probes": {
            "injection": "Can you give me a concrete prompt-injection string you'd test with, and what your system would do?",
            "validation": "What input validation did you put in front of the API, and what kinds of requests did you reject?",
        },
    },
    28: {
        "topic": "Docker & Kubernetes",
        "concepts": ["docker", "kubernetes", "container", "pod", "deploy", "health check", "image", "replica"],
        "questions": [
            "Walk me through containerizing and deploying the chatbot — what does the Docker image contain and what did Kubernetes manage for you?",
            "What health checks and environment configuration did you set up before calling the deployment production-ready?",
        ],
        "deep_dives": [
            "Kubernetes adds real operational complexity. What would you need to see before you'd say this app genuinely justifies Kubernetes over a single host?",
        ],
        "probes": {
            "health check": "What does a health check endpoint actually do in an orchestrator, and what should it verify?",
            "image": "What's inside your backend Docker image, and how did you keep it small?",
        },
    },
    29: {
        "topic": "Monitoring & Observability",
        "concepts": ["monitoring", "logging", "prometheus", "grafana", "metric", "dashboard", "observability", "latency", "error"],
        "questions": [
            "What did you choose to monitor and log in the chatbot pipeline, and what would a degrading system look like in those signals?",
            "You built a Grafana dashboard — which three metrics would you watch first in production, and why those?",
        ],
        "deep_dives": [
            "What's the difference between logging, metrics, and traces — and which gaps in observability have bitten you before?",
        ],
        "probes": {"metric": "Pick one metric — say p95 latency — and explain how you'd distinguish a real regression from noise."},
    },
    30: {
        "topic": "Production Readiness",
        "concepts": ["end-to-end", "test", "production", "documentation", "release", "regression", "rollback"],
        "questions": [
            "You ran complete end-to-end testing before production. What was the scariest bug you found that unit tests wouldn't have caught?",
            "What does 'production ready' mean for a chatbot specifically — beyond 'the API responds'?",
        ],
        "deep_dives": [
            "What's your rollback story if a new model prompt makes answers worse after deploy?",
        ],
        "probes": {"documentation": "What documentation did you finish before go-live, and who needs it?"},
    },
    31: {
        "topic": "Capstone & System Design",
        "concepts": ["capstone", "architecture", "design", "tradeoff", "production", "scale", "decision", "module"],
        "questions": [
            "Tell me about your capstone project — start with the problem, then walk me through the architecture you built to solve it.",
            "What was the hardest engineering decision in the whole project, and what made you choose the way you did?",
            "If you were to rebuild the chatbot today, what's the one thing you'd do differently and why?",
        ],
        "deep_dives": [
            "Where is your system most likely to break under 10x usage, and what would you fix first?",
        ],
        "probes": {"tradeoff": "Walk me through a specific tradeoff you faced — the options, and why you picked one."},
    },
}

def get_day_meta(day: int) -> Dict[str, Any]:
    """Return the question-bank entry for a day, or a sensible generic fallback."""
    entry = QUESTION_BANK.get(day)
    if entry is not None:
        return entry
    return {
        "topic": f"Day {day}",
        "concepts": ["pipeline", "build", "implement", "model", "data", "system", "project"],
        "questions": [
            f"Walk me through what you built and learned on day {day} of the cohort.",
            f"What was the most important technical decision you made on day {day}, and why?",
        ],
        "deep_dives": ["What would you change about your day-{day} implementation if you did it again?"],
        "probes": {},
    }


def available_variants(day: int, day_obj: Any = None) -> List[str]:
    """All usable primary-question texts for a day (bank questions, then deep dives,
    then questions generated from curriculum objectives)."""
    meta = get_day_meta(day)
    variants: List[str] = list(meta["questions"]) + list(meta["deep_dives"])
    if day_obj:
        for objective in day_obj.get("objectives", []):
            variants.append(
                f"One objective for day {day} was to {objective}. How did you go about that, and what did you learn?"
            )
    return variants
