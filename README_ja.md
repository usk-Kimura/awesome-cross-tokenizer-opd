# 異なる語彙・Tokenizer間の On-Policy Distillation サーベイ

> 教師と生徒が同じ tokenizer／語彙を持たない場合の On-Policy
> Distillation（OPD）を、一次文献の根拠に基づいて整理した研究マップです。

[English README](README.md) · [機械可読データ](data/papers.yml) ·
[BibTeX](references.bib)

最終確認日は **2026-08-15** です。英語版 README を正本とし、この文書は
スコープと読み方を日本語で案内します。「確認済み」は論文本文で記述を確認した
という意味で、実験を独立に再現したという意味ではありません。

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

特に SimCT、BTB、BPM は、いずれも「token alignment」と一括りにしないことが
重要です。有限候補、実現経路、全語彙周辺分布という異なる事象を監督します。

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

- [REOPOLD](https://openreview.net/forum?id=NPhEUvT1jH) の ICML 2026 最終版は、
  Phi-4-Mini-Reasoning → DeepSeek-R1-Distill-Qwen-1.5B を「異なる語彙」と
  明記して評価しています。ただし、sampled-token likelihood を両語彙間でどう
  同一事象として計算したかは公開本文に記載がありません。そのため
  「異語彙での評価報告」として掲載し、再現可能な interface 提案とは分けています。
- [OPRD / OPRD-Bridge](https://arxiv.org/abs/2606.06021) は hidden
  representation を low-rank projector で合わせ、Phi-4-mini-reasoning →
  Qwen3-1.7B-Base を「完全に異なる tokenizer」として報告します。一方、確認時点の
  公開コードは [両モデルに生徒 tokenizer の token ID を入力すると明記](https://github.com/ShenzhiYang2000/OPRD/blob/a63236c990b1bfa9551e9d020719490d3ecd93e8/scripts/analysis/cross_arch_repr_analysis.py#L5-L8)
  し、projector 学習でも同じ ID を両モデルに渡します。異なる語彙の同じ ID は同じ
  文字列を意味しないため、実装が訂正・説明されるまでは Core ではなく
  「論文の主張と公開実装に不整合がある研究」として扱います。

### 境界的な応用

- [OVD](https://arxiv.org/abs/2601.21968) は、現在の生徒 trajectory を教師が
  0–9 の verbal score で評価するため token alignment を必要としません。ただし
  低 score の trajectory を教師 demonstration で置換し、学習分布が生徒と教師の
  mixture になるため pure student-policy OPD とは分けています。
- [OmniDraft](https://arxiv.org/abs/2507.02659) は、生徒に相当する drafter 自身の
  proposal からオンライン学習する cross-vocabulary speculative decoding です。
  最終出力分布は target model の verification で決まるため、通常の応答全体を
  対象とする OPD の Core には入れていません。

## 実装・資料

- [GOLD](https://huggingface.co/spaces/HuggingFaceH4/on-policy-distillation) /
  [TRL `GOLDTrainer`](https://huggingface.co/docs/trl/main/gold_trainer): 復号
  span の逐次対応と ULD fallback。重要な実装資料ですが論文ではありません。
- [KDFlow](https://arxiv.org/abs/2603.01875): on/off-policy と DSKDv2 系の
  cross-tokenizer KD を支援する分散 framework。
- [EasyOPD](https://arxiv.org/abs/2607.11012): `verl` 上で SimCT 等を比較・実行
  できる framework。

Off-policy の cross-tokenizer KD、文字列確率の理論的基礎、既存の一般 OPD
サーベイは [英語版 README](README.md) にまとめています。

## 読むときの注意

- full-vocabulary、finite-candidate、aligned subset、sampled path は互いに
  supervision coverage が異なります。
- 「完全一致位置の exact alignment」「質量保存」「同じ文字列の全 tokenization
  path を周辺化した exact probability」は別の性質です。
- EOS/BOS、chat template、空白、Unicode、invalid byte、code indentation の扱いは
  結果に直結しますが、報告の粒度は論文ごとに大きく異なります。
- code not found は 2026-08-15 に公式実装を発見できなかったという意味です。

## 更新への協力

追加・訂正は歓迎します。[CONTRIBUTING.md](CONTRIBUTING.md) に従い、
student rollout と tokenizer mismatch の両方について一次文献の箇所を示して
ください。構造化情報は [`data/papers.yml`](data/papers.yml) にあります。

このサーベイのメタデータは [CC0 1.0](LICENSE) で公開します。各論文・コード・
外部ページには、それぞれのライセンスが適用されます。
