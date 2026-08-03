# TECHNICAL.md — EBOM-viewer

## 概要

EBOM（Engineering Bill of Materials）の階層構造を macOS Finder 風のマルチカラムビューで閲覧する Streamlit アプリ。
Structure → Parts List → Part Specification の 3 段階のドリルダウン操作で部品情報を参照できる。

---

## ディレクトリ構成

```
EBOM-viewer/
├── app.py          # Streamlit エントリポイント（全ロジックを含む）
├── requirements.txt
└── ebom.xlsx       # データソース（固定ファイル名）
```

---

## データソース仕様（`ebom.xlsx`）

アプリはファイルアップロードを持たず、起動ディレクトリの `ebom.xlsx` を固定読み込みする。

| シート名 | 必須列 | 説明 |
|---------|--------|------|
| `Structure` | `親品番`、`子品番` + 属性列 | 品番の階層関係 |
| `Parts List` | `親品番`、`部品番号`、`符号`、`構成数` | 末端品番の部品リスト |
| `Parts` | `部品番号` + スペック列 | 部品詳細仕様 |

- NaN はすべて空文字列に変換して処理
- `@st.cache_data` でロード結果をキャッシュ（TTL なし）

---

## アーキテクチャ

### 画面構成

```
Structure ウィンドウ（マルチカラム）
  Level 1  |  Level 2  |  Level 3  | ...
  [ラジオ]  → [ラジオ]  → [ラジオ]  → ...
                          ↓（末端に到達）
Attribute ウィンドウ（expander）
                          ↓
Parts List ウィンドウ（左）｜ Part Specification ウィンドウ（右）
```

### 操作フロー

```
Level 1 選択（親品番='装置'の子品番一覧）
  → Level 2 選択（Level 1 選択品番の子品番一覧）
  → ... 子品番なしの末端に到達
  → Attribute 表示（Structure の追加属性列）
  → Parts List 表示（末端品番を親品番として Parts List を検索）
  → 部品番号選択 → Part Specification 表示
```

### 階層の起点

`Structure` シートで `親品番 == '装置'` の行を Level 1 として使用。
起点文字列 `'装置'` は app.py 内にハードコードされている。

---

## セッション状態

| キー | 型 | 内容 |
|------|-----|------|
| `selected_path` | list[str] | 現在選択中の品番パス（Level 1〜N）|
| `selected_part_number` | str\|None | Parts List で選択中の部品番号 |

`selected_path` が変更されると `st.rerun()` を呼び出して全体を再描画する。

---

## カラム表示ロジック

- 最大同時表示カラム数: 3（`max_display_cols = 3`）
- 選択パスが 3 を超えた場合は「横スクロールで次のレベルを表示」と案内（実際の横スクロールは未実装）
- 末端判定: 選択品番を `親品番` として Structure を検索し子品番が 0 件の場合

---

## 依存パッケージ

```
streamlit>=1.40.0
pandas>=2.0.0
openpyxl>=3.1.0
```

---

## 既知の制限

| 制限 | 詳細 |
|------|------|
| データソース固定 | `ebom.xlsx` をアップロードする機能がなく、ファイルをサーバーに配置する必要がある |
| 起点品番固定 | Level 1 の起点が `'装置'` にハードコードされている |
| 横スクロール未実装 | 4 列目以降のレベルにアクセスする UI が実質存在しない |
| 検索機能なし | 特定の品番を直接検索する手段がない |
| キャッシュ無効化 | `ebom.xlsx` を更新しても `st.cache_data` が残るためアプリ再起動が必要 |

---

## 機能拡張ポイント

| テーマ | 実装アプローチ |
|--------|--------------|
| ファイルアップロード対応 | `st.file_uploader` を追加し `load_data()` を BytesIO 受け付けに変更 |
| 起点品番の設定化 | サイドバーの `st.text_input` で起点品番を変更可能にする |
| 横スクロール実装 | `st.columns` の数を動的に変更し CSS オーバーフロー制御を適用 |
| 品番検索 | `st.text_input` + Structure/Parts の DataFrame `str.contains()` で絞り込み |
| BOM エクスポート | 選択パス以下の全品番を再帰的に収集して Excel ダウンロード |
| キャッシュ無効化ボタン | `st.cache_data.clear()` を呼び出す「データ再読み込み」ボタンを追加 |
