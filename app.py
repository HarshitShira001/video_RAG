import streamlit as st
import time
from dotenv import load_dotenv
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="video_rag",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helpers ────────────────────────────────────────────────────────────────────
STEP_ICONS = {
    "audio":      "🔊",
    "transcript": "📝",
    "title":      "🏷️",
    "summary":    "📋",
    "extract":    "🔍",
    "rag":        "🧠",
}

STEP_LABELS = {
    "audio":      "Audio Processing",
    "transcript": "Transcription",
    "title":      "Title Generation",
    "summary":    "Summarisation",
    "extract":    "Extraction",
    "rag":        "RAG Engine",
}

STATUS_SYMBOLS = {
    "done":    "✅",
    "active":  "⏳",
    "pending": "⬜",
}

def render_pipeline_status():
    """Render each pipeline step as a native Streamlit metric/caption row."""
    for key in ["audio", "transcript", "title", "summary", "extract", "rag"]:
        state  = st.session_state.pipeline_steps.get(key, "pending")
        symbol = STATUS_SYMBOLS.get(state, "⬜")
        icon   = STEP_ICONS[key]
        label  = STEP_LABELS[key]
        st.write(f"{symbol} {icon} {label}")

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎬 video_rag")
    st.caption("Meeting Intelligence")
    st.divider()

    st.subheader("⚙️ Input")
    source = st.text_input(
        "YouTube URL or File Path",
        placeholder="https://youtube.com/watch?v=... or /path/to/file.mp4",
    )
    language = st.selectbox("Language", ["english", "hinglish"], index=0)
    run_btn = st.button("⚡ Analyse", use_container_width=True)

    if st.session_state.pipeline_done:
        st.divider()
        st.subheader("📊 Pipeline Status")
        render_pipeline_status()

# ─── Main Header ────────────────────────────────────────────────────────────────
st.title("🎬 video_rag")
st.caption("Transcribe · Summarise · Chat with your meetings")
st.divider()

# ─── Run Pipeline ────────────────────────────────────────────────────────────────
if run_btn:
    if not source.strip():
        st.error("Please enter a YouTube URL or file path.")
    else:
        st.session_state.pipeline_done  = False
        st.session_state.result         = None
        st.session_state.chat_history   = []
        st.session_state.pipeline_steps = {}

        progress_placeholder = st.empty()

        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state

        try:
            progress_placeholder.info("⚙️ Pipeline running — see sidebar for live status…")

            update_step("audio", "active")
            chunks = process_input(source)
            update_step("audio", "done")

            update_step("transcript", "active")
            transcript = transcribe_all(chunks, language)
            update_step("transcript", "done")

            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            update_step("extract", "active")
            action_items = extract_action_items(transcript)
            decisions    = extract_key_decisions(transcript)
            questions    = extract_questions(transcript)
            update_step("extract", "done")

            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            st.session_state.result = {
                "title":          title,
                "transcript":     transcript,
                "summary":        summary,
                "action_items":   action_items,
                "key_decisions":  decisions,
                "open_questions": questions,
                "rag_chain":      rag_chain,
            }
            st.session_state.pipeline_done = True
            progress_placeholder.success("✅ Analysis complete!")
            time.sleep(0.5)
            progress_placeholder.empty()
            st.rerun()

        except Exception as e:
            for k in ["audio", "transcript", "title", "summary", "extract", "rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            progress_placeholder.error(f"❌ Error: {e}")

# ─── Results ─────────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    # ── Session Title ──────────────────────────────────────────────────────────
    st.subheader(f"📌 {r['title']}")
    st.divider()

    # ── Summary + Transcript ───────────────────────────────────────────────────
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.subheader("📋 Summary")
        st.write(r["summary"])

    with col2:
        with st.expander("📝 Full Transcript", expanded=False):
            st.text_area(
                label="Transcript",
                value=r["transcript"],
                height=300,
                disabled=True,
                label_visibility="collapsed",
            )

    st.divider()

    # ── Action Items | Decisions | Questions ───────────────────────────────────
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.subheader("✅ Action Items")
        st.write(r["action_items"])

    with c2:
        st.subheader("🔑 Key Decisions")
        st.write(r["key_decisions"])

    with c3:
        st.subheader("❓ Open Questions")
        st.write(r["open_questions"])

    st.divider()

    # ── RAG Chat ───────────────────────────────────────────────────────────────
    st.subheader("💬 Chat with your Meeting")

    # Display chat history using st.chat_message
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.write(msg["content"])

    if not st.session_state.chat_history:
        st.info("💬 Ask anything about your meeting transcript.")

    # Chat input row
    chat_col1, chat_col2 = st.columns([5, 1], gap="small")
    with chat_col1:
        user_input = st.text_input(
            "Your question",
            placeholder="What were the main decisions made?",
            label_visibility="collapsed",
            key="chat_input",
        )
    with chat_col2:
        send_btn = st.button("Send →", use_container_width=True)

    if send_btn and user_input.strip():
        with st.spinner("Thinking…"):
            answer = ask_question(r["rag_chain"], user_input.strip())
        st.session_state.chat_history.append({"role": "user",      "content": user_input.strip()})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

else:
    # ── Empty / Welcome State ──────────────────────────────────────────────────
    st.info(
        "🎬 **Ready to Analyse**\n\n"
        "Paste a YouTube URL or local file path in the sidebar, "
        "choose your language, and hit **Analyse** to get started.\n\n"
        "**Features:** 🔊 Transcription · 📋 Summarisation · 🧠 RAG Chat"
    )