# 跨 Tokenizer 的 On-Policy Distillation 研究综述

> 基于一手文献，梳理教师与学生使用不同 tokenizer／词表时的 On-Policy Distillation（OPD）。

[English](README.md) · [日本語](README_ja.md) · **简体中文** · [한국어](README_ko.md)

[交互式研究目录](https://usk-kimura.github.io/awesome-cross-tokenizer-opd/?lang=zh) ·
[结构化数据](data/papers.yml) · [BibTeX](references.bib)

更新日期：**2026-10-14**。英文 README 是规范版本。本页提供中文研究地图与阅读说明。
“已核查”表示对照公开论文全文确认了相应表述，不表示独立复现实验。
每条记录的 `last_verified` 是全文论断的核查日期；`metadata_last_verified` 和
`code_last_checked` 分别记录版本／链接核查与官方代码检索日期。旧的全文核查日期不会因网站更新而改变。

## 收录范围

核心研究必须同时满足以下条件：

1. 有公开的英文论文或预印本。
2. 在学生生成的 rollout 或学生访问的状态上提供教师监督。
3. 明确存在教师与学生的 tokenizer／词表差异。
4. 说明跨越该差异传递监督的具体接口。
5. 报告至少一组 tokenizer 不匹配的训练实验。

不同模型家族本身不能证明 tokenizer 不同。离策略 KD、软件框架、推测解码，
以及没有充分说明映射接口的跨词表实验，与核心方法分开列出。所有模型对均按 **教师 → 学生** 排列。

## 核心研究

### 输出空间接口

| 研究 | 比较接口 | 监督覆盖 | 概率语义 | 代表性模型对 |
|---|---|---|---|---|
| [DSKD / DSKDv2](https://arxiv.org/abs/2504.11426) | 将隐藏状态投影到对方表示空间，复用对应 LM head；ETA 保留严格对齐位置 | 保留位置上的稠密分布 | 共享 head 空间的分布，不是字符串概率输运 | Qwen2-1.5B → GPT2-120M；Mistral-7B → TinyLLaMA-1.1B |
| [SimCT](https://arxiv.org/abs/2605.07711) | 共享表面 token 与双方 tokenizer 可实现的最短多 token continuation | 有限的局部候选集合 | 候选集合内归一化的分数，不是完整教师边缘分布 | Qwen2.5-7B-Instruct → Phi-4-mini-Instruct / Gemma-2-2B-IT |
| [ESR](https://arxiv.org/abs/2605.27028) | 将学生 rollout 重新编码为教师 token，贪心对齐文本 span | rollout 前段的对齐 token | 部分对齐目标，没有完整的映射分布 | Qwen3-4B → Gemma-2-2B 等 |
| [BTB](https://arxiv.org/abs/2606.09456) | 双指针构造解码文本同步的最小 chunk | 实际生成的学生路径 | 路径似然与标量 credit，不是全词表目标 | Qwen3-8B → Llama-3.1-8B-SFT |
| [BPM](https://arxiv.org/abs/2607.22334) | 把教师 token 概率分配给其字节序列的最长学生 token 前缀 | 学生全词表及 residual | 质量守恒；论文报告超过 99% 的位置满足精确条件，其余采用链式分解下界 | Qwen3-32B / GLM-Z1-9B / MiniMax-M2.7 → Qwen3.5-2B |
| [SimpleOPD](https://arxiv.org/abs/2608.14277) | 使用教师自己的模板重新编码学生文本，匹配起止位置完全相同的 token | 实际生成的严格 1:1 对齐 token | 部分 reverse-KL surrogate；未对齐位置的蒸馏 advantage 为零 | SU-01 → GLM-4.7-Flash / Gemma-4-26B-A4B；Qwen3.5 学生 |
| [CompassOPD](https://arxiv.org/abs/2609.10154) | 在对齐文本 span 上，传递强教师相对同家族 reference 的似然变化 | 实际生成的对齐单元 | span 平均的似然差，不是教师分布输运 | Qwen3.5-35B-A3B → Granite4.1-3B / Qwen3-4B / OLMo-3-7B |
| [DVLM](https://arxiv.org/abs/2609.33816) | 平行 tokenization 与 Hybrid-Prefix Attention，训练面向学生词表的教师 head | 学生位置上的稠密 logits | 学习得到的适配教师分布，不是原教师字符串概率的精确边缘化 | Qwen3-4B → Llama-3.2-1B-Instruct / OLMo-2-1B-Instruct |
| [ESCD](https://arxiv.org/abs/2609.34738) | 教师字节事件被部分生成后，在已访问的子状态监督完成集合 | 可用单步完成 token 的总概率 | 不规定集合内部各 token 的概率分配 | Qwen3-32B / GLM-Z1-9B → Qwen3.5-2B；Kimi-K2.7-Code → Qwen3.6-35B-A3B |
| [Rethinking Cross-Tokenizer OPD](https://arxiv.org/abs/2610.08448) | 严格 1:1 span 对齐，在共享词表或学生选择的 top-k 子集上计算 reverse KL | 严格对齐位置；评估 top-16 | 子集内重新归一化，不是全词表概率输运 | Qwen2.5-7B-Instruct → Llama-3.2-3B-Instruct；Granite-4.1-8B → Phi-4-mini-instruct / Qwen2.5-7B-Base |
| [CAST](https://arxiv.org/abs/2610.13257) | 解码文本对齐后，按学生不确定性与教师分数平滑度分配 chunk credit | 已对齐的实际 token；未对齐位置锚定初始学生 policy | 保留 chunk advantage，不等于词表概率质量守恒 | Qwen3-8B → Mistral-7B / Llama-3.1-8B（SFT 初始化） |

SimCT、BTB、BPM 分别监督有限候选、实际路径、全词表字节前缀目标，不能仅凭“token alignment”这个名称把它们视为同一方法。

### 覆盖范围与监督可靠性

[Rethinking 的 Sections 3–5](https://arxiv.org/html/2610.08448v1) 报告：在所研究的训练 run 中，
严格对齐覆盖 85.57–96.98% 的学生 token；学生选择的 top-16 子集保留了完整共享词表 OPD
相对未蒸馏学生的至少 96% 的提升。对不匹配 span 的 log-probability 加入 MSE 后，
18 种正权重配置的平均精度均下降。这是对所测试目标与模型对的观察，不能推广为所有不匹配监督都有害。
论文链接的匿名代码在核查时返回 HTTP 401，因此代码内容尚未审计。

[ESCD](https://arxiv.org/html/2609.34738v1) 监督满足残余字节约束的完成集合总概率。
完成 token 可能越过残余边界；单 token 完成集合为空时，不施加子状态辅助损失。
[CAST](https://arxiv.org/html/2610.13257v1) 研究 chunk credit 的分配与未对齐位置的 policy 漂移。
比较这些研究时，应区分监督事件、初始化与评价条件。

### 避开词表概率映射的方法

- [GAD](https://arxiv.org/abs/2511.10643)：共同演化的 discriminator 区分固定教师回答与当前学生回答，提供序列级 RL reward。评估 GPT-5-Chat → Qwen2.5 / Llama。
- [ROPD](https://arxiv.org/abs/2605.07396)：对比教师与学生回答生成 prompt 专属 rubric，再由 verifier 评分学生 rollout。无需 token alignment；评估 GPT-5.2-Chat → Qwen3 / Gemma-3。
- [OmniOPD](https://arxiv.org/abs/2606.01476)：对教师 continuation 做 Monte Carlo sampling，以解码 chunk 的语义相似度监督学生。支持 Claude、Gemini 等仅提供文本的教师。

### 应用训练流程

[Mint-Agent](https://arxiv.org/abs/2608.16386) v2 的 Section 5.2 在学生失败轨迹的关键 turn
重新采样 action，并将 DeepSeek-V4-Pro 的文本 chunk 路径分数分配到学生 token。
该步骤用于 Qwen3.5-9B／Qwen3.6-27B 的 agentic specialist。
最终 Mint-Cu／Mint-Ag 的结果结合 SFT、OPD、RLVR 与模型合并，不能单独归因于跨 tokenizer 阶段。
后续多教师整合使用 tokenizer 相同的 specialist。

## 需要保留证据限制的研究

- [REOPOLD](https://openreview.net/forum?id=NPhEUvT1jH) 的旧审计版本报告 Phi-4-Mini-Reasoning → DeepSeek-R1-Distill-Qwen-1.5B，但没有充分说明两套词表中 sampled-token 事件如何对应。[作者最新页面](https://www.microsoft.com/en-us/research/publication/relaxed-on-policy-distillation-selective-credit-allocation-for-scaling-reasoning-efficiently/) 列为 NeurIPS 2026，已纠正此前的 ICML 标注。[新的 OpenReview 版本](https://openreview.net/forum?id=l0h1SzRI7H) 因浏览器验证未能取得全文，因此尚未重新审计该版本。
- [OPRD / OPRD-Bridge](https://arxiv.org/abs/2606.06021) 提出低秩隐藏表示 projector，并报告 Phi → Qwen 的不同 tokenizer 实验。然而，在审计的公开 commit 中，[两模型接收相同的学生 token ID](https://github.com/ShenzhiYang2000/OPRD/blob/a63236c990b1bfa9551e9d020719490d3ecd93e8/scripts/analysis/cross_arch_repr_analysis.py#L5-L8)。不同词表中的相同 ID 不表示相同文本；有公开代码不等于已验证语义对齐。

## 边界应用与实现资源

- [OVD](https://arxiv.org/abs/2601.21968) v2 用 verbal score 保留学生子轨迹或替换低分 query／suffix，再在学生与教师混合轨迹上训练。一些评价配置在推理时也调用教师，因此与纯学生 policy 数据区分。
- [OmniDraft](https://arxiv.org/abs/2507.02659) 是从 drafter 自身 proposal 在线学习的跨词表推测解码；最终输出分布受目标模型 verification 控制。
- [GOLD](https://huggingface.co/spaces/HuggingFaceH4/on-policy-distillation)／[TRL 文档](https://huggingface.co/docs/trl/main/gold_trainer) 对齐解码 span、合并概率，并使用 ULD fallback。`trl.experimental.gold` 是实验接口；全文覆盖不意味着保留 token 语义的概率输运。
- [KDFlow](https://arxiv.org/abs/2603.01875) v4 是支持多种 KD 路径的框架；Qwen3-14B → Llama3.2-3B 的跨 tokenizer 实验在 Appendix A.1 中属于 off-policy，不能据此证明跨 tokenizer OPD。
- [EasyOPD](https://arxiv.org/abs/2607.11012) 在 `verl` 上提供 SimCT 等方法的可运行模块。
- [ACTD](https://arxiv.org/abs/2608.29662) 通过 anchor 与 residual regularization 处理映射噪声；Section 4.1 明确使用数据集 reference solution 进行 off-policy 训练，因此是相关 KD 文献，不属于核心 OPD。

## 阅读与复现

- 先比较教师访问要求：完整 logits、指定 token 的 log-probability、隐藏状态、纯文本是不同的信息预算。
- 全词表、有限候选、共享子集、实际路径与完成集合的监督事件不同。
- 严格位置对齐、质量守恒与对所有 tokenization 路径求和的精确字符串概率，是不同性质。
- 检查 EOS/BOS、chat template、空白、Unicode、无效字节与代码缩进的处理。
- 有代码只表示找到官方实现；不表示实验已复现，也不消除论文与实现的证据限制。

更多相关 off-policy KD、字符串概率理论、研究问题与综述列表见 [英文版](README.md)。

<!-- CODE-STATUS:START -->
<a id="code-availability"></a>

## 官方代码公开情况

状态来自官方资料检索，不是独立复现。“未找到”不表示代码不存在。计划公开、不可访问的代码链接与已确认的公开实现分别标记。OPRD 虽有代码，仍存在下文所述的实现疑问。

| 研究 | 分类 | 官方实现 | 核查日期 |
|---|---|---|---|
| [DSKD / DSKDv2](https://arxiv.org/abs/2504.11426) | 输出空间接口 | [有官方代码](https://github.com/songmzhang/DSKDv2) | 2026-10-14 |
| [SimCT](https://arxiv.org/abs/2605.07711) | 输出空间接口 | [有官方代码](https://github.com/sunjie279/SimCT-) | 2026-10-14 |
| [ESR](https://arxiv.org/abs/2605.27028) | 输出空间接口 | 未找到官方代码 | 2026-10-14 |
| [GAD](https://arxiv.org/abs/2511.10643) | 避开词表映射 | [有官方代码](https://github.com/microsoft/LMOps/tree/main/gad) | 2026-10-14 |
| [ROPD](https://arxiv.org/abs/2605.07396) | 避开词表映射 | [有官方代码](https://github.com/Peregrine123/ROPD_official) | 2026-10-14 |
| [OmniOPD](https://arxiv.org/abs/2606.01476) | 避开词表映射 | 未找到官方代码 | 2026-10-14 |
| [OPRD / OPRD-Bridge](https://arxiv.org/abs/2606.06021) | 公开实现存在疑问 | [有官方代码](https://github.com/ShenzhiYang2000/OPRD) | 2026-10-14 |
| [BTB](https://arxiv.org/abs/2606.09456) | 输出空间接口 | [有官方代码](https://github.com/ivanniu/On-Policy-Distill) | 2026-10-14 |
| [REOPOLD](https://openreview.net/forum?id=NPhEUvT1jH) | 接口描述不足 | 未找到官方代码 | 2026-10-14 |
| [BPM](https://arxiv.org/abs/2607.22334) | 输出空间接口 | [有官方代码](https://github.com/K1XE/BPM) | 2026-10-14 |
| [OVD](https://arxiv.org/abs/2601.21968) | 边界应用 | [有官方代码](https://github.com/menik1126/OVD-code) | 2026-10-14 |
| [OmniDraft](https://arxiv.org/abs/2507.02659) | 边界应用 | 未找到官方代码 | 2026-10-14 |
| [KDFlow](https://arxiv.org/abs/2603.01875) | 框架 | [有官方代码](https://github.com/songmzhang/KDFlow) | 2026-10-14 |
| [EasyOPD](https://arxiv.org/abs/2607.11012) | 框架 | [有官方代码](https://github.com/lds-ustc/EasyOPD) | 2026-10-14 |
| [GOLD](https://huggingface.co/spaces/HuggingFaceH4/on-policy-distillation) | 实现与研究资料 | [有官方代码（实验性）](https://github.com/huggingface/trl) | 2026-10-14 |
| [SimpleOPD](https://arxiv.org/abs/2608.14277) | 输出空间接口 | [有官方代码](https://github.com/hhnqqq/SimpleOPD) | 2026-10-14 |
| [CompassOPD](https://arxiv.org/abs/2609.10154) | 输出空间接口 | 未找到官方代码 | 2026-10-14 |
| [DVLM](https://arxiv.org/abs/2609.33816) | 输出空间接口 | 未找到官方代码 | 2026-10-14 |
| [ESCD](https://arxiv.org/abs/2609.34738) | 输出空间接口 | 代码计划公开（未确认） | 2026-10-14 |
| [Rethinking Cross-Tokenizer OPD](https://arxiv.org/abs/2610.08448) | 输出空间接口 | [有代码链接（访问未确认）](https://anonymous.4open.science/r/Cross-Tokenizer-OPD) | 2026-10-14 |
| [CAST](https://arxiv.org/abs/2610.13257) | 输出空间接口 | 未找到官方代码 | 2026-10-14 |
| [Mint-Agent](https://arxiv.org/abs/2608.16386) | 应用训练流程 | 未找到官方代码 | 2026-10-14 |
| [ACTD](https://arxiv.org/abs/2608.29662) | 相关／off-policy KD | [有官方代码](https://github.com/hyhy892/ACTD) | 2026-10-14 |

<!-- CODE-STATUS:END -->

## 贡献与引用

请根据 [CONTRIBUTING.md](CONTRIBUTING.md) 提供一手文献的具体章节、版本与教师 → 学生模型对。
使用 [CITATION.cff](CITATION.cff) 引用本综述，并引用实际使用的原论文。
元数据及原创摘要使用 [CC0 1.0](LICENSE)；链接的论文、代码与外部页面保留各自的许可。
