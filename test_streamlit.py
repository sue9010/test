import streamlit as st
import pandas as pd
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. Page Configuration (기본 설정)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="생산 요청서 (COX ERP)",
    page_icon="🏭",
    layout="centered"  # 폼 입력이므로 중앙 정렬이 깔끔함
)

# -----------------------------------------------------------------------------
# 2. Session State (데이터 임시 저장소)
# -----------------------------------------------------------------------------
if 'requests' not in st.session_state:
    st.session_state.requests = []

# -----------------------------------------------------------------------------
# 3. Helper Functions (스타일 및 유틸리티)
# -----------------------------------------------------------------------------
def get_status_color(status):
    colors = {
        "준비": "gray",
        "생산중": "blue",
        "대기": "orange",
        "완료": "green",
        "중지": "red"
    }
    return colors.get(status, "gray")

# -----------------------------------------------------------------------------
# 4. Main UI - Production Request Form
# -----------------------------------------------------------------------------
st.title("🏭 생산 요청서 작성")
st.markdown("---")

# 기존 PyQt 팝업의 기능을 Streamlit Form으로 구현
with st.form("production_form", clear_on_submit=False):
    
    # [섹션 1] 기본 정보 (Header)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("기본 정보")
        request_no = st.text_input("의뢰 번호 (자동 생성)", value=f"REQ-{datetime.now().strftime('%Y%m%d')}-001", disabled=True)
        client = st.text_input("거래처명", placeholder="거래처 이름을 입력하세요")
    
    with col2:
        st.subheader("일정 정보")
        req_date = st.date_input("의뢰일", value=datetime.now())
        exp_date = st.date_input("출고 예정일", value=None)

    st.markdown("") # 간격

    # [섹션 2] 제품 상세 (Product Card 개념)
    st.info("📦 제품 상세 정보")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        model = st.selectbox("제품 모델", ["선택하세요", "MODEL-A (Standard)", "MODEL-B (Pro)", "MODEL-C (Lite)"])
    with c2:
        quantity = st.number_input("수량", min_value=1, value=10)
    with c3:
        lens_supplier = st.selectbox("렌즈 공급사", ["자사", "공급사 A", "공급사 B"])

    # [섹션 3] 상세 사양 (Details)
    st.markdown("##### 상세 사양")
    details = st.text_area("제품 사양 (Details)", height=100, placeholder="- 사양 1\n- 사양 2")
    
    # [섹션 4] 추가 요청 및 파일 (Accordion 사용)
    with st.expander("➕ 추가 요청 사항 및 첨부파일", expanded=True):
        other_requests = st.text_area("기타 요청사항", height=80)
        uploaded_file = st.file_uploader("참고 도면/문서 첨부", type=['pdf', 'png', 'jpg', 'xlsx'])
    
    # [섹션 5] 관리자 메모 (특이사항)
    special_notes = st.text_input("⚠️ 특이사항 (관리자용)", placeholder="주의가 필요한 사항을 입력하세요")

    # 버튼 영역
    st.markdown("---")
    submitted = st.form_submit_button("✅ 요청서 등록", type="primary", use_container_width=True)

    if submitted:
        if not client or model == "선택하세요":
            st.error("거래처명과 모델명은 필수 입력 항목입니다.")
        else:
            # 데이터 저장 로직 (실제로는 Supabase에 insert)
            new_req = {
                "번호": request_no,
                "거래처": client,
                "모델": model,
                "수량": quantity,
                "상태": "준비",
                "날짜": str(req_date)
            }
            st.session_state.requests.append(new_req)
            st.success(f"'{client}' 건의 생산 요청이 등록되었습니다!")
            st.balloons()

# -----------------------------------------------------------------------------
# 5. Data Preview (등록된 목록 확인용)
# -----------------------------------------------------------------------------
if st.session_state.requests:
    st.markdown("### 📋 최근 등록된 요청 목록")
    df = pd.DataFrame(st.session_state.requests)
    st.dataframe(
        df, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "상태": st.column_config.TextColumn(
                "상태",
                help="현재 진행 상태",
                validate="^(준비|생산중|완료)$"
            )
        }
    )
