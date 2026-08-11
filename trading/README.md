# 종가매매 수급분석 프로토타입

`trading/prototype/` — Python으로 짠 최소 실행 가능한 종가매매 신호/백테스트 스캐폴드.
실 KIS API 데이터 없이도 mock 데이터로 파이프라인 전체가 돈다.

> 이 폴더는 CLAUDE.md 의 로스쿨 위키 스키마와 **무관**하다. `sources/`, `wiki/` 는 건드리지 않는다.

---

## 왜 이 구성인가

- **차트만 보는 것보다 거래량+수급이 먼저**: 차트는 오염될 수 있지만 체결 데이터·거래원은 흔적을 남긴다.
- **손익비 기반 승률 게임**: 100% 예측은 없다. 승률 50% + 손익비 1.5~2 면 양의 기대값. 프로토타입 백테스트가 이 구조를 그대로 보여준다.
- **LLM 은 스캘핑이 아니라 상위 레이어**: KIS REST 유량(1계좌 1초 18건), WebSocket 41건 제약으로 초단타는 여전히 룰기반. LLM 은 종가 결정, RMS, 종목 선정, 대응 전략처럼 5~10분 추론 여유가 있는 층에.
- 그래서 이 프로토타입은 **하드 필터(룰) → 수급 스코어(정량) → 진입/청산**의 3단 파이프라인이다. LLM 은 이 위에 얹는다 (예: score 55~70 회색지대 종목에 한해 뉴스/공시/차트 종합 판단).

---

## 파이프라인

```
raw OHLCV + 수급 (외인/기관/프로그램/거래원)
        │
        ▼ features.build_features
[ema20/60, vol_ratio, close_pos, pivot S/R,
 foreign_ratio_5d, inst_ratio_5d, prog_nonarb_ratio_5d, broker_imbalance_5d]
        │
        ▼ signals.close_entry_signal  (하드 필터 + 스코어 컷오프)
enter? / score 0~100 / rejections
        │
        ▼ backtest.run_backtest       (종가 진입 → 익일 이후 SL/TP/time)
trades / win_rate / payoff / expectancy / MDD
```

### 진입 하드 필터 (모두 통과해야 후보)

| 조건 | 기본값 | 이유 |
|---|---|---|
| 종가 ≥ EMA20 × 0.98 | | 추세선 위/근처만 |
| 종가 ≤ EMA20 × 1.08 | | 과열 방지 |
| vol_ratio ≥ 1.5x | 20일 평균 대비 | 장대양봉+거래량 |
| close_pos ≥ 0.65 | 당일 range 상위 35% | 종가 강도 |
| 저항 gap ≥ -2% | 브레이크아웃까지 허용 | 전고점 돌파 시나리오 우대 |

### 수급 스코어 (0~100)

5일 누적 순매수 대금 ÷ 거래대금 을 정규화한 뒤 가중합:

- 외인 25 / 기관 25 / 프로그램 비차익 15 / 상위5 거래원 순매수 편중 15
- 종가 위치(브레이크아웃 보너스 포함) 10 / 거래량 10

기본 컷오프 55. 필터 통과 + 스코어 ≥ 55 → 매수.

### 청산

익일부터 매 봉의 high/low 를 확인해 SL(-3%) 또는 TP(+5%) 우선. 미도달이면 max_hold(3영업일) 종가에 청산.

---

## 실행

```bash
pip3 install pandas numpy

# 최신봉 신호 조회
python3 -m trading.prototype.main signal --days 60 --threshold 55

# 백테스트 (500 영업일 mock)
python3 -m trading.prototype.main backtest --days 500 --threshold 55 --hold 3 --sl -0.03 --tp 0.05
```

500일 mock, threshold 45 기준 참고 결과:
```
trades                 8
win_rate               0.5
payoff_ratio           1.87
expectancy_per_trade   +1.17%
total_return           +9.1%
max_drawdown           -3.0%
```

승률 50% 인데 손익비 1.87 로 양의 기대값 — 종가매매의 이상적인 프로파일.

---

## 실 데이터 연결 (다음 단계)

`main._load()` 를 KIS API 어댑터로 교체. 필요한 컬럼은 아래.

```
date, open, high, low, close, volume,
foreign_net_val, inst_net_val, retail_net_val,        # 외인/기관/개인 순매수 대금
prog_arb_net_val, prog_nonarb_net_val,                # 프로그램 차익/비차익
top5_buyer_net_val, top5_seller_net_val               # 상위 거래원 순매수/순매도 대금
```

KIS 매핑 (개략):
- OHLCV: `국내주식-일봉조회` (FHKST01010400)
- 투자자별 매매동향: `종목별 외국인 기관 매매종합`, `종목별투자자매매동향`
- 프로그램 매매: `프로그램매매 종합현황`
- 거래원: `주식현재가 회원사`

유량(1계좌 1초 18건) 안에서 종목 순회하려면:
- 종가매매 판단은 하루 1회(14:50) 배치 → 유량 걱정 거의 없음
- 실시간이 필요하면 WebSocket (실시간체결+호가 등록 총 41건 상한) 로 종목당 4건 × 10종목 정도

---

## 다음 확장 후보

1. **거래원 실제 식별**: 상위5 대신 특정 창구(외국계 회원사, 자기매매) 지정 매칭
2. **단주 프로그램 매매 탐지**: 체결 tick 에서 1주 단위 반복 매매 패턴 카운트
3. **LLM 판정 레이어**: score 55~70 회색지대 종목에 한해 공시/뉴스/차트 종합 판단
4. **포트폴리오 백테스트**: 다종목 동시 신호 + 자본 배분 룰
5. **RMS**: 일일 손실 한도, 종목당 비중 상한, 상관도 기반 클러스터 리스크
