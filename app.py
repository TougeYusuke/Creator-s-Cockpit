import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import time
import pandas as pd

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

# カラーパレット定義（一括管理）
COLORS = {
    "bg_gradient": "linear-gradient(135deg, #0a0a0a 0%, #0E1117 50%, #000000 100%)",
    "text_main": "#e0e0e0",
    "accent_cyan": "#00FFFF",
    "accent_green": "#10b981",
    "accent_blue": "#4dabf7",
    "accent_warn": "#fbbf24",
    "glass_bg": "rgba(14, 17, 23, 0.8)",
}

# ==========================================
# 2. CSS & UI コンポーネント
# ==========================================
def inject_custom_css():
    st.markdown(f"""
    <style>
    /* ベーススタイル */
    .stApp {{
        background: {COLORS['bg_gradient']};
        color: {COLORS['text_main']};
    }}
    
    /* フォント設定 (デジタル感) */
    .digital-font {{
        font-family: 'Courier New', monospace;
        letter-spacing: 0.1em;
    }}
    
    /* ヘッダーHUD */
    .header-hud {{
        background: rgba(0, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(0, 255, 255, 0.3);
        padding: 1.5rem;
        margin-bottom: 2rem;
        position: relative;
    }}
    .header-hud::before, .header-hud::after {{
        content: ''; position: absolute; top: 0; width: 8px; height: 8px;
        border-top: 1px solid #00FFFF;
    }}
    .header-hud::before {{ left: 0; border-left: 1px solid #00FFFF; }}
    .header-hud::after {{ right: 0; border-right: 1px solid #00FFFF; }}
    
    /* Warp Gate (サイドバーリンク) */
    .warp-gate-btn {{
        display: block;
        width: 100%;
        padding: 8px 12px;
        margin: 4px 0;
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid rgba(0, 255, 255, 0.2);
        color: #00FFFF;
        text-align: left;
        text-decoration: none;
        border-radius: 4px;
        transition: all 0.2s;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
    }}
    .warp-gate-btn:hover {{
        background: rgba(0, 255, 255, 0.2);
        border-color: #00FFFF;
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
        color: #fff;
    }}
    
    /* タスクカード */
    .task-card {{
        background: rgba(0, 0, 0, 0.4);
        border-left: 3px solid #333;
        padding: 12px;
        margin-bottom: 8px;
        border-radius: 0 4px 4px 0;
        transition: transform 0.2s;
    }}
    .task-card:hover {{
        transform: translateX(5px);
        background: rgba(0, 255, 255, 0.05);
    }}
    
    /* カスタムタグ */
    .status-tag {{
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: bold;
        border: 1px solid;
    }}
    
    /* Streamlit標準要素のオーバーライド */
    .stButton > button {{
        border: 1px solid {COLORS['accent_cyan']};
        color: {COLORS['accent_cyan']};
        background: rgba(0,0,0,0.5);
        font-family: 'Courier New', monospace;
    }}
    .stButton > button:hover {{
        background: {COLORS['accent_cyan']};
        color: black;
        box-shadow: 0 0 15px {COLORS['accent_cyan']};
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. データ管理クラス (DataManager)
# ==========================================
class SheetManager:
    def __init__(self):
        self.credentials = self._get_credentials()
        self.client = self._auth()
        self.spreadsheet = self._get_spreadsheet()
        
    def _get_credentials(self):
        """Secretsから認証情報を構築"""
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
            st.error(f"認証情報の読み込みエラー: {e}")
            st.stop()

    def _auth(self):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(self.credentials, scopes=scope)
        return gspread.authorize(creds)

    def _get_spreadsheet(self):
        try:
            return self.client.open_by_key(st.secrets["spreadsheet"]["id"])
        except Exception as e:
            st.error(f"スプレッドシート接続エラー: {e}")
            st.stop()

    @st.cache_data(ttl=60)
    def get_records(_self, sheet_name):
        """指定シートの全レコードを辞書リストとして取得"""
        try:
            sheet = _self.spreadsheet.worksheet(sheet_name)
            return sheet.get_all_records()
        except gspread.exceptions.WorksheetNotFound:
            # シートがない場合はNoneを返すか空リスト
            return []
        except Exception as e:
            st.error(f"データ取得エラー ({sheet_name}): {e}")
            return []

    def clear_cache(self):
        """キャッシュをクリア"""
        self.get_records.clear()

    def add_row(self, sheet_name, row_data):
        """行を追加"""
        try:
            sheet = self.spreadsheet.worksheet(sheet_name)
            sheet.append_row(row_data)
            self.clear_cache()
            return True
        except Exception as e:
            st.error(f"データ追加エラー: {e}")
            return False

    def update_cell_by_id(self, sheet_name, id_val, col_name, new_value):
        """IDを指定してセルを更新 (ヘッダー名から列を特定)"""
        try:
            sheet = self.spreadsheet.worksheet(sheet_name)
            # ヘッダー行を取得して列インデックスを探す
            headers = sheet.row_values(1)
            try:
                col_index = headers.index(col_name) + 1
            except ValueError:
                st.error(f"カラム '{col_name}' が見つかりません")
                return False

            # IDの列を探す (通常は1列目 'id' と仮定)
            cell = sheet.find(str(id_val), in_column=1)
            if cell:
                sheet.update_cell(cell.row, col_index, new_value)
                self.clear_cache()
                return True
            else:
                st.error(f"ID {id_val} が見つかりません")
                return False
        except Exception as e:
            st.error(f"更新エラー: {e}")
            return False

    def get_next_id(self, sheet_name):
        """自動採番用ID取得"""
        records = self.get_records(sheet_name)
        if not records:
            return 1
        # 文字列IDの場合も考慮してint変換
        ids = [int(r['id']) for r in records if str(r['id']).isdigit()]
        return max(ids) + 1 if ids else 1

# ==========================================
# 4. ヘルパー関数
# ==========================================
def get_now_jst():
    return datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')

def add_log(message):
    """セッションステート内ログに追加"""
    if 'system_log' not in st.session_state:
        st.session_state.system_log = []
    
    time_str = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%H:%M:%S')
    st.session_state.system_log.append(f"[{time_str}] {message}")
    # 最新20件保持
    st.session_state.system_log = st.session_state.system_log[-20:]

# ==========================================
# 5. 各ページコンポーネント
# ==========================================

def render_warp_gate(manager):
    """サイドバー：外部リンク集 (Warp Gate)"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🌌 Warp Gate")
    
    # シートからショートカット読み込み
    shortcuts = manager.get_records("shortcuts")
    
    if not shortcuts:
        st.sidebar.info("No links connected.")
        return

    # カテゴリごとにグループ化
    df = pd.DataFrame(shortcuts)
    if 'category' in df.columns:
        categories = df['category'].unique()
        for cat in categories:
            with st.sidebar.expander(f"📂 {cat}", expanded=True):
                cat_items = df[df['category'] == cat]
                for _, item in cat_items.iterrows():
                    icon = item.get('icon', '🔗')
                    label = item.get('label', 'Link')
                    url = item.get('url', '#')
                    
                    # HTMLでリンクボタンを描画
                    st.markdown(f"""
                    <a href="{url}" target="_blank" class="warp-gate-btn">
                        {icon} {label}
                    </a>
                    """, unsafe_allow_html=True)

def render_dashboard(manager):
    """ダッシュボード画面"""
    # --- HUD ---
    st.markdown('<div class="header-hud">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.title("COMMAND CENTER")
        st.caption("SYSTEM ONLINE | CREATOR'S COCKPIT v2.0")
    with c2:
        daily_exp = st.session_state.get('daily_exp', 0)
        st.metric("DAILY EXP", f"{daily_exp}", delta="+1")
    with c3:
        # Settingsから前回レポート日時取得
        settings = manager.get_records("settings")
        last_report = "N/A"
        for s in settings:
            if s.get('key') == 'last_report_at':
                last_report = s.get('value')
        st.metric("LAST SAVE", last_report[:16] if len(last_report)>10 else last_report)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- MAIN GRID ---
    col_main, col_sub = st.columns([2, 1])

    with col_main:
        st.markdown("### > ACTIVE QUESTS (Tasks)")
        
        # タスク取得とフィルタリング
        tasks = manager.get_records("tasks")
        pending_tasks = [t for t in tasks if t.get('status') == '未']
        
        if not pending_tasks:
            st.info("✨ 全てのクエストを完了しました！")
        
        for task in pending_tasks[:5]: # 最大5件
            # カード表示
            border_color = COLORS['accent_cyan']
            if task.get('category') == '制作': border_color = COLORS['accent_warn']
            
            with st.container():
                cols = st.columns([0.1, 0.9])
                with cols[0]:
                    # 完了ボタン
                    if st.button("⬜", key=f"done_{task['id']}", help="完了にする"):
                        manager.update_cell_by_id("tasks", task['id'], "status", "済")
                        manager.update_cell_by_id("tasks", task['id'], "completed_at", get_now_jst())
                        st.session_state.daily_exp = st.session_state.get('daily_exp', 0) + 1
                        add_log(f"クエスト完了: {task['title']}")
                        st.rerun()
                with cols[1]:
                    st.markdown(f"""
                    <div class="task-card" style="border-left-color: {border_color};">
                        <div style="font-weight:bold;">{task['title']}</div>
                        <span class="status-tag" style="color:{border_color}; border-color:{border_color};">
                            [{task.get('category')}]
                        </span>
                        <span style="font-size:0.8em; color:#888;">{task.get('memo', '')}</span>
                    </div>
                    """, unsafe_allow_html=True)

        # タスク追加フォーム
        with st.expander("➕ Add New Quest"):
            with st.form("add_task"):
                new_title = st.text_input("Title")
                new_cat = st.selectbox("Category", ["制作", "開発", "学習", "事務", "その他"])
                new_memo = st.text_area("Memo")
                if st.form_submit_button("Deploy"):
                    new_id = manager.get_next_id("tasks")
                    manager.add_row("tasks", [new_id, new_title, new_cat, "未", new_memo, get_now_jst(), ""])
                    add_log(f"新規クエスト追加: {new_title}")
                    st.success("Added!")
                    st.rerun()

    with col_sub:
        st.markdown("### > CAMPAIGN MAP")
        projects = manager.get_records("projects")
        
        # プロジェクト簡易表示
        for proj in projects[:5]:
            status = proj.get('status', '進行中')
            color = COLORS['accent_green'] if status=='完了' else COLORS['accent_blue']
            
            st.markdown(f"""
            <div style="margin-bottom:10px; padding:10px; border:1px solid {color}; border-radius:4px;">
                <div style="font-size:0.8em; color:{color}">{proj.get('theme')}</div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.7em;">{proj.get('type')}</span>
                    <span class="status-tag" style="border-color:{color}; color:{color}">{status}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    # --- LOG ---
    st.markdown("---")
    st.markdown("### > SYSTEM LOG")
    log_area = st.empty()
    logs = st.session_state.get('system_log', [])
    log_text = "<br>".join([f"<span style='color:#00FFFF'>{l}</span>" for l in reversed(logs)])
    log_area.markdown(f"<div style='background:#050505; padding:10px; font-family:monospace; font-size:0.8em;'>{log_text}</div>", unsafe_allow_html=True)


def render_project_manager(manager):
    """プロジェクト管理画面"""
    st.title("📁 CAMPAIGN MANAGER")
    
    projects = manager.get_records("projects")
    if not projects:
        st.warning("No Data.")
    
    # 一覧表示と編集
    for proj in projects:
        with st.expander(f"🔹 {proj.get('theme')} ({proj.get('status')})"):
            c1, c2 = st.columns(2)
            with c1:
                # 実際のアプリではIDを使って更新処理を書く
                st.text_input("Theme", value=proj.get('theme'), key=f"p_th_{proj['id']}", disabled=True)
                st.write(f"Type: {proj.get('type')}")
            with c2:
                st.markdown(f"[Blog]({proj.get('blog_url')}) | [Note]({proj.get('note_url')}) | [Stamp]({proj.get('stamp_url')})")
            
            # 簡易ステータス更新ボタン
            if st.button("Mark Completed", key=f"comp_p_{proj['id']}"):
                manager.update_cell_by_id("projects", proj['id'], "status", "完了")
                manager.update_cell_by_id("projects", proj['id'], "updated_at", get_now_jst())
                st.success("Updated!")
                st.rerun()

    with st.expander("➕ New Campaign", expanded=False):
        with st.form("new_proj"):
            theme = st.text_input("Theme")
            ptype = st.selectbox("Type", ["mix", "single"])
            if st.form_submit_button("Launch"):
                new_id = manager.get_next_id("projects")
                # 簡易実装：URLは空で作成
                manager.add_row("projects", [new_id, theme, ptype, "", "", "", "進行中", get_now_jst()])
                st.rerun()


def render_note_generator(manager):
    """Note記事生成 (差分抽出)"""
    st.title("📝 REPORT GENERATOR")
    
    # 前回出力日時の取得
    settings = manager.get_records("settings")
    last_report_at = "2000-01-01 00:00:00"
    for s in settings:
        if s.get('key') == 'last_report_at':
            last_report_at = s.get('value')
    
    st.info(f"Checking updates since: {last_report_at}")
    
    # データ抽出
    tasks = manager.get_records("tasks")
    projects = manager.get_records("projects")
    
    completed_tasks = [t for t in tasks if t.get('status') == '済' and t.get('completed_at', '') > last_report_at]
    updated_projects = [p for p in projects if p.get('updated_at', '') > last_report_at]
    
    # テキスト生成
    report_md = "## 🚀 本日の作業ログ\n\n"
    if completed_tasks:
        report_md += "### ✅ 完了クエスト\n"
        for t in completed_tasks:
            report_md += f"- {t['title']} ({t['category']})\n"
    
    if updated_projects:
        report_md += "\n### 🏗 進捗プロジェクト\n"
        for p in updated_projects:
            report_md += f"- {p['theme']} : {p['status']}\n"
            
    report_md += "\n### 💭 振り返り\n（ここに感想を書く）\n"

    # プレビュー
    edited = st.text_area("Report Preview", value=report_md, height=400)
    
    if st.button("Generate & Update Timestamp"):
        # タイムスタンプ更新処理
        # settingsシートの行を探して更新する処理が必要（簡略化のため追記か更新か判断が必要）
        # ここでは簡易的に「settingsシートの1行目を上書き」などのロジックにするか、
        # settingsシートの構造を {'key':..., 'value':...} としているので検索して更新
        
        settings_sheet = manager.spreadsheet.worksheet("settings")
        cell = settings_sheet.find("last_report_at")
        if cell:
            settings_sheet.update_cell(cell.row, cell.col + 1, get_now_jst())
        else:
            settings_sheet.append_row(["last_report_at", get_now_jst()])
            
        manager.clear_cache()
        st.success("Saved! Timestamp updated.")


# ==========================================
# 6. メイン実行関数
# ==========================================
def main():
    inject_custom_css()
    
    # データマネージャー初期化
    manager = SheetManager()
    
    # サイドバー
    with st.sidebar:
        st.title("NAVIGATOR")
        page = st.radio("Mode Select", ["DASHBOARD", "CAMPAIGN", "ASSETS", "REPORT"])
        
        # Warp Gate (新規追加機能)
        render_warp_gate(manager)
    
    # ページルーティング
    if page == "DASHBOARD":
        render_dashboard(manager)
    elif page == "CAMPAIGN":
        render_project_manager(manager)
    elif page == "ASSETS":
        st.title("📦 ASSETS")
        st.info("ここにプロンプト管理などを実装")
    elif page == "REPORT":
        render_note_generator(manager)

if __name__ == "__main__":
    main()