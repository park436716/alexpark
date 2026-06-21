# 방송국 바이브코딩 워크숍 준비

방송국 직원(경영/마케팅/광고 담당자) 대상 바이브코딩 강의 제안을 위한 준비 자료.
Claude Cowork로 자연어 요청만으로 데이터 분석을 해내는 모습을 보여주는 것이 핵심.

- `proposal-email.md` — 방송국에 보낼 제안/일정·비용 협의 메일 초안
- `curriculum.md` — 오프라인 반나절(3~4시간) 강의 커리큘럼
- `demo/` — 라이브 데이터 분석 데모용 가상 시청률·광고매출 데이터셋과 진행 스크립트
  - `demo/data/viewership_ad_revenue.csv` — 가상 데이터 (2024년 1년치, 1TV/2TV × 6개 시간대)
  - `demo/generate_sample_data.py` — 위 CSV를 만든 생성 스크립트 (재생성/변형 가능)
  - `demo/demo-script.md` — 강의 중 Claude Cowork에 입력할 프롬프트와 예상 결과

## 다음 할 일

- [ ] 일정 후보 확정 (방송국 회신 대기)
- [ ] 강의료 확정 후 `proposal-email.md`의 `[ ]` 부분 채우기
- [ ] 데모 1회 리허설 (`demo/demo-script.md` 순서대로)
- [ ] 참가자 인원/직군 최종 확인 후 커리큘럼 미세 조정
