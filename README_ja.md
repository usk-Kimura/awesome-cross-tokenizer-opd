# 異なるトークナイザー間のOn-Policy Distillationサーベイ

> 教師と生徒のトークナイザーや語彙が異なる場合に、On-Policy Distillation（OPD）でどのように学習させるかを、一次文献に基づいて整理しています。

[English](README.md) · [日本語](README_ja.md) · [简体中文](README_zh.md) · [한국어](README_ko.md)

[研究カタログ](https://usk-kimura.github.io/awesome-cross-tokenizer-opd/ja/) · [コード公開状況](#code-availability) · [機械可読データ](data/papers.yml) · [BibTeX](references.bib)

最終更新日は**2026-10-14**です。[英語版README](README.md)を基準として、この文書では対象となる研究と読み方を日本語で説明しています。「確認済み」は公開された論文本文の記述を確認したという意味で、実験を独立に再現したという意味ではありません。

各研究の`last_verified`は、本文の主張を確認した日です。バージョンやリンクを確認した日を`metadata_last_verified`、公式コードを探した日を`code_last_checked`に記録しています。本文を再確認していない場合は、以前の確認日を残しています。

## 対象となる研究

このサーベイでいうOPDは、生徒自身が生成した軌跡や、生徒が訪れた状態に対して教師信号を与える学習です。中核研究には、次の条件を満たす公開英語論文・プレプリントを含めます。

1. 生徒が生成した軌跡、または生徒が訪れた状態を使っている。
2. 教師と生徒のトークナイザーや語彙が異なると明記している。
3. その違いに対応し、教師信号を学習に使う具体的な方法を説明している。
4. トークナイザーが異なるモデルの組み合わせで、学習実験を報告している。

モデル系列が異なるだけでは、トークナイザーも異なるとは判断しません。教師が生成したデータだけを使うoff-policy KD、実装資料、推測デコーディング、語彙の対応方法が十分に説明されていない研究は、中核研究と区別して掲載しています。

以下のモデルの組み合わせは、すべて**教師 → 生徒**の順です。

## 中核研究

### 出力空間を対応づける方法

| 研究 | 対応づける単位・方法 | 学習信号の範囲 | 確率の扱いと制約 | 代表的なモデルの組み合わせ |
|---|---|---|---|---|
| [DSKD / DSKDv2](https://arxiv.org/abs/2504.11426) | 隠れ状態を相手の表現空間に射影し、同じ出力ヘッドを使用。ETAで厳密に一致する位置を選択 | 対応位置の全次元の分布 | 共通の出力ヘッド空間で分布を比較。文字列事象の確率輸送とは異なる | Qwen2-1.5B → GPT2-120M、Mistral-7B → TinyLLaMA-1.1B |
| [SimCT](https://arxiv.org/abs/2605.07711) | 両トークナイザーで表せる最小の続き | 有限の候補集合 | 候補内で正規化したスコア。教師の全確率質量を周辺化した分布とは異なる | Qwen2.5-7B-Instruct → Phi-4-mini-Instruct / Gemma-2-2B-IT |
| [ESR](https://arxiv.org/abs/2605.27028) | 生徒の応答を教師で再分割し、文字列区間を貪欲法で照合 | 応答の冒頭で一致するトークン | 一致部分で計算する目的関数。完全な写像分布は定義していない | Qwen3-4B → Gemma-2-2Bなど |
| [BTB](https://arxiv.org/abs/2606.09456) | 復号した文字列が一致する最小区間 | 実際に生成した生徒の経路 | 経路の尤度から計算する学習信号。全語彙の候補分布とは異なる | Qwen3-8B → Llama-3.1-8B-SFT |
| [BPM](https://arxiv.org/abs/2607.22334) | 教師トークンのバイト列に対し、接頭辞が一致する最長の生徒トークンへ確率を割り当てる | 生徒の全語彙と残余カテゴリ | 確率質量を保存。報告では99%超の位置で厳密な周辺分布を得て、残りには連鎖分解による下界を使用 | Qwen3-32B / GLM-Z1-9B / MiniMax-M2.7 → Qwen3.5-2B |
| [SimpleOPD](https://arxiv.org/abs/2608.14277) | 生徒の応答を教師で再符号化し、始点と終点が一致するトークンを対応づける | 実際に生成した1対1の一致トークン | 一致位置で逆KLの代理目的を計算。不一致位置の蒸留信号はゼロ | SU-01 → GLM-4.7-Flash / Gemma-4-26B-A4B、Qwen3.5系 |
| [CompassOPD](https://arxiv.org/abs/2609.10154) | 共通の文字列区間で、強い教師と同系列の参照モデルの尤度差を計算 | 実際に生成した対応区間 | 区間内で平均した尤度の変化を使用。教師分布の確率輸送とは異なる | Qwen3.5-35B-A3B → Granite4.1-3B / Qwen3-4B / OLMo-3-7B |
| [DVLM](https://arxiv.org/abs/2609.33816) | 並列にトークン化した入力とHybrid-Prefix Attentionで、生徒の語彙に対応する教師の出力ヘッドを学習 | 生徒の位置での全次元のlogits | 学習した教師ヘッドの分布。元の教師の文字列確率を厳密に周辺化する方法とは異なる | Qwen3-4B → Llama-3.2-1B-Instruct / OLMo-2-1B-Instruct |
| [ESCD](https://arxiv.org/abs/2609.34738) | 教師トークンのバイト列を一部生成した後、残りを完成できるトークン集合を使用 | 生徒が訪れた次状態で、補完集合の合計確率を計算 | 集合内の各トークンへの確率配分は固定しない | Qwen3-32B / GLM-Z1-9B → Qwen3.5-2B、Kimi-K2.7-Code → Qwen3.6-35B-A3B |
| [Rethinking Cross-Tokenizer OPD](https://arxiv.org/abs/2610.08448) | 厳密な1対1の区間対応と、共有語彙または生徒が選ぶ上位候補を使用 | 一致位置。上位16候補を評価 | 候補集合内で再正規化した分布。全語彙の確率輸送とは異なる | Qwen2.5-7B-Instruct → Llama-3.2-3B-Instruct、Granite-4.1-8B → Phi-4-mini-instruct / Qwen2.5-7B-Base |
| [CAST](https://arxiv.org/abs/2610.13257) | 復号した文字列を対応づけ、不確実性と教師スコアの滑らかさに応じて区間の学習信号を配分 | 生成したトークン。不一致位置には初期生徒モデルへの制約を適用 | 区間のadvantageの総量を保存。語彙の確率質量を保存する性質とは異なる | Qwen3-8B → Mistral-7B / Llama-3.1-8B（SFT初期化） |

SimCT、BTB、BPMは、いずれもトークンの対応を扱いますが、学習信号の対象は異なります。SimCTは有限の候補、BTBは実際に生成した経路、BPMは全語彙の周辺分布を使います。

### 学習信号の範囲と信頼性

[Rethinking Cross-Tokenizer OPDのSections 3–5](https://arxiv.org/html/2610.08448v1)では、実験した学習過程で、厳密な1対1対応が生徒トークンの85.57–96.98%を覆ったと報告しています。また、共有語彙から生徒が選んだ上位16候補だけを使っても、共有語彙全体を使うOPDの改善幅の少なくとも96%を保持したとしています。

一方、不一致区間の対数確率にMSEを加えた18通りの正の重み設定では、すべて平均精度が低下しました。この結果は、評価した目的関数とモデルの組み合わせについての報告です。不一致位置への学習信号全般に、そのまま当てはめることはできません。論文中の[コードリンク](https://anonymous.4open.science/r/Cross-Tokenizer-OPD)は、確認時にHTTP 401が返され、実装の内容を確認できませんでした。

ESCDは、残りのバイト列を完成できるトークン集合の合計確率を学習に使います。この集合には、残りのバイト列の境界を越えるトークンも含まれる場合があります。1トークンで完成できる候補がなければ、補助損失は加えません。CASTは、区間内での学習信号の配分と、不一致位置で生徒モデルが変化しすぎないようにする制約を扱います。どちらも、対応づける範囲の広さだけでは比較できません。

### 学習パイプラインでの利用

[Mint-Agent](https://arxiv.org/abs/2608.16386)のv2、Section 5.2では、生徒が失敗した軌跡の重要なステップで行動を再生成し、DeepSeek-V4-Proの経路スコアを、同じ復号文字列の区間から生徒トークンの学習信号に配分する方法を説明しています。この方法は、Qwen3.5-9B／Qwen3.6-27Bを使ったエージェント専門モデルで用いられています。

ただし、最終モデルMint-Cu／Mint-Agの成績は、SFT・OPD・RLVR・モデル統合を組み合わせた結果です。後段では、同じトークナイザーを使う専門モデルを複数教師のOPDで統合しています。そのため、最終成績を、異なるトークナイザー間の蒸留段階だけの効果とはみなしません。

### 語彙を直接対応づけない方法

- [GAD](https://arxiv.org/abs/2511.10643)では、固定した教師の回答と現在の生徒の回答を見分ける識別器を、生徒とともに更新します。識別器が返す応答全体のスコアを学習に使い、GPT-5-Chat → Qwen2.5 / Llama-3系で評価しています。
- [ROPD](https://arxiv.org/abs/2605.07396)では、教師と生徒の回答を比較し、質問ごとの採点基準を作ります。検証モデルが基準の各項目に従って生徒の応答を採点します。論文では、トークナイザーの対応づけなしに異なる構造のモデル間で蒸留できると説明し、GPT-5.2-Chat → Qwen3 / Gemma-3で評価しています。
- [OmniOPD](https://arxiv.org/abs/2606.01476)では、教師の続きのテキストをモンテカルロ法で複数生成し、復号した区間の意味的な類似度を使って生徒を学習させます。トークンのlogitsを取得する必要がなく、ClaudeやGeminiのような非公開の教師モデルも使えます。

### 記述や実装に注意が必要な研究

- [REOPOLD](https://openreview.net/forum?id=NPhEUvT1jH)の以前に確認したOpenReviewバージョンでは、Phi-4-Mini-Reasoning → DeepSeek-R1-Distill-Qwen-1.5Bを「異なる語彙」と明記して評価しています。ただし、標本トークンの尤度を異なる語彙間でどう同じ事象として計算するか、本文に記載がありません。そのため、語彙の異なるモデルで評価した報告として掲載し、再現可能な対応方法の提案とは区別しています。[著者の最新ページ](https://www.microsoft.com/en-us/research/publication/relaxed-on-policy-distillation-selective-credit-allocation-for-scaling-reasoning-efficiently/)にはNeurIPS 2026と記載されているため、以前のICMLという記載を訂正しました。[新しいOpenReviewレコード](https://openreview.net/forum?id=l0h1SzRI7H)ではブラウザ検証の画面が表示されて本文を取得できず、最新版の対応方法は再確認できていません。
- [OPRD / OPRD-Bridge](https://arxiv.org/abs/2606.06021)では、低ランク射影を使って隠れ状態を対応づけます。Phi-4-mini-reasoning → Qwen3-1.7B-Baseを、トークナイザーが完全に異なるモデル対として報告しています。一方、確認時点の公開コードには、[両モデルに生徒のトークンIDを入力すると明記されています](https://github.com/ShenzhiYang2000/OPRD/blob/a63236c990b1bfa9551e9d020719490d3ecd93e8/scripts/analysis/cross_arch_repr_analysis.py#L5-L8)。射影の学習でも、同じIDを両モデルに入力しています。異なる語彙の同じIDは、同じ文字列を意味しません。実装が訂正されるか説明が加えられるまでは、中核研究から外し、論文の説明と公開実装に不整合がある研究として掲載しています。

### 関連分野への応用

- [OVD](https://arxiv.org/abs/2601.21968)のv2では、教師の言葉によるスコアで生徒の軌跡の一部を選び、低評価の質問や後続の生成部分を、教師が生成した続きで置き換えます。生徒が生成したトークンと教師が置き換えたトークンの両方を、結果に基づくadvantageで学習に使います。両者が混在するため、生徒が生成した経路だけを使うOPDとは区別しています。一部の評価では推論時にも教師が介入します。[公式コード](https://github.com/menik1126/OVD-code)が公開されています。
- [OmniDraft](https://arxiv.org/abs/2507.02659)は、ドラフトモデル自身の提案からオンライン学習する、異なる語彙間の推測デコーディング手法です。最終出力分布は対象モデルの検証で決まるため、通常の応答全体を対象とするOPDの中核研究には含めていません。

## 実装・資料

- [GOLD](https://huggingface.co/spaces/HuggingFaceH4/on-policy-distillation) / [TRLのGOLDTrainer](https://huggingface.co/docs/trl/main/gold_trainer)では、復号した区間の対応づけ、確率の併合、ULDへのフォールバック処理を組み合わせます。現在は`trl.experimental.gold`にある実装資料です。論文としては扱っていません。
- [KDFlow](https://arxiv.org/abs/2603.01875)は、on-policy・off-policyの蒸留と、DSKD系の異なるトークナイザー間の蒸留手法に対応した分散フレームワークです。v4のQwen3-14B → Llama3.2-3Bの実験は、Appendix A.1のoff-policy設定で行われており、on-policyの実験とは区別しています。
- [EasyOPD](https://arxiv.org/abs/2607.11012)は、verl上でSimCTなどを比較・実行できるフレームワークです。
- [BPMの公式コード](https://github.com/K1XE/BPM)は、2026-09-01に公開されました。
- [ACTD](https://arxiv.org/abs/2608.29662)は、確率の高い候補と残余部分の学習を扱う関連研究です。Section 4.1では、データセットの正解解法を使うoff-policy学習を明記しています。そのため、OPDの中核研究には含めていません。

Off-policyの異なるトークナイザー間の蒸留、文字列確率の理論、一般的なOPDのサーベイは、[英語版README](README.md)にまとめています。

## 結果を読む際の注意点

- 全語彙の分布、有限の候補集合、一致した部分集合、標本経路では、学習信号を与える範囲が異なります。
- 厳密に一致する位置での対応づけ、確率質量の保存、同じ文字列を表す全トークン化経路を周辺化した厳密な確率は、それぞれ異なる性質です。
- EOS/BOS、チャットテンプレート、空白、Unicode、不正なバイト列、コードのインデントの扱いは、結果に直結します。どこまで詳しく報告されているかは、論文によって大きく異なります。
- 「公式コードを確認できず」は、`code_last_checked`時点で公式実装を見つけられなかったという意味です。リンク先の内容を確認できない場合や、コードの公開を確認した場合とは区別しています。

<!-- CODE-STATUS:START -->
<a id="code-availability"></a>

## 公式コードの公開状況

論文や公式資料で確認したコードの公開状況をまとめています。「公式コードを確認できず」は、コードが存在しないという意味ではありません。公開予定のものと、リンク先の内容を確認できなかったものは区別しています。コードの公開を確認しただけでは、実験を再現できるとは限りません。OPRDの実装に関する注意点は本文を参照してください。

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
| [REOPOLD](https://openreview.net/forum?id=NPhEUvT1jH) | 語彙の対応方法が不明確 | 公式コードを確認できず | 2026-10-14 |
| [BPM](https://arxiv.org/abs/2607.22334) | 出力分布・トークンの対応 | [公式コードあり](https://github.com/K1XE/BPM) | 2026-10-14 |
| [OVD](https://arxiv.org/abs/2601.21968) | 関連分野への応用 | [公式コードあり](https://github.com/menik1126/OVD-code) | 2026-10-14 |
| [OmniDraft](https://arxiv.org/abs/2507.02659) | 関連分野への応用 | 公式コードを確認できず | 2026-10-14 |
| [KDFlow](https://arxiv.org/abs/2603.01875) | 学習フレームワーク | [公式コードあり](https://github.com/songmzhang/KDFlow) | 2026-10-14 |
| [EasyOPD](https://arxiv.org/abs/2607.11012) | 学習フレームワーク | [公式コードあり](https://github.com/lds-ustc/EasyOPD) | 2026-10-14 |
| [GOLD](https://huggingface.co/spaces/HuggingFaceH4/on-policy-distillation) | 実装・解説資料 | [公式コードあり（実験的）](https://github.com/huggingface/trl) | 2026-10-14 |
| [SimpleOPD](https://arxiv.org/abs/2608.14277) | 出力分布・トークンの対応 | [公式コードあり](https://github.com/hhnqqq/SimpleOPD) | 2026-10-14 |
| [CompassOPD](https://arxiv.org/abs/2609.10154) | 出力分布・トークンの対応 | 公式コードを確認できず | 2026-10-14 |
| [DVLM](https://arxiv.org/abs/2609.33816) | 出力分布・トークンの対応 | 公式コードを確認できず | 2026-10-14 |
| [ESCD](https://arxiv.org/abs/2609.34738) | 出力分布・トークンの対応 | コード公開予定（未確認） | 2026-10-14 |
| [Rethinking Cross-Tokenizer OPD](https://arxiv.org/abs/2610.08448) | 出力分布・トークンの対応 | [コードリンクあり（アクセス未確認）](https://anonymous.4open.science/r/Cross-Tokenizer-OPD) | 2026-10-14 |
| [CAST](https://arxiv.org/abs/2610.13257) | 出力分布・トークンの対応 | 公式コードを確認できず | 2026-10-14 |
| [Mint-Agent](https://arxiv.org/abs/2608.16386) | 学習パイプラインでの利用 | 公式コードを確認できず | 2026-10-14 |
| [ACTD](https://arxiv.org/abs/2608.29662) | 関連・off-policy KD | [公式コードあり](https://github.com/hyhy892/ACTD) | 2026-10-14 |

<!-- CODE-STATUS:END -->

## 追加・訂正への協力

研究の追加や記述の訂正は、[CONTRIBUTING.md](CONTRIBUTING.md)の手順で提案できます。生徒の生成データとトークナイザーの違いについて、一次文献の該当箇所を示してください。構造化した情報は、[`data/papers.yml`](data/papers.yml)に記録しています。

このサーベイのメタデータは[CC0 1.0](LICENSE)で公開しています。各論文・コード・外部ページには、それぞれのライセンスが適用されます。
