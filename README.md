## 폴더와 파일 안내

### `for_prof/` — 교수님께 연구를 설명하는 자료

| 파일 | 용도 |
|---|---|
| `for_ryoo.html` | 유수희 교수님께 연구를 처음부터 설명하는 현재의 전체 안내 페이지입니다. 논문 전체 흐름과 현재 분석이 재검토 단계라는 점까지 포함합니다.|
| `for_kim.html` | 김현수 교수님께 공유하기 위해 만든 이전의 상세 설명 페이지입니다. 연구의 현실적 의미, CDP, 큰 자료를 다루는 방식과 AI의 역할을 설명합니다. |

### `manuals/` — 연구 판단 기준

| 파일 | 용도 |
|---|---|
| `keyword.docx` | 자료 수집 단계에서 사용한 AI 도구명, 일반 AI 용어와 정규표현식을 기록합니다. |
| `relevance_and_flag.docx` | 개인적 AI 사용 경험의 relevance, 자해·자살 위험 수준, psychosis flag를 판단한 초기 screening 기준입니다. |
| `exclusion.docx` | pilot 과정에서 정리한 EX-1~EX-9 제외 기준입니다. 개인적 AI 사용이 없거나, AI가 단순 요약·검색·인용 대상으로만 쓰인 경우 등을 구분합니다. |
| `rickwood_coding_manual.docx` | corpus를 `Timeframe`, 도움 요청 생태계에서의 `Source`, 사용 목적 `Type`으로 coding하는 상세 manual입니다. 이 coding은 CDP 결론이 아니라 sampling을 위한 corpus 지도입니다. |
| `sampling_strategy.docx` | 조합별 빈도, 표면 내용 요약, community 내·간 동질성 확인, residual 확인을 거쳐 purposeful sample을 만드는 절차입니다. |
| `first_sampling_claim.docx` | sampling 규칙을 실제 corpus에 적용한 결과입니다. 63개 sample의 구성과 각 slot의 배정 근거를 담습니다. |

### `manuals/logs/` — sampling 결정의 실제 기록

| 파일 | 용도 |
|---|---|
| `first_sampling_decision_log.docx` | dominant combination부터 community별 잔여 조합까지 실제로 검토한 순서, 비율, 동질성 판단과 결정 과정을 기록합니다. |
| `first_sampling_decision_evaluation.docx` | 분석결과에 따른 sampling 틀에 대한 pass/fail 평가, 그 이유와 63개 sample 구성을 요약·평가합니다(아직 작성 중). |

### `analysis/` — 현재 진행 중인 close reading 기록

| 파일 | 용도 |
|---|---|
| `result_first_round.docx` | 여러 도움 요청 상황에서 시도한 1차 CDP 분석을 한 문서에 모은 것입니다. 아직 중국어로 작성중인데 다 작성하면 한국어 버전도 올릴 것입니다. |


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


### 그 밖의 항목

- `reader/`는 게시물을 찾고 읽는 부담을 줄이기 위해 연구자가 자신의 작업 방식에 맞춰 만든 개인용 reader입니다. 
- `data/`와 원문 수준의 post 자료는 저장소에 공개하지 않습니다. 저장소에는 연구 절차를 확인할 수 있는 manual, 판단 log, validation output과 실행 코드만 남깁니다.
- `docs/`는 개인용 메모입니다. 
- `.vscode/`는 편집기 설정이며 연구 내용과 관계없습니다.
- `.gitignore`는 원자료, 문헌, API KEY, API 설정과 실행 중 생성되는 checkpoint가 GitHub에 올라가지 않도록 관리합니다.

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

