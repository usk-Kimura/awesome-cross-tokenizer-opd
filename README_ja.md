# 異なる語彙・Tokenizer間の On-Policy Distillation サーベイ

> 教師と生徒が同じ tokenizer／語彙を持たない場合の On-Policy
> Distillation（OPD）を、一次文献の根拠に基づいて整理した研究マップです。

[English](README.md) · [日本語](README_ja.md) · [简体中文](README_zh.md) · [한국어](README_ko.md)

[研究カタログ](https://usk-kimura.github.io/awesome-cross-tokenizer-opd/?lang=ja) · [コード公開状況](#code-availability) · [機械可読データ](data/papers.yml) · [BibTeX](references.bib)

更新日は **2026-10-14** です。英語版 README を正本とし、この文書は
スコープと読み方を日本語で案内します。「確認済み」は論文本文で記述を確認した
という意味で、実験を独立に再現したという意味ではありません。

各レコードの `last_verified` は本文の主張を確認した日です。版・リンクの確認日
`metadata_last_verified`、実装を探した日 `code_last_checked` と区別し、変更のない
過去の本文監査日は保持しています。

## 何を対象にするか

本リポジトリでいう OPD は、生徒自身が生成した trajectory／生徒が訪れた状態に
対して教師信号を与える学習です。Core に含めるのは、次を満たす公開英語論文・
プレプリントです。

1. student-generated rollout または student-visited state を使う。
2. 教師・生徒の tokenizer／語彙が異なることを明示する。
3. 語彙差を越えて教師信号を渡す具体的な interface がある。
4. 異なる tokenizer の model pair で学習実験を報告する。

単に model family が異なるだけでは cross-tokenizer とは判定しません。また、
teacher-generated data のみを使う off-policy KD、実装資料、speculative decoding、
語彙差で評価したものの対応方法が書かれていない研究は、Core と分離します。

以下のモデル対はすべて **教師 → 生徒** の順です。

## 中核研究

### 出力空間を対応させる方法

| 研究 | 共通化の単位 | 信号の範囲 | 確率としての注意 | 代表的なモデル対 |
|---|---|---|---|---|
| [DSKD / DSKDv2](https://arxiv.org/abs/2504.11426) | hidden state を相手側の表現空間に射影し、同じ LM head を使う。ETA で完全一致位置を残す | 対応した位置の dense 分布 | 文字列事象への確率輸送ではなく、共通 head 空間の分布 | Qwen2-1.5B → GPT2-120M、Mistral-7B → TinyLLaMA-1.1B |
| [SimCT](https://arxiv.org/abs/2605.07711) | 両 tokenizer が実現できる最小の短い continuation | 有限候補集合 | 候補内で正規化した score であり、教師の全確率質量の周辺化ではない | Qwen2.5-7B-Instruct → Phi-4-mini-Instruct / Gemma-2-2B-IT |
| [ESR](https://arxiv.org/abs/2605.27028) | 生徒 rollout を教師で再 tokenization し、greedy に text span を合わせる | rollout 冒頭の一致 token | 部分的な一致位置の目的で、完全な写像分布は定義しない | Qwen3-4B → Gemma-2-2B など |
| [BTB](https://arxiv.org/abs/2606.09456) | 復号文字列が同期する最小 chunk | 実現した生徒経路 | path likelihood／scalar credit であり、全語彙候補分布ではない | Qwen3-8B → Llama-3.1-8B-SFT |
| [BPM](https://arxiv.org/abs/2607.22334) | 教師 token の byte 列を最長の生徒-token byte prefix に割り当てる | 生徒全語彙＋residual | 質量保存。報告上 99% 超の位置で厳密、残りは chain-factorized lower bound | Qwen3-32B / GLM-Z1-9B / MiniMax-M2.7 → Qwen3.5-2B |
| [SimpleOPD](https://arxiv.org/abs/2608.14277) | 生徒応答を教師 tokenizer で再符号化し、始点・終点の一致する token を対応 | 実現した1対1一致 token | 一致位置の reverse-KL surrogate。不一致位置の蒸留 advantage はゼロ | SU-01 → GLM-4.7-Flash / Gemma-4-26B-A4B、Qwen3.5 系 |
| [CompassOPD](https://arxiv.org/abs/2609.10154) | 共通 text span 上の強い教師と教師 family 内 reference の尤度差 | 実現した対応 span | span 平均の尤度変化であり、教師分布の確率輸送ではない | Qwen3.5-35B-A3B → Granite4.1-3B / Qwen3-4B / OLMo-3-7B |
| [DVLM](https://arxiv.org/abs/2609.33816) | parallel-tokenized input と Hybrid-Prefix Attention を使い、生徒語彙の教師 head を学習 | 生徒位置の dense logits | 学習した教師 head の分布。元の教師の文字列確率を厳密に周辺化するものではない | Qwen3-4B → Llama-3.2-1B-Instruct / OLMo-2-1B-Instruct |
| [ESCD](https://arxiv.org/abs/2609.34738) | 教師 byte 事象を部分生成した後の、残余を完成できる token 集合 | 生徒が訪れた次状態での completion 集合の合計確率 | 集合内の各 token への確率配分は固定しない | Qwen3-32B / GLM-Z1-9B → Qwen3.5-2B、Kimi-K2.7-Code → Qwen3.6-35B-A3B |
| [Rethinking Cross-Tokenizer OPD](https://arxiv.org/abs/2610.08448) | 厳密な1対1 span 対応と共有語彙／生徒が選ぶ top-k 候補 | 一致位置。top-16 を評価 | 候補集合で再正規化した分布。全語彙の確率輸送ではない | Qwen2.5-7B-Instruct → Llama-3.2-3B-Instruct、Granite-4.1-8B → Phi-4-mini-instruct / Qwen2.5-7B-Base |
| [CAST](https://arxiv.org/abs/2610.13257) | 復号 text 対応後、uncertainty と教師 score の smoothness に応じて chunk credit を配分 | 実現 token。不一致位置は初期生徒 policy へ anchor | chunk advantage を保存するが、語彙の確率質量保存とは異なる | Qwen3-8B → Mistral-7B / Llama-3.1-8B（SFT 初期化） |

特に SimCT、BTB、BPM は、いずれも「token alignment」と一括りにしないことが
重要です。有限候補、実現経路、全語彙周辺分布という異なる事象を監督します。

### 監督範囲と信頼性

[Rethinking Cross-Tokenizer OPD の Sections 3–5](https://arxiv.org/html/2610.08448v1)
は、実験した学習 run で厳密な1対1対応が生徒 token の 85.57–96.98% を覆い、
共有語彙から生徒が選ぶ top-16 の監督で full 共有語彙 OPD の改善幅の少なくとも
96% を保持すると報告しています。一方、不一致 span の log-probability に MSE を
加えた18通りの正の重み設定では、すべて平均精度が低下しました。この結果は
検証された目的関数・モデル対の範囲で読み、不一致位置への監督一般に拡張しません。
本文の [コードリンク](https://anonymous.4open.science/r/Cross-Tokenizer-OPD) は
取得時に HTTP 401 となったため、実装内容は未監査です。

ESCD は残余 byte 条件を満たす token 集合の合計確率を監督します。残余境界を
越える token も含み得て、1 token で完成できる集合が空なら補助損失はありません。
CAST は chunk 内の credit 配分と不一致位置での policy drift を扱います。
両者とも、単なる alignment coverage の大小だけでは比較できません。

### 実際の学習 pipeline での利用

[Mint-Agent](https://arxiv.org/abs/2608.16386) v2 の Section 5.2 は、失敗した
生徒 trajectory の重要 turn で現在の生徒が action を再生成し、DeepSeek-V4-Pro の
path score を同じ復号 text の chunk から生徒 token に配分する方法を記載します。
Qwen3.5-9B／Qwen3.6-27B の agentic specialist で使われますが、最終モデル
Mint-Cu／Mint-Ag の成績は SFT・OPD・RLVR・merging を組み合わせた結果です。
後段の multi-teacher 統合は同じ tokenizer の specialist 間で行うため、
cross-tokenizer 段階の効果を単独に示す結果とは区別します。

### 語彙写像を回避する方法

- [GAD](https://arxiv.org/abs/2511.10643) は、固定した教師応答と現在の生徒応答を
  見分ける discriminator を生徒と同時更新し、その sequence-level score で
  生徒を学習します。GPT-5-Chat → Qwen2.5 / Llama-3 系で評価されています。
- [ROPD](https://arxiv.org/abs/2605.07396) は、教師・生徒応答の対比から
  prompt ごとの rubric を作り、verifier が現在の生徒 rollout を rubric 項目ごとに
  採点します。論文は tokenizer alignment 不要の cross-architecture 蒸留を明記し、
  GPT-5.2-Chat → Qwen3 / Gemma-3 で評価しています。
- [OmniOPD](https://arxiv.org/abs/2606.01476) は、教師の text rollout を
  Monte Carlo sampling し、復号後の chunk の意味的類似度で生徒を監督します。
  token logits を要求せず、Claude や Gemini のような black-box 教師も扱います。

### 根拠に留保が必要な研究

- [REOPOLD](https://openreview.net/forum?id=NPhEUvT1jH) の以前に監査した OpenReview 版は、
  Phi-4-Mini-Reasoning → DeepSeek-R1-Distill-Qwen-1.5B を「異なる語彙」と
  明記して評価しています。ただし、sampled-token likelihood を両語彙間でどう
  同一事象として計算したかは公開本文に記載がありません。そのため
  「異語彙での評価報告」として掲載し、再現可能な interface 提案とは分けています。
  [著者側の最新ページ](https://www.microsoft.com/en-us/research/publication/relaxed-on-policy-distillation-selective-credit-allocation-for-scaling-reasoning-efficiently/)
  は NeurIPS 2026 と記載するため、旧記載の ICML を訂正しました。リンク先の
  [新しい OpenReview レコード](https://openreview.net/forum?id=l0h1SzRI7H) は
  browser verification で本文を取得できず、最新版での interface 再監査は未完了です。
- [OPRD / OPRD-Bridge](https://arxiv.org/abs/2606.06021) は hidden
  representation を low-rank projector で合わせ、Phi-4-mini-reasoning →
  Qwen3-1.7B-Base を「完全に異なる tokenizer」として報告します。一方、確認時点の
  公開コードは [両モデルに生徒 tokenizer の token ID を入力すると明記](https://github.com/ShenzhiYang2000/OPRD/blob/a63236c990b1bfa9551e9d020719490d3ecd93e8/scripts/analysis/cross_arch_repr_analysis.py#L5-L8)
  し、projector 学習でも同じ ID を両モデルに渡します。異なる語彙の同じ ID は同じ
  文字列を意味しないため、実装が訂正・説明されるまでは Core ではなく
  「論文の主張と公開実装に不整合がある研究」として扱います。

### 境界的な応用

- [OVD](https://arxiv.org/abs/2601.21968) v2 は verbal score で生徒の
  sub-trajectory を選別し、低 score の query／suffix を教師 continuation で
  置換します。生徒 token と教師置換 token の両方を outcome advantage で学習する
  mixture のため pure student-policy OPD とは分けています。一部の評価では
  推論時にも教師が介入します。[公式コード](https://github.com/menik1126/OVD-code) が公開されています。
- [OmniDraft](https://arxiv.org/abs/2507.02659) は、生徒に相当する drafter 自身の
  proposal からオンライン学習する cross-vocabulary speculative decoding です。
  最終出力分布は target model の verification で決まるため、通常の応答全体を
  対象とする OPD の Core には入れていません。

## 実装・資料

- [GOLD](https://huggingface.co/spaces/HuggingFaceH4/on-policy-distillation) /
  [TRL `GOLDTrainer`](https://huggingface.co/docs/trl/main/gold_trainer): 復号
  span の対応・確率併合と ULD fallback。現在は `trl.experimental.gold` にあり、
  重要な実装資料ですが論文ではありません。
- [KDFlow](https://arxiv.org/abs/2603.01875): on/off-policy と DSKDv2 系の
  cross-tokenizer KD を支援する分散 framework。v4 の Qwen3-14B → Llama3.2-3B
  実験は Appendix A.1 の off-policy 設定であり、on-policy 実験とは別です。
- [EasyOPD](https://arxiv.org/abs/2607.11012): `verl` 上で SimCT 等を比較・実行
  できる framework。
- [BPM の公式コード](https://github.com/K1XE/BPM) は 2026-09-01 に公開されました。
- [ACTD](https://arxiv.org/abs/2608.29662) は anchor と residual の監督を扱う
  関連研究です。Section 4.1 が dataset の reference solution に対する off-policy
  学習を明記するため、Core OPD には含めません。

Off-policy の cross-tokenizer KD、文字列確率の理論的基礎、既存の一般 OPD
サーベイは [英語版 README](README.md) にまとめています。

## 読むときの注意

- full-vocabulary、finite-candidate、aligned subset、sampled path は互いに
  supervision coverage が異なります。
- 「完全一致位置の exact alignment」「質量保存」「同じ文字列の全 tokenization
  path を周辺化した exact probability」は別の性質です。
- EOS/BOS、chat template、空白、Unicode、invalid byte、code indentation の扱いは
  結果に直結しますが、報告の粒度は論文ごとに大きく異なります。
- code not found は各レコードの `code_last_checked` 時点で公式実装を
  発見できなかったという意味です。リンクだけある場合と公開実装を確認できた
  場合も区別します。

<!-- CODE-STATUS:START -->
<a id="code-availability"></a>

## 公式コードの公開状況

公式資料で確認したコードの状況です。「公式コードを確認できず」は、コードが存在しないという意味ではありません。公開予定と、リンクへのアクセスを確認できない状態も区別します。コード公開は実験の再現を保証しません。OPRD の実装上の懸念は本文を参照してください。

| 研究 | 分類 | 公式実装 | 確認日 |
|---|---|---|---|
| [DSKD / DSKDv2](https://arxiv.org/abs/2504.11426) | 出力分布・トークンの対応 | [公式コードあり](https://github.com/songmzhang/DSKDv2) | 2026-10-14 |
| [SimCT](https://arxiv.org/abs/2605.07711) | 出力分布・トークンの対応 | [公式コードあり](https://github.com/sunjie279/SimCT-) | 2026-10-14 |
| [ESR](https://arxiv.org/abs/2605.27028) | 出力分布・トークンの対応 | 公式コードを確認できず | 2026-10-14 |
| [GAD](https://arxiv.org/abs/2511.10643) | 語彙を直接対応させない方法 | [公式コードあり](https://github.com/microsoft/LMOps/tree/main/gad) | 2026-10-14 |
| [ROPD](https://arxiv.org/abs/2605.07396) | 語彙を直接対応させない方法 | [公式コードあり](https://github.com/Peregrine123/ROPD_official) | 2026-10-14 |
| [OmniOPD](https://arxiv.org/abs/2606.01476) | 語彙を直接対応させない方法 | 公式コードを確認できず | 2026-10-14 |
| [OPRD / OPRD-Bridge](https://arxiv.org/abs/2606.06021) | 公開実装に懸念 | [公式コードあり](https://github.com/ShenzhiYang2000/OPRD) | 2026-10-14 |
| [BTB](https://arxiv.org/abs/2606.09456) | 出力分布・トークンの対応 | [公式コードあり](https://github.com/ivanniu/On-Policy-Distill) | 2026-10-14 |
| [REOPOLD](https://openreview.net/forum?id=NPhEUvT1jH) | 対応方法の説明が不十分 | 公式コードを確認できず | 2026-10-14 |
| [BPM](https://arxiv.org/abs/2607.22334) | 出力分布・トークンの対応 | [公式コードあり](https://github.com/K1XE/BPM) | 2026-10-14 |
| [OVD](https://arxiv.org/abs/2601.21968) | 境界的な応用 | [公式コードあり](https://github.com/menik1126/OVD-code) | 2026-10-14 |
| [OmniDraft](https://arxiv.org/abs/2507.02659) | 境界的な応用 | 公式コードを確認できず | 2026-10-14 |
| [KDFlow](https://arxiv.org/abs/2603.01875) | 学習フレームワーク | [公式コードあり](https://github.com/songmzhang/KDFlow) | 2026-10-14 |
| [EasyOPD](https://arxiv.org/abs/2607.11012) | 学習フレームワーク | [公式コードあり](https://github.com/lds-ustc/EasyOPD) | 2026-10-14 |
| [GOLD](https://huggingface.co/spaces/HuggingFaceH4/on-policy-distillation) | 実装・解説資料 | [公式コードあり（実験的）](https://github.com/huggingface/trl) | 2026-10-14 |
| [SimpleOPD](https://arxiv.org/abs/2608.14277) | 出力分布・トークンの対応 | [公式コードあり](https://github.com/hhnqqq/SimpleOPD) | 2026-10-14 |
| [CompassOPD](https://arxiv.org/abs/2609.10154) | 出力分布・トークンの対応 | 公式コードを確認できず | 2026-10-14 |
| [DVLM](https://arxiv.org/abs/2609.33816) | 出力分布・トークンの対応 | 公式コードを確認できず | 2026-10-14 |
| [ESCD](https://arxiv.org/abs/2609.34738) | 出力分布・トークンの対応 | コード公開予定（未確認） | 2026-10-14 |
| [Rethinking Cross-Tokenizer OPD](https://arxiv.org/abs/2610.08448) | 出力分布・トークンの対応 | [コードリンクあり（アクセス未確認）](https://anonymous.4open.science/r/Cross-Tokenizer-OPD) | 2026-10-14 |
| [CAST](https://arxiv.org/abs/2610.13257) | 出力分布・トークンの対応 | 公式コードを確認できず | 2026-10-14 |
| [Mint-Agent](https://arxiv.org/abs/2608.16386) | 実際の学習工程での利用 | 公式コードを確認できず | 2026-10-14 |
| [ACTD](https://arxiv.org/abs/2608.29662) | 関連・off-policy KD | [公式コードあり](https://github.com/hyhy892/ACTD) | 2026-10-14 |

<!-- CODE-STATUS:END -->

## 更新への協力

追加・訂正は歓迎します。[CONTRIBUTING.md](CONTRIBUTING.md) に従い、
student rollout と tokenizer mismatch の両方について一次文献の箇所を示して
ください。構造化情報は [`data/papers.yml`](data/papers.yml) にあります。

このサーベイのメタデータは [CC0 1.0](LICENSE) で公開します。各論文・コード・
外部ページには、それぞれのライセンスが適用されます。
