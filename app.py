import time
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="나는 어떤 모동숲 주민일까?🌿",
    page_icon="🌿",
    layout="centered",
)

# -----------------------------
# OpenAI Client (Streamlit Cloud: use st.secrets)
# -----------------------------
API_KEY = st.secrets.get("OPENAI_API_KEY", None)
client = OpenAI(api_key=API_KEY) if API_KEY else None

# -----------------------------
# Session State 초기화
# -----------------------------
NUM_QUESTIONS = 5

if "answers" not in st.session_state:
    st.session_state.answers = [None] * NUM_QUESTIONS

if "ai_result" not in st.session_state:
    st.session_state.ai_result = ""

if "has_result" not in st.session_state:
    st.session_state.has_result = False

# -----------------------------
# 리셋 함수
# -----------------------------
def reset_test():
    st.session_state.answers = [None] * NUM_QUESTIONS
    st.session_state.ai_result = ""
    st.session_state.has_result = False
    for i in range(NUM_QUESTIONS):
        key = f"q_{i}"
        if key in st.session_state:
            del st.session_state[key]

# -----------------------------
# 클립보드 복사 (JS)
# -----------------------------
def copy_to_clipboard(text: str):
    js_text = repr(text)  # safely escape quotes/newlines
    components.html(
        f"""
        <script>
        async function copyText() {{
            try {{
                await navigator.clipboard.writeText({js_text});
            }} catch (err) {{
                console.log("Clipboard copy failed:", err);
            }}
        }}
        copyText();
        </script>
        """,
        height=0,
    )

# -----------------------------
# Prompts
# -----------------------------
SYSTEM_PROMPT = """
당신은 유쾌한 동물 심리학자입니다. 재밌있는 비유와 이모지를 사용해서 결과를 알려주세요.

답변 형식:
1. 🐾 당신과 어울리는 동물: [동물 이름]
2. 📝 이유: [답변 패턴을 바탕으로 2-3문장 설명]
3. 💡 조언: [이 유형에게 맞는 조언 1-2개]

전체적으로 가볍고 친근한 톤을 유지해주세요.
"""

def build_user_answers_text(answers):
    return ", ".join([f"질문{i+1}: {ans}" for i, ans in enumerate(answers)])

def stream_ai_result(user_text: str):
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        stream=True,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        token = getattr(delta, "content", None)
        if token:
            yield token

# -----------------------------
# UI - Title & Intro
# -----------------------------
st.title("나는 어떤 모동숲 주민일까?🌿 동숲 대사선택으로 보는 인간관계 스타일")
st.markdown(
    """
가볍게 대사를 골라보면,  
AI가 당신의 **인간관계 스타일**을 분석해 **어울리는 동물**로 알려줘요 🐾✨

아래 5개 질문에 답하고 **결과 보기**를 눌러주세요!
"""
)

st.divider()

# -----------------------------
# 질문/선택지 데이터
# -----------------------------
questions = [
    {
        "q": "1. 마을에 새 주민이 이사 왔다.\n그 주민이 당신을 보고 말을 걸어왔다면?",
        "options": [
            "와! 반가워 😊 우리 마을 어때?",
            "안녕. (웃으며 짧게 인사한다)",
            "짐 옮기는 거 도와줄까?",
            "… (상대가 더 말할 때까지 기다린다)",
        ],
    },
    {
        "q": "2. 친하다고 생각한 주민이 요즘 먼저 말을 안 건다. 이럴 때 당신은?",
        "options": [
            "내가 뭐 잘못했나? 바로 말을 건다",
            "굳이 캐묻지 않고 거리를 유지한다",
            "괜히 신경 쓰여서 먼저 챙긴다",
            "이유를 곰곰이 생각하며 상황을 본다",
        ],
    },
    {
        "q": "3. 주민이 고민을 털어놓으며 도움을 요청했다. 당신의 반응은?",
        "options": [
            "에이, 당연하지! 내가 옆에 있잖아",
            "이건 이렇게 해보는 게 어때? (현실적 조언)",
            "많이 힘들었겠다… 감정부터 공감한다",
            "조용히 끝까지 들어준다",
        ],
    },
    {
        "q": "4. 마을 회의에서 의견이 갈렸다. 당신의 선택은?",
        "options": [
            "분위기를 부드럽게 만들려고 농담한다",
            "필요 이상으로 나서지 않는다",
            "모두가 상처받지 않는 쪽을 고른다",
            "핵심만 정리해서 말한다",
        ],
    },
    {
        "q": "5. 하루가 끝나고 집에 돌아온 밤. 당신에게 가장 필요한 건?",
        "options": [
            "누군가와 수다 떨며 하루 정리",
            "아무도 없는 조용한 시간",
            "오늘 잘했어라는 한마디",
            "혼자 생각하며 정리하는 시간",
        ],
    },
]

# -----------------------------
# 질문 렌더링
# -----------------------------
for i, item in enumerate(questions):
    st.subheader(f"Q{i+1}")
    selected = st.radio(
        item["q"],
        item["options"],
        key=f"q_{i}",
        index=None if st.session_state.answers[i] is None else item["options"].index(st.session_state.answers[i]),
    )
    st.session_state.answers[i] = selected
    st.write("")

st.divider()

# -----------------------------
# 버튼 UI
# -----------------------------
col1, col2 = st.columns(2)
with col1:
    analyze_clicked = st.button("결과 보기", type="primary")
with col2:
    if st.button("다시 테스트하기"):
        reset_test()
        st.rerun()

# -----------------------------
# 결과 분석 (로딩 + 스트리밍)
# -----------------------------
if analyze_clicked:
    if not API_KEY:
        st.error("Streamlit Cloud의 Secrets에 OPENAI_API_KEY를 설정해주세요.")
    elif any(a is None for a in st.session_state.answers):
        st.warning("모든 질문에 답해주세요!")
    else:
        st.session_state.ai_result = ""
        st.session_state.has_result = False

        user_text = build_user_answers_text(st.session_state.answers)

        with st.container(border=True):
            st.subheader("🧠 유쾌한 동물 심리학자가 분석 중이에요... 🐾")
            placeholder = st.empty()

            with st.spinner("결과를 만들고 있어요... 잠깐만요! 🌿"):
                full_text = ""
                try:
                    for token in stream_ai_result(user_text):
                        full_text += token
                        placeholder.markdown(full_text)
                        time.sleep(0.02)  # typing effect
                    st.session_state.ai_result = full_text
                    st.session_state.has_result = True
                except Exception as e:
                    st.error(f"AI 분석 중 오류가 발생했습니다: {e}")

# -----------------------------
# 결과 표시 (테두리 + 공유 버튼 + 클립보드 복사)
# -----------------------------
if st.session_state.has_result and st.session_state.ai_result:
    st.write("")
    with st.container(border=True):
        st.subheader("🌿 당신의 심리테스트 결과")
        st.markdown(st.session_state.ai_result)

        st.divider()

        if st.button("결과 공유하기", use_container_width=True):
            copy_to_clipboard(st.session_state.ai_result)
            st.success("클립보드에 복사했어요! 📋✨ (붙여넣기 해보세요)")
