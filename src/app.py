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
        font-weight: 600;
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

    /* タブのスタイル調整（選択中タブの赤色を上書き） */
    div[data-testid="stTabs"] button[role="tab"] {{
        color: {COLORS['text_dim']} !important;
    }}
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
        color: {COLORS['accent_cyan']} !important;
        border-bottom: 2px solid {COLORS['accent_cyan']} !important;
    }}
    /* アニメーションする下線バーの色も上書き（BaseWeb Tabs） */
    div[data-baseweb="tab-list"] > button[aria-selected="true"]::after {{
        border-bottom: 2px solid {COLORS['accent_cyan']} !important;
    }}
    /* もしハイライトバー要素が使われている場合はこちらも上書き */
    div[data-baseweb="tab-highlight"] {{
        background-color: {COLORS['accent_cyan']} !important;
    }}
    
    /* クイックランチパッドのボタンスタイル */
    .launchpad-btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        padding: 12px 8px;
        background: linear-gradient(145deg, rgba(30,30,35,0.9), rgba(20,20,25,0.8));
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 8px;
        color: #e0e0e0;
        text-decoration: none;
        font-weight: bold;
        transition: all 0.2s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 8px;
    }}
    .launchpad-btn:hover {{
        background: rgba(0, 255, 255, 0.15);
        border-color: #00FFFF;
        color: #fff;
        transform: translateY(-2px);
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
    }}
    .launchpad-icon {{
        margin-right: 8px;
        font-size: 1.2rem;
    }}
    </style>
    """, unsafe_allow_html=True)

def inject_warpgate_scroll_script():
    """ワープゲートexpanderが開かれたときに自動スクロールするJavaScriptを注入"""
    try:
        import streamlit.components.v1 as components
        
        # st.components.v1.htmlを使って確実に実行されるようにする
        # 親ウィンドウのDOMにアクセスするため、window.parentを使用
        components.html("""
    <script>
    (function() {
        try {
            // 親ウィンドウのDOMにアクセス（iframe内で実行される場合）
            let targetWindow, targetDoc;
            try {
                targetWindow = window.parent !== window ? window.parent : window;
                targetDoc = targetWindow.document;
            } catch (e) {
                targetWindow = window;
                targetDoc = document;
            }
        
        function initScrollHandler() {
            // サイドバーが存在するか確認
            const sidebar = targetDoc.querySelector('[data-testid="stSidebar"]');
            
            if (!sidebar) {
                return false;
            }
            
            function findScrollableElement(element) {
                let current = element;
                while (current && current !== targetDoc.body) {
                    const style = targetWindow.getComputedStyle(current);
                    if (style.overflowY === 'auto' || style.overflowY === 'scroll' || 
                        style.overflow === 'auto' || style.overflow === 'scroll') {
                        return current;
                    }
                    current = current.parentElement;
                }
                return null;
            }
            
            function scrollToElement(element) {
                const scrollable = findScrollableElement(element) || sidebar;
                
                // scrollIntoViewを使う方法（より確実）
                try {
                    element.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start',
                        inline: 'nearest'
                    });
                } catch (e) {
                    // フォールバック: 手動でスクロール位置を計算
                    const rect = element.getBoundingClientRect();
                    const scrollableRect = scrollable.getBoundingClientRect();
                    const targetScroll = scrollable.scrollTop + (rect.top - scrollableRect.top) - 20;
                    scrollable.scrollTo({
                        top: targetScroll,
                        behavior: 'smooth'
                    });
                }
            }
            
            // 既に監視が設定されているexpanderを追跡
            const observedExpanders = new WeakSet();
            
            // expanderに監視を設定する関数（クリックイベントとMutationObserverの両方を使用）
            function setupExpanderObserver(expander) {
                // 既に監視済みの場合はスキップ
                if (observedExpanders.has(expander)) {
                    return;
                }
                
                // クリックイベントを監視（より確実）
                const header = expander.querySelector('summary') || expander.querySelector('[role="button"]') || expander;
                header.addEventListener('click', function(e) {
                    // クリック前の高さを記録
                    const initialHeight = expander.offsetHeight;
                    
                    // 定期的に状態をチェックして、開いたときにスクロール
                    let checkCount = 0;
                    const maxChecks = 30; // 最大30回チェック（3秒間）
                    const checkInterval = setInterval(function() {
                        checkCount++;
                        const currentHeight = expander.offsetHeight;
                        // 高さが初期高さから50px以上増加した場合、開いていると判断
                        const isExpanded = currentHeight > initialHeight + 50;
                        
                        // 高さが大幅に増加した場合（開いた場合）
                        if (isExpanded) {
                            clearInterval(checkInterval);
                            // アニメーション完了を待つ
                            setTimeout(function() {
                                scrollToElement(expander);
                            }, 500);
                        } else if (checkCount >= maxChecks) {
                            // 最大チェック回数に達したら停止
                            clearInterval(checkInterval);
                        }
                    }, 100); // 100msごとにチェック
                }, true);
                
                // MutationObserverも設定（バックアップ）
                const observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        if (mutation.type === 'attributes' && mutation.attributeName === 'aria-expanded') {
                            const isExpanded = expander.getAttribute('aria-expanded') === 'true';
                            
                            if (isExpanded) {
                                // アニメーション完了を待つ
                                setTimeout(function() {
                                    scrollToElement(expander);
                                }, 400);
                            }
                        }
                    });
                });
                
                observer.observe(expander, {
                    attributes: true,
                    attributeFilter: ['aria-expanded'],
                    attributeOldValue: true
                });
                
                // 監視済みとしてマーク
                observedExpanders.add(expander);
            }
            
            // expanderが存在するか確認
            const expanders = sidebar.querySelectorAll('[data-testid="stExpander"]');
            
            // 各expanderにaria-expanded属性の変化を監視するMutationObserverを設定
            expanders.forEach(function(expander) {
                setupExpanderObserver(expander);
            });
            
            // サイドバー全体にクリックイベントリスナーを設定（イベント委譲）
            // 注意: このリスナーは各expanderの個別リスナーと重複する可能性があるため、
            // 個別リスナーで処理される場合はここでは処理しない
            sidebar.addEventListener('click', function(e) {
                // クリックされた要素がexpanderか確認
                const clickedExpander = e.target.closest('[data-testid="stExpander"]');
                if (clickedExpander) {
                    // クリック前の高さを記録
                    const initialHeight = clickedExpander.offsetHeight;
                    
                    // 定期的に状態をチェックして、開いたときにスクロール
                    let checkCount = 0;
                    const maxChecks = 30; // 最大30回チェック（3秒間）
                    const checkInterval = setInterval(function() {
                        checkCount++;
                        const currentHeight = clickedExpander.offsetHeight;
                        // 高さが初期高さから50px以上増加した場合、開いていると判断
                        const isExpanded = currentHeight > initialHeight + 50;
                        
                        // 高さが大幅に増加した場合（開いた場合）
                        if (isExpanded) {
                            clearInterval(checkInterval);
                            // アニメーション完了を待つ
                            setTimeout(function() {
                                scrollToElement(clickedExpander);
                            }, 500);
                        } else if (checkCount >= maxChecks) {
                            // 最大チェック回数に達したら停止
                            clearInterval(checkInterval);
                        }
                    }, 100); // 100msごとにチェック
                }
            }, true);
            
            // サイドバーの内容変更を監視して、新しいexpanderが追加されたときに監視を設定
            const sidebarObserver = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    Array.from(mutation.addedNodes).forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            let newExpanders = [];
                            if (node.querySelectorAll) {
                                newExpanders = Array.from(node.querySelectorAll('[data-testid="stExpander"]'));
                            }
                            if (node.getAttribute && node.getAttribute('data-testid') === 'stExpander') {
                                newExpanders.push(node);
                            }
                            newExpanders.forEach(function(expander) {
                                setupExpanderObserver(expander);
                            });
                        }
                    });
                });
            });
            
            sidebarObserver.observe(sidebar, {
                childList: true,
                subtree: true
            });
            
            return true;
        }
        
            // 即座に初期化を試みる
            try {
                if (!initScrollHandler()) {
                    // サイドバーが見つからない場合、少し待ってから再試行
                    setTimeout(function() {
                        try {
                            initScrollHandler();
                        } catch (e) {
                            // エラーは無視
                        }
                    }, 1000);
                }
            } catch (e) {
                // エラーは無視
            }
        } catch (e) {
            // エラーは無視
        }
    })();
    </script>
    """, height=0)
    except Exception as e:
        # エラーは無視
        pass

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

    def delete_row_by_id(self, sheet_name, id_val):
        """id列（1列目）で行を特定して削除する"""
        try:
            sheet = self.spreadsheet.worksheet(sheet_name)
            cell = sheet.find(str(id_val), in_column=1)
            if cell:
                sheet.delete_rows(cell.row)
                self.clear_cache()
                return True
            return False
        except Exception as e:
            st.error(f"削除エラー: {e}")
            return False

    def ensure_sheet_exists(self, sheet_name, headers):
        """シートが存在しない場合は作成し、ヘッダーを設定する"""
        try:
            sheet = self.spreadsheet.worksheet(sheet_name)
            # シートが存在する場合は、ヘッダーを確認
            existing_headers = sheet.row_values(1)
            if not existing_headers:
                # ヘッダーが存在しない場合は追加
                sheet.insert_row(headers, 1)
            elif existing_headers != headers:
                # ヘッダーが一致しない場合は、既存データを保持したままヘッダーのみ更新
                # 既存データがある場合は、ヘッダーのみ更新（データは保持）
                if len(existing_headers) == len(headers):
                    # 列数が同じ場合は、ヘッダー行のみ更新
                    for col_idx, header in enumerate(headers, 1):
                        sheet.update_cell(1, col_idx, header)
                else:
                    # 列数が異なる場合は、警告を出してスキップ（既存データを保護）
                    st.warning(f"シート '{sheet_name}' のヘッダーが異なりますが、既存データを保護するため更新をスキップしました。")
            return sheet
        except gspread.exceptions.WorksheetNotFound:
            # シートが存在しない場合は作成
            try:
                sheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))
                sheet.append_row(headers)
                self.clear_cache()
                return sheet
            except Exception as e:
                st.error(f"シート作成エラー: {e}")
                return None
        except Exception as e:
            st.error(f"シート作成エラー: {e}")
            return None

    def add_comment_history(self, project_id, theme, memo, updated_at):
        """プロジェクトコメント履歴を記録（後方互換性のため残す）
        project_comments_historyシートにのみ記録し、activity_historyには記録しない"""
        try:
            headers = ["id", "project_id", "theme", "memo", "updated_at"]
            sheet = self.ensure_sheet_exists("project_comments_history", headers)
            if not sheet:
                return False
            
            new_id = self.get_next_id("project_comments_history")
            sheet.append_row([new_id, project_id, theme, memo, updated_at])
            self.clear_cache()
            return True
        except Exception as e:
            st.error(f"履歴記録エラー: {e}")
            return False

    def add_activity_history(self, action_type, entity_type, entity_id, entity_name, old_value="", new_value="", details=""):
        """すべての活動履歴を記録する汎用メソッド"""
        try:
            headers = ["id", "action_type", "entity_type", "entity_id", "entity_name", "old_value", "new_value", "details", "created_at"]
            sheet = self.ensure_sheet_exists("activity_history", headers)
            if not sheet:
                return False
            
            new_id = self.get_next_id("activity_history")
            # get_now_jst()をインポートして使用
            from datetime import datetime
            import pytz
            now_str = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')
            
            sheet.append_row([new_id, action_type, entity_type, str(entity_id), entity_name, old_value, new_value, details, now_str])
            self.clear_cache()
            return True
        except Exception as e:
            # エラーメッセージを詳細に表示
            import traceback
            st.error(f"履歴記録エラー: {e}")
            st.error(f"詳細: {traceback.format_exc()}")
            return False

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

def parse_links(text):
    """リンクテキストからURLとラベルのペアを抽出する
    戻り値: [(label, url), ...] のリスト
    """
    if not text:
        return []
    
    links = []
    lines = text.split('\n')
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    markdown_link_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Markdown形式のリンクをチェック [ラベル](URL)
        markdown_match = markdown_link_pattern.search(line)
        if markdown_match:
            label = markdown_match.group(1)
            url = markdown_match.group(2)
            links.append((label, url))
        else:
            # 通常のURLを検索
            urls = url_pattern.findall(line)
            if urls:
                url = urls[0]
                # URLを除去した部分からラベルを抽出
                remaining = line.replace(url, '').strip()
                
                # 形式1: "ラベル: URL" または "ラベル : URL"
                if ':' in remaining:
                    label = remaining.split(':')[0].strip()
                # 形式2: "URL ラベル" または "URL (ラベル)"
                elif remaining.startswith('(') and remaining.endswith(')'):
                    label = remaining[1:-1].strip()
                elif remaining:
                    # URLの後に続くテキストをラベルとして使用
                    label = remaining.strip()
                else:
                    label = ""
                
                links.append((label, url))
    
    return links

def format_links(links):
    """リンクのリストを保存用のテキスト形式に変換する
    引数: [(label, url), ...] のリスト
    戻り値: 保存用のテキスト文字列
    """
    if not links:
        return ""
    
    formatted = []
    for label, url in links:
        if label and label.strip():
            formatted.append(f"{label.strip()}: {url}")
        else:
            formatted.append(url)
    
    return "\n".join(formatted)

def extract_urls_as_html(text):
    """テキスト内のURLをHTMLリンクに変換して返す
    形式: 
    - ラベル: https://example.com
    - https://example.com ラベル
    - https://example.com (ラベル)
    - [ラベル](https://example.com) (Markdown形式)
    """
    if not text:
        return ""
    lines = text.split('\n')
    links_html = []
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    markdown_link_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Markdown形式のリンクをチェック [ラベル](URL)
        markdown_match = markdown_link_pattern.search(line)
        if markdown_match:
            label = markdown_match.group(1)
            url = markdown_match.group(2)
        else:
            # 通常のURLを検索
            urls = url_pattern.findall(line)
            if urls:
                url = urls[0]
                # URLを除去した部分からラベルを抽出
                remaining = line.replace(url, '').strip()
                
                # 形式1: "ラベル: URL" または "ラベル : URL"
                if ':' in remaining:
                    label = remaining.split(':')[0].strip()
                # 形式2: "URL ラベル" または "URL (ラベル)"
                elif remaining.startswith('(') and remaining.endswith(')'):
                    label = remaining[1:-1].strip()
                elif remaining:
                    # URLの後に続くテキストをラベルとして使用
                    label = remaining.strip()
                else:
                    label = "Link"
            else:
                continue
        
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

def render_quick_launchpad(manager):
    """ヘッダー直下に配置する一軍リンク集（クイック・ランチパッド）"""
    shortcuts = manager.get_records("shortcuts")
    if not shortcuts:
        return
    
    # placementが'header'のものだけ抽出
    header_links = [s for s in shortcuts if str(s.get('placement', '')).lower() == 'header']
    
    if not header_links:
        return
    
    st.markdown("##### 🚀 Quick Launch")
    
    # 列数を計算 (最大6列程度で折り返し)
    cols_num = min(len(header_links), 6)
    cols = st.columns(cols_num)
    
    for i, item in enumerate(header_links):
        col_idx = i % cols_num
        with cols[col_idx]:
            url = item.get('url', '#')
            label = item.get('label', 'Link')
            icon = item.get('icon', '🔗')
            
            # ファビコンURLを取得
            favicon_url = get_favicon_url(url)
            
            # ファビコン＋ラベルの形式で表示
            if favicon_url:
                st.markdown(f"""
                <div style="text-align:center; margin-bottom:12px;">
                    <a href="{url}" target="_blank" style="text-decoration:none; color:inherit;">
                        <div style="
                            width:64px; height:64px; margin:0 auto 8px;
                            background:rgba(40,40,45,0.8);
                            border-radius:50%;
                            display:flex; align-items:center; justify-content:center;
                            border:2px solid rgba(255,255,255,0.1);
                            transition: all 0.2s;
                        " onmouseover="this.style.background='rgba(0,255,255,0.15)'; this.style.borderColor='#00FFFF'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 0 15px rgba(0,255,255,0.2)';" onmouseout="this.style.background='rgba(40,40,45,0.8)'; this.style.borderColor='rgba(255,255,255,0.1)'; this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                            <div style="
                                width:48px; height:48px;
                                background:white;
                                border-radius:4px;
                                display:flex; align-items:center; justify-content:center;
                            ">
                                <img src="{favicon_url}" 
                                     style="width:40px; height:40px; object-fit:contain;" 
                                     onerror="this.style.display='none'; this.parentElement.innerHTML='{icon}';" />
                            </div>
                        </div>
                        <div style="
                            color:{COLORS['text_main']};
                            font-size:0.85em;
                            font-weight:500;
                            white-space: nowrap;
                            overflow: hidden;
                            text-overflow: ellipsis;
                        ">{label}</div>
                    </a>
                </div>
                """, unsafe_allow_html=True)
            else:
                # ファビコンが取得できない場合はアイコンを表示
                st.markdown(f"""
                <div style="text-align:center; margin-bottom:12px;">
                    <a href="{url}" target="_blank" style="text-decoration:none; color:inherit;">
                        <div style="
                            width:64px; height:64px; margin:0 auto 8px;
                            background:rgba(40,40,45,0.8);
                            border-radius:50%;
                            display:flex; align-items:center; justify-content:center;
                            border:2px solid rgba(255,255,255,0.1);
                            transition: all 0.2s;
                        " onmouseover="this.style.background='rgba(0,255,255,0.15)'; this.style.borderColor='#00FFFF'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 0 15px rgba(0,255,255,0.2)';" onmouseout="this.style.background='rgba(40,40,45,0.8)'; this.style.borderColor='rgba(255,255,255,0.1)'; this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                            <div style="
                                width:48px; height:48px;
                                background:white;
                                border-radius:4px;
                                display:flex; align-items:center; justify-content:center;
                                font-size:24px;
                            ">{icon}</div>
                        </div>
                        <div style="
                            color:{COLORS['text_main']};
                            font-size:0.85em;
                            font-weight:500;
                            white-space: nowrap;
                            overflow: hidden;
                            text-overflow: ellipsis;
                        ">{label}</div>
                    </a>
                </div>
                """, unsafe_allow_html=True)

def get_favicon_url(url):
    """URLからファビコンURLを生成"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        if domain:
            # GoogleのファビコンAPIを使用
            return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
    except:
        pass
    return None

def truncate_label(label, max_length=6):
    """ラベルを指定文字数に切り詰め（日本語対応）"""
    if not label:
        return ""
    if len(label) <= max_length:
        return label
    return label[:max_length] + "..."

def show_warpgate_modal_content(manager):
    """モーダルウィンドウ内に全リンクを表示（Quick Launchの項目も含む）"""
    shortcuts = manager.get_records("shortcuts")
    if not shortcuts:
        st.info("ショートカット設定がありません")
        return
    
    df = pd.DataFrame(shortcuts)
    
    # 全てのリンクを表示（placementが'header'のものも含む）
    library_links = df
    
    if library_links.empty:
        st.info("ワープゲートに表示するリンクがありません")
        return
    
    st.caption("全てのブックマークへのアクセス")
    
    # カテゴリごとに分類表示
    if 'category' in library_links.columns:
        categories = library_links['category'].astype(str).fillna("").unique()
        categories = [c for c in categories if c.strip()]
        
        if categories:
            for cat in categories:
                st.markdown(f"### 📂 {cat}")
                cat_items = library_links[library_links['category'].astype(str).fillna("") == cat]
                
                # 6列グリッドでリンクを表示（ファビコン＋6文字ラベル形式）
                cols = st.columns(6)
                for idx, (_, item) in enumerate(cat_items.iterrows()):
                    with cols[idx % 6]:
                        label = item.get('label', 'Link')
                        url = item.get('url', '#')
                        icon = item.get('icon', '🔗')
                        
                        # ファビコンURLを取得
                        favicon_url = get_favicon_url(url)
                        
                        # ラベルを6文字に切り詰め
                        truncated_label = truncate_label(label, 6)
                        
                        # ファビコン＋6文字ラベルの形式で表示
                        if favicon_url:
                            st.markdown(f"""
                            <div style="text-align:center; margin-bottom:12px;">
                                <a href="{url}" target="_blank" style="text-decoration:none; color:inherit;">
                                    <div style="
                                        width:64px; height:64px; margin:0 auto 8px;
                                        background:rgba(40,40,45,0.8);
                                        border-radius:50%;
                                        display:flex; align-items:center; justify-content:center;
                                        border:2px solid rgba(255,255,255,0.1);
                                    ">
                                        <div style="
                                            width:48px; height:48px;
                                            background:white;
                                            border-radius:4px;
                                            display:flex; align-items:center; justify-content:center;
                                        ">
                                            <img src="{favicon_url}" 
                                                 style="width:40px; height:40px; object-fit:contain;" 
                                                 onerror="this.style.display='none'; this.parentElement.innerHTML='{icon}';" />
                                        </div>
                                    </div>
                                    <div style="
                                        color:{COLORS['text_main']};
                                        font-size:0.85em;
                                        font-weight:500;
                                        white-space: nowrap;
                                        overflow: hidden;
                                        text-overflow: ellipsis;
                                    ">{truncated_label}</div>
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # ファビコンが取得できない場合はアイコンを表示
                            st.markdown(f"""
                            <div style="text-align:center; margin-bottom:12px;">
                                <a href="{url}" target="_blank" style="text-decoration:none; color:inherit;">
                                    <div style="
                                        width:64px; height:64px; margin:0 auto 8px;
                                        background:rgba(40,40,45,0.8);
                                        border-radius:50%;
                                        display:flex; align-items:center; justify-content:center;
                                        border:2px solid rgba(255,255,255,0.1);
                                    ">
                                        <div style="
                                            width:48px; height:48px;
                                            background:white;
                                            border-radius:4px;
                                            display:flex; align-items:center; justify-content:center;
                                            font-size:24px;
                                        ">{icon}</div>
                                    </div>
                                    <div style="
                                        color:{COLORS['text_main']};
                                        font-size:0.85em;
                                        font-weight:500;
                                        white-space: nowrap;
                                        overflow: hidden;
                                        text-overflow: ellipsis;
                                    ">{truncated_label}</div>
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                st.markdown("---")
        
        # カテゴリが空欄のリンクを表示
        no_cat_items = library_links[library_links['category'].astype(str).fillna("").str.strip() == ""]
        if not no_cat_items.empty:
            st.markdown("### 📌 その他")
            cols = st.columns(6)
            for idx, (_, item) in enumerate(no_cat_items.iterrows()):
                with cols[idx % 6]:
                    label = item.get('label', 'Link')
                    url = item.get('url', '#')
                    icon = item.get('icon', '🔗')
                    
                    # ファビコンURLを取得
                    favicon_url = get_favicon_url(url)
                    
                    # ラベルを6文字に切り詰め
                    truncated_label = truncate_label(label, 6)
                    
                    # ファビコン＋6文字ラベルの形式で表示
                    if favicon_url:
                        st.markdown(f"""
                        <div style="text-align:center; margin-bottom:12px;">
                            <a href="{url}" target="_blank" style="text-decoration:none; color:inherit;">
                                <div style="
                                    width:64px; height:64px; margin:0 auto 8px;
                                    background:rgba(40,40,45,0.8);
                                    border-radius:50%;
                                    display:flex; align-items:center; justify-content:center;
                                    border:2px solid rgba(255,255,255,0.1);
                                ">
                                    <div style="
                                        width:48px; height:48px;
                                        background:white;
                                        border-radius:4px;
                                        display:flex; align-items:center; justify-content:center;
                                    ">
                                        <img src="{favicon_url}" 
                                             style="width:40px; height:40px; object-fit:contain;" 
                                             onerror="this.style.display='none'; this.parentElement.innerHTML='{icon}';" />
                                    </div>
                                </div>
                                <div style="
                                    color:{COLORS['text_main']};
                                    font-size:0.85em;
                                    font-weight:500;
                                    white-space: nowrap;
                                    overflow: hidden;
                                    text-overflow: ellipsis;
                                ">{truncated_label}</div>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # ファビコンが取得できない場合はアイコンを表示
                        st.markdown(f"""
                        <div style="text-align:center; margin-bottom:12px;">
                            <a href="{url}" target="_blank" style="text-decoration:none; color:inherit;">
                                <div style="
                                    width:64px; height:64px; margin:0 auto 8px;
                                    background:rgba(40,40,45,0.8);
                                    border-radius:50%;
                                    display:flex; align-items:center; justify-content:center;
                                    border:2px solid rgba(255,255,255,0.1);
                                ">
                                    <div style="
                                        width:48px; height:48px;
                                        background:white;
                                        border-radius:4px;
                                        display:flex; align-items:center; justify-content:center;
                                        font-size:24px;
                                    ">{icon}</div>
                                </div>
                                <div style="
                                    color:{COLORS['text_main']};
                                    font-size:0.85em;
                                    font-weight:500;
                                    white-space: nowrap;
                                    overflow: hidden;
                                    text-overflow: ellipsis;
                                ">{truncated_label}</div>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)

def render_warp_gate_trigger(manager):
    """サイドバー：ワープゲート起動ボタン"""
    st.sidebar.markdown("---")
    
    # 起動ボタン
    if st.sidebar.button("🌌 ワープゲートを開く", use_container_width=True, type="primary"):
        st.session_state['show_warpgate'] = True
        st.rerun()
    
    # モーダル表示（st.dialogが使えない場合はメイン画面にexpanderで表示）
    if st.session_state.get('show_warpgate', False):
        # Streamlit 1.34.0以降のst.dialogを試行、失敗した場合はexpanderで代用
        try:
            # st.dialogが利用可能かチェック
            if hasattr(st, 'dialog'):
                with st.dialog("🌌 ワープゲート (Link Library)"):
                    show_warpgate_modal_content(manager)
                    if st.button("閉じる", use_container_width=True):
                        st.session_state['show_warpgate'] = False
                        st.rerun()
            else:
                # st.dialogが使えない場合はメイン画面にexpanderで表示（自動展開）
                with st.expander("🌌 ワープゲート (Link Library)", expanded=True):
                    show_warpgate_modal_content(manager)
                    if st.button("閉じる", use_container_width=True):
                        st.session_state['show_warpgate'] = False
                        st.rerun()
        except Exception:
            # エラー時はメイン画面にexpanderで表示（自動展開）
            with st.expander("🌌 ワープゲート (Link Library)", expanded=True):
                show_warpgate_modal_content(manager)
                if st.button("閉じる", use_container_width=True):
                    st.session_state['show_warpgate'] = False
                    st.rerun()

def render_dashboard(manager):
    """ダッシュボード (メイン画面)"""
    # --- クイックアイデア追加ボタン（ページ最上部） ---
    st.markdown("### 💡 クイックアイデア追加")
    col_idea_btn, col_idea_dummy = st.columns([3, 1])
    with col_idea_btn:
        if st.button("💡 新しいアイデアを追加する", type="primary", use_container_width=True, key="add_idea_top"):
            st.session_state["show_idea_form"] = True

    # ボタン押下時に表示するアイデア入力フォーム
    if st.session_state.get("show_idea_form", False):
        with st.expander("✏️ アイデアを登録する", expanded=True):
            with st.form("idea_quick_add_form"):
                idea_content = st.text_area("アイデア内容 (必須)", height=4)

                submitted_idea = st.form_submit_button("このアイデアを保存する", use_container_width=True)
                if submitted_idea:
                    if idea_content:
                        new_idea_id = manager.get_next_id("ideas")
                        # カラム構成: id, content, created_at
                        ok = manager.add_row("ideas", [new_idea_id, idea_content, get_now_jst()])
                        if ok:
                            # 活動履歴に記録
                            manager.add_activity_history(
                                action_type="アイデア追加",
                                entity_type="ideas",
                                entity_id=new_idea_id,
                                entity_name=idea_content[:50] + "..." if len(idea_content) > 50 else idea_content,
                                old_value="",
                                new_value=idea_content,
                                details=""
                            )
                            add_log(f"新規アイデア追加: {idea_content[:20]}...")
                            st.success("アイデアを保存しました！")
                            st.session_state["show_idea_form"] = False
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.error("アイデア内容を入力してください。")

    # --- クイック・ランチパッド (ヘッダー直下) ---
    render_quick_launchpad(manager)
    
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
                now_str = get_now_jst()
                manager.update_cell_by_id("tasks", task['id'], "status", "済")
                manager.update_cell_by_id("tasks", task['id'], "completed_at", now_str)
                # 活動履歴に記録
                manager.add_activity_history(
                    action_type="タスク完了",
                    entity_type="tasks",
                    entity_id=task['id'],
                    entity_name=title,
                    old_value="未",
                    new_value="済",
                    details=f"カテゴリ: {cat}" + (f", メモ: {memo}" if memo else "")
                )
                st.session_state.daily_exp = st.session_state.get('daily_exp', 0) + 1
                add_log(f"クエスト完了: {title}")
                st.rerun()

        # 新規タスク追加フォーム
        # フォームリセット用のキーを管理
        if 'task_form_key' not in st.session_state:
            st.session_state.task_form_key = 0
        
        with st.expander("➕ 新しいクエストを受注する", expanded=False):
            with st.form(f"add_task_form_{st.session_state.task_form_key}"):
                c_title, c_cat = st.columns([3, 1])
                with c_title:
                    new_title = st.text_input("クエスト名 (必須)", key=f"task_title_{st.session_state.task_form_key}")
                with c_cat:
                    new_cat = st.selectbox("カテゴリ", list(CATEGORY_ICONS.keys()), key=f"task_cat_{st.session_state.task_form_key}")
                
                new_memo = st.text_area("メモ (任意)", height=3, key=f"task_memo_{st.session_state.task_form_key}")
                
                if st.form_submit_button("登録する", use_container_width=True):
                    if new_title:
                        new_id = manager.get_next_id("tasks")
                        now_str = get_now_jst()
                        manager.add_row("tasks", [new_id, new_title, new_cat, "未", new_memo, now_str, ""])
                        # 活動履歴に記録
                        manager.add_activity_history(
                            action_type="タスク追加",
                            entity_type="tasks",
                            entity_id=new_id,
                            entity_name=new_title,
                            old_value="",
                            new_value="未",
                            details=f"カテゴリ: {new_cat}" + (f", メモ: {new_memo}" if new_memo else "")
                        )
                        add_log(f"新規クエスト追加: {new_title}")
                        # フォームをリセットするためにキーを変更
                        st.session_state.task_form_key += 1
                        st.success("登録しました")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("クエスト名を入力してください")

    # === 右カラム: プロジェクト状況 ===
    with col_right:
        st.subheader("📊 プロジェクト戦況")
        
        projects = manager.get_records("projects")
        # 進行中のものを優先表示（完了プロジェクトは非表示）
        active_projects = [p for p in projects if p.get('status') == '進行中']
        other_projects = [p for p in projects if p.get('status') != '進行中' and p.get('status') != '完了']
        
        display_list = active_projects + other_projects
        
        for proj in display_list[:5]: # 最大5件表示
            status = proj.get('status', '進行中')
            theme = proj.get('theme', 'No Theme')
            current_memo = proj.get('memo', '')
            
            # ステータス色分け
            color = COLORS['accent_blue']
            if status == '完了': color = COLORS['accent_green']
            elif status == '保留': color = COLORS['text_dim']
            elif status == '進行中': color = COLORS['accent_cyan']

            # リンクHTML生成
            links_html = extract_urls_as_html(proj.get('links', ''))
            
            # メモ編集用のキー
            edit_memo_key = f"dashboard_edit_memo_{proj['id']}"
            is_editing_memo = st.session_state.get(edit_memo_key, False)
            
            if is_editing_memo:
                # 編集モード - カード全体を再構築
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
                
                # 編集フォームを表示
                with st.form(f"dashboard_memo_edit_{proj['id']}"):
                    new_memo = st.text_area("💬 メモ", value=current_memo, height=4, key=f"dashboard_memo_{proj['id']}")
                    col_save, col_cancel = st.columns([1, 1])
                    with col_save:
                        if st.form_submit_button("保存", use_container_width=True, type="primary"):
                            if new_memo != current_memo:
                                old_memo = current_memo
                                now_str = get_now_jst()
                                manager.update_cell_by_id("projects", proj['id'], "memo", new_memo)
                                manager.update_cell_by_id("projects", proj['id'], "memo_updated_at", now_str)
                                # 活動履歴に記録
                                manager.add_activity_history(
                                    action_type="プロジェクトコメント更新",
                                    entity_type="projects",
                                    entity_id=proj['id'],
                                    entity_name=theme,
                                    old_value=old_memo,
                                    new_value=new_memo,
                                    details=""
                                )
                                # 後方互換性のため、project_comments_historyにも記録
                                manager.add_comment_history(proj['id'], theme, new_memo, now_str)
                                add_log(f"プロジェクトメモ更新(ダッシュボード): {theme}")
                                st.success("メモを更新しました")
                                st.session_state[edit_memo_key] = False
                                time.sleep(0.3)
                                st.rerun()
                            else:
                                st.session_state[edit_memo_key] = False
                                st.rerun()
                    with col_cancel:
                        if st.form_submit_button("キャンセル", use_container_width=True):
                            st.session_state[edit_memo_key] = False
                            st.rerun()
            else:
                # 通常表示モード - メモを含む完全なカードを表示
                # メモ表示用HTML
                if current_memo:
                    memo_lines = current_memo.replace('\n', '<br>')
                    memo_html = f'<div style="margin-top:8px; padding:8px; background:rgba(0,0,0,0.2); border-radius:4px; color:{COLORS["text_dim"]}; font-size:0.9em; white-space:pre-wrap;">💬 {memo_lines}</div>'
                else:
                    memo_html = '<div style="margin-top:8px; padding:8px; background:rgba(0,0,0,0.1); border-radius:4px; color:rgba(160,160,160,0.5); font-size:0.85em; font-style:italic;">💬 メモがありません</div>'
                
                # HTMLカード描画（メモを含む、完全に閉じる）
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
                    {memo_html}
                </div>
                """, unsafe_allow_html=True)
                
                # 編集ボタン（カードの下に配置）
                if st.button("✏️ メモを編集", key=f"dashboard_edit_btn_{proj['id']}", use_container_width=True):
                    st.session_state[edit_memo_key] = True
                    st.rerun()
            
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
        return
    
    # 完了プロジェクト表示のチェックボックス
    show_completed = st.checkbox("完了したプロジェクトを表示", value=False, key="show_completed_projects")
    
    # 完了プロジェクトをフィルタリング
    if not show_completed:
        projects = [p for p in projects if p.get('status', '進行中') != '完了']
    
    if not projects:
        st.info("表示するプロジェクトがありません。")
        return
        
    # アコーディオンで一覧表示（デフォルトはすべて閉じる）
    for proj in projects:
        status = proj.get('status', '進行中')
        icon = "🔹" if status == '進行中' else "✅" if status == '完了' else "💤"
        
        with st.expander(f"{icon} {proj.get('theme')}", expanded=False):
            c_edit, c_view = st.columns([1, 1])
            
            # 編集エリア
            with c_edit:
                st.caption("🛠 設定変更")
                new_theme = st.text_input("テーマ名", value=proj.get('theme'), key=f"th_{proj['id']}")
                new_status = st.selectbox("状態", ["進行中", "完了", "保留"], 
                                        index=["進行中", "完了", "保留"].index(status) if status in ["進行中", "完了", "保留"] else 0,
                                        key=f"st_{proj['id']}")
                
                if st.button("更新を保存", key=f"upd_{proj['id']}"):
                    old_theme = proj.get('theme', '')
                    old_status = proj.get('status', '')
                    now_str = get_now_jst()
                    
                    # テーマが変更された場合
                    if new_theme != old_theme:
                        manager.update_cell_by_id("projects", proj['id'], "theme", new_theme)
                        manager.add_activity_history(
                            action_type="プロジェクトテーマ更新",
                            entity_type="projects",
                            entity_id=proj['id'],
                            entity_name=new_theme,
                            old_value=old_theme,
                            new_value=new_theme,
                            details=""
                        )
                    
                    # ステータスが変更された場合
                    if new_status != old_status:
                        manager.update_cell_by_id("projects", proj['id'], "status", new_status)
                        manager.add_activity_history(
                            action_type="プロジェクトステータス更新",
                            entity_type="projects",
                            entity_id=proj['id'],
                            entity_name=new_theme if new_theme != old_theme else old_theme,
                            old_value=old_status,
                            new_value=new_status,
                            details=""
                        )
                    
                    manager.update_cell_by_id("projects", proj['id'], "updated_at", now_str)
                    st.success("更新しました！")
                    time.sleep(0.5)
                    st.rerun()

            # 詳細エリア
            with c_view:
                st.caption("📝 詳細情報")
                # リンク編集とメモ編集
                st.markdown("**関連リンク**")
                
                # リンクデータの初期化
                links_key = f"project_links_{proj['id']}"
                if links_key not in st.session_state:
                    # 既存のリンクをパース
                    existing_links = parse_links(proj.get('links', ''))
                    if not existing_links:
                        existing_links = [("", "")]
                    st.session_state[links_key] = existing_links
                
                # リンク入力項目
                links_to_remove = []
                for idx, (label, url) in enumerate(st.session_state[links_key]):
                    col1, col2, col3 = st.columns([3, 3, 1])
                    with col1:
                        new_label = st.text_input("ラベル", value=label, key=f"link_label_{proj['id']}_{idx}", placeholder="例: Note記事")
                    with col2:
                        new_url = st.text_input("URL", value=url, key=f"link_url_{proj['id']}_{idx}", placeholder="https://example.com")
                    with col3:
                        if st.button("削除", key=f"link_del_{proj['id']}_{idx}"):
                            links_to_remove.append(idx)
                    
                    # 値を更新
                    if idx < len(st.session_state[links_key]):
                        st.session_state[links_key][idx] = (new_label, new_url)
                
                # 削除処理
                for idx in sorted(links_to_remove, reverse=True):
                    if idx < len(st.session_state[links_key]):
                        st.session_state[links_key].pop(idx)
                        st.rerun()
                
                # リンク追加ボタン
                if st.button("➕ リンクを追加", key=f"link_add_{proj['id']}"):
                    st.session_state[links_key].append(("", ""))
                    st.rerun()
                
                new_memo = st.text_area("メモ", value=proj.get('memo', ''), height=80, key=f"mm_{proj['id']}")
                
                # ここだけ個別保存ボタン（誤操作防止のため）
                if st.button("詳細を保存", key=f"det_{proj['id']}"):
                    old_memo = proj.get('memo', '')
                    # リンクをフォーマットして保存
                    formatted_links = format_links(st.session_state[links_key])
                    manager.update_cell_by_id("projects", proj['id'], "links", formatted_links)
                    manager.update_cell_by_id("projects", proj['id'], "memo", new_memo)
                    # メモが変更された場合、memo_updated_atを更新し、履歴に記録
                    if new_memo != old_memo:
                        now_str = get_now_jst()
                        manager.update_cell_by_id("projects", proj['id'], "memo_updated_at", now_str)
                        # 活動履歴に記録
                        theme = proj.get('theme', '')
                        manager.add_activity_history(
                            action_type="プロジェクトコメント更新",
                            entity_type="projects",
                            entity_id=proj['id'],
                            entity_name=theme,
                            old_value=old_memo,
                            new_value=new_memo,
                            details=""
                        )
                        # 後方互換性のため、project_comments_historyにも記録（activity_historyには記録しない）
                        manager.add_comment_history(proj['id'], theme, new_memo, now_str)
                        add_log(f"プロジェクトコメント履歴記録: {theme}")
                    st.success("詳細を保存しました")
                    time.sleep(0.5)
                    st.rerun()

    st.markdown("---")
    with st.expander("➕ 新規プロジェクト立ち上げ", expanded=False):
        # 新規プロジェクト用のリンクデータの初期化
        if 'new_project_links' not in st.session_state:
            st.session_state.new_project_links = [("", "")]
        
        st.subheader("New Project")
        f_theme = st.text_input("プロジェクトテーマ (必須)", key="new_proj_theme")
        st.markdown("**関連リンク**")
        
        # リンク入力項目
        links_to_remove = []
        for idx, (label, url) in enumerate(st.session_state.new_project_links):
            col1, col2, col3 = st.columns([3, 3, 1])
            with col1:
                new_label = st.text_input("ラベル", value=label, key=f"new_link_label_{idx}", placeholder="例: Note記事")
            with col2:
                new_url = st.text_input("URL", value=url, key=f"new_link_url_{idx}", placeholder="https://example.com")
            with col3:
                if len(st.session_state.new_project_links) > 1:
                    if st.button("削除", key=f"new_link_del_{idx}"):
                        links_to_remove.append(idx)
                else:
                    st.write("")  # スペーサー
            
            # 値を更新
            if idx < len(st.session_state.new_project_links):
                st.session_state.new_project_links[idx] = (new_label, new_url)
        
        # 削除処理
        if links_to_remove:
            for idx in sorted(links_to_remove, reverse=True):
                if idx < len(st.session_state.new_project_links):
                    st.session_state.new_project_links.pop(idx)
            st.rerun()
        
        # リンク追加ボタン
        if st.button("➕ リンクを追加", key="new_link_add"):
            st.session_state.new_project_links.append(("", ""))
            st.rerun()
        
        f_memo = st.text_area("メモ", key="new_proj_memo")
        
        if st.button("作成する", type="primary", use_container_width=True, key="new_proj_submit"):
            if f_theme:
                new_id = manager.get_next_id("projects")
                now_str = get_now_jst()
                # リンクをフォーマットして保存
                f_links = format_links(st.session_state.new_project_links)
                # id, theme, status, links, memo, updated_at, memo_updated_at
                # メモが入力されている場合、memo_updated_atも設定し、履歴に記録
                memo_updated_at = now_str if f_memo.strip() else ""
                manager.add_row("projects", [new_id, f_theme, "進行中", f_links, f_memo, now_str, memo_updated_at])
                # リンクデータをリセット
                st.session_state.new_project_links = [("", "")]
                # 活動履歴に記録
                manager.add_activity_history(
                    action_type="プロジェクト作成",
                    entity_type="projects",
                    entity_id=new_id,
                    entity_name=f_theme,
                    old_value="",
                    new_value="進行中",
                    details=f"メモ: {f_memo}" if f_memo.strip() else ""
                )
                # メモが入力されている場合、コメント履歴にも記録
                if f_memo.strip():
                    manager.add_comment_history(new_id, f_theme, f_memo, now_str)
                    add_log(f"新規プロジェクトコメント履歴記録: {f_theme}")
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
    
    # 活動履歴シートからすべての履歴を取得
    activity_history = manager.get_records("activity_history")
    
    # 日時をdatetimeオブジェクトに変換して比較
    try:
        from datetime import datetime
        import pytz
        # last_report_atをdatetimeオブジェクトに変換
        if last_report_at and last_report_at != "2000-01-01 00:00:00":
            try:
                last_report_dt = datetime.strptime(last_report_at, '%Y-%m-%d %H:%M:%S')
            except:
                # フォーマットが異なる場合のフォールバック
                last_report_dt = datetime.strptime("2000-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        else:
            last_report_dt = datetime.strptime("2000-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        st.warning(f"日時変換エラー: {e}")
        last_report_dt = datetime.strptime("2000-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
    
    # 日時を比較してフィルタリング
    recent_activities = []
    for a in activity_history:
        created_at_str = a.get('created_at', '')
        if created_at_str and created_at_str.strip():
            try:
                # created_atをdatetimeオブジェクトに変換
                created_at_dt = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                if created_at_dt > last_report_dt:
                    recent_activities.append(a)
            except Exception as e:
                # 日時変換に失敗した場合は文字列比較でフォールバック
                if created_at_str > last_report_at:
                    recent_activities.append(a)
    
    # 時系列でソート（文字列としてソート）
    recent_activities.sort(key=lambda x: x.get('created_at', ''))
    
    # レポート本文作成
    report_text = f"## 🚀 活動レポート ({get_now_jst()[:10]})\n\n"
    
    if recent_activities:
        report_text += "### 📋 活動履歴（時系列）\n\n"
        
        # アクションタイプごとにアイコンを設定
        action_icons = {
            "タスク追加": "➕",
            "タスク完了": "✅",
            "プロジェクト作成": "🆕",
            "プロジェクトステータス更新": "🔄",
            "プロジェクトテーマ更新": "✏️",
            "プロジェクトコメント更新": "💬",
            "アイデア追加": "💡"
        }
        
        for activity in recent_activities:
            action_type = activity.get('action_type', '')
            entity_name = activity.get('entity_name', '')
            entity_type = activity.get('entity_type', '')
            old_value = activity.get('old_value', '')
            new_value = activity.get('new_value', '')
            details = activity.get('details', '')
            created_at = activity.get('created_at', '')
            
            icon = action_icons.get(action_type, "📝")
            
            report_text += f"**{icon} {action_type}** ({created_at})\n"
            report_text += f"- **対象**: {entity_name} ({entity_type})\n"
            
            # プロジェクトコメント更新の場合は、コメント内容を詳細に表示（通常の内容表示はスキップ）
            if action_type == "プロジェクトコメント更新" and new_value:
                memo_lines = new_value.strip().split('\n')
                if len(memo_lines) > 1 or (len(memo_lines) == 1 and memo_lines[0].strip()):
                    report_text += f"- **コメント内容**:\n"
                    for line in memo_lines:
                        if line.strip():
                            report_text += f"  - {line.strip()}\n"
            else:
                # その他のアクションタイプは通常の表示
                if old_value and new_value:
                    report_text += f"- **変更**: {old_value} → {new_value}\n"
                elif new_value:
                    report_text += f"- **内容**: {new_value}\n"
            
            if details:
                report_text += f"- **詳細**: {details}\n"
            
            report_text += "\n"
        
        report_text += "\n"
    else:
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


def render_assets_and_ideas(manager):
    """資産・アイデアBOX画面"""
    st.title("📦 資産・アイデアBOX")
    st.caption("アイデアのストックや各種資産をここから確認できます")

    tab_ideas, tab_assets = st.tabs(["💡 アイデア一覧", "📚 その他の資産（準備中）"])

    # --- アイデア一覧タブ ---
    with tab_ideas:
        # ideasシートを直接読み込み（ヘッダー行を明示的に扱う）
        try:
            ideas_sheet = manager.spreadsheet.worksheet("ideas")
            values = ideas_sheet.get_all_values()
        except gspread.exceptions.WorksheetNotFound:
            values = []
        except Exception as e:
            st.error(f"ideasシートの読み込みでエラーが発生しました: {e}")
            values = []

        # 1行目をヘッダーとして解釈し、2行目以降をデータとして扱う
        if not values or len(values) <= 1:
            st.info("まだアイデアが登録されていません。右上のボタンやダッシュボードから登録できます。")
        else:
            headers = values[0]
            rows = values[1:]
            df_ideas = pd.DataFrame(rows, columns=headers)

            # 期待するカラム名を揃える（ユーザー要望: id, content, created_at）
            if "content" not in df_ideas.columns and "title" in df_ideas.columns:
                df_ideas.rename(columns={"title": "content"}, inplace=True)

            # --- 一覧表示をメインに ---
            # フォーム開閉フラグの初期化
            if "show_assets_idea_form" not in st.session_state:
                st.session_state["show_assets_idea_form"] = False

            top_cols = st.columns([3, 1])
            with top_cols[0]:
                st.subheader("💡 ストックされたアイデア一覧")
            with top_cols[1]:
                # 現在の状態に応じてラベルを決定
                current = st.session_state["show_assets_idea_form"]
                btn_label = "➕ アイデアを登録" if not current else "✖️ 閉じる"
                if st.button(btn_label, key="toggle_assets_idea_form"):
                    # 状態を反転させて即座に再実行（ラベルとフォーム表示を同期させる）
                    st.session_state["show_assets_idea_form"] = not current
                    st.rerun()

            # --- 一覧の下に、ボタンで開閉する登録フォーム ---
            if st.session_state.get("show_assets_idea_form", False):
                st.subheader("✏️ 新規アイデア登録")
                with st.form("idea_add_from_assets"):
                    new_content = st.text_area("アイデア内容 (必須)", height=4)
                    submitted_new = st.form_submit_button("このアイデアを登録する", use_container_width=True)
                    if submitted_new:
                        if new_content:
                            new_id = manager.get_next_id("ideas")
                            ok = manager.add_row("ideas", [new_id, new_content, get_now_jst()])
                            if ok:
                                # 活動履歴に記録
                                manager.add_activity_history(
                                    action_type="アイデア追加",
                                    entity_type="ideas",
                                    entity_id=new_id,
                                    entity_name=new_content[:50] + "..." if len(new_content) > 50 else new_content,
                                    old_value="",
                                    new_value=new_content,
                                    details=""
                                )
                                add_log(f"新規アイデア追加(ASSETS): {new_content[:20]}...")
                                st.success("アイデアを登録しました！")
                                st.session_state["show_assets_idea_form"] = False
                                time.sleep(0.5)
                                st.rerun()
                        else:
                            st.error("アイデア内容を入力してください。")
                st.markdown("---")

            # フィルタUI
            keyword = st.text_input("キーワードで絞り込み", placeholder="アイデア内容から検索")

            # 絞り込み処理（contentカラム前提 / なければスキップ）
            if "content" in df_ideas.columns and keyword:
                mask = df_ideas["content"].astype(str).str.contains(keyword, case=False)
                df_ideas = df_ideas[mask]

            # 日付があれば新しい順に
            if "created_at" in df_ideas.columns:
                try:
                    df_ideas["created_at"] = pd.to_datetime(df_ideas["created_at"])
                    df_ideas = df_ideas.sort_values("created_at", ascending=False)
                except Exception:
                    pass

            # 行ごとに削除ボタン付きで表示（IDは内部用としてのみ使用）
            if df_ideas.empty:
                st.info("該当するアイデアがありません。")
            else:
                for idx, row in df_ideas.iterrows():
                    idea_id = row.get("id", "")
                    content = row.get("content", "")
                    created = row.get("created_at", "")
                    
                    # 編集中のアイデアIDを管理
                    edit_key = f"idea_edit_{idea_id}"
                    is_editing = st.session_state.get(edit_key, False)

                    if is_editing:
                        # 編集フォーム
                        with st.expander(f"✏️ アイデアを編集 (ID: {idea_id})", expanded=True):
                            with st.form(f"idea_edit_form_{idea_id}"):
                                edited_content = st.text_area("アイデア内容", value=content, height=4, key=f"idea_edit_content_{idea_id}")
                                
                                col_save, col_cancel = st.columns([1, 1])
                                with col_save:
                                    if st.form_submit_button("保存", use_container_width=True, type="primary"):
                                        if edited_content.strip():
                                            old_content = content
                                            ok = manager.update_cell_by_id("ideas", idea_id, "content", edited_content)
                                            if ok:
                                                # 活動履歴に記録
                                                manager.add_activity_history(
                                                    action_type="アイデア編集",
                                                    entity_type="ideas",
                                                    entity_id=idea_id,
                                                    entity_name=edited_content[:50] + "..." if len(edited_content) > 50 else edited_content,
                                                    old_value=old_content,
                                                    new_value=edited_content,
                                                    details=""
                                                )
                                                add_log(f"アイデア編集: id={idea_id}")
                                                st.success("アイデアを更新しました。")
                                                st.session_state[edit_key] = False
                                                time.sleep(0.3)
                                                st.rerun()
                                        else:
                                            st.error("アイデア内容を入力してください。")
                                with col_cancel:
                                    if st.form_submit_button("キャンセル", use_container_width=True):
                                        st.session_state[edit_key] = False
                                        st.rerun()
                    else:
                        # 通常表示
                        cols = st.columns([5, 2, 1, 1])
                        with cols[0]:
                            st.markdown(f"{content}")
                            if created:
                                st.caption(f"登録日時: {created}")
                        with cols[2]:
                            if st.button("編集", key=f"idea_edit_btn_{idea_id}"):
                                st.session_state[edit_key] = True
                                st.rerun()
                        with cols[3]:
                            if st.button("削除", key=f"idea_del_{idea_id}"):
                                if idea_id:
                                    ok = manager.delete_row_by_id("ideas", idea_id)
                                    if ok:
                                        add_log(f"アイデア削除: id={idea_id}")
                                        st.success("アイデアを削除しました。")
                                        time.sleep(0.3)
                                        st.rerun()

                    # 各アイテムの上に区切り線を表示（先頭要素は除く）
                    if idx != 0:
                        st.markdown("---")

    # --- その他の資産タブ（将来拡張用） ---
    with tab_assets:
        st.info("今後、プロンプト集やテンプレートなどの資産をここに整理していく予定です。")

# ==========================================
# 6. メイン実行関数
# ==========================================
def main():
    inject_custom_css()
    inject_warpgate_scroll_script()
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
            
        render_warp_gate_trigger(manager)
    
    # ページルーティング
    page = st.session_state['current_page']
    
    if page == "DASHBOARD":
        render_dashboard(manager)
    elif page == "CAMPAIGN":
        render_project_manager(manager)
    elif page == "ASSETS":
        render_assets_and_ideas(manager)
    elif page == "REPORT":
        render_report_generator(manager)

if __name__ == "__main__":
    main()