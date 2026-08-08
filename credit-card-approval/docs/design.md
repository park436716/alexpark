# 신용카드 간이심사 모델 설계 문서

**목표**: CB(신용평가사) 조회 없이, 신청서 정보 + 디바이스/행동 데이터만으로 심사 통과 확률 `p_approve` 산출.

**사용 시나리오**: 정식 심사 이전 단계에서 (a) 사용자에게 예상 승인률을 즉시 안내하거나, (b) 저위험 신청 건만 CB 조회로 넘겨서 조회 비용을 절감하는 "프리 스크리닝" 용도.

---

## 1. 문제 정의

### 1.1 예측 대상

- **`y = 1`**: 정식 심사에서 승인된 신청 (또는 승인 후 6개월 내 30일 이상 연체 없음)
- **`y = 0`**: 심사 거절된 신청 (또는 승인 후 6개월 내 연체 발생)

두 정의의 트레이드오프:

| 레이블 정의 | 장점 | 단점 |
|---|---|---|
| 승인/거절 이진 | 데이터 풍부, 즉시 관측 | 과거 심사자의 편향을 그대로 학습 |
| 승인 + 연체 없음 | 실제 리스크와 정렬 | 관측까지 6개월 대기, 리젝트 인퍼런스 필요 |

**권장**: 1차 모델은 승인/거절 이진으로 시작 → 6개월 후 후자로 재학습. 리젝트 인퍼런스(Reject Inference)는 아래 §7에서 다룸.

### 1.2 산출물

```python
{
    "p_approve": 0.73,              # 캘리브레이션된 확률
    "risk_band": "B",               # A(≥0.85) / B(0.60-0.85) / C(0.35-0.60) / D(<0.35)
    "top_reasons": [                # 확률에 가장 큰 영향을 준 상위 3개 피처
        "재직기간이 짧음 (6개월)",
        "신청 시각이 새벽 (03:12)",
        "연소득 대비 요청한도가 높음",
    ],
    "model_version": "v0.1.0",
}
```

---

## 2. 피처 스키마

### 2.1 신청서 정보 (Application)

CB 조회를 대체할 신청자 자기신고 데이터.

| 피처 | 타입 | 예시 | 비고 |
|---|---|---|---|
| `age` | int | 34 | 만 나이 |
| `gender` | cat | M/F | 규제상 사용 여부 검토 필요 (§8) |
| `marital_status` | cat | single/married/... | |
| `dependents` | int | 2 | |
| `education` | cat | high_school/bachelor/... | |
| `job_category` | cat | office/self_employed/... | KSIC 대분류 축약 |
| `employer_size` | cat | large/mid/small/gov | |
| `employment_years` | float | 3.5 | 재직기간(년) |
| `annual_income` | float | 55_000_000 | 원 |
| `income_type` | cat | salary/business/... | |
| `housing` | cat | owned/jeonse/monthly/family | 자가/전세/월세/가족소유 |
| `residence_years` | float | 2.0 | 현 거주지 거주기간 |
| `requested_credit_limit` | float | 5_000_000 | 원 |
| `has_other_cards` | bool | true | 자기신고 |

**파생 피처**:
- `income_to_limit_ratio = annual_income / requested_credit_limit`
- `age_bucket ∈ {20s, 30s, 40s, 50s, 60s+}`
- `income_bucket` (분위)
- `stability_score`: `employment_years + residence_years` (가중)

### 2.2 디바이스 지문 (Device)

| 피처 | 타입 | 예시 | 비고 |
|---|---|---|---|
| `device_type` | cat | mobile/tablet/desktop | |
| `os_family` | cat | ios/android/windows/mac | |
| `os_version_age_days` | int | 45 | 최신 OS 대비 얼마나 오래된 버전인지 |
| `browser` | cat | safari/chrome/... | |
| `screen_resolution` | cat | 1920x1080 등 | 저해상도는 에뮬레이터 신호 |
| `is_emulator_signal` | bool | false | 하드웨어 지문 이상치 |
| `timezone_offset` | int | 540 | 분 단위, 한국은 540 |
| `language` | cat | ko-KR | |
| `ip_country` | cat | KR | |
| `ip_country_matches_locale` | bool | true | 언어와 IP 국가 일치 |
| `is_vpn_proxy` | bool | false | 상용 IP 정보 사용 |
| `device_seen_count_7d` | int | 0 | 최근 7일 동일 디바이스로 신청한 횟수 |
| `device_seen_count_90d` | int | 0 | 최근 90일 |

### 2.3 행동 시그널 (Behavior)

폼 세션 로깅 기반. 정상 신청 vs 브로커 대필 vs 봇 판별에 결정적.

| 피처 | 타입 | 예시 | 비고 |
|---|---|---|---|
| `session_duration_sec` | int | 180 | 신청 시작~제출 |
| `keystroke_count` | int | 420 | 총 키 입력 |
| `paste_ratio` | float | 0.05 | 붙여넣기로 채운 필드 비율 (높으면 대필 의심) |
| `field_edit_count` | int | 3 | 재수정 횟수 (0이면 봇 의심) |
| `avg_field_dwell_sec` | float | 4.2 | 필드당 평균 체류시간 |
| `submit_hour` | int | 14 | 0~23, 새벽 신청은 리스크 신호 |
| `submit_day_of_week` | int | 2 | |
| `autofill_used` | bool | true | 브라우저 자동완성 사용 여부 |
| `back_navigation_count` | int | 1 | 뒤로가기 횟수 |
| `time_since_prior_attempt_min` | int | -1 | 같은 디바이스의 직전 시도 이후 경과 시간, -1=최초 |

### 2.4 결측 처리 원칙

- 디바이스/행동은 자바스크립트 비활성/구형 브라우저에서 일부 결측 가능 → **결측 자체를 신호로 인코딩** (`_is_missing` 플래그 유지)
- 신청서는 필수 항목 결측 시 신청 자체가 성립하지 않음
- XGBoost는 결측을 자동 처리, LR 베이스라인은 중앙값/최빈값 대치 + 결측 플래그

---

## 3. 데이터 파이프라인

```
[신청 이벤트] ─▶ 이벤트 스토어 (Kafka)
                        │
                        ▼
[신청서 폼]  ──▶  피처 스토어 (온라인/오프라인)
[JS 클라이언트 로그]         │
[IP intel API]              ▼
                    학습 데이터셋 (오프라인)
                            │
                            ▼
                     모델 학습 + 캘리브레이션
                            │
                            ▼
                      추론 서비스 (온라인)
```

- **온라인 피처**: `device_seen_count_7d` 같은 카운터는 Redis + 슬라이딩 윈도우
- **오프라인 피처**: 학습 시점 재현을 위해 이벤트 시간 기준 스냅샷 (point-in-time correctness)
- **타임 리키지 방지**: 신청 시각 이후에 관측된 데이터(승인 여부, 연체 여부)는 절대 피처로 쓰지 않음

---

## 4. 모델 아키텍처

### 4.1 후보 모델 3종 비교

| 모델 | 판별력 | 해석성 | 운영 편의 | 결측 |
|---|---|---|---|---|
| Logistic Regression + WoE | 중 | **높음** | 높음 | 사전 처리 필요 |
| XGBoost | **높음** | 중 (SHAP) | 중 | 자동 처리 |
| Neural Net (MLP) | 높음 | 낮음 | 낮음 | 사전 처리 |

**채택**:
- **베이스라인**: WoE(Weight of Evidence) 인코딩 + Logistic Regression. 규제 대응·설명력·모니터링 유리.
- **주력**: XGBoost (`objective=binary:logistic`, `max_depth=4~6`, `n_estimators=300~600`, early stopping)
- MLP는 초기에 도입하지 않음 (설명 부담 큼).

### 4.2 학습 절차

1. **분할**: 시간 기반 분할 (train: T-12~T-3개월, valid: T-3~T-1개월, test: T-1~T개월). 랜덤 분할은 시간 리키지로 낙관 편향.
2. **불균형 처리**: 실제 승인률이 60~80%로 심하지 않음. `scale_pos_weight` 조정 대신 threshold 조정 위주.
3. **하이퍼파라미터 탐색**: Optuna, 50 trials, `AUC-PR` 기준 (승인 클래스가 majority이므로 거절 예측력 위주로 보려면 minority focus).
4. **캘리브레이션**: XGBoost 확률은 편향되어 있어 **isotonic regression**으로 후처리. 소량 데이터일 때는 Platt scaling.

### 4.3 캘리브레이션이 왜 중요한가

이 모델의 산출물은 "확률"이라 명시했으므로, `p_approve = 0.7`이면 유사한 신청 100건 중 실제로 70건 승인되어야 합니다. 트리 모델의 raw score는 이 성질을 보장하지 않으므로:

```
raw_score = xgb.predict_proba(x)[:, 1]
p_approve = isotonic_calibrator.transform(raw_score)
```

캘리브레이션 품질은 **Brier score**와 **reliability diagram**으로 검증.

---

## 5. 평가 지표

| 지표 | 용도 | 목표 |
|---|---|---|
| ROC-AUC | 순위 판별력 전반 | ≥ 0.75 |
| PR-AUC | 거절 클래스 판별 | (베이스라인 대비) |
| KS 통계량 | 승인/거절 분포 분리 | ≥ 0.35 |
| Brier score | 확률 정확도 | ≤ 0.18 |
| Calibration ECE | 캘리브레이션 오차 | ≤ 0.03 |
| PSI (population stability) | 배포 후 drift 감시 | < 0.1 (안정), 0.1~0.25 (관찰), ≥0.25 (재학습) |

---

## 6. 임계값 (Cutoff) 설계

산출물이 확률이므로 최종 통과 여부는 별도 정책. 3구간 정책 예시:

- `p ≥ 0.85` → **A/B**: 프리스크리닝 통과, CB 조회 없이 저한도 즉시 발급 가능
- `0.35 ≤ p < 0.85` → **C**: CB 조회로 넘겨 정식 심사
- `p < 0.35` → **D**: 조회 없이 거절 (신청자에게는 "이번엔 어려워요, 3개월 후 재신청" 안내)

임계값은 사업부의 목표 (승인률, 조회비 절감률, 예상 손실률) 3원 방정식으로 잡음. 예:
```
조회 스킵률 = P(p ≥ 0.85) + P(p < 0.35)  (목표: 30~40%)
저한도 즉시발급 손실률 = E[default | p ≥ 0.85]  (목표: < 2%)
```

---

## 7. 리젝트 인퍼런스

과거 심사자가 거절한 신청은 승인 이후 성과(=연체 여부)를 관측할 수 없음.
→ 승인/거절 이진 레이블로 학습하면 "심사자가 좋아하는 신청" 모델이 될 뿐, 리스크 모델이 아님.

**대응**:
1. 초기: 승인/거절 레이블로 학습 → 프리스크리닝 용도로만 사용, "리스크 모델"이라 부르지 않음.
2. 6개월 후: 승인건에서 관측된 연체 레이블로 리스크 모델 학습 + 거절건에 대해 **parceling** 또는 **augmentation** 기법으로 리젝트 인퍼런스.
3. 챔피언/챌린저: 소량 (5%) 트래픽에서 모델 임계값을 완화해서 "원래 거절될 신청"의 성과를 관측 → 편향 보정.

---

## 8. 편향·규제 고려사항

- **성별, 나이, 지역**을 직접 피처로 쓰는 것은 관련 법령/공정성 정책과 충돌 가능. 1차 모델은 나이만 사용, 성별·지역은 제외.
- **간접 차별 (disparate impact)**: 디바이스/행동 피처가 특정 계층의 신청을 체계적으로 불이익 주는지 정기 감사. 그룹별 승인률 갭 모니터링.
- **설명 요건**: 거절 사유를 신청자에게 안내해야 하는 경우, SHAP top-3를 자연어 템플릿에 매핑.

---

## 9. 모니터링

배포 후 매일:

- **입력 drift**: 피처별 PSI, KS
- **출력 drift**: `p_approve` 분포 히스토그램
- **성능 drift**: 매일 승인된 건의 승인률과 예측 확률 평균 비교 (calibration drift)
- **신규 디바이스 비율**: `device_seen_count_90d = 0` 비율 급증하면 어뷰징 신호

트리거:
- PSI ≥ 0.25 → 자동 재학습 후보
- Calibration ECE > 0.05 → 캘리브레이터만 재학습
- ROC-AUC 롤링 4주 평균이 학습 기준 대비 −0.05 이상 하락 → 전면 재학습

---

## 10. 한계와 향후 과제

- **자기신고 피처의 검증 부재**: 연소득, 재직기간이 실제와 다를 수 있음. 급여이체 통장 조회 동의를 유도해서 검증 신호 하나만 얻어도 판별력이 크게 개선됨.
- **콜드스타트 디바이스**: `device_seen_count_90d = 0`인 신청은 판별이 어려움. 초기에는 이런 신청을 자동으로 C 구간으로 보내 CB 조회로 넘김.
- **적대적 신청자**: 브로커가 이 모델의 피처를 알면 우회 가능. 피처 목록은 비공개, 정기적 피처 교체(feature rotation) 필요.
- **레이블 편향 상속**: §1.1의 트레이드오프. 승인/거절 레이블만 쓰는 동안은 프리스크리닝 용도로만 한정.
