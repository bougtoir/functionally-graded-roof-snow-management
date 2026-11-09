# R1改訂パッケージ 引き継ぎ（内部用・日本語）

## 状態
- ブランチ `devin/1794200841-crst-major-revision`。投稿版ベースラインはタグ `crst-submitted-v1`（472807b）に固定。旧出力（results/generated 等）は未変更。
- 改訂解析一式は `make r1 PYTHON=./.venv/bin/python` で再現（全体で数時間。robustness が最長）。文書のみ再生成は `make r1-docs`。
- `make all` は投稿版パイプラインで、旧出力を再生成するため意図的に再実行していない。
- 提出物ZIP: `submission/r1/R1_revision_package.zip`（130ファイル、SHA-256マニフェスト同梱）。

## 主な結果（数値はすべて results/r1 のCSVから自動生成）
- 物理イベント指標 S_event,max は dt=1〜0.0625 h で事前基準を満たし、本番 dt=1 h。旧 per-step S_max は dt に比例して変化。
- 施工可能な一様屋根は L_max 91.9〜6417 kg/m の範囲に解がない。傾斜付け屋根は26組の中間解（S_event,max 11.5〜91.8 kg/m）を全15回の最適化で再現。ただし hypervolume は 0.982→0.988 と小さい。
- 頑健性：中間解の Q95 S_event,max は中央値771・最大4340 kg/m（公称≦92）。小さい落雪量は頑健でない。Q95 空間でも一様屋根の空白は残る。
- イベント分離時間（10分/3時間）で一様屋根の落雪量評価は大きく変わる（Table 3）。中間解の存在自体は全条件で維持。
- JMA 12観測冬（日値を24時間に均等配分）でも各冬6〜10組の中間解。検証ではなくシナリオ。

## 未完了（ユーザー入力が必要）
1. Editor 決定レター・Reviewer 1/2 コメント全文 → 回答書と対応表（`CHANGES_FOR_RESPONSE.md` を下地として用意済み）。
2. Editorial Manager に実際に提出した DOCX → 履歴版の差分基準の確定（現在はリポジトリ版を代用）。
3. 所属・住所、Funding、Competing interests、CRediT（原稿に REQUIRED が5箇所）。
4. 査読者指定の3 DOI は雪と無関係のため未引用。引用要否はコメント原文で判断。

## 品質確認
- ruff 全通過、pytest 41件通過、`scripts/r1_qc.py` 45項目中44通過（残りは REQUIRED のみ）。
- 投稿・編集者連絡・マージは未実施（未承認）。
