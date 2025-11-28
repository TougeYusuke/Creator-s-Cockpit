import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import pandas as pd
import re
import time

# ==========================================
# 1. 設定 & 定数
# ==========================================
PAGE_CONFIG = {
    "page_title": "Creator's Cockpit",
    "page_icon": "🚀",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

st.set_page_config(**PAGE_CONFIG)

# カラーパレット定義（視認性重視のダークテーマ）
COLORS = {
    "bg_gradient": "linear-gradient(135deg, #0a0a0a 0%, #1a1b26 100%)", # 少し青みのある深い黒
    "text_main": "#e0e0e0",
    "text_dim": "#a0a0a0",
    "accent_cyan": "#00FFFF",  # メインアクセント
    "accent_green": "#10b981", # 完了・成功
    "accent_blue": "#3b82f6",  # 情報・リンク
    "accent_warn": "#f59e0b",  # 注意・制作
    "glass_bg": "rgba(20, 24, 33, 0.7)", # ガラス風背景
    "border_color": "rgba(0, 255, 255, 0.2)"
}

# カテゴリごとのアイコン定義
CATEGORY_ICONS = {
    "制作": "🎨",
    "開発": "💻",
    "学習": "📚",
    "事務": "📎",
    "その他": "🤔"
}

# ==========================================
# 2. CSS & UI コンポーネント
# ==========================================
def inject_custom_css():
    st.markdown(f"""
    <style>
    /* 全体設定 */
    .stApp {{
        background: {COLORS['bg_gradient']};
        color: {COLORS['text_main']};
    }}
    
    /* フォント調整 (日本語メイリオ等) */
    body, button, input, textarea {{
        font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif !important;
    }}
    
    /* デジタル数字用フォント */
    .digital-font {{
        font-family: 'Courier New', monospace;
        letter-spacing: 0.05em;
        font-weight: bold;
    }}

    /* ヘッダーHUD (ヘッドアップディスプレイ) */
    .header-hud {{
        background: {COLORS['glass_bg']};
        border: 1px solid {COLORS['border_color']};
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }}
    /* 装飾ライン */
    .header-hud::after {{
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, {COLORS['accent_cyan']}, transparent);
    }}

    /* ワープゲート (サイドバーリンクボタン) */
    .warp-gate-btn {{
        display: block;
        width: 100%;
        padding: 10px 12px;
        margin: 6px 0;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: {COLORS['accent_cyan']};
        text-align: left;
        text-decoration: none;
        border-radius: 6px;
        transition: all 0.2s;
        font-size: 0.9rem;
    }}
    .warp-gate-btn:hover {{
        background: rgba(0, 255, 255, 0.1);
        border-color: {COLORS['accent_cyan']};
        color: #fff;
        transform: translateX(2px);
    }}

    /* ステータスタグ */
    .status-tag {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid;
    }}

    /* -----------------------------------------------------------
       タスクボタンのスタイル (見やすさ重視)
       Streamlitのボタンをカード風にカスタマイズ
    ----------------------------------------------------------- */
    div[data-testid="stButton"] > button {{
        width: 100% !important;
        height: auto !important;
        padding: 12px 16px !important;
        background: rgba(30, 30, 35, 0.6) !important;
        color: {COLORS['text_main']} !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-left: 4px solid {COLORS['text_dim']} !important;
        border-radius: 4px !important;
        
        /* テキスト左寄せ設定 */
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
        text-align: left !important;
        
        transition: all 0.2s ease !important;
    }}

    /* ボタン内のテキスト調整 */
    div[data-testid="stButton"] > button p {{
        font-size: 1rem !important;
        line-height: 1.5 !important;
        margin: 0 !important;
    }}

    /* ホバー時 */
    div[data-testid="stButton"] > button:hover {{
        background: rgba(0, 255, 255, 0.08) !important;
        border-color: {COLORS['accent_cyan']} !important;
        border-left-color: {COLORS['accent_cyan']} !important;
        color: #fff !important;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.1);
        transform: translateY(-2px);
    }}
    
    /* アクティブ時 */
    div[data-testid="stButton"] > button:active {{
        background: {COLORS['accent_cyan']} !important;
        color: #000 !important;
    }}

    /* 入力フォームの背景色調整 */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
        background-color: rgba(0, 0, 0, 0.3) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: {COLORS['text_main']} !important;
    }}
    
    /* Metric（数値表示）のスタイル */
    [data-testid="stMetricValue"] {{
        font-family: 'Courier New', monospace;
        color: {COLORS['accent_cyan']} !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: {COLORS['text_dim']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. データ管理クラス (SheetManager)
# ==========================================
class SheetManager:
    def __init__(self):
        self.credentials = self._get_credentials()
        self.client = self._auth()
        self.spreadsheet = self._get_spreadsheet()
        
    def _get_credentials(self):
        try:
            secrets = st.secrets["gcp_service_account"]
            return {
                "type": secrets["type"],
                "project_id": secrets["project_id"],
                "private_key_id": secrets["private_key_id"],
                "private_key": secrets["private_key"].replace("\\n", "\n"),
                "client_email": secrets["client_email"],
                "client_id": secrets["client_id"],
                "auth_uri": secrets["auth_uri"],
                "token_uri": secrets["token_uri"],
                "auth_provider_x509_cert_url": secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": secrets["client_x509_cert_url"]
            }
        except Exception as e:
            st.error(f"認証エラー: {e}")
            st.stop()

    def _auth(self):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(self.credentials, scopes=scope)
        return gspread.authorize(creds)

    def _get_spreadsheet(self):
        try:
            return self.client.open_by_key(st.secrets["spreadsheet"]["id"])
        except Exception as e:
            st.error(f"接続エラー: {e}")
            st.stop()

    @st.cache_data(ttl=60)
    def get_records(_self, sheet_name):
        try:
            sheet = _self.spreadsheet.worksheet(sheet_name)
            return sheet.get_all_records()
        except gspread.exceptions.WorksheetNotFound:
            return []
        except Exception:
            return []

    def clear_cache(self):
        self.get_records.clear()

    def add_row(self, sheet_name, row_data):
        try:
            sheet = self.spreadsheet.worksheet(sheet_name)
            sheet.append_row(row_data)
            self.clear_cache()
            return True
        except Exception as e:
            st.error(f"追加エラー: {e}")
            return False

    def update_cell_by_id(self, sheet_name, id_val, col_name, new_value):
        try:
            sheet = self.spreadsheet.worksheet(sheet_name)
            headers = sheet.row_values(1)
            try:
                col_index = headers.index(col_name) + 1
            except ValueError:
                st.error(f"列 '{col_name}' が見つかりません")
                return False

            cell = sheet.find(str(id_val), in_column=1)
            if cell:
                sheet.update_cell(cell.row, col_index, new_value)
                self.clear_cache()
                return True
            return False
        except Exception as e:
            st.error(f"更新エラー: {e}")
            return False

    def get_next_id(self, sheet_name):
        records = self.get_records(sheet_name)
        if not records:
            return 1
        ids = [int(r['id']) for r in records if str(r['id']).isdigit()]
        return max(ids) + 1 if ids else 1

@st.cache_resource
def get_sheet_manager():
    return SheetManager()

# ==========================================
# 4. ヘルパー関数
# ==========================================
def get_now_jst():
    return datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')

def add_log(message):
    if 'system_log' not in st.session_state:
        st.session_state.system_log = []
    time_str = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%H:%M:%S')
    st.session_state.system_log.append(f"[{time_str}] {message}")
    st.session_state.system_log = st.session_state.system_log[-20:]

def extract_urls_as_html(text):
    """テキスト内のURLをHTMLリンクに変換して返す"""
    if not text:
        return ""
    lines = text.split('\n')
    links_html = []
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    
    for line in lines:
        urls = url_pattern.findall(line)
        if urls:
            url = urls[0]
            # ラベル生成 (URLを除去した部分)
            label = line.replace(url, '').strip().strip(':').strip()
            if not label:
                label = "Link"
            
            link_html = f"""
            <a href="{url}" target="_blank" style="
                color: {COLORS['accent_cyan']};
                text-decoration: none;
                margin-right: 10px;
                border: 1px solid rgba(0,255,255,0.3);
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 0.8rem;
            ">🔗 {label}</a>
            """
            links_html.append(link_html)
            
    return "".join(links_html)

# ==========================================
# 5. コンポーネント (UIパーツ)
# ==========================================

def render_warp_gate(manager):
    """サイドバー：外部リンク集"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🌌 ワープゲート")
    
    # セッション初期化 (全て閉じた状態でスタート)
    if 'warp_gate_init' not in st.session_state:
        st.session_state['warp_gate_init'] = True
    
    shortcuts = manager.get_records("shortcuts")
    
    if not shortcuts:
        st.sidebar.info("リンク設定がありません (shortcutsシート)")
        return

    df = pd.DataFrame(shortcuts)
    if 'category' in df.columns:
        categories = df['category'].unique()
        for cat in categories:
            # アイコンがあれば先頭につける
            label = f"📂 {cat}"
            with st.sidebar.expander(label, expanded=False):
                cat_items = df[df['category'] == cat]
                for _, item in cat_items.iterrows():
                    icon = item.get('icon', '🔗')
                    label = item.get('label', 'Link')
                    url = item.get('url', '#')
                    
                    st.markdown(f"""
                    <a href="{url}" target="_blank" class="warp-gate-btn">
                        {icon} {label}
                    </a>
                    """, unsafe_allow_html=True)

def render_dashboard(manager):
    """ダッシュボード (メイン画面)"""
    
    # --- HUD (上部ステータス) ---
    st.markdown('<div class="header-hud">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.title("Creator's Cockpit")
        st.caption("🚀 システム稼働中 | 全システム正常")
    with c2:
        daily_exp = st.session_state.get('daily_exp', 0)
        st.metric("本日のクエスト達成数", f"{daily_exp}", delta="Keep going!")
    with c3:
        settings = manager.get_records("settings")
        last_report = "未記録"
        for s in settings:
            if s.get('key') == 'last_report_at':
                last_report = s.get('value')
        # 日時を短縮表示 (MM-DD HH:MM)
        disp_time = last_report[5:16] if len(last_report) > 10 else last_report
        st.metric("最終レポート出力", disp_time)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- メインエリア (2カラム) ---
    col_left, col_right = st.columns([2, 1])

    # === 左カラム: タスク管理 ===
    with col_left:
        st.subheader("📝 進行中のクエスト (未完了タスク)")
        st.caption("クリックで完了扱いにできます")
        
        tasks = manager.get_records("tasks")
        pending_tasks = [t for t in tasks if t.get('status') == '未']
        
        if not pending_tasks:
            st.balloons()
            st.info("🎉 全てのクエストを完了しました！素晴らしい進捗です。")
        
        for task in pending_tasks[:10]: # 表示数を制限
            cat = task.get('category', 'その他')
            icon = CATEGORY_ICONS.get(cat, "📌")
            
            # ラベル作成
            title = task.get('title', 'No Title')
            memo = task.get('memo', '')
            
            # 見やすい横並びラベル
            label = f"⬜ {icon} {title}"
            if memo:
                label += f" : {memo}" # メモを横につなげる
            
            # タスクボタン
            if st.button(label, key=f"task_{task['id']}", use_container_width=True, help="完了にする"):
                manager.update_cell_by_id("tasks", task['id'], "status", "済")
                manager.update_cell_by_id("tasks", task['id'], "completed_at", get_now_jst())
                st.session_state.daily_exp = st.session_state.get('daily_exp', 0) + 1
                add_log(f"クエスト完了: {title}")
                st.rerun()

        # 新規タスク追加フォーム
        with st.expander("➕ 新しいクエストを受注する", expanded=False):
            with st.form("add_task_form"):
                c_title, c_cat = st.columns([3, 1])
                with c_title:
                    new_title = st.text_input("クエスト名 (必須)")
                with c_cat:
                    new_cat = st.selectbox("カテゴリ", list(CATEGORY_ICONS.keys()))
                
                new_memo = st.text_area("メモ (任意)", height=3)
                
                if st.form_submit_button("登録する", use_container_width=True):
                    if new_title:
                        new_id = manager.get_next_id("tasks")
                        manager.add_row("tasks", [new_id, new_title, new_cat, "未", new_memo, get_now_jst(), ""])
                        add_log(f"新規クエスト追加: {new_title}")
                        st.success("登録しました")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("クエスト名を入力してください")

    # === 右カラム: プロジェクト状況 ===
    with col_right:
        st.subheader("📊 プロジェクト戦況")
        
        projects = manager.get_records("projects")
        # 進行中のものを優先表示
        active_projects = [p for p in projects if p.get('status') == '進行中']
        other_projects = [p for p in projects if p.get('status') != '進行中']
        
        display_list = active_projects + other_projects
        
        for proj in display_list[:5]: # 最大5件表示
            status = proj.get('status', '進行中')
            theme = proj.get('theme', 'No Theme')
            
            # ステータス色分け
            color = COLORS['accent_blue']
            if status == '完了': color = COLORS['accent_green']
            elif status == '保留': color = COLORS['text_dim']
            elif status == '進行中': color = COLORS['accent_cyan']

            # リンクHTML生成
            links_html = extract_urls_as_html(proj.get('links', ''))
            
            # HTMLカード描画
            st.markdown(f"""
            <div style="
                margin-bottom:12px; 
                padding:12px; 
                border:1px solid {color}44; 
                border-left: 3px solid {color};
                border-radius:4px;
                background: rgba(20,20,20,0.4);
            ">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:bold; color:{COLORS['text_main']}">{theme}</span>
                    <span style="
                        font-size:0.7em; 
                        color:{color}; 
                        border:1px solid {color}; 
                        padding:1px 6px; 
                        border-radius:10px;
                    ">{status}</span>
                </div>
                <div style="margin-top:8px;">{links_html}</div>
            </div>
            """, unsafe_allow_html=True)
            
        if st.button("プロジェクト一覧へ移動", use_container_width=True):
            st.session_state['current_page'] = "CAMPAIGN"
            st.rerun()

    # --- システムログ ---
    st.markdown("---")
    with st.expander("🖥 システムログ", expanded=False):
        logs = st.session_state.get('system_log', [])
        log_text = "<br>".join([f"<span style='color:{COLORS['accent_cyan']}'>{l}</span>" for l in reversed(logs)])
        st.markdown(f"<div style='font-family:monospace; font-size:0.8em;'>{log_text}</div>", unsafe_allow_html=True)


def render_project_manager(manager):
    """プロジェクト管理画面"""
    st.title("📁 プロジェクト作戦本部")
    st.caption("すべてのプロジェクトの詳細確認と編集ができます")
    
    projects = manager.get_records("projects")
    if not projects:
        st.warning("データがありません")
        
    # アコーディオンで一覧表示
    for proj in projects:
        status = proj.get('status', '進行中')
        icon = "🔹" if status == '進行中' else "✅" if status == '完了' else "💤"
        
        with st.expander(f"{icon} {proj.get('theme')}", expanded=(status=='進行中')):
            c_edit, c_view = st.columns([1, 1])
            
            # 編集エリア
            with c_edit:
                st.caption("🛠 設定変更")
                new_theme = st.text_input("テーマ名", value=proj.get('theme'), key=f"th_{proj['id']}")
                new_status = st.selectbox("状態", ["進行中", "完了", "保留"], 
                                        index=["進行中", "完了", "保留"].index(status) if status in ["進行中", "完了", "保留"] else 0,
                                        key=f"st_{proj['id']}")
                
                if st.button("更新を保存", key=f"upd_{proj['id']}"):
                    manager.update_cell_by_id("projects", proj['id'], "theme", new_theme)
                    manager.update_cell_by_id("projects", proj['id'], "status", new_status)
                    manager.update_cell_by_id("projects", proj['id'], "updated_at", get_now_jst())
                    st.success("更新しました！")
                    time.sleep(0.5)
                    st.rerun()

            # 詳細エリア
            with c_view:
                st.caption("📝 詳細情報")
                # リンク編集とメモ編集
                new_links = st.text_area("関連リンク (URL)", value=proj.get('links', ''), height=80, key=f"lk_{proj['id']}")
                new_memo = st.text_area("メモ", value=proj.get('memo', ''), height=80, key=f"mm_{proj['id']}")
                
                # ここだけ個別保存ボタン（誤操作防止のため）
                if st.button("詳細を保存", key=f"det_{proj['id']}"):
                    manager.update_cell_by_id("projects", proj['id'], "links", new_links)
                    manager.update_cell_by_id("projects", proj['id'], "memo", new_memo)
                    st.success("詳細を保存しました")

    st.markdown("---")
    with st.expander("➕ 新規プロジェクト立ち上げ", expanded=False):
        with st.form("new_proj_form"):
            st.subheader("New Project")
            f_theme = st.text_input("プロジェクトテーマ (必須)")
            f_links = st.text_area("関連URL", placeholder="Note: https://...")
            f_memo = st.text_area("メモ")
            
            if st.form_submit_button("作成する"):
                if f_theme:
                    new_id = manager.get_next_id("projects")
                    # id, theme, status, links, memo, updated_at
                    manager.add_row("projects", [new_id, f_theme, "進行中", f_links, f_memo, get_now_jst()])
                    st.success(f"プロジェクト「{f_theme}」を作成しました")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("テーマ名は必須です")


def render_report_generator(manager):
    """レポート生成画面"""
    st.title("📝 活動レポート出力")
    st.caption("前回の出力以降の差分（完了タスク・プロジェクト更新）を自動抽出します")
    
    # Settings取得
    settings = manager.get_records("settings")
    last_report_at = "2000-01-01 00:00:00"
    for s in settings:
        if s.get('key') == 'last_report_at':
            last_report_at = s.get('value')
            
    st.info(f"🕒 前回のセーブ日時: **{last_report_at}**")
    
    # データ抽出
    tasks = manager.get_records("tasks")
    projects = manager.get_records("projects")
    
    completed_tasks = [t for t in tasks if t.get('status') == '済' and t.get('completed_at', '') > last_report_at]
    updated_projects = [p for p in projects if p.get('updated_at', '') > last_report_at]
    
    # レポート本文作成
    report_text = f"## 🚀 活動レポート ({get_now_jst()[:10]})\n\n"
    
    if completed_tasks:
        report_text += "### ✅ 完了したクエスト\n"
        for t in completed_tasks:
            cat = t.get('category', '')
            title = t.get('title', '')
            memo = t.get('memo', '')
            report_text += f"- {title} 【{cat}】\n"
            if memo:
                report_text += f"  - 📝 {memo}\n"
        report_text += "\n"
        
    if updated_projects:
        report_text += "### 🏗 プロジェクト進捗\n"
        for p in updated_projects:
            theme = p.get('theme', '')
            status = p.get('status', '')
            report_text += f"- {theme} : **{status}**\n"
        report_text += "\n"
        
    if not completed_tasks and not updated_projects:
        report_text += "（前回の出力から更新されたデータはありません）\n\n"
        
    report_text += "### 💭 振り返り・メモ\n(ここに本日の感想を記入...)\n"
    
    # プレビューと編集
    col1, col2 = st.columns([1, 1])
    with col1:
        edited_report = st.text_area("レポート内容 (編集可能)", value=report_text, height=400)
    
    with col2:
        st.markdown("### 📤 アクション")
        st.write("内容を確認したら、以下のボタンで日時を更新（セーブ）してください。")
        
        if st.button("レポート完了としてセーブ (日時更新)", type="primary", use_container_width=True):
            # Settings更新
            settings_sheet = manager.spreadsheet.worksheet("settings")
            cell = settings_sheet.find("last_report_at")
            now_str = get_now_jst()
            
            if cell:
                settings_sheet.update_cell(cell.row, cell.col + 1, now_str)
            else:
                settings_sheet.append_row(["last_report_at", now_str])
                
            manager.clear_cache()
            st.success(f"✅ セーブ完了！ 基準日時を {now_str} に更新しました。")
            st.balloons()
            
        st.markdown("---")
        st.caption("※ Noteやブログに貼り付ける場合は、左のテキストをコピーしてください。")

# ==========================================
# 6. メイン実行関数
# ==========================================
def main():
    inject_custom_css()
    manager = get_sheet_manager()
    
    # サイドバーナビゲーション
    with st.sidebar:
        st.title("NAVIGATION")
        
        # ページ遷移管理
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = "DASHBOARD"
            
        # メニューボタン
        if st.button("📊 ダッシュボード", use_container_width=True):
            st.session_state['current_page'] = "DASHBOARD"
        if st.button("📁 プロジェクト管理", use_container_width=True):
            st.session_state['current_page'] = "CAMPAIGN"
        if st.button("📦 資産・アイデア", use_container_width=True):
            st.session_state['current_page'] = "ASSETS"
        if st.button("📝 レポート出力", use_container_width=True):
            st.session_state['current_page'] = "REPORT"
            
        render_warp_gate(manager)
    
    # ページルーティング
    page = st.session_state['current_page']
    
    if page == "DASHBOARD":
        render_dashboard(manager)
    elif page == "CAMPAIGN":
        render_project_manager(manager)
    elif page == "ASSETS":
        st.title("📦 資産・アイデアBOX")
        st.info("ここにプロンプト集やアイデアメモ機能を実装できます")
    elif page == "REPORT":
        render_report_generator(manager)

if __name__ == "__main__":
    main()