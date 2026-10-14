# 서로 다른 Tokenizer 간 On-Policy Distillation 연구 지도

> 교사와 학생의 tokenizer／어휘가 다른 On-Policy Distillation（OPD）을 일차 문헌에 근거하여 정리합니다.

[English](README.md) · [日本語](README_ja.md) · [简体中文](README_zh.md) · **한국어**

[대화형 연구 목록](https://usk-kimura.github.io/awesome-cross-tokenizer-opd/?lang=ko) ·
[구조화 데이터](data/papers.yml) · [BibTeX](references.bib)

갱신일은 **2026-10-14**입니다. 영어 README가 기준 문서이며, 이 문서는 한국어 연구 지도와 읽기 안내를 제공합니다.
“확인됨”은 공개 논문 본문에서 해당 주장을 확인했다는 뜻이며, 실험을 독립적으로 재현했다는 뜻은 아닙니다.
각 기록의 `last_verified`는 본문 주장 확인일, `metadata_last_verified`는 버전／링크 확인일,
`code_last_checked`는 공식 코드 검색일입니다. 사이트가 갱신되더라도 과거 본문 감사일은 유지합니다.

## 수록 범위

핵심 연구는 다음 조건을 모두 충족해야 합니다.

1. 공개된 영어 논문 또는 프리프린트가 있습니다.
2. 학생이 생성한 rollout 또는 학생이 방문한 상태에서 교사 감독을 받습니다.
3. 교사와 학생의 tokenizer／어휘 불일치를 명시합니다.
4. 불일치를 넘어 감독 신호를 전달하는 구체적 인터페이스를 설명합니다.
5. tokenizer가 다른 모델 쌍의 학습 실험을 보고합니다.

모델 계열이 다르다는 사실만으로 tokenizer가 다르다고 판단하지 않습니다.
Off-policy KD, 소프트웨어 프레임워크, 추측 디코딩, 대응 인터페이스가 불명확한 교차 어휘 실험은 별도로 분류합니다.
모든 모델 쌍은 **교사 → 학생** 순서입니다.

## 핵심 연구

### 출력 공간 인터페이스

| 연구 | 비교 인터페이스 | 감독 범위 | 확률 의미 | 대표 모델 쌍 |
|---|---|---|---|---|
| [DSKD / DSKDv2](https://arxiv.org/abs/2504.11426) | 은닉 상태를 상대 표현 공간에 투영하고 해당 LM head 사용; ETA로 정확히 대응하는 위치 유지 | 유지된 위치의 밀집 분포 | 공통 head 공간의 분포이며 문자열 확률 수송은 아님 | Qwen2-1.5B → GPT2-120M; Mistral-7B → TinyLLaMA-1.1B |
| [SimCT](https://arxiv.org/abs/2605.07711) | 공통 표면 token과 양쪽 tokenizer가 실현할 수 있는 최소 다중 token continuation | 유한한 지역 후보 집합 | 후보 집합 안에서 정규화한 점수이며 전체 교사 주변분포는 아님 | Qwen2.5-7B-Instruct → Phi-4-mini-Instruct / Gemma-2-2B-IT |
| [ESR](https://arxiv.org/abs/2605.27028) | 학생 rollout을 교사 tokenizer로 재인코딩한 뒤 텍스트 span을 탐욕적으로 대응 | rollout 앞부분의 대응 token | 부분 대응 목적이며 완전한 사상 분포를 정의하지 않음 | Qwen3-4B → Gemma-2-2B 등 |
| [BTB](https://arxiv.org/abs/2606.09456) | 이중 포인터로 디코딩 문자열이 동기화되는 최소 chunk 구성 | 실제 학생 생성 경로 | 경로 우도와 스칼라 credit이며 전체 어휘 목표는 아님 | Qwen3-8B → Llama-3.1-8B-SFT |
| [BPM](https://arxiv.org/abs/2607.22334) | 교사 token의 바이트열을 가장 긴 학생 token 바이트 접두사에 할당 | 학생 전체 어휘와 residual | 확률 질량 보존; 논문에서는 99% 이상 위치가 정확성 조건을 충족하며 나머지는 연쇄 분해 하한 사용 | Qwen3-32B / GLM-Z1-9B / MiniMax-M2.7 → Qwen3.5-2B |
| [SimpleOPD](https://arxiv.org/abs/2608.14277) | 교사 고유 template로 학생 텍스트를 재인코딩하고 시작／끝 위치가 같은 token 대응 | 실제 생성된 엄격한 1:1 token | 부분 reverse-KL surrogate; 불일치 위치의 증류 advantage는 0 | SU-01 → GLM-4.7-Flash / Gemma-4-26B-A4B; Qwen3.5 학생 |
| [CompassOPD](https://arxiv.org/abs/2609.10154) | 대응 텍스트 span에서 강한 교사와 같은 계열 reference 간 우도 변화 전달 | 실제 대응 단위 | span 평균 우도 차이이며 교사 분포 수송은 아님 | Qwen3.5-35B-A3B → Granite4.1-3B / Qwen3-4B / OLMo-3-7B |
| [DVLM](https://arxiv.org/abs/2609.33816) | 병렬 tokenization과 Hybrid-Prefix Attention으로 학생 어휘용 교사 head 학습 | 학생 위치의 밀집 logits | 학습된 적응 교사 분포이며 원래 교사의 문자열 확률을 정확히 주변화한 것은 아님 | Qwen3-4B → Llama-3.2-1B-Instruct / OLMo-2-1B-Instruct |
| [ESCD](https://arxiv.org/abs/2609.34738) | 교사 바이트 사건을 일부 생성한 뒤, 방문한 자식 상태에서 완성 집합 감독 | 한 단계 완성 token 집합의 합계 확률 | 집합 내부 token별 확률 배분을 고정하지 않음 | Qwen3-32B / GLM-Z1-9B → Qwen3.5-2B; Kimi-K2.7-Code → Qwen3.6-35B-A3B |
| [Rethinking Cross-Tokenizer OPD](https://arxiv.org/abs/2610.08448) | 엄격한 1:1 span 대응과 공통 어휘／학생 선택 top-k 후보에서 reverse KL | 정확히 대응하는 위치; top-16 평가 | 부분집합에서 재정규화한 분포이며 전체 어휘 수송은 아님 | Qwen2.5-7B-Instruct → Llama-3.2-3B-Instruct; Granite-4.1-8B → Phi-4-mini-instruct / Qwen2.5-7B-Base |
| [CAST](https://arxiv.org/abs/2610.13257) | 텍스트 대응 후 학생 불확실성과 교사 점수 평활도에 따라 chunk credit 배분 | 실제 대응 token; 불일치 위치는 초기 학생 policy에 고정 | chunk advantage 보존과 어휘 확률 질량 보존은 다름 | Qwen3-8B → Mistral-7B / Llama-3.1-8B（SFT 초기화） |

SimCT, BTB, BPM은 각각 유한 후보, 실제 경로, 전체 어휘 바이트 접두사 목표를 감독합니다.
“token alignment”라는 이름만으로 같은 방법으로 취급하지 않습니다.

### 감독 범위와 신뢰성

[Rethinking의 Sections 3–5](https://arxiv.org/html/2610.08448v1)는 연구한 학습 run에서
엄격한 대응이 학생 token의 85.57–96.98%를 포함하고, 학생 선택 top-16이 전체 공통 어휘 OPD의
미증류 학생 대비 개선 폭을 적어도 96% 유지한다고 보고합니다.
불일치 span의 log-probability에 MSE를 추가한 18개 양의 가중치 설정에서는 모두 평균 정확도가 낮아졌습니다.
이 결과는 평가한 목적함수와 모델 쌍에 한정되며, 모든 불일치 감독이 해롭다는 결론으로 일반화하지 않습니다.
논문에 연결된 익명 코드는 확인 시 HTTP 401을 반환했으므로 구현 내용은 감사하지 못했습니다.

[ESCD](https://arxiv.org/html/2609.34738v1)는 남은 바이트 조건을 충족하는 완성 집합의 총확률을 감독합니다.
완성 token은 남은 부분의 경계를 넘어갈 수도 있고, 한 token으로 완성할 집합이 비어 있으면 자식 상태 보조 손실을 적용하지 않습니다.
[CAST](https://arxiv.org/html/2610.13257v1)는 chunk credit 배분과 불일치 위치의 policy 변화 제어를 다룹니다.
감독 사건, 초기화, 평가 조건을 구분해서 비교해야 합니다.

### 어휘 확률 사상을 우회하는 방법

- [GAD](https://arxiv.org/abs/2511.10643): 고정 교사 응답과 현재 학생 응답을 구분하는 discriminator를 함께 갱신하여 시퀀스 단위 RL reward를 제공합니다. GPT-5-Chat → Qwen2.5 / Llama로 평가합니다.
- [ROPD](https://arxiv.org/abs/2605.07396): 교사와 학생 응답을 비교하여 prompt별 rubric을 만든 뒤 verifier로 학생 rollout을 채점합니다. Token alignment가 필요 없으며 GPT-5.2-Chat → Qwen3 / Gemma-3를 평가합니다.
- [OmniOPD](https://arxiv.org/abs/2606.01476): 교사 continuation을 Monte Carlo로 표집하고 디코딩한 chunk의 의미 유사도로 감독합니다. Claude, Gemini 같은 텍스트 전용 교사도 지원합니다.

### 실제 학습 pipeline에서의 활용

[Mint-Agent](https://arxiv.org/abs/2608.16386) v2의 Section 5.2는 학생 실패 trajectory의 중요 turn에서
현재 학생이 action을 재생성하고, DeepSeek-V4-Pro의 텍스트 chunk 경로 점수를 학생 token에 배분합니다.
Qwen3.5-9B／Qwen3.6-27B agentic specialist에서 사용하지만, 최종 Mint-Cu／Mint-Ag 성능은
SFT, OPD, RLVR, 모델 병합을 결합한 결과입니다. 교차 tokenizer 단계의 효과만을 분리해서 보여주지는 않습니다.
이후 다중 교사 통합은 같은 tokenizer의 specialist를 사용합니다.

## 근거에 제한이 있는 연구

- [REOPOLD](https://openreview.net/forum?id=NPhEUvT1jH)의 이전 감사 버전은 Phi-4-Mini-Reasoning → DeepSeek-R1-Distill-Qwen-1.5B를 보고하지만, 두 어휘의 sampled-token 사건을 어떻게 대응시켰는지는 충분히 설명하지 않습니다. [저자 최신 페이지](https://www.microsoft.com/en-us/research/publication/relaxed-on-policy-distillation-selective-credit-allocation-for-scaling-reasoning-efficiently/)가 NeurIPS 2026으로 표기하므로 기존 ICML 표기를 수정했습니다. [새 OpenReview 버전](https://openreview.net/forum?id=l0h1SzRI7H)은 브라우저 확인 절차 때문에 본문을 받지 못해 다시 감사하지 못했습니다.
- [OPRD / OPRD-Bridge](https://arxiv.org/abs/2606.06021)는 저랭크 은닉 표현 projector를 제안하고 서로 다른 Phi／Qwen tokenizer 실험을 보고합니다. 그러나 감사한 공개 commit에서는 [두 모델에 같은 학생 token ID를 입력](https://github.com/ShenzhiYang2000/OPRD/blob/a63236c990b1bfa9551e9d020719490d3ecd93e8/scripts/analysis/cross_arch_repr_analysis.py#L5-L8)합니다. 다른 어휘의 같은 ID는 같은 텍스트가 아니므로, 코드 공개만으로 의미적 대응이 검증되지는 않습니다.

## 경계 응용과 구현 자료

- [OVD](https://arxiv.org/abs/2601.21968) v2는 verbal score로 학생 부분 trajectory를 유지하거나 낮은 점수의 query／suffix를 교사 continuation으로 대체합니다. 학생과 교사가 섞인 trajectory로 학습하고 일부 평가에서는 추론 중에도 교사를 호출하므로 순수 학생 policy 데이터와 구분합니다.
- [OmniDraft](https://arxiv.org/abs/2507.02659)는 drafter 자신의 proposal에서 온라인 학습하는 교차 어휘 추측 디코딩입니다. 최종 출력 분포는 target model의 verification이 결정합니다.
- [GOLD](https://huggingface.co/spaces/HuggingFaceH4/on-policy-distillation)／[TRL 문서](https://huggingface.co/docs/trl/main/gold_trainer)는 디코딩 span 대응, 확률 병합, ULD fallback을 제공합니다. `trl.experimental.gold`는 실험 API이며 전체 응답의 coverage가 token 의미를 유지하는 확률 수송을 뜻하지는 않습니다.
- [KDFlow](https://arxiv.org/abs/2603.01875) v4는 여러 KD 경로를 지원하는 프레임워크입니다. Qwen3-14B → Llama3.2-3B 실험은 Appendix A.1의 off-policy 설정으로, 교차 tokenizer OPD의 근거로 취급하지 않습니다.
- [EasyOPD](https://arxiv.org/abs/2607.11012)는 `verl`에서 SimCT 등 방법을 실행하는 모듈을 제공합니다.
- [ACTD](https://arxiv.org/abs/2608.29662)는 anchor와 residual regularization으로 사상 잡음을 다룹니다. Section 4.1은 dataset reference solution을 사용하는 off-policy 학습을 명시하므로 핵심 OPD 대신 인접 KD 연구로 분류합니다.

## 읽기와 재현

- 전체 logits, 지정 token log-probability, 은닉 상태, 텍스트 전용 API는 서로 다른 교사 정보 예산입니다.
- 전체 어휘, 유한 후보, 공통 부분집합, 실제 경로, 완성 집합의 감독 사건은 다릅니다.
- 엄격한 위치 대응, 질량 보존, 모든 tokenization 경로에 대한 정확한 문자열 주변확률은 다른 성질입니다.
- EOS/BOS, chat template, 공백, Unicode, 잘못된 바이트, 코드 들여쓰기 처리도 확인해야 합니다.
- 코드가 있다는 표시는 공식 구현을 찾았다는 뜻입니다. 실험 재현이나 논문／구현 일치까지 보장하지 않습니다.

추가 off-policy KD, 문자열 확률 이론, 연구 질문과 관련 목록은 [영어 문서](README.md)에 있습니다.

<!-- CODE-STATUS:START -->
<a id="code-availability"></a>

## 공식 코드 공개 현황

공식 자료 검색으로 확인한 상태이며 독립 재현 결과가 아닙니다. “찾지 못함”은 코드가 없다는 뜻이 아닙니다. 공개 예정, 접근 미확인 링크, 확인된 공개 구현을 구분합니다. OPRD는 공개 코드가 있지만 아래에 설명된 구현상 우려가 있습니다.

| 연구 | 분류 | 공식 구현 | 확인일 |
|---|---|---|---|
| [DSKD / DSKDv2](https://arxiv.org/abs/2504.11426) | 출력 공간 인터페이스 | [공식 코드 있음](https://github.com/songmzhang/DSKDv2) | 2026-10-14 |
| [SimCT](https://arxiv.org/abs/2605.07711) | 출력 공간 인터페이스 | [공식 코드 있음](https://github.com/sunjie279/SimCT-) | 2026-10-14 |
| [ESR](https://arxiv.org/abs/2605.27028) | 출력 공간 인터페이스 | 공식 코드 미확인 | 2026-10-14 |
| [GAD](https://arxiv.org/abs/2511.10643) | 어휘 사상 우회 | [공식 코드 있음](https://github.com/microsoft/LMOps/tree/main/gad) | 2026-10-14 |
| [ROPD](https://arxiv.org/abs/2605.07396) | 어휘 사상 우회 | [공식 코드 있음](https://github.com/Peregrine123/ROPD_official) | 2026-10-14 |
| [OmniOPD](https://arxiv.org/abs/2606.01476) | 어휘 사상 우회 | 공식 코드 미확인 | 2026-10-14 |
| [OPRD / OPRD-Bridge](https://arxiv.org/abs/2606.06021) | 공개 구현에 우려 | [공식 코드 있음](https://github.com/ShenzhiYang2000/OPRD) | 2026-10-14 |
| [BTB](https://arxiv.org/abs/2606.09456) | 출력 공간 인터페이스 | [공식 코드 있음](https://github.com/ivanniu/On-Policy-Distill) | 2026-10-14 |
| [REOPOLD](https://openreview.net/forum?id=NPhEUvT1jH) | 인터페이스 설명 부족 | 공식 코드 미확인 | 2026-10-14 |
| [BPM](https://arxiv.org/abs/2607.22334) | 출력 공간 인터페이스 | [공식 코드 있음](https://github.com/K1XE/BPM) | 2026-10-14 |
| [OVD](https://arxiv.org/abs/2601.21968) | 경계 응용 | [공식 코드 있음](https://github.com/menik1126/OVD-code) | 2026-10-14 |
| [OmniDraft](https://arxiv.org/abs/2507.02659) | 경계 응용 | 공식 코드 미확인 | 2026-10-14 |
| [KDFlow](https://arxiv.org/abs/2603.01875) | 프레임워크 | [공식 코드 있음](https://github.com/songmzhang/KDFlow) | 2026-10-14 |
| [EasyOPD](https://arxiv.org/abs/2607.11012) | 프레임워크 | [공식 코드 있음](https://github.com/lds-ustc/EasyOPD) | 2026-10-14 |
| [GOLD](https://huggingface.co/spaces/HuggingFaceH4/on-policy-distillation) | 구현·연구 자료 | [공식 코드 있음（실험적）](https://github.com/huggingface/trl) | 2026-10-14 |
| [SimpleOPD](https://arxiv.org/abs/2608.14277) | 출력 공간 인터페이스 | [공식 코드 있음](https://github.com/hhnqqq/SimpleOPD) | 2026-10-14 |
| [CompassOPD](https://arxiv.org/abs/2609.10154) | 출력 공간 인터페이스 | 공식 코드 미확인 | 2026-10-14 |
| [DVLM](https://arxiv.org/abs/2609.33816) | 출력 공간 인터페이스 | 공식 코드 미확인 | 2026-10-14 |
| [ESCD](https://arxiv.org/abs/2609.34738) | 출력 공간 인터페이스 | 코드 공개 예정（미확인） | 2026-10-14 |
| [Rethinking Cross-Tokenizer OPD](https://arxiv.org/abs/2610.08448) | 출력 공간 인터페이스 | [코드 링크 있음（접근 미확인）](https://anonymous.4open.science/r/Cross-Tokenizer-OPD) | 2026-10-14 |
| [CAST](https://arxiv.org/abs/2610.13257) | 출력 공간 인터페이스 | 공식 코드 미확인 | 2026-10-14 |
| [Mint-Agent](https://arxiv.org/abs/2608.16386) | 실제 학습 pipeline | 공식 코드 미확인 | 2026-10-14 |
| [ACTD](https://arxiv.org/abs/2608.29662) | 인접／off-policy KD | [공식 코드 있음](https://github.com/hyhy892/ACTD) | 2026-10-14 |

<!-- CODE-STATUS:END -->

## 기여와 인용

[CONTRIBUTING.md](CONTRIBUTING.md)에 따라 일차 문헌의 구체적인 절, 버전, 교사 → 학생 모델 쌍을 제시해주세요.
[CITATION.cff](CITATION.cff)로 이 연구 지도를 인용하고 실제 사용한 원 논문도 인용해주세요.
메타데이터와 직접 작성한 요약은 [CC0 1.0](LICENSE)로 공개하며, 연결된 논문과 코드에는 각각의 라이선스가 적용됩니다.
