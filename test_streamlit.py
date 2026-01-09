import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

# -----------------------------------------------------------------------------
# 1. Mock Data Manager (기존 DataManager 역할을 하는 가상 클래스)
# -----------------------------------------------------------------------------
class MockDataManager:
    def __init__(self):
        # 세션 스테이트에 데이터가 없으면 초기화
        if 'db_data' not in st.session_state:
            st.session_state.db_data = {
                "REQ-20241125-001": {
                    "request_no": "REQ-20241125-001",
                    "client": "알파광학",
                    "model": "LEN-500X (Pro)",
                    "quantity": 50,
                    "details": "고굴절 렌즈 적용\nUV 코팅 필수",
                    "request_date": "2024-11-25",
                    "expected_date": None,
                    "out_date": None,
                    "status": "준비",  # 준비, 생산중, 대기, 중지, 완료
                    "lens_supplier": "자사",
                    "memo": [], # List of {user, content, time}
                    "serials": [] # List of {seq, serial_no}
                }
            }

    def get_request(self, req_no):
        return st.session_state.db_data.get(req_no, {})

    def update_status(self, req_no, new_status, extra_data=None):
        if req_no in st.session_state.db_data:
            st.session_state.db_data[req_no]['status'] = new_status
            if extra_data:
                st.session_state.db_data[req_no].update(extra_data)
            return True, f"상태가 '{new_status}'(으)로 변경되었습니다."
        return False, "데이터를 찾을 수 없습니다."

    def add_memo(self, req_no, user, content):
        if req_no in st.session_state.db_data:
            memo_entry = {
                "user": user,
                "content": content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.db_data[req_no]['memo'].append(memo_entry)
            return True
        return False

# -----------------------------------------------------------------------------
# 2. Page Config & CSS (BasePopup 스타일 이식)
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="생산 관리 - COX ERP", page_icon="🏭")

# Custom CSS for Dark Theme & Card Style
st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp {
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    
    /* Product Card 스타일 (BasePopup 느낌) */
    .product-card {
        background-color: #2d2d2d;
        border: 1px solid #3d3d3d;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 상태 배지 스타일 */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.9em;
    }
    .status-준비 { background-color: #555; color: white; }
    .status-생산중 { background-color: #2196F3; color: white; }
    .status-대기 { background-color: #FF9800; color: white; }
    .status-중지 { background-color: #F44336; color: white; }
    .status-완료 { background-color: #4CAF50; color: white; }

    /* 입력 필드 스타일 조정 */
    .stTextInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #333 !important;
        color: white !important;
        border: 1px solid #444 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. Main Application Logic
# -----------------------------------------------------------------------------

def main():
    dm = MockDataManager()
    
    # URL 파라미터나 사이드바에서 요청 번호 선택 시뮬레이션
    with st.sidebar:
        st.title("🏭 COX ERP")
        req_id = st.text_input("요청 번호 검색", value="REQ-20241125-001")
        st.markdown("---")
        st.caption("개발 모드 설정")
        current_user = st.text_input("작업자 명", value="관리자")

    # 데이터 가져오기
    data = dm.get_request(req_id)
    
    if not data:
        st.error("해당 요청 번호의 데이터를 찾을 수 없습니다.")
        return

    # --- Header Area (TitleBar 역할) ---
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"## 📄 생산 요청서: `{data['request_no']}`")
    with col_h2:
        status = data['status']
        st.markdown(f'<div style="text-align:right;"><span class="status-badge status-{status}">{status}</span></div>', unsafe_allow_html=True)

    st.markdown("---")

    # --- Main Content Area ---
    # Layout: Left (Info & Actions) | Right (Details & Logs)
    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        # [Component] Product Card (기본 정보)
        st.markdown('<div class="product-card">', unsafe_allow_html=True)
        st.subheader("📦 제품 정보")
        
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("거래처", value=data['client'], disabled=True)
            st.text_input("제품 모델", value=data['model'], disabled=True)
        with c2:
            st.date_input("의뢰일", value=datetime.strptime(data['request_date'], "%Y-%m-%d"), disabled=True)
            st.number_input("수량", value=data['quantity'], disabled=True)
        
        st.text_area("제품 사양 (Details)", value=data['details'], height=80, disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [Component] Action Panel (상태별 버튼 로직)
        st.subheader("⚙️ 생산 관리 (Actions)")
        
        if status == "준비":
            st.info("생산 일정을 등록하여 작업을 시작하세요.")
            with st.form("schedule_form"):
                exp_date = st.date_input("출고 예정일 설정", min_value=date.today())
                if st.form_submit_button("🚀 생산 시작 (Schedule)", use_container_width=True, type="primary"):
                    dm.update_status(req_id, "생산중", {"expected_date": str(exp_date)})
                    st.rerun()

        elif status in ["생산중", "대기", "중지"]:
            c_act1, c_act2, c_act3 = st.columns(3)
            
            # 상태 변경 버튼들
            if status == "생산중":
                if c_act1.button("⏸ 대기", use_container_width=True):
                    dm.update_status(req_id, "대기")
                    st.rerun()
                if c_act2.button("⛔ 중지", use_container_width=True):
                    dm.update_status(req_id, "중지")
                    st.rerun()
            else:
                if c_act1.button("▶️ 재개", use_container_width=True, type="primary"):
                    dm.update_status(req_id, "생산중")
                    st.rerun()

            # 시리얼 입력 (ProductionPopup.open_serial_input 대체)
            st.markdown("#### 🔢 시리얼 번호 관리")
            st.caption(f"목표 수량: {data['quantity']}개")
            
            # Data Editor for Serials
            current_serials = data.get('serials', [])
            
            # 빈 시리얼 데이터프레임 생성 (수량만큼)
            if not current_serials:
                df_template = pd.DataFrame({
                    "Seq": range(1, data['quantity'] + 1),
                    "Serial No": [""] * data['quantity'],
                    "Note": [""] * data['quantity'],
                    "Completed": [False] * data['quantity']
                })
            else:
                df_template = pd.DataFrame(current_serials)

            edited_df = st.data_editor(
                df_template, 
                hide_index=True, 
                use_container_width=True,
                column_config={
                    "Completed": st.column_config.CheckboxColumn("완료", help="작업 완료 여부")
                }
            )

            # 완료 처리
            if st.button("✅ 생산 완료 처리 (Finalize)", type="primary", use_container_width=True):
                # 모든 시리얼이 입력되었는지 체크하는 로직 등을 여기에 추가
                dm.update_status(req_id, "완료", {"serials": edited_df.to_dict('records'), "out_date": str(date.today())})
                st.success("생산이 완료되었습니다!")
                time.sleep(1)
                st.rerun()

        elif status == "완료":
            st.success(f"생산이 완료된 건입니다. (출고일: {data.get('out_date')})")
            if st.button("내역 수정 (Re-open)"):
                dm.update_status(req_id, "생산중")
                st.rerun()

    with right_col:
        # [Component] Memo & Logs (MemoWidget 대체)
        st.markdown('<div class="product-card">', unsafe_allow_html=True)
        st.subheader("💬 메모 및 로그")
        
        # 채팅 UI 스타일로 메모 표시
        memo_container = st.container(height=400)
        with memo_container:
            if not data['memo']:
                st.info("작성된 메모가 없습니다.")
            for m in data['memo']:
                with st.chat_message("user", avatar="👤"):
                    st.write(f"**{m['user']}** ({m['timestamp']})")
                    st.write(m['content'])
        
        # 새 메모 입력
        with st.form("new_memo"):
            new_content = st.text_area("새 메모 작성", placeholder="특이사항을 입력하세요...")
            if st.form_submit_button("등록"):
                if new_content:
                    dm.add_memo(req_id, current_user, new_content)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
