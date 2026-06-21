"""Generate a synthetic broadcast viewership/ad-revenue dataset for the
vibe-coding data analysis demo. Pure stdlib so it runs anywhere.

Run: python3 generate_sample_data.py
Output: data/viewership_ad_revenue.csv
"""
import csv
import random
from datetime import date, timedelta

random.seed(42)

OUT_PATH = "data/viewership_ad_revenue.csv"

CHANNELS = ["1TV", "2TV"]

TIME_SLOTS = [
    # (slot_label, start_hour, base_rating, base_slots, base_price_krw)
    ("06:00-09:00", 6, 2.5, 6, 3_000_000),
    ("09:00-12:00", 9, 1.8, 6, 2_200_000),
    ("12:00-15:00", 12, 2.0, 5, 2_500_000),
    ("15:00-18:00", 15, 2.2, 5, 2_800_000),
    ("18:00-21:00", 18, 6.0, 8, 9_000_000),
    ("21:00-24:00", 21, 5.0, 7, 7_500_000),
]

WEEKDAY_PROGRAMS = {
    "06:00-09:00": ("뉴스", "굿모닝 코리아"),
    "09:00-12:00": ("시사교양", "정보가 산다"),
    "12:00-15:00": ("드라마", "오후의 드라마(재방)"),
    "15:00-18:00": ("생활정보", "생활의 발견"),
    "18:00-21:00": ("뉴스", "메인뉴스 9"),
    "21:00-24:00": ("드라마", "월화수목 드라마"),
}

WEEKEND_PROGRAMS = {
    "06:00-09:00": ("뉴스", "주말 아침뉴스"),
    "09:00-12:00": ("다큐멘터리", "세상 이야기"),
    "12:00-15:00": ("스포츠", "주말 스포츠 중계"),
    "15:00-18:00": ("예능", "주말 예능 스페셜"),
    "18:00-21:00": ("예능", "주말 버라이어티"),
    "21:00-24:00": ("영화", "주말 특선영화"),
}

GENRE_DEMO = {
    "뉴스": "전체가구",
    "시사교양": "40대 이상",
    "드라마": "30-40대",
    "생활정보": "30-40대",
    "다큐멘터리": "40대 이상",
    "스포츠": "전체가구",
    "예능": "20-30대",
    "영화": "20-30대",
}

# A handful of "event" dates with a big rating spike on 1TV prime time,
# e.g. a drama finale or a national-team match - good outlier-detection material.
SPECIAL_EVENTS = {
    date(2024, 2, 7): "18:00-21:00",   # 설 특집
    date(2024, 3, 26): "21:00-24:00",  # 드라마 시즌 파이널
    date(2024, 6, 15): "18:00-21:00",  # 국가대표 경기 중계
    date(2024, 8, 11): "21:00-24:00",  # 올림픽 결승 중계
    date(2024, 9, 28): "21:00-24:00",  # 추석 특집극
    date(2024, 12, 24): "18:00-21:00", # 연말 특집
}

START = date(2024, 1, 1)
END = date(2024, 12, 31)

rows = []
day = START
while day <= END:
    is_weekend = day.weekday() >= 5  # 5=Sat, 6=Sun
    programs = WEEKEND_PROGRAMS if is_weekend else WEEKDAY_PROGRAMS

    # Slow year-long erosion trend for 1TV (linear-TV-losing-to-OTT narrative),
    # and a mild seasonal dip in summer (Jul-Aug) when people are out more.
    day_index = (day - START).days
    year_trend = 1.0 - 0.15 * (day_index / 365)  # -15% by year end
    season_dip = 0.85 if day.month in (7, 8) else 1.0

    for slot_label, _, base_rating, base_slots, base_price in TIME_SLOTS:
        genre, program_name = programs[slot_label]
        target_demo = GENRE_DEMO[genre]

        for channel in CHANNELS:
            channel_mult = 1.0 if channel == "1TV" else 0.65

            rating = base_rating * channel_mult * season_dip
            if channel == "1TV":
                rating *= year_trend
            rating *= random.uniform(0.85, 1.15)

            is_event = (
                channel == "1TV"
                and SPECIAL_EVENTS.get(day) == slot_label
            )
            if is_event:
                rating *= random.uniform(2.0, 2.8)

            rating = round(max(rating, 0.1), 2)

            sns_buzz = rating * random.uniform(80, 140)
            if is_event:
                sns_buzz *= random.uniform(2.5, 4.0)
            sns_buzz = round(sns_buzz)

            slot_count = base_slots + random.randint(-1, 1)
            slot_count = max(slot_count, 1)

            price_per_slot = base_price * channel_mult * (
                1 + (rating - base_rating * channel_mult) / max(base_rating, 0.1) * 0.3
            )
            price_per_slot = max(round(price_per_slot / 10000) * 10000, 500_000)

            ad_revenue = slot_count * price_per_slot
            # ~5% of rows get a small discount/exception so the numbers
            # aren't a perfectly clean slot_count * price formula.
            if random.random() < 0.05:
                ad_revenue = round(ad_revenue * random.uniform(0.85, 0.97))

            rows.append([
                day.isoformat(),
                day.strftime("%a"),
                int(is_weekend),
                channel,
                slot_label,
                genre,
                program_name,
                target_demo,
                rating,
                sns_buzz,
                slot_count,
                int(price_per_slot),
                int(ad_revenue),
            ])

    day += timedelta(days=1)

header = [
    "date", "weekday", "is_weekend", "channel", "time_slot",
    "program_genre", "program_name", "target_demo",
    "viewership_rating", "sns_buzz_index",
    "ad_slot_count", "ad_price_per_slot_krw", "ad_revenue_krw",
]

with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {OUT_PATH}")
