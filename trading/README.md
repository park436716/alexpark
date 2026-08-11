# 종가매매 수급분석 프로토타입 → Digital Analyst

`trading/prototype/` — Python으로 짠 종가매매 신호/백테스트/Digital Analyst 스캐폴드.
실 KIS API 데이터 없이 mock 데이터로 전체 파이프라인이 돈다.

> 이 폴더는 CLAUDE.md 의 로스쿨 위키 스키마와 **무관**하다. `sources/`, `wiki/` 는 건드리지 않는다.

---

## 프레임: Patterns & Process

> "This experiment tells me we are getting closer to the promise of the Digital Analyst"
>  — Patterns: 시장에 반복적으로 존재하는 set-up 을 식별하고 forward table-odds 를 매긴다.
>  — Process: Digital Analyst 가 감시 계획대로 massive context 를 실시간 흡수해 inflection/revision 을 (fundamental swarm 보다) 먼저 잡는다.

이 프로토타입은 그 프레임을 종가매매·수급 도메인에 맞춘 최소 구현이다.

- **Patterns 라이브러리** (`patterns.py`): 4개의 셋업. 각 셋업은 `detect()` + 실측 forward odds(승률/손익비/기대값).
- **Digital Analyst** (`analyst.py`): 감시 종목 × Pattern 조합을 매일 돌려서 BUY/WATCH/PASS + 향후 감시 플랜을 뽑음.
- **원시 signal + backtest** (`signals.py`, `backtest.py`): 하드 필터 + 수급 스코어 기반 종가매매 신호 (하나의 셋업에 해당).

---

## 왜 이 구성인가

- **차트만 보는 것보다 거래량+수급이 먼저**: 차트는 오염될 수 있지만 체결 데이터·거래원은 흔적을 남긴다.
- **손익비 기반 승률 게임**: 100% 예측은 없다. 각 셋업의 forward odds(승률·payoff·E) 를 실측으로 관리하면 손실비 × 승률 이 양이면 규모만 조절.
- **LLM 은 스캘핑이 아닌 상위 레이어**: KIS REST 유량(1계좌 1초 18건), WebSocket 41건 제약 때문에 초단타는 룰기반. LLM 은 회색지대 종목(strength 중간대) 에 대해 공시·뉴스·차트를 종합하는 판정자로.

---

## 파이프라인

```
raw OHLCV + 수급 (외인/기관/프로그램/거래원)
        │
        ▼ features.build_features
[ema20/60, vol_ratio, close_pos, pivot S/R,
 foreign_ratio_5d, inst_ratio_5d, prog_nonarb_ratio_5d, broker_imbalance_5d]
        │
        ├──▶ signals.close_entry_signal → backtest        (단일 셋업 파이프)
        │
        └──▶ patterns.PATTERNS.detect + compute_forward_odds
                                 │
                                 ▼ analyst.run_analyst   (Digital Analyst)
                    per-ticker × per-pattern → AnalystNote:
                      matched / strength / forward odds / edge / recommendation / monitoring
```

---

## Patterns 라이브러리

| Pattern | 의미 | window | TP / SL |
|---|---|---|---|
| `accumulation_breakout` | 5일 수급 매집 + 20일 신고가 브레이크아웃 + 거래량 | 5d | +5% / -3% |
| `supply_shock_reversal` | 3일 급락 순매도 후 반전 캔들 + 거래량 | 3d | +4% / -2.5% |
| `broker_stealth_accumulation` | 상위 거래원 편중 + 낮은 변동성 (조용한 매집) | 10d | +8% / -4% |
| `pullback_to_ema20` | 직전 5일 상승 후 EMA20 지지 + 수급 유지 | 3d | +4% / -2% |

각 pattern 은 독립적으로 detect + forward odds 계산이 되도록 설계 — Skills library 처럼 필요한 것만 조합해서 쓴다.

1500일 mock 캘리브레이션 (seed 42) 예시:

```
pattern                                 n       WR   avg_win  avg_loss         E  payoff
------------------------------------------------------------------------------------------
accumulation_breakout                  28    71.4%    +4.33%    -2.78%    +2.30%    1.56
supply_shock_reversal                   1     0.0%    +0.00%    -2.50%    -2.50%    0.00
broker_stealth_accumulation           127    44.9%    +7.03%    -3.50%    +1.23%    2.01
pullback_to_ema20                       7    57.1%    +4.00%    -1.51%    +1.64%    2.65
```

`supply_shock_reversal` n=1 은 mock 데이터 특성 (급락-반전 시나리오가 거의 없음) — 실 데이터로 붙이면 다른 프로파일이 나올 것.

---

## Digital Analyst 실행 예시

```bash
python3 -m trading.prototype.main analyst --days 500 --seed 23 --lookback 500
```

출력:

```
[BUY] CCC  broker_stealth_accumulation
   date=2026-12-02  matched=True  strength=0.65
   odds: n=40  WR=67.5%  avg_win=+6.31%  avg_loss=-3.22%  E=+3.21%  payoff=1.96
   edge_score=0.0209  detail={'broker_5d': 0.161, 'realized_vol_5d': 0.0116}
   → 진입 후 10영업일 내 TP +8.0% / SL -4.0% 첫 터치 청산. 익일 시가 갭 확인 후 재평가.
```

한 노트에 담기는 것: 종목 × 셋업 × 성립여부 × strength × 이 셋업의 실측 forward odds × edge_score × 향후 감시 플랜.

---

## 실행 커맨드 요약

```bash
pip3 install pandas numpy

# 1. 원시 신호 (하드필터 + 수급스코어) 최신봉 조회
python3 -m trading.prototype.main signal --days 60 --threshold 55

# 2. 원시 신호 백테스트
python3 -m trading.prototype.main backtest --days 500 --threshold 45 --hold 3 --sl -0.03 --tp 0.05

# 3. Pattern 라이브러리 캘리브레이션 (셋업별 forward odds)
python3 -m trading.prototype.main patterns --days 1500

# 4. Digital Analyst — 감시 종목 × Pattern 조합 일일 노트
python3 -m trading.prototype.main analyst --days 500 --seed 23 --lookback 500
```

---

## 실 데이터 연결 (다음 단계)

`main._load()` 를 KIS API 어댑터로 교체. 필요한 컬럼:

```
date, open, high, low, close, volume,
foreign_net_val, inst_net_val, retail_net_val,        # 외인/기관/개인 순매수 대금
prog_arb_net_val, prog_nonarb_net_val,                # 프로그램 차익/비차익
top5_buyer_net_val, top5_seller_net_val               # 상위 거래원 순매수/순매도 대금
```

KIS 매핑(개략):
- OHLCV: `국내주식-일봉조회` (FHKST01010400)
- 투자자별: `종목별 외국인 기관 매매종합`, `종목별투자자매매동향`
- 프로그램: `프로그램매매 종합현황`
- 거래원: `주식현재가 회원사`

유량(1계좌 1초 18건) 안에서:
- 종가매매 일일 배치(14:50) → 유량 걱정 거의 없음
- 실시간 감시는 WebSocket(총 41건) 로 종목당 4건 × 최대 ~10종목

---

## 다음 확장 후보

1. **Pattern 추가**: `earnings_gap_setup`, `program_sell_climax`, `sector_rotation_lead`
2. **LLM 판정 레이어**: analyst 가 WATCH 로 분류한 케이스만 LLM 에 넘겨 뉴스/공시/차트 종합 판정
3. **Monitoring Plan 상태화**: 노트에 lifecycle(pending → active → exited) 부여, 매일 갱신
4. **Skills 분리**: 현재 `signals.py` 를 `skills/technical_setup.py`, `skills/supply_demand.py` 로 쪼개 pattern 이 필요한 skill 만 호출
5. **포트폴리오/RMS**: 다종목 동시 신호 처리, 자본 배분, 상관도 클러스터 리스크
6. **거래원 창구 매칭**: 상위5 대신 외국계 창구 지정 트래킹, 단주 프로그램 패턴 카운트
