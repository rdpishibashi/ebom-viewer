import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(
    page_title="EBOM Viewer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# カスタムCSS - MacOS Finderスタイル
st.markdown("""
<style>
    /* 全体のパディングを調整 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* リストアイテムのスタイル */
    .stRadio > div {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 0.5rem;
        max-height: 400px;
        overflow-y: auto;
    }

    /* 選択されたアイテムのハイライト */
    .stRadio > div > label > div[data-checked="true"] {
        background-color: #0066cc !important;
        color: white !important;
    }

    /* ヘッダースタイル */
    .structure-header {
        background-color: #e9ecef;
        padding: 0.5rem;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    /* 横スクロール可能なコンテナ */
    .scrollable-columns {
        overflow-x: auto;
        white-space: nowrap;
    }

    /* 縦スクロール可能なコンテナ */
    .scrollable-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 0.5rem;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        background-color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# タイトル
st.title("EBOM Viewer")

# Excelファイルの読み込み
@st.cache_data
def load_data():
    """Excelファイルからデータを読み込む"""
    try:
        structure_df = pd.read_excel('ebom.xlsx', sheet_name='Structure')
        parts_list_df = pd.read_excel('ebom.xlsx', sheet_name='Parts List')
        parts_df = pd.read_excel('ebom.xlsx', sheet_name='Parts')
        return structure_df, parts_list_df, parts_df
    except Exception as e:
        st.error(f"Excelファイルの読み込みに失敗しました: {e}")
        return None, None, None

# データ読み込み
structure_df, parts_list_df, parts_df = load_data()

if structure_df is not None and parts_list_df is not None and parts_df is not None:
    # NaN値を処理
    structure_df = structure_df.fillna('')
    parts_list_df = parts_list_df.fillna('')
    parts_df = parts_df.fillna('')

    # セッション状態の初期化
    if 'selected_path' not in st.session_state:
        st.session_state.selected_path = []  # 選択されたパス [level1_item, level2_item, ...]

    if 'selected_part_number' not in st.session_state:
        st.session_state.selected_part_number = None

    # Structure ウィンドウ
    st.markdown('<div class="structure-header">Structure</div>', unsafe_allow_html=True)

    # 横スクロール可能なカラムのコンテナ
    structure_container = st.container()

    with structure_container:
        # 動的に必要なカラム数を計算（最初は3カラム表示）
        max_display_cols = 3
        total_levels = len(st.session_state.selected_path) + 1
        num_cols = min(max_display_cols, total_levels)

        # カラムを動的に生成
        if num_cols > 0:
            cols = st.columns(num_cols)
        else:
            cols = [st.container()]

        # Level 1: 親品番が「装置」の子品番を表示
        with cols[0]:
            st.markdown("**Level 1**")

            # 親品番が「装置」である子品番を取得
            level1_items = structure_df[structure_df['親品番'] == '装置']['子品番'].unique().tolist()
            level1_items = [item for item in level1_items if item != '']

            if level1_items:
                # 現在の選択を取得
                current_selection = st.session_state.selected_path[0] if len(st.session_state.selected_path) > 0 else None

                # ラジオボタンで選択
                selected_level1 = st.radio(
                    "Level 1 選択",
                    options=level1_items,
                    index=level1_items.index(current_selection) if current_selection in level1_items else 0,
                    key="level1_radio",
                    label_visibility="collapsed"
                )

                # 選択が変更された場合
                if len(st.session_state.selected_path) == 0 or st.session_state.selected_path[0] != selected_level1:
                    st.session_state.selected_path = [selected_level1]
                    st.session_state.selected_part_number = None
                    st.rerun()
            else:
                st.info("Level 1 データがありません")

        # Level 2以降を動的に表示
        for level_idx in range(1, len(cols)):
            if level_idx <= len(st.session_state.selected_path):
                with cols[level_idx]:
                    st.markdown(f"**Level {level_idx + 1}**")

                    # 前のレベルで選択されたアイテムを親として、子品番を取得
                    parent_item = st.session_state.selected_path[level_idx - 1]
                    child_items = structure_df[structure_df['親品番'] == parent_item]['子品番'].unique().tolist()
                    child_items = [item for item in child_items if item != '']

                    if child_items:
                        # 現在の選択を取得
                        current_selection = st.session_state.selected_path[level_idx] if len(st.session_state.selected_path) > level_idx else None

                        # ラジオボタンで選択
                        selected_item = st.radio(
                            f"Level {level_idx + 1} 選択",
                            options=child_items,
                            index=child_items.index(current_selection) if current_selection in child_items else 0,
                            key=f"level{level_idx + 1}_radio",
                            label_visibility="collapsed"
                        )

                        # 選択が変更された場合
                        if len(st.session_state.selected_path) <= level_idx or st.session_state.selected_path[level_idx] != selected_item:
                            st.session_state.selected_path = st.session_state.selected_path[:level_idx] + [selected_item]
                            st.session_state.selected_part_number = None
                            st.rerun()
                    else:
                        st.info("子品番がありません")

        # 次のレベルがあるかチェック（まだ選択していないレベル）
        if len(st.session_state.selected_path) > 0:
            last_selected = st.session_state.selected_path[-1]
            next_level_items = structure_df[structure_df['親品番'] == last_selected]['子品番'].unique().tolist()
            next_level_items = [item for item in next_level_items if item != '']

            # 次のレベルが存在し、かつ表示カラム数が足りない場合
            if next_level_items and len(cols) <= len(st.session_state.selected_path):
                st.info("→ 横スクロールで次のレベルを表示")

    st.divider()

    # Attribute ウィンドウ
    st.markdown('<div class="structure-header">Attribute</div>', unsafe_allow_html=True)

    if len(st.session_state.selected_path) > 0:
        last_selected = st.session_state.selected_path[-1]

        # 最後に選択された子品番のStructure情報を取得（親品番と子品番のペアで）
        if len(st.session_state.selected_path) >= 2:
            parent = st.session_state.selected_path[-2]
            child = st.session_state.selected_path[-1]
        else:
            parent = '装置'
            child = st.session_state.selected_path[0]

        attr_data = structure_df[(structure_df['親品番'] == parent) & (structure_df['子品番'] == child)]

        if not attr_data.empty:
            # 親品番と子品番以外のカラムを表示
            display_columns = [col for col in structure_df.columns if col not in ['親品番', '子品番']]
            attr_display = attr_data[display_columns].iloc[0]

            # 空でない属性のみを表示
            non_empty_attrs = {k: v for k, v in attr_display.items() if v != '' and pd.notna(v)}

            if non_empty_attrs:
                # 属性を縦に表示（スクロール可能）
                with st.container():
                    st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
                    for key, value in non_empty_attrs.items():
                        st.write(f"**{key}:** {value}")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("表示する属性がありません")
        else:
            st.info("属性データが見つかりません")
    else:
        st.info("Structure でアイテムを選択してください")

    st.divider()

    # Parts List と Part Specs ウィンドウ
    # Structure の選択が終わった時点（次のレベルがない）で表示
    if len(st.session_state.selected_path) > 0:
        last_selected = st.session_state.selected_path[-1]
        next_level_check = structure_df[structure_df['親品番'] == last_selected]['子品番'].unique().tolist()
        next_level_check = [item for item in next_level_check if item != '']

        # 次のレベルが存在しない場合のみ Parts List を表示
        if not next_level_check:
            parts_cols = st.columns([1, 1])

            # Parts List ウィンドウ
            with parts_cols[0]:
                st.markdown('<div class="structure-header">Parts List</div>', unsafe_allow_html=True)

                # 最後に選択した子品番を親品番として Parts List から検索
                parts_list_filtered = parts_list_df[parts_list_df['親品番'] == last_selected]

                if not parts_list_filtered.empty:
                    # 部品番号のリストを作成（符号と構成数も表示）
                    part_display_list = []
                    part_number_map = {}

                    for idx, row in parts_list_filtered.iterrows():
                        part_num = str(row['部品番号'])
                        if part_num and part_num != '' and part_num != 'nan':
                            fugou = str(row['符号']) if pd.notna(row['符号']) and row['符号'] != '' else ''
                            qty = str(row['構成数']) if pd.notna(row['構成数']) and row['構成数'] != '' else ''

                            # 表示用テキストを作成
                            if fugou and qty:
                                display_text = f"{part_num} [符号:{fugou}, 数:{qty}]"
                            elif fugou:
                                display_text = f"{part_num} [符号:{fugou}]"
                            elif qty:
                                display_text = f"{part_num} [数:{qty}]"
                            else:
                                display_text = part_num

                            part_display_list.append(display_text)
                            part_number_map[display_text] = part_num

                    if part_display_list:
                        selected_part_display = st.radio(
                            "部品番号を選択",
                            options=part_display_list,
                            key="parts_list_radio",
                            label_visibility="collapsed"
                        )

                        st.session_state.selected_part_number = part_number_map[selected_part_display]
                    else:
                        st.info("表示可能な部品番号がありません")
                        st.session_state.selected_part_number = None
                else:
                    st.info("該当する Parts List がありません")
                    st.session_state.selected_part_number = None

            # Part Specs ウィンドウ
            with parts_cols[1]:
                st.markdown('<div class="structure-header">Part Specs</div>', unsafe_allow_html=True)

                if st.session_state.selected_part_number:
                    # Parts シートから該当する部品番号の情報を取得
                    part_specs = parts_df[parts_df['部品番号'] == st.session_state.selected_part_number]

                    if not part_specs.empty:
                        spec = part_specs.iloc[0]

                        # 要求された4つのフィールドを表示（スクロール可能）
                        with st.container():
                            st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
                            st.write(f"**品目名称:**")
                            st.write(f"{spec.get('品目名称', '')}")
                            st.divider()

                            st.write(f"**メーカ名:**")
                            st.write(f"{spec.get('メーカ名', '')}")
                            st.divider()

                            st.write(f"**メーカ型式:**")
                            st.write(f"{spec.get('メーカ型式', '')}")
                            st.divider()

                            st.write(f"**統一名称:**")
                            st.write(f"{spec.get('統一名称', '')}")
                            st.markdown('</div>', unsafe_allow_html=True)

                        # その他の情報を展開表示
                        with st.expander("📋 詳細情報を表示"):
                            for col in part_specs.columns:
                                value = spec.get(col, '')
                                if value != '' and pd.notna(value):
                                    st.write(f"**{col}:** {value}")
                    else:
                        st.warning("部品仕様が見つかりません")
                else:
                    st.info("Parts List から部品番号を選択してください")
        else:
            st.info("Structure で最終レベルまで選択してください")

else:
    st.error("データの読み込みに失敗しました。ebom.xlsxファイルが存在することを確認してください。")
