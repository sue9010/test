import streamlit as st
import pandas as pd
from datetime import datetime, date
import time
import random

# -----------------------------------------------------------------------------
# 1. Config & Styles
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="COX Production Manager", page_icon="🏭")

# 커스텀 CSS (PyQt의 다크 테마 느낌 구현)
st.markdown("""
<style>
    /* 카드 스타일 (BasePopup 대체) */
    .card {
        background-color: #262730;
        border: 1px solid #3d3d3d;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    /* 상태 배지 */
    .badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.85em;
        color: white;
    }
    .badge-ready { background-color: #757575; }
    .badge-prod { background-color: #2196F3; }
    .badge-hold { background-color: #FF9800; }
    .badge-done { background-color: #4CAF50; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Mock Data Manager (DB 대체)
# -----------------------------------------------------------------------------
if 'data' not in st.session_state:
    # 초기 샘플 데이터 생성
    st.session_state.data = [
        {
            "id": 1, "request_no": "REQ-241125-001", "client": "알파광학", "model": "LEN-500X", 
            "quantity": 50, "status": "준비", "request_date": "2024-11-25", "expected_date": None,
            "details": "UV 코팅 필수, 개별 포장", "serials": [], "memo": []
        },
        {
            "id": 2, "request_no": "REQ-241125-002", "client": "베타시스템", "model": "CAM-LENS-A", 
            "quantity": 100, "status": "생산중", "request_date": "2024-11-20", "expected_date": "2024-11-30",
            "details": "정밀 공차 적용", "serials": [{"seq": 1, "sn": "SN001", "done": True}], "memo": [{"user": "관리자", "msg": "자재 입고 완료", "time": "11/21 10:00"}]
        },
        {
            "id": 3, "request_no": "REQ-241124-005", "client": "감마테크", "model": "FILTER-PRO", 
            "quantity": 30, "status": "완료", "request_date": "2024-11-15", "expected_date": "2024-11-18",
            "details": "", "serials": [], "memo": []
        }
    ]

# 데이터 헬퍼 함수
def get_all_requests():
    return st.session_state.data

def get_request_by_no(req_no):
    for row in st.session_state.data:
        if row['request_no'] == req_no:
            return row
    return None

def update_request_status(req_no, status, extra={}):
    row = get_request_by_no(req_no)
    if row:
        row['status'] = status
        row.update(extra)
        st.toast(f"상태가 '{status}'(으)로 변경되었습니다.", icon="✅")

def add_memo(req_no, user, msg):
    row = get_request_by_no(req_no)
    if row:
        row['memo'].append({"user": user, "msg": msg, "time": datetime.now().strftime("%m/%d %H:%M")})

# -----------------------------------------------------------------------------
# 3. Views (화면 구성요소)
# -----------------------------------------------------------------------------

def view_dashboard():
    """📊 대시보드 뷰"""
    st.header("📊 생산 현황 대시보드")
    
    df = pd.DataFrame(get_all_requests())
    
    # 1. KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    total = len(df)
    ready = len(df[df['status'] == '준비'])
    prod = len(df[df['status'] == '생산중'])
    done = len(df[df['status'] == '완료'])
    
    col1.metric("전체 요청", f"{total}건")
    col2.metric("준비 대기", f"{ready}건", delta_color="off")
    col3.metric("생산 진행중", f"{prod}건", delta_color="normal")
    col4.metric("금주 완료", f"{done}건", delta_color="inverse")
    
    st.divider()
    
    # 2. Charts & Recent
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("상태별 분포")
        if not df.empty:
            status_counts = df['status'].value_counts()
            st.bar_chart(status_counts, color="#2eaadc")
    
    with c2:
        st.subheader("최근 활동 로그")
        # 가상의 로그 데이터
        st.info("ℹ️ 11/25 14:00 - [베타시스템] 생산 시작됨\n\nℹ️ 11/25 10:30 - [감마테크] 출고 완료 처리됨")

def view_table_list():
    """📋 테이블 리스트 뷰"""
    st.header("📋 프로젝트 목록 (Table View)")
    
    df = pd.DataFrame(get_all_requests())
    
    # DataFrame 표시 설정
    # use_container_width=True로 꽉 차게, on_select로 클릭 이벤트 감지
    
    # 보기 좋게 컬럼 정리
    display_df = df[['request_no', 'status', 'client', 'model', 'quantity', 'request_date', 'expected_date']]
    display_df.columns = ['요청번호', '상태', '거래처', '모델', '수량', '의뢰일', '출고예정일']
    
    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",  # 행 선택 시 리런
        column_config={
            "상태": st.column_config.TextColumn(
                "상태",
                help="현재 진행 상태",
                validate="^(준비|생산중|완료)$"
            ),
            "수량": st.column_config.ProgressColumn(
                "수량", format="%d", min_value=0, max_value=200
            )
        }
    )
    
    # 행을 클릭했을 때 로직
    if len(event.selection.rows) > 0:
        selected_idx = event.selection.rows[0]
        selected_req_no = df.iloc[selected_idx]['request_no']
        
        # 세션에 선택된 ID 저장하고 리런 -> 상세 페이지로 이동
        st.session_state['selected_req_no'] = selected_req_no
        st.rerun()

def view_production_popup(req_no):
    """🏭 생산 팝업 (Detail View)"""
    data = get_request_by_no(req_no)
    
    if not data:
        st.error("데이터를 찾을 수 없습니다.")
        if st.button("목록으로 돌아가기"):
            del st.session_state['selected_req_no']
            st.rerun()
        return

    # --- Header ---
    c_back, c_title, c_status = st.columns([1, 4, 1])
    if c_back.button("⬅ 목록"):
        del st.session_state['selected_req_no']
        st.rerun()
    
    c_title.markdown(f"## {data['request_no']} / {data['client']}")
    
    # 상태별 배지 색상 매핑
    badge_color = {
        "준비": "badge-ready", "생산중": "badge-prod", "완료": "badge-done"
    }.get(data['status'], "badge-ready")
    
    c_status.markdown(f'<span class="badge {badge_color}">{data["status"]}</span>', unsafe_allow_html=True)

    st.divider()

    # --- Main Content (Grid Layout) ---
    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        # 1. Product Card Info
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📦 제품 상세 정보")
        f1, f2 = st.columns(2)
        f1.text_input("모델명", value=data['model'], disabled=True)
        f2.number_input("수량", value=data['quantity'], disabled=True)
        st.text_area("사양 (Details)", value=data['details'], height=100, disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. Production Actions (상태에 따라 UI 변경)
        st.subheader("⚙️ 생산 관리")
        
        if data['status'] == "준비":
            with st.container(border=True):
                st.info("현재 '준비' 상태입니다. 생산 일정을 입력하고 시작하세요.")
                date_val = st.date_input("출고 예정일", value=date.today())
                if st.button("🚀 생산 시작 (Start)", type="primary", use_container_width=True):
                    update_request_status(req_no, "생산중", {"expected_date": str(date_val)})
                    st.rerun()
        
        elif data['status'] == "생산중":
            with st.container(border=True):
                st.success(f"생산 진행 중 (예정일: {data['expected_date']})")
                
                # 시리얼 번호 입력 (Data Editor)
                st.markdown("##### 🔢 시리얼 번호 입력")
                
                # 기존 시리얼 데이터가 없으면 템플릿 생성
                if not data['serials']:
                    init_df = pd.DataFrame([{
                        "No": i+1, "Serial": "", "Note": "", "Check": False
                    } for i in range(data['quantity'])])
                else:
                    init_df = pd.DataFrame(data['serials'])
                
                edited_df = st.data_editor(
                    init_df, 
                    hide_index=True, 
                    use_container_width=True,
                    num_rows="fixed",
                    column_config={
                        "Check": st.column_config.CheckboxColumn("완료", width="small")
                    }
                )
                
                # 하단 버튼 그룹
                b1, b2, b3 = st.columns(3)
                if b1.button("임시 저장"):
                    data['serials'] = edited_df.to_dict('records')
                    st.toast("시리얼 번호가 저장되었습니다.")
                
                if b2.button("⛔ 중지 (Hold)"):
                    update_request_status(req_no, "중지")
                    st.rerun()

                if b3.button("✅ 생산 완료 (Finish)", type="primary"):
                    # 실제로는 Validation 로직 필요
                    data['serials'] = edited_df.to_dict('records')
                    update_request_status(req_no, "완료", {"out_date": str(date.today())})
                    st.balloons()
                    time.sleep(1)
                    st.rerun()

        elif data['status'] == "완료":
             with st.container(border=True):
                st.info(f"생산이 완료되었습니다. (출고일: {data.get('out_date')})")
                if st.button("🔄 상태 되돌리기 (Re-open)"):
                    update_request_status(req_no, "생산중")
                    st.rerun()

    with col_right:
        # 3. Memos (Chat Style)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("💬 메모 및 이력")
        
        # 메모 표시 영역
        memo_container = st.container(height=400)
        with memo_container:
            if not data['memo']:
                st.caption("작성된 메모가 없습니다.")
            for m in data['memo']:
                with st.chat_message("user"):
                    st.write(f"**{m['user']}** ({m['time']})")
                    st.write(m['msg'])
        
        # 메모 입력
        with st.form("memo_form", clear_on_submit=True):
            new_msg = st.text_area("새 메모", placeholder="내용을 입력하세요...")
            if st.form_submit_button("등록"):
                if new_msg:
                    add_memo(req_no, "현재사용자", new_msg)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. Main App Router
# -----------------------------------------------------------------------------
def main():
    # 사이드바 네비게이션
    st.sidebar.title("COX ERP")
    
    # 만약 상세 페이지 모드라면(req_no가 선택되어 있다면) 사이드바 메뉴는 단순화
    if 'selected_req_no' in st.session_state:
        st.sidebar.info("현재 상세 보기 중입니다.")
        if st.sidebar.button("📋 목록으로 돌아가기"):
            del st.session_state['selected_req_no']
            st.rerun()
            
        # 상세 페이지 렌더링
        view_production_popup(st.session_state['selected_req_no'])
        
    else:
        # 기본 메뉴
        menu = st.sidebar.radio("메뉴 이동", ["대시보드", "생산 목록 (Table)"])
        
        if menu == "대시보드":
            view_dashboard()
        elif menu == "생산 목록 (Table)":
            view_table_list()

    # 사이드바 하단 정보
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Ver 1.0.0 | Dev Mode")

if __name__ == "__main__":
    main()
