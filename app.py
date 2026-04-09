# ============================================================
# 사내 정보 챗봇 - 메인 앱 파일
# Streamlit(화면)과 Google Gemini API(AI)를 연결합니다.
# ============================================================

import streamlit as st          # 웹 화면을 만들어주는 라이브러리
import google.generativeai as genai  # Google Gemini AI를 사용하는 라이브러리
import os                        # 파일 경로 등 운영체제 기능을 쓸 때 사용

# ============================================================
# [1단계] 회사 규정 파일 읽기
# 같은 폴더에 있는 'company_rules.md' 파일을 불러옵니다.
# 이 내용이 AI의 "지식"이 됩니다.
# ============================================================

@st.cache_data  # 한 번 읽은 파일은 캐시에 저장해서 속도를 높입니다
def load_company_rules():
    """company_rules.md 파일을 읽어서 텍스트로 반환하는 함수"""
    file_path = "company_rules.md"
    
    # 파일이 존재하는지 먼저 확인합니다
    if not os.path.exists(file_path):
        return None
    
    # 파일을 열어서 내용을 읽습니다 (한국어 처리를 위해 utf-8 인코딩 사용)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content


# ============================================================
# [2단계] AI에게 줄 "역할 지침" 만들기 (시스템 프롬프트)
# AI가 어떻게 행동해야 하는지 규칙을 정해줍니다.
# 핵심 규칙: 파일에 없는 내용은 절대 답변하지 않도록 합니다.
# ============================================================

def build_system_prompt(rules_content: str) -> str:
    """회사 규정 내용을 바탕으로 AI 지침(시스템 프롬프트)을 만드는 함수"""
    return f"""당신은 사내 규정 안내 챗봇입니다.
아래의 [회사 규정] 내용만을 근거로 직원들의 질문에 답변해야 합니다.

[중요 규칙]
1. 반드시 아래 [회사 규정] 내용에 있는 정보만 사용해서 답변하세요.
2. 질문에 대한 답이 [회사 규정]에 없으면, 어떤 경우에도 "죄송합니다. 해당 내용은 규정에서 찾을 수 없습니다."라고만 답변하세요.
3. 외부 지식이나 일반적인 상식으로 답변을 추측하거나 보충하지 마세요.
4. 답변할 때는 어느 규정 항목을 근거로 했는지 간략히 언급해 주세요.
5. 친절하고 정중한 말투를 사용하세요.

[회사 규정]
{rules_content}
"""


# ============================================================
# [3단계] 화면(UI) 구성하기
# 웹 페이지의 제목, 사이드바, 채팅창 등을 만듭니다.
# ============================================================

# 브라우저 탭에 표시될 제목과 아이콘 설정
st.set_page_config(
    page_title="사내 규정 챗봇",
    page_icon="🏢",
    layout="centered"
)

# 메인 화면 제목
st.title("🏢 사내 규정 챗봇")
st.caption("회사 규정에 대해 궁금한 점을 질문해 보세요.")

# ── 사이드바 구성 ──────────────────────────────────────────
# 사이드바: 화면 왼쪽에 나타나는 설정 패널입니다
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 사용자가 Gemini API 키를 직접 입력하는 칸
    # type="password"로 설정하면 입력한 키가 별표(**)로 가려집니다
    api_key = st.text_input(
        "🔑 Gemini API 키 입력",
        type="password",
        placeholder="여기에 API 키를 붙여넣으세요",
        help="Google AI Studio(aistudio.google.com)에서 무료로 발급받을 수 있습니다."
    )
    
    # API 키 발급 안내 링크
    st.markdown("[🔗 Gemini API 키 무료 발급받기](https://aistudio.google.com/app/apikey)")
    
    st.divider()  # 구분선
    
    # 대화 초기화 버튼: 채팅 기록을 모두 지웁니다
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []  # 저장된 대화 기록을 비웁니다
        st.rerun()                        # 화면을 새로 고침합니다
    
    st.divider()
    st.markdown("**사용 방법**")
    st.markdown("""
    1. Gemini API 키를 입력하세요  
    2. `company_rules.md` 파일을 앱과 같은 폴더에 두세요  
    3. 채팅창에 질문을 입력하세요
    """)


# ============================================================
# [4단계] 회사 규정 파일 불러오기 및 오류 처리
# ============================================================

rules_content = load_company_rules()

# 파일을 찾지 못했을 때 사용자에게 안내 메시지를 보여줍니다
if rules_content is None:
    st.error(
        "⚠️ `company_rules.md` 파일을 찾을 수 없습니다.  \n"
        "앱 파일(`app.py`)과 같은 폴더에 `company_rules.md`를 넣어주세요."
    )
    st.stop()  # 파일이 없으면 여기서 앱 실행을 멈춥니다


# ============================================================
# [5단계] 대화 기록 관리
# Streamlit은 화면이 새로 그려질 때마다 코드를 처음부터 다시 실행합니다.
# 'st.session_state'를 사용하면 새로 고침 후에도 데이터를 유지할 수 있습니다.
# ============================================================

# 대화 기록이 아직 없으면 빈 목록으로 초기화합니다
if "messages" not in st.session_state:
    st.session_state.messages = []

# 저장된 대화 기록을 화면에 순서대로 표시합니다
for message in st.session_state.messages:
    # role이 "user"면 사용자 말풍선, "assistant"면 AI 말풍선으로 표시됩니다
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# [6단계] 사용자 입력 처리 및 AI 답변 생성
# ============================================================

# 화면 하단에 채팅 입력창을 만듭니다
user_input = st.chat_input("규정에 대해 궁금한 점을 질문하세요...")

# 사용자가 메시지를 입력했을 때만 아래 코드가 실행됩니다
if user_input:
    
    # ── API 키 확인 ──────────────────────────────────────────
    # API 키가 없으면 경고를 표시하고 진행을 멈춥니다
    if not api_key:
        st.warning("⬅️ 왼쪽 사이드바에서 Gemini API 키를 먼저 입력해 주세요.")
        st.stop()
    
    # ── 사용자 메시지를 화면에 표시하고 기록에 저장 ──────────
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 대화 기록 목록에 사용자 메시지를 추가합니다
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # ── Gemini AI 연결 및 답변 생성 ──────────────────────────
    try:
        # API 키로 Gemini 서비스에 연결합니다
        genai.configure(api_key=api_key)
        
        # 사용할 AI 모델을 선택합니다 (gemini-2.0-flash: 빠르고 무료 한도가 넉넉함)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=build_system_prompt(rules_content)  # AI 역할 지침 전달
        )
        
        # 지금까지의 대화 기록을 Gemini가 이해하는 형식으로 변환합니다
        # (Gemini는 "user"와 "model"이라는 역할명을 사용합니다)
        chat_history = []
        for msg in st.session_state.messages[:-1]:  # 방금 입력한 메시지 제외
            role = "model" if msg["role"] == "assistant" else "user"
            chat_history.append({"role": role, "parts": [msg["content"]]})
        
        # 대화 세션을 시작하고 메시지를 전송합니다
        chat_session = model.start_chat(history=chat_history)
        
        # AI 답변을 스트리밍(글자가 하나씩 나타나는 방식)으로 받습니다
        with st.chat_message("assistant"):
            # st.write_stream을 사용하면 답변이 실시간으로 화면에 표시됩니다
            response_stream = chat_session.send_message(
                user_input,
                stream=True  # 스트리밍 모드 활성화
            )
            full_response = st.write_stream(
                chunk.text for chunk in response_stream
                if hasattr(chunk, "text") and chunk.text
            )
        
        # AI 답변도 대화 기록에 저장합니다 (다음 질문 때 문맥으로 활용)
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
    
    # ── 오류 처리: 문제가 생겼을 때 사용자에게 알려줍니다 ────
    except Exception as e:
        error_msg = str(e)
        
        # API 키가 잘못된 경우 친절한 안내 메시지를 표시합니다
        if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            st.error("❌ API 키가 올바르지 않습니다. 사이드바에서 키를 다시 확인해 주세요.")
        else:
            st.error(f"❌ 오류가 발생했습니다: {error_msg}")
