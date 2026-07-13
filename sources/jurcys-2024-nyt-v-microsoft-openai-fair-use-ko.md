---
title: "NY Times vs Microsoft & OpenAI: Should it be an 'easy' fair use case to decide? (한글 번역)"
authors: Paulius Jurcys, Mark Fenwick (Korean translation)
year: 2024
doi: SSRN abstract 4685275
category: intellectual-property
pdf_path: /home/user/alexpark/papers/jurcys-2024-nyt-v-microsoft-openai-fair-use-ko.pdf
pdf_filename: jurcys-2024-nyt-v-microsoft-openai-fair-use-ko.pdf
source_collection: google-drive
drive_id: 1ocdN5yA-q5SN5rsJcTojCgoNCX2Vc_Ju
drive_url: https://drive.google.com/file/d/1ocdN5yA-q5SN5rsJcTojCgoNCX2Vc_Ju/view
---

## One-line Summary

2023년 12월 뉴욕타임스가 마이크로소프트/OpenAI를 상대로 제기한 저작권 소송에 대한 초기 사건평석. 6가지 청구원인(직접·대위·기여 저작권 침해, DMCA §1202 저작권관리정보 제거, 부정경쟁, 상표 희석)과 공정이용 항변 예상, 그리고 화해(settlement)를 가장 합리적인 결과로 전망.

## 1. Document Information

- **저자**: Paulius Jurcys LL.M. (Harvard), Mark Fenwick 교수
- **발표일**: 2024년 1월
- **형식**: 사건평석 (Case Comment), 7페이지
- **출처**: SSRN, 초록번호 4685275
- **원어**: 영문 (본 PDF는 한글 번역본)

## 2. Key Contributions

1. **NYT 소장의 6가지 청구원인 상세 표 정리**:
   - 직접 저작권 침해 (훈련데이터 구축·저장·처리, GPT 모델 저장·처리, 생성 출력물 배포)
   - 대위 저작권 침해 (Microsoft의 슈퍼컴퓨팅 인프라 통제)
   - 기여 저작권 침해 (Bing 플러그인, 공동 개발)
   - DMCA §1202 (저작권관리정보 제거)
   - 부정경쟁 (링크 제거로 참조 수익 박탈)
   - 상표 희석 (품질 저하/오정보의 NYT 마크 부여)
2. **손해배상 규모 지적**: US Copyright Act상 단일 침해당 최대 $150,000 법정손해; NYT 기사 수백만 건 복제 → "천문학적" 배상 가능성.
3. **공정이용 항변 예상**: 4요소를 넘어서 정책·지정학 요인까지 다층 분석.
4. **화해가 가장 합리적** 이라는 정책 제언 — 양사의 평판·혁신 리스크 관리 관점.
5. **주요 정책적 관점 5가지**: (1) 데이터 활용 방식 전환, (2) 사업 모델 재검토, (3) 화해 필요성, (4) John Lennon 사고실험(생성 AI로 옛 녹음 복원 → NYT도 자체 LLM 스타일북 구축 가능?), (5) 지정학적 함의(미국의 AI 주도권과 공정이용 확대 논리).

## 3. Methodology and Architecture

법률 사건평석. 공식 소장(69페이지)의 청구원인을 표로 재구성하고, 예상 항변(공정이용)과 정책 논거를 검토. 판결이 아직 없으므로 규범적 분석 중심.

**청구·행위·피고 매트릭스**:

| 청구 | 침해 행위 | 피고 |
|---|---|---|
| 직접 침해 1.1 | 훈련데이터셋에 NYT 저작물 포함 | OpenAI |
| 직접 침해 1.2 | 저장·처리·복제로 GPT 훈련 | OpenAI, Microsoft |
| 직접 침해 1.3 | 훈련된 GPT 모델 저장·처리·복제 | OpenAI, Microsoft |
| 직접 침해 1.4 | ChatGPT 통한 파생 출력물 배포 | OpenAI |
| 직접 침해 1.5 | Bing Chat 통한 파생 출력물 배포 | Microsoft |
| 대위 침해 2.1 | OpenAI 침해 통제/지시/수익 | Microsoft |
| 대위 침해 2.2 | 상호 통제 및 수익 | Both |
| 기여 침해 3.1 | 슈퍼컴퓨팅 인프라 제공 | Microsoft |
| 기여 침해 3.2 | 공동 LLM 개발 | All |
| DMCA §1202 | 저작권관리정보 제거 | All |
| 부정경쟁 | 링크 제거로 참조수익 박탈 | All |
| 상표 희석 | 저품질 컨텐츠에 NYT 마크 오귀속 | All |

## 4. Key Results and Benchmarks

- 논문 발표(2024년 1월) 당시 예측: "쉬운" 공정이용 사건이어야 함 — 그러나 저자들은 화해가 실현 가능성 높다고 예상.
- 2025년 10월 27일 Stein 판사의 판결(별도 위키 페이지)로 각하 신청은 기각되어 소송은 계속됨 → 저자들의 초기 예상과 달리 화해는 아직 이루어지지 않음.

## 5. Limitations and Future Work

- 소송 초기의 사건평석이므로 판단 근거는 소장에 한정.
- 훈련 단계 공정이용과 출력 단계 침해를 별도로 분석하지 않음.
- 실제 판결(Stein Op. 2025)에서 부각된 "실질적 유사성" 논쟁, "더 분별력 있는 관찰자" 테스트 미포함.

## 6. Related Work

- [[intellectual-property/stein-2025-in-re-openai-copyright-litigation]] — 이 소장에 대한 실제 각하 신청 기각 판결(2025).
- Google Books 사건 — 전체 복제에도 공정이용 인정(대비 사례).
- USCO 2023 comment (Sequoia, a16z) — 지정학적 관점의 공정이용 확대 논리.

## 7. Glossary

- **공정이용 (Fair Use)** — 미국 저작권법 §107의 항변; 4요소(목적·성격, 저작물의 성격, 이용된 부분의 양·질, 시장에 미치는 영향)를 종합 판단.
- **DMCA §1202** — Digital Millennium Copyright Act 저작권관리정보(Copyright Management Information) 제거 금지 조항.
- **파생저작물 (derivative work)** — 원저작물에 기초한 2차적 저작물.
- **부정경쟁 (unfair competition by misappropriation)** — 뉴욕주 보통법상 무단 유용.
- **법정 손해배상 (statutory damages)** — 17 U.S.C. §504(c); 단일 침해당 최대 $150,000(고의) / $30,000(일반).
- **LLM 스타일북** — 언론사가 자체 콘텐츠로 훈련한 언어모델(정책 제언).
