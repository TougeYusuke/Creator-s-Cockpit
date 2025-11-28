import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# ページ設定
st.set_page_config(
    page_title="Creator's Cockpit",
    page_icon="🚀",
    layout="wide"
)

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

# シート取得関数
def get_sheet(sheet_name):
    """指定されたシートを取得"""
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"シート '{sheet_name}' が見つかりません。")
        return None
    except Exception as e:
        st.error(f"シート '{sheet_name}' の取得エラー: {str(e)}")
        return None

# 現在日時を取得（JST）
def get_now_jst():
    """JSTの現在日時を文字列で返す"""
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')

# ダッシュボード画面
def show_dashboard():
    st.title("📊 ダッシュボード")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚡ クイックツール")
        st.markdown("---")
        
        # 定型文の定義
        quick_texts = {
            "ハッシュタグ（クリエイター）": "#クリエイター #副業 #創作活動",
            "ハッシュタグ（ブログ）": "#ブログ #アウトプット #note",
            "ハッシュタグ（開発）": "#プログラミング #開発 #Python",
            "ハッシュタグ（学習）": "#学習 #勉強 #成長",
        }
        
        for label, text in quick_texts.items():
            st.code(text, language=None)
            if st.button(f"📋 {label}をコピー", key=f"copy_{label}"):
                st.code(text, language=None)
                st.success(f"コピーしました: {text}")
    
    with col2:
        st.subheader("📝 新規タスク追加")
        st.markdown("---")
        
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
                        # 既存のIDの最大値を取得
                        try:
                            existing_ids = [int(row[0]) for row in sheet.get_all_values()[1:] if row[0].isdigit()]
                            new_id = max(existing_ids) + 1 if existing_ids else 1
                        except:
                            new_id = 1
                        
                        # 新規タスクを追加
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
                        st.success(f"タスク「{task_title}」を追加しました！")
                        st.rerun()
                else:
                    st.warning("タスクタイトルを入力してください。")
    
    st.markdown("---")
    st.subheader("📋 未完了タスク一覧")
    
    sheet = get_sheet("tasks")
    if sheet:
        all_data = sheet.get_all_values()
        if len(all_data) > 1:
            headers = all_data[0]
            rows = all_data[1:]
            
            # 未完了タスクをフィルタリング
            incomplete_tasks = []
            for i, row in enumerate(rows, start=2):
                if len(row) > 3 and row[3] == "未":
                    incomplete_tasks.append((i, row))
            
            if incomplete_tasks:
                for row_num, row in incomplete_tasks:
                    # データの長さを調整
                    while len(row) < len(headers):
                        row.append("")
                    
                    task_id = row[0] if len(row) > 0 else ""
                    title = row[1] if len(row) > 1 else ""
                    category = row[2] if len(row) > 2 else ""
                    status = row[3] if len(row) > 3 else ""
                    memo = row[4] if len(row) > 4 else ""
                    created_at = row[5] if len(row) > 5 else ""
                    
                    with st.container():
                        col1, col2, col3 = st.columns([1, 8, 1])
                        with col1:
                            if st.checkbox("完了", key=f"complete_{row_num}"):
                                # タスクを完了にする
                                sheet.update_cell(row_num, 4, "済")  # status
                                sheet.update_cell(row_num, 7, get_now_jst())  # completed_at
                                st.success(f"タスク「{title}」を完了にしました！")
                                st.rerun()
                        with col2:
                            st.markdown(f"**{title}** ({category})")
                            if memo:
                                st.caption(f"メモ: {memo}")
                            st.caption(f"作成日時: {created_at}")
                        with col3:
                            st.caption(f"ID: {task_id}")
                        st.markdown("---")
            else:
                st.info("未完了のタスクはありません。素晴らしい！🎉")
        else:
            st.info("タスクがまだ登録されていません。")
    else:
        st.error("タスクシートを読み込めませんでした。")

# プロジェクト管理画面
def show_projects():
    st.title("📁 プロジェクト管理")
    
    sheet = get_sheet("projects")
    if not sheet:
        return
    
    st.subheader("新規プロジェクト追加")
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
                try:
                    existing_ids = [int(row[0]) for row in sheet.get_all_values()[1:] if row[0].isdigit()]
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
                st.success(f"プロジェクト「{project_theme}」を追加しました！")
                st.rerun()
            else:
                st.warning("テーマを入力してください。")
    
    st.markdown("---")
    st.subheader("プロジェクト一覧")
    
    all_data = sheet.get_all_values()
    if len(all_data) > 1:
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
                    sheet.update_cell(i, 2, new_theme)
                    sheet.update_cell(i, 3, new_type)
                    sheet.update_cell(i, 4, new_blog_url)
                    sheet.update_cell(i, 5, new_note_url)
                    sheet.update_cell(i, 6, new_stamp_url)
                    sheet.update_cell(i, 7, new_status)
                    sheet.update_cell(i, 8, get_now_jst())
                    st.success("プロジェクトを更新しました！")
                    st.rerun()
    else:
        st.info("プロジェクトがまだ登録されていません。")

# 資産・アイデア画面
def show_assets():
    st.title("💡 資産・アイデア管理")
    
    tab1, tab2 = st.tabs(["📝 プロンプト管理", "💭 アイデア箱"])
    
    with tab1:
        st.subheader("新規プロンプト追加")
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
                            existing_ids = [int(row[0]) for row in sheet.get_all_values()[1:] if row[0].isdigit()]
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
                        st.success(f"プロンプト「{prompt_title}」を追加しました！")
                        st.rerun()
                else:
                    st.warning("タイトルと内容を入力してください。")
        
        st.markdown("---")
        st.subheader("プロンプト一覧")
        
        sheet = get_sheet("prompts")
        if sheet:
            all_data = sheet.get_all_values()
            if len(all_data) > 1:
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
        st.subheader("新規アイデア追加")
        with st.form("new_idea_form"):
            idea_content = st.text_area("アイデア内容", height=150, key="new_idea_content")
            submitted = st.form_submit_button("追加")
            
            if submitted:
                if idea_content:
                    sheet = get_sheet("ideas")
                    if sheet:
                        try:
                            existing_ids = [int(row[0]) for row in sheet.get_all_values()[1:] if row[0].isdigit()]
                            new_id = max(existing_ids) + 1 if existing_ids else 1
                        except:
                            new_id = 1
                        
                        new_row = [
                            str(new_id),
                            idea_content,
                            get_now_jst()
                        ]
                        sheet.append_row(new_row)
                        st.success("アイデアを追加しました！")
                        st.rerun()
                else:
                    st.warning("アイデア内容を入力してください。")
        
        st.markdown("---")
        st.subheader("アイデア一覧")
        
        sheet = get_sheet("ideas")
        if sheet:
            all_data = sheet.get_all_values()
            if len(all_data) > 1:
                rows = all_data[1:]
                # 新しい順に表示
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
    st.title("📝 Noteネタ生成")
    
    # Settingsシートからlast_report_atを取得
    settings_sheet = get_sheet("settings")
    last_report_at = None
    
    if settings_sheet:
        all_data = settings_sheet.get_all_values()
        for row in all_data:
            if len(row) >= 2 and row[0] == "last_report_at":
                last_report_at = row[1]
                break
    
    if last_report_at:
        st.info(f"前回のレポート出力日時: {last_report_at}")
    else:
        st.warning("前回のレポート出力日時が記録されていません。全データを対象にします。")
        last_report_at = "2000-01-01 00:00:00"  # デフォルト値
    
    # 差分抽出
    st.subheader("📊 差分抽出結果")
    
    completed_tasks = []
    updated_projects = []
    
    # 完了したタスクを抽出
    tasks_sheet = get_sheet("tasks")
    if tasks_sheet:
        all_data = tasks_sheet.get_all_values()
        if len(all_data) > 1:
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
    projects_sheet = get_sheet("projects")
    if projects_sheet:
        all_data = projects_sheet.get_all_values()
        if len(all_data) > 1:
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
    
    # 編集可能なテキストエリア
    st.subheader("📝 プレビュー・編集")
    edited_text = st.text_area(
        "Note記事の内容（編集可能）",
        value=preview_text,
        height=500,
        key="note_preview"
    )
    
    # 更新ボタン
    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 更新してコピー", type="primary", use_container_width=True):
            # Settingsシートのlast_report_atを更新
            if settings_sheet:
                # 既存のレコードを探す
                all_data = settings_sheet.get_all_values()
                found = False
                for i, row in enumerate(all_data, start=1):
                    if len(row) >= 1 and row[0] == "last_report_at":
                        settings_sheet.update_cell(i, 2, get_now_jst())
                        found = True
                        break
                
                if not found:
                    # 新規追加
                    settings_sheet.append_row(["last_report_at", get_now_jst()])
            
            # 最終テキストを表示
            st.subheader("📋 コピー用テキスト")
            st.code(edited_text, language=None)
            st.success("✅ レポート出力日時を更新しました！上記のテキストをコピーしてNoteに投稿してください。")
    
    # 統計情報
    st.markdown("---")
    st.subheader("📈 統計情報")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("完了タスク数", len(completed_tasks))
    with col2:
        st.metric("更新プロジェクト数", len(updated_projects))
    with col3:
        st.metric("文字数", len(edited_text))

# メイン処理
def main():
    # サイドバー
    st.sidebar.title("🚀 Creator's Cockpit")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "ページ選択",
        ["📊 ダッシュボード", "📁 プロジェクト", "💡 資産・アイデア", "📝 Note生成"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"最終更新: {get_now_jst()}")
    
    # ページに応じた処理
    if page == "📊 ダッシュボード":
        show_dashboard()
    elif page == "📁 プロジェクト":
        show_projects()
    elif page == "💡 資産・アイデア":
        show_assets()
    elif page == "📝 Note生成":
        show_note_generator()

if __name__ == "__main__":
    main()

