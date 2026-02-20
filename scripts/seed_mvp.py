import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import engine

SEED_SQL = [
    """
    INSERT INTO locations (id, latitude, longitude, admin_dong, legal_dong, address, point)
    VALUES
      (1, 37.4869890, 127.1014030, '정자동', '정자동', '경기도 성남시 분당구 정자동', ST_GeogFromText('POINT(127.1014030 37.4869890)')),
      (2, 37.4981120, 127.0276210, '역삼동', '역삼동', '서울특별시 강남구 역삼동', ST_GeogFromText('POINT(127.0276210 37.4981120)')),
      (3, 37.5134110, 127.1051120, '잠실동', '잠실동', '서울특별시 송파구 잠실동', ST_GeogFromText('POINT(127.1051120 37.5134110)')),
      (4, 37.5216610, 126.9241250, '여의도동', '여의도동', '서울특별시 영등포구 여의도동', ST_GeogFromText('POINT(126.9241250 37.5216610)')),
      (5, 37.5669020, 126.9786520, '서소문동', '서소문동', '서울특별시 중구 서소문동', ST_GeogFromText('POINT(126.9786520 37.5669020)')),
      (6, 37.5490420, 126.9138270, '합정동', '합정동', '서울특별시 마포구 합정동', ST_GeogFromText('POINT(126.9138270 37.5490420)'))
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO complexes (id, location_id, name, address, built_year, household_count, centroid_latitude, centroid_longitude)
    VALUES
      (101, 1, '분당 샘플자이', '경기도 성남시 분당구 정자동 100', 2012, 1240, 37.4875000, 127.1022000),
      (102, 2, '강남 샘플래미안', '서울특별시 강남구 역삼동 200', 2015, 980, 37.4983000, 127.0280000),
      (103, 3, '잠실 샘플엘스', '서울특별시 송파구 잠실동 300', 2008, 1567, 37.5139000, 127.1049000),
      (104, 4, '여의도 샘플파크', '서울특별시 영등포구 여의도동 40', 2019, 620, 37.5220000, 126.9249000),
      (105, 5, '시청 샘플센트럴', '서울특별시 중구 서소문동 80', 2021, 430, 37.5671000, 126.9791000),
      (106, 6, '합정 샘플하우스', '서울특별시 마포구 합정동 20', 2017, 710, 37.5494000, 126.9141000)
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO unit_types (id, complex_id, exclusive_area_m2, supply_area_m2, type_code, room_count, bathroom_count, structure_keyword)
    VALUES
      (1001, 101, 59.95, 82.10, 'A', 3, 2, '판상형'),
      (1002, 101, 84.99, 112.40, 'B', 4, 2, '타워형'),
      (1003, 102, 58.20, 79.40, 'A', 3, 2, '판상형'),
      (1004, 102, 74.60, 98.10, 'B', 3, 2, '타워형'),
      (1005, 103, 84.20, 110.30, 'A', 4, 2, '판상형'),
      (1006, 103, 101.80, 132.70, 'P', 4, 2, '판상형'),
      (1007, 104, 59.10, 81.20, 'C', 3, 2, '복도형'),
      (1008, 104, 84.30, 109.40, 'D', 4, 2, '타워형'),
      (1009, 105, 42.80, 61.10, 'S', 2, 1, '원룸형'),
      (1010, 106, 72.10, 95.00, 'M', 3, 2, '판상형')
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO vendors (id, name, region, rating, contact_url)
    VALUES
      (501, '샘플 인테리어', '분당', 4.7, 'https://example.com/vendors/501'),
      (502, '어반 리모델링', '강남', 4.6, 'https://example.com/vendors/502'),
      (503, '레이크하우스 디자인', '송파', 4.8, 'https://example.com/vendors/503')
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO portfolios (
      id, complex_id, unit_type_id, vendor_id, title, before_image_url, after_image_url,
      work_scope, style, budget_min_krw, budget_max_krw, duration_days, tags, summary, status, published_at
    ) VALUES
      (9001, 101, 1001, 501, '59A 미니멀 화이트 리모델링', 'https://cdn.example.com/9001-before.jpg', 'https://cdn.example.com/9001-after.jpg',
       'full_remodeling', 'minimal', 35000000, 45000000, 28, '화이트,간접조명,수납', '주방 동선과 수납을 확장한 전체 리모델링', 'published', NOW()),
      (9002, 101, 1002, 501, '84B 우드톤 욕실/주방 개선', 'https://cdn.example.com/9002-before.jpg', 'https://cdn.example.com/9002-after.jpg',
       'partial', 'wood', 18000000, 26000000, 18, '우드톤,아일랜드,욕실', '주방+욕실 중심 부분 공사', 'published', NOW()),
      (9003, 102, 1003, 502, '58A 웜그레이 신혼집 리뉴얼', 'https://cdn.example.com/9003-before.jpg', 'https://cdn.example.com/9003-after.jpg',
       'partial', 'modern', 22000000, 30000000, 21, '웜그레이,펜던트,신혼', '거실/주방 중심의 감도 높은 부분 리뉴얼', 'published', NOW()),
      (9004, 102, 1004, 502, '74B 수납강화 패밀리 하우스', 'https://cdn.example.com/9004-before.jpg', 'https://cdn.example.com/9004-after.jpg',
       'full_remodeling', 'natural', 42000000, 52000000, 30, '수납강화,원목,패밀리', '복도 팬트리와 붙박이장 확장 중심의 전체 공사', 'published', NOW()),
      (9005, 103, 1005, 503, '84A 호텔라이크 마스터존', 'https://cdn.example.com/9005-before.jpg', 'https://cdn.example.com/9005-after.jpg',
       'full_remodeling', 'luxury', 50000000, 65000000, 35, '호텔라이크,간접조명,대리석', '침실/드레스룸/욕실을 통합한 프리미엄 리모델링', 'published', NOW()),
      (9006, 103, 1006, 503, '101P 홈오피스 맞춤 설계', 'https://cdn.example.com/9006-before.jpg', 'https://cdn.example.com/9006-after.jpg',
       'partial', 'minimal', 26000000, 36000000, 24, '홈오피스,미니멀,방음', '대형 평형의 서재/업무공간 최적화 공사', 'published', NOW()),
      (9007, 104, 1007, 501, '59C 소형평형 공간확장', 'https://cdn.example.com/9007-before.jpg', 'https://cdn.example.com/9007-after.jpg',
       'partial', 'scandinavian', 17000000, 24000000, 16, '북유럽,확장,화이트오크', '동선 재배치로 체감 면적을 키운 소형평형 공사', 'published', NOW()),
      (9008, 104, 1008, 502, '84D 키친 중심 리디자인', 'https://cdn.example.com/9008-before.jpg', 'https://cdn.example.com/9008-after.jpg',
       'kitchen', 'modern', 14000000, 22000000, 14, '키친,아일랜드,수납', '주방 동선/수납/조명을 집중 개선', 'published', NOW()),
      (9009, 105, 1009, 503, '42S 도심형 컴팩트 리모델링', 'https://cdn.example.com/9009-before.jpg', 'https://cdn.example.com/9009-after.jpg',
       'partial', 'minimal', 12000000, 18000000, 12, '컴팩트,모듈가구,수납', '소형 주거의 공간 활용 극대화', 'published', NOW()),
      (9010, 106, 1010, 501, '72M 아이방 확장형 리뉴얼', 'https://cdn.example.com/9010-before.jpg', 'https://cdn.example.com/9010-after.jpg',
       'bathroom', 'natural', 19000000, 28000000, 17, '아이방,욕실,원목', '아이방과 욕실 동선 개선 중심의 패밀리 리뉴얼', 'published', NOW())
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO floor_plan_pins (id, portfolio_id, x_ratio, y_ratio, title, sort_order)
    VALUES
      (91001, 9001, 42.5, 36.0, '거실 포인트', 1),
      (91002, 9001, 58.0, 47.0, '주방 포인트', 2),
      (91003, 9002, 39.0, 34.0, '욕실 포인트', 1),
      (91004, 9002, 63.5, 52.0, '현관 포인트', 2),
      (91005, 9003, 44.0, 38.0, '주방 포인트', 1),
      (91006, 9003, 67.0, 55.0, '침실 포인트', 2)
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO floor_plan_pin_images (id, floor_plan_pin_id, image_side, image_url, sort_order)
    VALUES
      (92001, 91001, 'before', 'https://cdn.example.com/9001-pin1-before-1.jpg', 1),
      (92002, 91001, 'before', 'https://cdn.example.com/9001-pin1-before-2.jpg', 2),
      (92003, 91001, 'after', 'https://cdn.example.com/9001-pin1-after-1.jpg', 1),
      (92004, 91001, 'after', 'https://cdn.example.com/9001-pin1-after-2.jpg', 2),
      (92005, 91002, 'before', 'https://cdn.example.com/9001-pin2-before-1.jpg', 1),
      (92006, 91002, 'after', 'https://cdn.example.com/9001-pin2-after-1.jpg', 1),
      (92007, 91003, 'before', 'https://cdn.example.com/9002-pin1-before-1.jpg', 1),
      (92008, 91003, 'after', 'https://cdn.example.com/9002-pin1-after-1.jpg', 1),
      (92009, 91004, 'before', 'https://cdn.example.com/9002-pin2-before-1.jpg', 1),
      (92010, 91004, 'after', 'https://cdn.example.com/9002-pin2-after-1.jpg', 1),
      (92011, 91005, 'before', 'https://cdn.example.com/9003-pin1-before-1.jpg', 1),
      (92012, 91005, 'after', 'https://cdn.example.com/9003-pin1-after-1.jpg', 1),
      (92013, 91006, 'before', 'https://cdn.example.com/9003-pin2-before-1.jpg', 1),
      (92014, 91006, 'after', 'https://cdn.example.com/9003-pin2-after-1.jpg', 1)
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO blog_posts (
      id, vendor_id, title, slug, excerpt, content, status, published_at
    ) VALUES
      (7001, 501, '59A 리모델링 동선 설계 포인트', 'flow-guide-59a',
       '좁은 주방에서 수납과 동선을 동시에 확보한 설계 사례입니다.',
       '공간별 동선 분석, 조명 계획, 수납 위치를 단계별로 정리했습니다.',
       'published', NOW())
    ON CONFLICT DO NOTHING
    """,
]


def seed() -> None:
    with engine.begin() as conn:
        for stmt in SEED_SQL:
            conn.execute(text(stmt))


if __name__ == "__main__":
    seed()
