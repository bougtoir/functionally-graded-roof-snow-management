# R1改訂パッケージ 引き継ぎ（内部用・日本語）

## 状態
- ブランチ `devin/1794200841-crst-major-revision`。投稿版ベースラインはタグ `crst-submitted-v1`（472807b）に固定。旧出力（results/generated 等）は未変更。
- 改訂解析一式は `make r1 PYTHON=./.venv/bin/python` で再現（全体で数時間。robustness が最長）。文書のみ再生成は `make r1-docs`。
- `make all` は投稿版パイプラインで、旧出力を再生成するため意図的に再実行していない。
- 公開用ZIP: `submission/r1/R1_revision_package.zip`（回答書なし）。回答書を含む提出用ZIP: `private/r1_response/R1_submission_package_with_response.zip`（git管理外）。

## 主な結果（数値はすべて results/r1 のCSVから自動生成）
- 物理イベント指標 S_event,max は dt=1〜0.0625 h で事前基準を満たし、本番 dt=1 h。旧 per-step S_max は dt に比例して変化。
- 施工可能な一様屋根は L_max 91.9〜6417 kg/m の範囲に解がない。傾斜付け屋根は26組の中間解（S_event,max 11.5〜91.8 kg/m）を全15回の最適化で再現。ただし hypervolume は 0.982→0.988 と小さい。
- 頑健性：中間解の Q95 S_event,max は中央値771・最大4340 kg/m（公称≦92）。小さい落雪量は頑健でない。Q95 空間でも一様屋根の空白は残る。
- イベント分離時間（10分/3時間）で一様屋根の落雪量評価は大きく変わる（Table 3）。中間解の存在自体は全条件で維持。
- JMA 12観測冬（日値を24時間に均等配分）でも各冬6〜10組の中間解。検証ではなくシナリオ。

## 査読対応（2026-11-19 追加）
- 査読コメント全37件（Reviewer 1: 29件、Reviewer 2: 8件）に回答。回答書 `response_to_reviewers_R1.docx` と対応表 `REVIEWER_RESPONSE_MATRIX.csv/.xlsx` は `private/r1_response/` に保存（公開リポのためgit管理外）。
- 追加解析：不確実性要因の寄与（Spearman）、落雪量急増の要因、屋根長4/12 m再評価、計算量・実行時間、一様屋根の閾値挙動。
- 原稿：モデル式（質量・圧密・摩擦、式1–3）、用語定義、研究フロー図（図1c）、気象入力図（図2a–f）、設計実務・基準への示唆（4.1節）、Wang/Zhang/Liu 2026の引用。
- 履歴付き版は実際の投稿ファイル（Editorial Manager版、表紙を除く）との差分。
- 一部対応（2件）：屋根規模の実測による検証は不可能（データなし）として限界に明記。

## 未完了（著者側）
1. 所属・住所、Funding、Competing interests、CRediT（原稿・カバーレターの REQUIRED 5箇所）。マスタープロンプト1.4に従い著者がローカルで記入。

## 品質確認
- ruff 全通過、pytest 41件通過、`scripts/r1_qc.py` 全項目通過（REQUIRED 5箇所は著者記入待ちとして別記）。
- 改訂期限は2026-11-29。査読コメント原文が届かない場合、期限延長依頼の草案を用意する（送付は著者承認後）。
- 投稿・編集者連絡・マージは未実施（未承認）。
