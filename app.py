import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import time

# ページ設定
st.set_page_config(
    page_title="Creator's Cockpit",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSSスタイリング
def inject_custom_css():
    st.markdown("""
    <style>
    /* メイン背景とダークテーマ */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #0E1117 50%, #000000 100%);
        color: #e0e0e0;
    }
    
    /* サイドバーのスタイリング */
    [data-testid="stSidebar"] {
        background-color: rgba(14, 17, 23, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0, 255, 255, 0.2);
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        background-color: transparent;
    }
    
    /* メインコンテンツエリア */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* タイトルとヘッダーのスタイリング */
    h1, h2, h3 {
        color: #00FFFF !important;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* カスタムコンテナ（ガラスモーフィズム効果） */
    .glass-container {
        background: rgba(14, 17, 23, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.05);
        margin-bottom: 1rem;
    }
    
    /* セクションタイトル */
    .section-title {
        color: #00FFFF;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    
    /* クイックツールボタン */
    .skill-button {
        background: rgba(14, 17, 23, 0.9);
        border: 1px solid rgba(0, 255, 255, 0.5);
        color: #e0e0e0;
        padding: 0.75rem 1.5rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        transition: all 0.3s;
        cursor: pointer;
        margin: 0.25rem;
    }
    
    .skill-button:hover {
        border-color: #00FFFF;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.4);
        background: rgba(0, 255, 255, 0.1);
    }
    
    /* タスクアイテム */
    .task-item {
        background: rgba(0, 0, 0, 0.4);
        border-left: 2px solid #00FFFF;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-radius: 4px;
        transition: all 0.3s;
    }
    
    .task-item:hover {
        background: rgba(0, 255, 255, 0.05);
    }
    
    .task-item.completed {
        opacity: 0.5;
        border-left-color: #666;
    }
    
    /* タグ */
    .quest-tag {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border: 1px solid;
        border-radius: 4px;
        font-size: 0.75rem;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        margin-left: 0.5rem;
    }
    
    .tag-crafting {
        color: #ff6b6b;
        border-color: rgba(255, 107, 107, 0.5);
        background: rgba(255, 107, 107, 0.2);
    }
    
    .tag-dev {
        color: #4dabf7;
        border-color: rgba(77, 171, 247, 0.5);
        background: rgba(77, 171, 247, 0.2);
    }
    
    .tag-grinding {
        color: #51cf66;
        border-color: rgba(81, 207, 102, 0.5);
        background: rgba(81, 207, 102, 0.2);
    }
    
    /* プログレスバー */
    .progress-container {
        background: #1a1a1a;
        border: 1px solid #333;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        position: relative;
    }
    
    .progress-fill {
        background: linear-gradient(90deg, #2563eb 0%, #00FFFF 100%);
        height: 100%;
        transition: width 0.3s;
    }
    
    /* ステータスバッジ */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border: 1px solid;
        border-radius: 4px;
        font-size: 0.75rem;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
    }
    
    .status-live {
        color: #10b981;
        border-color: rgba(16, 185, 129, 0.5);
        box-shadow: 0 0 5px #10b981;
    }
    
    .status-crafting {
        color: #fbbf24;
        border-color: rgba(251, 191, 36, 0.5);
    }
    
    .status-pending {
        color: #9ca3af;
        border-color: rgba(156, 163, 175, 0.5);
    }
    
    /* システムログ */
    .system-log {
        background: #05070A;
        border: 1px solid #1a1a1a;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.75rem;
        color: rgba(16, 185, 129, 0.8);
        border-radius: 4px;
        max-height: 200px;
        overflow-y: auto;
        line-height: 1.6;
    }
    
    /* ヘッダーHUD */
    .header-hud {
        background: rgba(0, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(0, 255, 255, 0.3);
        padding: 1.5rem;
        margin-bottom: 2rem;
        position: relative;
    }
    
    .header-hud::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 8px;
        height: 8px;
        border-top: 1px solid #00FFFF;
        border-left: 1px solid #00FFFF;
    }
    
    .header-hud::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 8px;
        height: 8px;
        border-top: 1px solid #00FFFF;
        border-right: 1px solid #00FFFF;
    }
    
    /* テキストカラー */
    .text-cyan {
        color: #00FFFF !important;
    }
    
    .text-green {
        color: #10b981 !important;
    }
    
    .text-blue {
        color: #4dabf7 !important;
    }
    
    /* テーブルスタイリング */
    .dataframe {
        background: rgba(14, 17, 23, 0.8);
        color: #e0e0e0;
    }
    
    .dataframe th {
        background: rgba(0, 255, 255, 0.1);
        color: #00FFFF;
        border-bottom: 1px solid rgba(0, 255, 255, 0.3);
    }
    
    .dataframe td {
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* ボタンスタイリング */
    .stButton > button {
        background: rgba(14, 17, 23, 0.9);
        border: 1px solid rgba(0, 255, 255, 0.5);
        color: #00FFFF;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        border-color: #00FFFF;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.4);
        background: rgba(0, 255, 255, 0.1);
    }
    
    /* 入力フィールド */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: rgba(14, 17, 23, 0.8);
        color: #e0e0e0;
        border: 1px solid rgba(0, 255, 255, 0.3);
    }
    
    /* チェックボックス */
    .stCheckbox > label {
        color: #00FFFF;
    }
    
    /* メトリクス */
    [data-testid="stMetricValue"] {
        color: #00FFFF;
    }
    
    [data-testid="stMetricLabel"] {
        color: #9ca3af;
    }
    </style>
    """, unsafe_allow_html=True)

# Google Sheets認証情報の取得
@st.cache_resource
def init_gsheet():
    """Google Sheetsへの接続を初期化"""
    try:
        # Streamlit Secretsから認証情報を取得
        creds_dict = {
            "type": st.secrets["gcp_service_account"]["type"],
            "project_id": st.secrets["gcp_service_account"]["project_id"],
            "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
            "private_key": st.secrets["gcp_service_account"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["gcp_service_account"]["client_email"],
            "client_id": st.secrets["gcp_service_account"]["client_id"],
            "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
            "token_uri": st.secrets["gcp_service_account"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
        }
        
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        gc = gspread.authorize(credentials)
        
        # スプレッドシートIDを取得
        spreadsheet_id = st.secrets["spreadsheet"]["id"]
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        return spreadsheet
    except Exception as e:
        st.error(f"Google Sheetsへの接続エラー: {str(e)}")
        st.stop()

# スプレッドシート接続
spreadsheet = init_gsheet()

# シート取得関数（リトライロジック付き）
def get_sheet_with_retry(sheet_name, max_retries=3, retry_delay=2):
    """指定されたシートを取得（リトライロジック付き）"""
    import time
    for attempt in range(max_retries):
        try:
            return spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"シート '{sheet_name}' が見つかりません。")
            return None
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429:  # Rate limit exceeded
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    st.warning(f"APIレート制限に達しました。{wait_time}秒後に再試行します... (試行 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    st.error(f"APIレート制限に達しました。しばらく待ってから再度お試しください。")
                    st.info("💡 ヒント: ページをリロードするか、数分待ってから再度アクセスしてください。")
                    return None
            else:
                st.error(f"シート '{sheet_name}' の取得エラー: {str(e)}")
                return None
        except Exception as e:
            st.error(f"シート '{sheet_name}' の取得エラー: {str(e)}")
            return None
    return None

# シート取得関数（後方互換性のため）
def get_sheet(sheet_name):
    """指定されたシートを取得"""
    return get_sheet_with_retry(sheet_name)

# シートデータ取得関数（キャッシュ付き）
@st.cache_data(ttl=30)  # 30秒間キャッシュ
def get_sheet_data(sheet_name):
    """シートの全データを取得（キャッシュ付き）"""
    sheet = get_sheet_with_retry(sheet_name)
    if sheet:
        try:
            return sheet.get_all_values()
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429:
                st.error(f"APIレート制限に達しました。しばらく待ってから再度お試しください。")
                st.info("💡 ヒント: ページをリロードするか、数分待ってから再度アクセスしてください。")
                return []
            else:
                st.error(f"データ取得エラー: {str(e)}")
                return []
        except Exception as e:
            st.error(f"データ取得エラー: {str(e)}")
            return []
    return []

# 現在日時を取得（JST）
def get_now_jst():
    """JSTの現在日時を文字列で返す"""
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')

def get_current_time():
    """現在時刻をHH:MM:SS形式で返す"""
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime('%H:%M:%S')

# システムログの管理
def get_system_log():
    """システムログを取得"""
    if 'system_log' not in st.session_state:
        st.session_state.system_log = [
            f"> [{get_current_time()}] システム起動しました。",
        ]
    return st.session_state.system_log

def add_log_entry(message):
    """システムログにエントリを追加"""
    if 'system_log' not in st.session_state:
        st.session_state.system_log = []
    timestamp = get_current_time()
    st.session_state.system_log.append(f"> [{timestamp}] {message}")
    # ログが長すぎる場合は古いものを削除
    if len(st.session_state.system_log) > 20:
        st.session_state.system_log = st.session_state.system_log[-20:]

# ダッシュボード画面
def show_dashboard():
    # ヘッダーHUD
    st.markdown('<div class="header-hud">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("""
        <h1 style="margin: 0; font-size: 2rem;">Creator's Cockpit</h1>
        <p style="color: #9ca3af; font-size: 0.8rem; letter-spacing: 0.2em; margin: 0;">クリエイター活動管理ツール</p>
        """, unsafe_allow_html=True)
    
    with col2:
        # Daily EXP
        daily_exp = st.session_state.get('daily_exp', 0)
        st.markdown(f"""
        <div style="background: rgba(14, 17, 23, 0.8); padding: 1rem; border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 4px;">
            <div style="color: #00FFFF; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;">今日の達成数</div>
            <div style="color: #fff; font-size: 1.5rem; font-weight: bold;">
                {daily_exp} <span style="color: #10b981; font-size: 0.8rem;">件</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # 前回のレポート出力日時
        last_report_at = "未記録"
        all_data = get_sheet_data("settings")
        if all_data:
            for row in all_data:
                if len(row) >= 2 and row[0] == "last_report_at":
                    last_report_at = row[1] if row[1] else "未記録"
                    break
        
        # 日時を短縮表示（YYYY-MM-DD HH:MM形式）
        display_time = last_report_at
        if last_report_at != "未記録" and len(last_report_at) > 16:
            # YYYY-MM-DD HH:MM:SS から YYYY-MM-DD HH:MM に変換
            try:
                dt = datetime.strptime(last_report_at, '%Y-%m-%d %H:%M:%S')
                display_time = dt.strftime('%Y-%m-%d %H:%M')
            except:
                display_time = last_report_at
        
        st.markdown(f"""
        <div style="background: rgba(14, 17, 23, 0.8); padding: 1rem; border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 4px; text-align: center;">
            <div style="color: #4dabf7; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">前回レポート出力</div>
            <div style="color: #fff; font-size: 1rem; font-family: 'Courier New', monospace; letter-spacing: 0.05em; line-height: 1.4;">{display_time}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # メイングリッドレイアウト
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Active Quests
        st.markdown("""
        <div class="section-title">
            > 未完了タスク_
        </div>
        """, unsafe_allow_html=True)
        
        all_data = get_sheet_data("tasks")
        if all_data:
            if len(all_data) > 1:
                headers = all_data[0]
                rows = all_data[1:]
                
                incomplete_tasks = []
                for i, row in enumerate(rows, start=2):
                    if len(row) > 3 and row[3] == "未":
                        incomplete_tasks.append((i, row))
                
                if incomplete_tasks:
                    for row_num, row in incomplete_tasks[:5]:  # 最大5つ表示
                        while len(row) < len(headers):
                            row.append("")
                        
                        task_id = row[0] if len(row) > 0 else ""
                        title = row[1] if len(row) > 1 else ""
                        category = row[2] if len(row) > 2 else ""
                        status = row[3] if len(row) > 3 else ""
                        memo = row[4] if len(row) > 4 else ""
                        
                        # カテゴリに応じたタグクラス
                        tag_class = "tag-dev"
                        if category == "制作":
                            tag_class = "tag-crafting"
                        elif category == "学習":
                            tag_class = "tag-grinding"
                        
                        tag_text = category
                        
                        st.markdown(f"""
                        <div class="task-item">
                            <div style="display: flex; align-items: start;">
                                <div style="margin-right: 0.5rem;">
                        """, unsafe_allow_html=True)
                        
                        if st.checkbox("", key=f"complete_{row_num}", label_visibility="collapsed"):
                            sheet = get_sheet("tasks")
                            if sheet:
                                sheet.update_cell(row_num, 4, "済")
                                sheet.update_cell(row_num, 7, get_now_jst())
                                # キャッシュをクリア
                                get_sheet_data.clear()
                                add_log_entry(f"タスク完了: {title[:30]}...")
                                st.session_state.daily_exp = st.session_state.get('daily_exp', 0) + 1
                                st.rerun()
                        
                        st.markdown(f"""
                                </div>
                                <div style="flex: 1;">
                                    <div style="color: #e0e0e0; margin-bottom: 0.25rem;">{title}</div>
                                    <span class="quest-tag {tag_class}">[{tag_text}]</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("未完了のタスクはありません。")
            else:
                st.info("タスクがまだ登録されていません。")
        else:
            st.error("タスクシートを読み込めませんでした。")
    
    with col2:
        # Campaign Map Status
        st.markdown("""
        <div class="section-title">
            > プロジェクト一覧_
        </div>
        """, unsafe_allow_html=True)
        
        all_data = get_sheet_data("projects")
        if all_data:
            if len(all_data) > 1:
                rows = all_data[1:]
                
                # テーブルデータを準備
                table_data = []
                for row in rows[:5]:  # 最大5つ表示
                    while len(row) < 8:
                        row.append("")
                    
                    theme = row[1] if len(row) > 1 else ""
                    ptype = row[2] if len(row) > 2 else ""
                    status = row[6] if len(row) > 6 else "進行中"
                    
                    # ステータスに応じた進捗率（簡易版）
                    progress = 0
                    if status == "完了":
                        progress = 100
                    elif status == "進行中":
                        progress = 50
                    else:
                        progress = 25
                    
                    media_type = "ブログ"
                    if ptype == "single":
                        media_type = "Note"
                    elif "スタンプ" in theme or "Stamp" in theme:
                        media_type = "Lineスタンプ"
                    
                    table_data.append({
                        "Media Type": f"[{media_type}]",
                        "Project Name": theme,
                        "Progress": progress,
                        "Status": status
                    })
                
                if table_data:
                    import pandas as pd
                    df = pd.DataFrame(table_data)
                    
                    # カスタム表示
                    for idx, row in df.iterrows():
                        status_class = "status-pending"
                        status_display = row["Status"]
                        if row["Status"] == "完了":
                            status_class = "status-live"
                            status_display = "公開中"
                        elif row["Status"] == "進行中":
                            status_class = "status-crafting"
                            status_display = "制作中"
                        elif row["Status"] == "保留":
                            status_class = "status-pending"
                            status_display = "保留中"
                        
                        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                        with col1:
                            st.markdown(f'<div style="color: #4dabf7;">{row["Media Type"]}</div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown(f'<div style="color: #e0e0e0;">{row["Project Name"]}</div>', unsafe_allow_html=True)
                        with col3:
                            st.markdown(f"""
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="color: #9ca3af; font-size: 0.75rem; width: 40px; text-align: right;">{row["Progress"]}%</span>
                                <div class="progress-container">
                                    <div class="progress-fill" style="width: {row["Progress"]}%;"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with col4:
                            st.markdown(f'<div class="status-badge {status_class}">{status_display}</div>', unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                else:
                    st.info("プロジェクトがまだ登録されていません。")
            else:
                st.info("プロジェクトがまだ登録されていません。")
        else:
            st.error("プロジェクトシートを読み込めませんでした。")
    
    # Save Point // System Log
    st.markdown("""
    <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
        <span>> アクティビティログ_</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        log_entries = get_system_log()
        log_html = '<div class="system-log">'
        for entry in log_entries[-10:]:  # 最新10件
            log_html += f'<p style="margin: 0.25rem 0;">{entry}</p>'
        log_html += '</div>'
        st.markdown(log_html, unsafe_allow_html=True)
    
    with col2:
        if st.button("Note生成", use_container_width=True, type="primary"):
            st.session_state.page = "📝 Note生成"
            add_log_entry("Note生成を開始しました。")
            st.rerun()
    
    # 新規タスク追加（折りたたみ可能）
    with st.expander("➕ 新規タスク追加", expanded=False):
        with st.form("new_task_form"):
            task_title = st.text_input("タスクタイトル", key="new_task_title")
            task_category = st.selectbox(
                "カテゴリ",
                ["制作", "開発", "学習", "事務", "その他"],
                key="new_task_category"
            )
            task_memo = st.text_area("メモ（任意）", key="new_task_memo")
            submitted = st.form_submit_button("追加")
            
            if submitted:
                if task_title:
                    sheet = get_sheet("tasks")
                    if sheet:
                        try:
                            all_data = get_sheet_data("tasks")
                            existing_ids = [int(row[0]) for row in all_data[1:] if row and row[0].isdigit()]
                            new_id = max(existing_ids) + 1 if existing_ids else 1
                        except:
                            new_id = 1
                        
                        new_row = [
                            str(new_id),
                            task_title,
                            task_category,
                            "未",
                            task_memo,
                            get_now_jst(),
                            ""
                        ]
                        sheet.append_row(new_row)
                        # キャッシュをクリア
                        get_sheet_data.clear()
                        add_log_entry(f"タスクを追加: {task_title}")
                        st.success(f"タスク「{task_title}」を追加しました！")
                        st.rerun()
                else:
                    st.warning("タスクタイトルを入力してください。")

# プロジェクト管理画面
def show_projects():
    st.markdown("""
    <h1 style="color: #00FFFF; font-family: 'Courier New', monospace; text-transform: uppercase; letter-spacing: 0.2em;">
        プロジェクト管理
    </h1>
    """, unsafe_allow_html=True)
    
    sheet = get_sheet("projects")
    if not sheet:
        return
    
    with st.expander("➕ 新規プロジェクト追加", expanded=False):
        with st.form("new_project_form"):
            col1, col2 = st.columns(2)
            with col1:
                project_theme = st.text_input("テーマ", key="new_project_theme")
                project_type = st.selectbox("タイプ", ["mix", "single"], key="new_project_type")
            with col2:
                project_blog_url = st.text_input("ブログURL", key="new_project_blog_url")
                project_note_url = st.text_input("Note URL", key="new_project_note_url")
                project_stamp_url = st.text_input("スタンプURL", key="new_project_stamp_url")
            
            submitted = st.form_submit_button("追加")
            
            if submitted:
                if project_theme:
                    sheet = get_sheet("projects")
                    if sheet:
                        try:
                            all_data = get_sheet_data("projects")
                            existing_ids = [int(row[0]) for row in all_data[1:] if row and row[0].isdigit()]
                            new_id = max(existing_ids) + 1 if existing_ids else 1
                        except:
                            new_id = 1
                        
                        new_row = [
                            str(new_id),
                            project_theme,
                            project_type,
                            project_blog_url or "",
                            project_note_url or "",
                            project_stamp_url or "",
                            "進行中",
                            get_now_jst()
                        ]
                        sheet.append_row(new_row)
                        # キャッシュをクリア
                        get_sheet_data.clear()
                        add_log_entry(f"プロジェクトを追加: {project_theme}")
                        st.success(f"プロジェクト「{project_theme}」を追加しました！")
                        st.rerun()
                else:
                    st.warning("テーマを入力してください。")
    
    st.markdown("---")
    st.markdown("""
    <div class="section-title">
        > プロジェクト一覧_
    </div>
    """, unsafe_allow_html=True)
    
    all_data = get_sheet_data("projects")
    if all_data and len(all_data) > 1:
        headers = all_data[0]
        rows = all_data[1:]
        
        for i, row in enumerate(rows, start=2):
            while len(row) < len(headers):
                row.append("")
            
            project_id = row[0] if len(row) > 0 else ""
            theme = row[1] if len(row) > 1 else ""
            ptype = row[2] if len(row) > 2 else ""
            blog_url = row[3] if len(row) > 3 else ""
            note_url = row[4] if len(row) > 4 else ""
            stamp_url = row[5] if len(row) > 5 else ""
            status = row[6] if len(row) > 6 else ""
            updated_at = row[7] if len(row) > 7 else ""
            
            with st.expander(f"📌 {theme} ({ptype}) - {status}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_theme = st.text_input("テーマ", value=theme, key=f"theme_{i}")
                    new_type = st.selectbox("タイプ", ["mix", "single"], 
                                          index=0 if ptype == "mix" else 1, 
                                          key=f"type_{i}")
                    new_status = st.selectbox("ステータス", ["進行中", "完了", "保留"], 
                                            index=["進行中", "完了", "保留"].index(status) if status in ["進行中", "完了", "保留"] else 0,
                                            key=f"status_{i}")
                with col2:
                    new_blog_url = st.text_input("ブログURL", value=blog_url, key=f"blog_{i}")
                    new_note_url = st.text_input("Note URL", value=note_url, key=f"note_{i}")
                    new_stamp_url = st.text_input("スタンプURL", value=stamp_url, key=f"stamp_{i}")
                
                if st.button("更新", key=f"update_{i}"):
                    sheet = get_sheet("projects")
                    if sheet:
                        sheet.update_cell(i, 2, new_theme)
                        sheet.update_cell(i, 3, new_type)
                        sheet.update_cell(i, 4, new_blog_url)
                        sheet.update_cell(i, 5, new_note_url)
                        sheet.update_cell(i, 6, new_stamp_url)
                        sheet.update_cell(i, 7, new_status)
                        sheet.update_cell(i, 8, get_now_jst())
                        # キャッシュをクリア
                        get_sheet_data.clear()
                        add_log_entry(f"プロジェクトを更新: {new_theme}")
                        st.success("プロジェクトを更新しました！")
                        st.rerun()
    else:
        st.info("プロジェクトがまだ登録されていません。")

# 資産・アイデア画面
def show_assets():
    st.markdown("""
    <h1 style="color: #00FFFF; font-family: 'Courier New', monospace; text-transform: uppercase; letter-spacing: 0.2em;">
        資産・アイデア管理
    </h1>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 プロンプト管理", "💭 アイデア箱"])
    
    with tab1:
        st.markdown("""
        <div class="section-title">
            > プロンプト管理_
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("➕ 新規プロンプト追加", expanded=False):
            with st.form("new_prompt_form"):
                prompt_title = st.text_input("タイトル", key="new_prompt_title")
                prompt_content = st.text_area("内容", height=200, key="new_prompt_content")
                prompt_tags = st.text_input("タグ（カンマ区切り）", key="new_prompt_tags")
                submitted = st.form_submit_button("追加")
                
                if submitted:
                    if prompt_title and prompt_content:
                        sheet = get_sheet("prompts")
                        if sheet:
                            try:
                                all_data = get_sheet_data("prompts")
                                existing_ids = [int(row[0]) for row in all_data[1:] if row and row[0].isdigit()]
                                new_id = max(existing_ids) + 1 if existing_ids else 1
                            except:
                                new_id = 1
                            
                            new_row = [
                                str(new_id),
                                prompt_title,
                                prompt_content,
                                prompt_tags or "",
                                get_now_jst()
                            ]
                            sheet.append_row(new_row)
                            # キャッシュをクリア
                            get_sheet_data.clear()
                            add_log_entry(f"新しいプロンプトを追加: {prompt_title}")
                            st.success(f"プロンプト「{prompt_title}」を追加しました！")
                            st.rerun()
                    else:
                        st.warning("タイトルと内容を入力してください。")
        
        st.markdown("---")
        st.subheader("プロンプト一覧")
        
        all_data = get_sheet_data("prompts")
        if all_data and len(all_data) > 1:
            rows = all_data[1:]
            for row in rows:
                while len(row) < 5:
                    row.append("")
                
                prompt_id = row[0] if len(row) > 0 else ""
                title = row[1] if len(row) > 1 else ""
                content = row[2] if len(row) > 2 else ""
                tags = row[3] if len(row) > 3 else ""
                created_at = row[4] if len(row) > 4 else ""
                
                with st.expander(f"📌 {title}"):
                    st.markdown(f"**タグ:** {tags}")
                    st.code(content, language=None)
                    if st.button("📋 コピー", key=f"copy_prompt_{prompt_id}"):
                        st.code(content, language=None)
                        st.success("コピーしました！")
                    st.caption(f"作成日時: {created_at}")
        else:
            st.info("プロンプトがまだ登録されていません。")
    
    with tab2:
        st.markdown("""
        <div class="section-title">
            > アイデアボックス_
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("➕ 新規アイデア追加", expanded=False):
            with st.form("new_idea_form"):
                idea_content = st.text_area("アイデア内容", height=150, key="new_idea_content")
                submitted = st.form_submit_button("追加")
                
                if submitted:
                    if idea_content:
                        sheet = get_sheet("ideas")
                        if sheet:
                            try:
                                all_data = get_sheet_data("ideas")
                                existing_ids = [int(row[0]) for row in all_data[1:] if row and row[0].isdigit()]
                                new_id = max(existing_ids) + 1 if existing_ids else 1
                            except:
                                new_id = 1
                            
                            new_row = [
                                str(new_id),
                                idea_content,
                                get_now_jst()
                            ]
                            sheet.append_row(new_row)
                            # キャッシュをクリア
                            get_sheet_data.clear()
                            add_log_entry("アイデアを追加しました。")
                            st.success("アイデアを追加しました！")
                            st.rerun()
                    else:
                        st.warning("アイデア内容を入力してください。")
        
        st.markdown("---")
        st.subheader("アイデア一覧")
        
        all_data = get_sheet_data("ideas")
        if all_data and len(all_data) > 1:
            rows = all_data[1:]
            for row in reversed(rows):
                while len(row) < 3:
                    row.append("")
                
                idea_id = row[0] if len(row) > 0 else ""
                content = row[1] if len(row) > 1 else ""
                created_at = row[2] if len(row) > 2 else ""
                
                st.markdown(f"💭 {content}")
                st.caption(f"作成日時: {created_at}")
                st.markdown("---")
        else:
            st.info("アイデアがまだ登録されていません。")

# Note生成画面
def show_note_generator():
    st.markdown("""
    <h1 style="color: #00FFFF; font-family: 'Courier New', monospace; text-transform: uppercase; letter-spacing: 0.2em;">
        Note記事生成
    </h1>
    """, unsafe_allow_html=True)
    
    # Settingsシートからlast_report_atを取得
    last_report_at = None
    all_data = get_sheet_data("settings")
    if all_data:
        for row in all_data:
            if len(row) >= 2 and row[0] == "last_report_at":
                last_report_at = row[1]
                break
    
    if last_report_at:
        st.info(f"前回のレポート出力日時: {last_report_at}")
    else:
        st.warning("前回のレポート出力日時が記録されていません。全データを対象にします。")
        last_report_at = "2000-01-01 00:00:00"
    
    st.markdown("""
    <div class="section-title">
        > 抽出結果_
    </div>
    """, unsafe_allow_html=True)
    
    completed_tasks = []
    updated_projects = []
    
    # 完了したタスクを抽出
    all_data = get_sheet_data("tasks")
    if all_data and len(all_data) > 1:
            rows = all_data[1:]
            for row in rows:
                while len(row) < 7:
                    row.append("")
                
                task_id = row[0] if len(row) > 0 else ""
                title = row[1] if len(row) > 1 else ""
                category = row[2] if len(row) > 2 else ""
                status = row[3] if len(row) > 3 else ""
                memo = row[4] if len(row) > 4 else ""
                created_at = row[5] if len(row) > 5 else ""
                completed_at = row[6] if len(row) > 6 else ""
                
                if status == "済" and completed_at and completed_at >= last_report_at:
                    completed_tasks.append({
                        "title": title,
                        "category": category,
                        "memo": memo,
                        "completed_at": completed_at
                    })
    
    # 更新されたプロジェクトを抽出
    all_data = get_sheet_data("projects")
    if all_data and len(all_data) > 1:
            rows = all_data[1:]
            for row in rows:
                while len(row) < 8:
                    row.append("")
                
                theme = row[1] if len(row) > 1 else ""
                ptype = row[2] if len(row) > 2 else ""
                blog_url = row[3] if len(row) > 3 else ""
                note_url = row[4] if len(row) > 4 else ""
                stamp_url = row[5] if len(row) > 5 else ""
                status = row[6] if len(row) > 6 else ""
                updated_at = row[7] if len(row) > 7 else ""
                
                if updated_at and updated_at >= last_report_at:
                    updated_projects.append({
                        "theme": theme,
                        "type": ptype,
                        "blog_url": blog_url,
                        "note_url": note_url,
                        "stamp_url": stamp_url,
                        "status": status,
                        "updated_at": updated_at
                    })
    
    # プレビュー生成
    preview_text = "## 今週の活動レポート\n\n"
    
    if completed_tasks:
        preview_text += "### ✅ 完了したタスク\n\n"
        for task in completed_tasks:
            preview_text += f"- **{task['title']}** ({task['category']})\n"
            if task['memo']:
                preview_text += f"  - メモ: {task['memo']}\n"
            preview_text += f"  - 完了日時: {task['completed_at']}\n\n"
    
    if updated_projects:
        preview_text += "### 📁 更新されたプロジェクト\n\n"
        for project in updated_projects:
            preview_text += f"- **{project['theme']}** ({project['type']}) - {project['status']}\n"
            if project['blog_url']:
                preview_text += f"  - ブログ: {project['blog_url']}\n"
            if project['note_url']:
                preview_text += f"  - Note: {project['note_url']}\n"
            if project['stamp_url']:
                preview_text += f"  - スタンプ: {project['stamp_url']}\n"
            preview_text += f"  - 更新日時: {project['updated_at']}\n\n"
    
    if not completed_tasks and not updated_projects:
        preview_text += "今回の期間に完了したタスクや更新されたプロジェクトはありません。\n\n"
    
    preview_text += "---\n\n### 💭 感想・振り返り\n\n（ここに感想を記入してください）\n"
    
    st.markdown("""
    <div class="section-title">
        > プレビュー & 編集_
    </div>
    """, unsafe_allow_html=True)
    
    edited_text = st.text_area(
        "Note記事の内容（編集可能）",
        value=preview_text,
        height=500,
        key="note_preview"
    )
    
    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 更新してコピー", type="primary", use_container_width=True):
            settings_sheet = get_sheet("settings")
            if settings_sheet:
                all_data = get_sheet_data("settings")
                found = False
                for i, row in enumerate(all_data, start=1):
                    if len(row) >= 1 and row[0] == "last_report_at":
                        settings_sheet.update_cell(i, 2, get_now_jst())
                        found = True
                        break
                
                if not found:
                    settings_sheet.append_row(["last_report_at", get_now_jst()])
                
                # キャッシュをクリア
                get_sheet_data.clear()
            
            add_log_entry("Note記事を生成しました。")
            st.subheader("📋 コピー用テキスト")
            st.code(edited_text, language=None)
            st.success("✅ レポート出力日時を更新しました！上記のテキストをコピーしてNoteに投稿してください。")
    
    st.markdown("---")
    st.markdown("""
    <div class="section-title">
        > 統計情報_
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("完了タスク数", len(completed_tasks))
    with col2:
        st.metric("更新プロジェクト数", len(updated_projects))
    with col3:
        st.metric("文字数", len(edited_text))

# メイン処理
def main():
    # CSSを注入
    inject_custom_css()
    
    # サイドバー
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(0, 255, 255, 0.3);">
        <h1 style="color: #00FFFF; font-family: 'Courier New', monospace; font-size: 1.5rem; margin: 0; text-transform: uppercase; letter-spacing: 0.2em;">
            Creator's<br>Cockpit
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    # セッション状態からページを取得、なければデフォルト
    default_page = st.session_state.get('page', "📊 ダッシュボード")
    
    page = st.sidebar.radio(
        "ナビゲーション",
        ["📊 ダッシュボード", "📁 プロジェクト管理", "💡 資産・アイデア", "📝 Note生成"],
        index=["📊 ダッシュボード", "📁 プロジェクト管理", "💡 資産・アイデア", "📝 Note生成"].index(default_page) if default_page in ["📊 ダッシュボード", "📁 プロジェクト管理", "💡 資産・アイデア", "📝 Note生成"] else 0,
        key="nav_radio",
        label_visibility="visible"
    )
    
    # ラジオボタンの値を常にセッション状態に同期（最新の選択を優先）
    st.session_state.page = page
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"最終更新: {get_now_jst()}")
    
    # ページに応じた処理
    if page == "📊 ダッシュボード":
        show_dashboard()
    elif page == "📁 プロジェクト管理":
        show_projects()
    elif page == "💡 資産・アイデア":
        show_assets()
    elif page == "📝 Note生成":
        show_note_generator()

if __name__ == "__main__":
    main()
