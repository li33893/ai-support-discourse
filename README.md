
## 먼저 읽을 자료

| 순서 | 파일 | 무엇을 보기 위한 자료인가 |
|---|---|---|
| 1 | [`for_prof/for_ryoo.html`](for_prof/for_ryoo.html) | 연구를 처음 접하는 교수님을 위한 전체 설명 페이지입니다. 연구 문제, CDP, 전체 논문 흐름, 자료와 LLM의 역할, sampling, 현재 분석 상태를 한 번에 설명합니다. |
| 2 | [`manuals/sampling_strategy.docx`](manuals/sampling_strategy.docx) | 어떤 원리와 순서로 close-reading 대상을 선정하기로 했는지 설명합니다. 실제 게시물을 뽑기 전에 정한 sampling 절차입니다. |
| 3 | [`manuals/first_sampling_claim.docx`](manuals/first_sampling_claim.docx) | 위의 원칙을 적용해 구성한 63개 1차 sample과 각 배정 수의 이유를 정리합니다. |
| 4 | [`manuals/logs/first_sampling_decision_log.docx`](manuals/logs/first_sampling_decision_log.docx) | 어떤 조합을 어떤 순서로 확인했고, 동질성·community 차이·잔여 사례를 실제로 어떻게 판단했는지 보여 주는 전체 기록입니다. |
| 5 | [`manuals/analysis_strategy.docx`](manuals/analysis_strategy.docx) | sample을 close reading한 뒤 variation과 반례를 어떻게 확인하고 전체 corpus로 돌아갈지 설명합니다. |
| 6 | [`analysis/result_first_round.docx`](analysis/result_first_round.docx) | 1차 분석에서 시도한 상황별 해석을 모은 작업 문서입니다. 현재 재분석 중이므로 완성된 결과가 아니라 분석이 어디까지 진행되었는지 확인하는 자료입니다. |

`for_prof/for_kim.html`은 김 교수님께 연구의 문제의식과 방법을 설명하기 위해 먼저 만든 상세 페이지입니다. `for_prof/for_ryoo.html`은 연구를 처음 접하는 독자를 위해 전체 논문 흐름과 현재 상태를 더 앞에서부터 설명한 버전입니다.

## 연구의 전체 흐름

1. 5개 community의 Reddit 게시물을 월별로 수집하고 AI 관련 keyword로 1차 선별합니다.
2. 개인의 실제 AI 사용 경험과 정신건강 도움 요청이 연결된 게시물인지 screening합니다.
3. relevance 판단에 대해 human–LLM agreement를 확인합니다.
4. 중복, 고위험 사례 및 방법론적 제외 대상을 정리해 corpus를 확정합니다.
5. 도움 요청 상황을 `Timeframe × Source × Type`으로 coding하여 전체 corpus의 지형을 만듭니다.
6. pilot validation과 별도의 50개 spot check로 coding의 일관성을 확인합니다.
7. 반복되는 조합, community contrast, hard-to-say 사례, 독특한 사례와 residual을 함께 포함해 63개 1차 purposeful sample을 구성합니다.
8. 게시물 전체를 CDP로 close reading합니다.
9. 새 variation이나 반례가 나오면 전체 corpus로 돌아가 다시 검색하고, 필요하면 re-sampling합니다.
10. 반복되는 repertoire, ideological dilemma, subject position과 각 claim의 적용 범위를 정리합니다.

## 폴더와 파일 안내

### `for_prof/` — 교수님께 연구를 설명하는 자료

| 파일 | 용도 |
|---|---|
| `for_ryoo.html` | 연구를 처음부터 설명하는 현재의 전체 안내 페이지입니다. 논문 전체 흐름과 현재 분석이 재검토 단계라는 점까지 포함합니다. |
| `for_kim.html` | 김 교수님께 공유하기 위해 만든 이전의 상세 설명 페이지입니다. 연구의 현실적 의미, CDP, 큰 자료를 다루는 방식과 AI의 역할을 설명합니다. |
| `for_kim_cdp.png` | `for_kim.html`에서 CDP의 분석 구조를 설명할 때 사용하는 그림입니다. 별도로 읽어야 하는 연구 문서는 아닙니다. |

### `manuals/` — 연구 판단 기준

| 파일 | 용도 |
|---|---|
| `keyword.docx` | 자료 수집 단계에서 사용한 AI 도구명, 일반 AI 용어와 정규표현식을 기록합니다. |
| `relevance_and_flag.docx` | 개인적 AI 사용 경험의 relevance, 자해·자살 위험 수준, psychosis flag를 판단한 초기 screening 기준입니다. |
| `exclusion.docx` | pilot 과정에서 정리한 EX-1~EX-9 제외 기준입니다. 개인적 AI 사용이 없거나, AI가 단순 요약·검색·인용 대상으로만 쓰인 경우 등을 구분합니다. |
| `rickwood_coding_manual.docx` | corpus를 `Timeframe`, 도움 요청 생태계에서의 `Source`, 사용 목적 `Type`으로 coding하는 상세 manual입니다. 이 coding은 CDP 결론이 아니라 sampling을 위한 corpus 지도입니다. |
| `sampling_strategy.docx` | 조합별 빈도, 표면 내용 요약, community 내·간 동질성 확인, residual 확인을 거쳐 purposeful sample을 만드는 절차입니다. |
| `first_sampling_claim.docx` | sampling 규칙을 실제 corpus에 적용한 결과입니다. 63개 sample의 구성과 각 slot의 배정 근거를 담습니다. |
| `analysis_strategy.docx` | close reading에서 발견한 variation이 sampling frame과 어떻게 연결되는지 확인하고, 분석 뒤 전체 corpus의 coverage를 다시 점검하는 계획입니다. |
| `repertoire_recognition_prompt_script.docx` | 현재 비어 있는 작업용 placeholder입니다. 현 단계의 분석이나 sampling에 사용한 파일이 아닙니다. |

### `manuals/logs/` — sampling 결정의 실제 기록

| 파일 | 용도 |
|---|---|
| `first_sampling_decision_log.docx` | dominant combination부터 community별 잔여 조합까지 실제로 검토한 순서, 비율, 동질성 판단과 결정 과정을 기록합니다. |
| `first_sampling_decision_evaluation.docx` | 위 기록을 바탕으로 각 주요 단위의 pass/fail 이유와 63개 sample 구성을 요약·평가합니다. |
| `~$first_sampling_decision_log.docx` | Word가 문서를 열 때 만든 임시 잠금 파일입니다. 연구 자료가 아니며 삭제해도 됩니다. |

### `analysis/` — 현재 진행 중인 close reading 기록

| 파일 | 용도 |
|---|---|
| `result_first_round.docx` | 여러 도움 요청 상황에서 시도한 1차 CDP 분석을 한 문서에 모은 것입니다. 현재 분석 구조를 다시 검토 중이므로 최종 결과로 사용하지 않습니다. |
| `Anxiety Episodic x SA/summary_anxiety_episodic_sa.docx` | r/Anxiety의 일회적 증상 평가·정보 검색 상황에서 책임 배치, 시간 구조, 정보 검색 chain과 subject position을 정리한 단위별 메모입니다. |
| `Habitual x Primary x CO or VE/summary_habitual_primary_co_ve.docx` | AI를 반복적인 주요 companionship·venting 수단으로 사용하는 게시물에서 공통된 서사 기능과 내부 variation을 검토한 단위별 메모입니다. |
| `~$*.docx` | Word 임시 잠금 파일입니다. 분석 내용이 들어 있는 본문 파일이 아닙니다. |

`analysis/`의 문서는 분석 과정의 흔적을 남기기 위한 working document입니다. 현재 목표는 이 문장을 바로 확정하는 것이 아니라, 같은 상황 안의 variation, 상황·community 사이의 차이, 반례와 새 변이를 다시 확인하여 분석을 재구성하는 것입니다.

### `outputs/` — 자료 지도와 validation 결과

이 폴더의 수치와 그림은 corpus와 coding의 상태를 확인하기 위한 것입니다. CDP findings를 보여 주는 결과물이 아닙니다.

| 파일 | 용도 |
|---|---|
| `posts_list_kw_hit_log.json` | community와 월별 전체 수집 건수, keyword 통과 건수와 hit rate를 기록합니다. |
| `rickwood_confusion_matrices.txt` | pilot에서 human coding과 LLM coding을 비교한 Timeframe·Source·Type confusion matrix와 kappa를 기록합니다. |
| `rickwood_disagreements.csv` | pilot coding에서 human과 LLM이 다르게 판단한 게시물과 판단 이유를 검토하기 위한 파일입니다. |
| `spot_check_validation_summary.csv` | full-corpus coding 뒤 별도로 뽑은 50개 spot check의 agreement, kappa, AC1 요약입니다. |
| `spot_check_category_performance.csv` | spot check에서 category별 precision과 recall을 확인합니다. |
| `spot_check_confusion_timeframe.csv` | Timeframe spot-check confusion matrix입니다. |
| `spot_check_confusion_source.csv` | Source spot-check confusion matrix입니다. |
| `spot_check_confusion_type.csv` | Type spot-check confusion matrix입니다. |
| `spot_check_disagreements.csv` | spot check에서 human과 LLM이 다르게 coding한 개별 사례 목록입니다. |
| `spot_check_disagreement_category_metrics.csv` | disagreement가 발생한 category의 성능을 다시 볼 수 있도록 정리한 표입니다. |
| `heatmap_type_by_subreddit.png` | community별 AI 사용 목적의 분포를 비교하는 heatmap입니다. |
| `stacked_timeframe_by_subreddit.png` | community별 Habitual·Episodic·NM 구성을 비교하는 100% stacked bar chart입니다. |
| `stacked_source_by_subreddit.png` | community별 도움 요청 생태계에서 AI가 놓이는 위치를 비교하는 100% stacked bar chart입니다. |

### `src/` — 재현 가능한 처리 코드

| 파일 | 수행 단계 |
|---|---|
| `01_collect.py` | Reddit 자료 수집, 50단어 기준과 AI keyword를 이용한 1차 선별, 월별 hit log 생성 |
| `02_screening_prompt.py` | relevance screening, 위험 수준 분류, psychosis flag 적용 |
| `03_agreement_check.py` | relevance screening의 human–LLM agreement 검증 |
| `04_data_cleaning.py` | relevant·분석 가능 게시물 유지, 고위험/flag 사례와 중복 제거 |
| `05_rickwood_coding.py` | pilot sample에 exclusion 및 Rickwood 3개 차원 coding 적용 |
| `06_rickwood_validation.py` | pilot의 human–LLM kappa, confusion matrix와 disagreement 검토 |
| `07_batch_coding.py` | 확정한 manual을 전체 cleaned corpus에 적용 |
| `08_spot_check_sample.py` | pilot과 겹치지 않는 50개 blind spot-check sample 생성 |
| `09_spot_check_validate.py` | spot check의 agreement, kappa, AC1과 disagreement 계산 |
| `10_code_combination_counts.py` | community × Timeframe × Type × Source 조합의 빈도와 비율 계산 |
| `11_descriptive_figure.py` | Type heatmap과 Timeframe·Source stacked chart 생성 |
| `12_sampling.py` | sampling claim에 따라 63개 1차 close-reading sample 추출 |
| `rickwood_prompt.py` | exclusion과 Rickwood coding에 실제로 사용한 system prompt |

### `docs/` — 내부 연구 메모

| 파일 | 용도 |
|---|---|
| `rationale_memo.docx` | 연구 설계와 판단 근거를 누적해서 적어 둔 내부 rationale memo입니다. 방법을 추적할 때 참고하지만 교수님께서 먼저 읽을 파일은 아닙니다. |
| `rationale_memo (자동 복구됨).docx` | Word가 자동 복구한 중복 사본입니다. 별도의 연구 자료로 보지 않습니다. |
| `새 Wordprocessor Document.docx` | sampling 이후 확인할 가설, 반례와 community 비교 지점을 빠르게 적어 둔 미정리 working memo입니다. |

### 그 밖의 항목

- `reader/`는 게시물을 찾고 읽는 부담을 줄이기 위해 연구자가 자신의 작업 방식에 맞춰 만든 개인용 reader입니다. 연구 방법이나 결과를 설명하는 자료는 아니므로 이 README의 설명 대상에서 제외합니다.
- `data/`와 원문 수준의 post 자료는 저장소에 공개하지 않습니다. 저장소에는 연구 절차를 확인할 수 있는 manual, 판단 log, validation output과 실행 코드만 남깁니다.
- `.vscode/`는 편집기 설정이며 연구 내용과 관계없습니다.
- `.gitignore`는 원자료, 문헌, API 설정과 실행 중 생성되는 checkpoint가 GitHub에 올라가지 않도록 관리합니다.

## 현재 상태

| 단계 | 상태 |
|---|---|
| 자료 수집과 keyword screening | 완료 |
| relevance screening과 agreement 검증 | 완료 |
| corpus cleaning과 중복 제거 | 완료 |
| Rickwood manual 개발과 pilot validation | 완료 |
| full-corpus coding과 50개 spot check | 완료 |
| 조합별 분포·동질성·contrast 검토 | 완료 |
| 63개 1차 purposeful sampling | 완료 |
| 상황별 CDP close reading | 재분석 중 |
| repertoire·dilemma·position 비교 | 재분석 중 |
| 반례·새 variation의 corpus 재검색 및 필요 시 re-sampling | 진행 중 |
| 최종 claim과 논의 | 이후 확정 |

