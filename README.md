# Credit Card Simple Approval Model (CB 조회 없이)

신용평가사(CB) 조회 없이 **신청서 정보**와 **디바이스/행동 데이터**만으로
신용카드 심사 통과 확률을 산출하는 간이 심사 모델의 설계 문서와 프로토타입.

- 산출물: `p_approve ∈ [0, 1]` — 심사 통과 확률 (캘리브레이션 완료)
- 부가 산출물: `risk_band ∈ {A, B, C, D}`, `top_reasons: List[str]`

## 폴더 구조

```
credit-card-approval/
├── README.md                   # 이 문서
├── requirements.txt
├── docs/
│   └── design.md               # 상세 설계 문서 (한국어)
├── src/
│   ├── schema.py               # 피처 스키마 (Pydantic)
│   ├── data.py                 # 합성 학습 데이터 생성
│   ├── features.py             # 피처 엔지니어링 파이프라인
│   ├── model.py                # 학습 (LR 베이스라인 + XGBoost + 캘리브레이션)
│   ├── evaluate.py             # 평가 지표 (AUC, KS, Brier, PSI)
│   └── inference.py            # 추론 API (확률 + 사유)
├── tests/
│   └── test_pipeline.py
└── train.py                    # end-to-end 학습 스크립트
```

## 빠른 실행

```bash
pip install -r requirements.txt
python train.py                 # 합성 데이터 → 학습 → artifacts/model.pkl 저장
python -m src.inference sample  # 샘플 신청서 1건 확률 출력
```

## 핵심 아이디어

CB 조회 없이 판별력을 확보하는 3가지 축:

1. **신청서 정보** — 나이, 직업군, 연소득, 재직기간, 주거형태, 요청한도 등
   신청자가 직접 입력. 자기신고 기반이라 검증 필요.
2. **디바이스 지문** — OS, 브라우저, 화면 해상도, 타임존, 언어, IP-지역 일치도
   과거 사기신청과의 유사도 판정에 강함.
3. **행동 시그널** — 입력 소요시간, 붙여넣기 비율, 필드 재수정 횟수, 신청 시간대,
   자동완성 사용 여부. 정상 신청자와 브로커/봇을 구분.

이 세 축은 상관관계가 낮아 결합했을 때 판별력이 크게 오릅니다. 자세한 내용은
[docs/design.md](docs/design.md) 참고.
