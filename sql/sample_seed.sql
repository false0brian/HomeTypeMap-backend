INSERT INTO locations (id, latitude, longitude, admin_dong, legal_dong, address, point)
VALUES
  (1, 37.4869890, 127.1014030, '정자동', '정자동', '경기도 성남시 분당구 정자동', ST_GeogFromText('POINT(127.1014030 37.4869890)'))
ON CONFLICT DO NOTHING;

INSERT INTO complexes (id, location_id, name, address, built_year, household_count, centroid_latitude, centroid_longitude)
VALUES
  (101, 1, '분당 샘플자이', '경기도 성남시 분당구 정자동 100', 2012, 1240, 37.4875000, 127.1022000)
ON CONFLICT DO NOTHING;

INSERT INTO unit_types (id, complex_id, exclusive_area_m2, supply_area_m2, type_code, room_count, bathroom_count, structure_keyword)
VALUES
  (1001, 101, 59.95, 82.10, 'A', 3, 2, '판상형'),
  (1002, 101, 84.99, 112.40, 'B', 4, 2, '타워형')
ON CONFLICT DO NOTHING;

INSERT INTO vendors (id, name, region, rating, contact_url)
VALUES
  (501, '샘플 인테리어', '분당', 4.7, 'https://example.com/vendors/501')
ON CONFLICT DO NOTHING;

INSERT INTO portfolios (
  id, complex_id, unit_type_id, vendor_id, title, before_image_url, after_image_url,
  work_scope, style, budget_min_krw, budget_max_krw, duration_days, tags, summary
) VALUES
  (9001, 101, 1001, 501, '59A 미니멀 화이트 리모델링', 'https://cdn.example.com/9001-before.jpg', 'https://cdn.example.com/9001-after.jpg',
   'full_remodeling', 'minimal', 35000000, 45000000, 28, '화이트,간접조명,수납', '주방 동선과 수납을 확장한 전체 리모델링'),
  (9002, 101, 1002, 501, '84B 우드톤 욕실/주방 개선', 'https://cdn.example.com/9002-before.jpg', 'https://cdn.example.com/9002-after.jpg',
   'partial', 'wood', 18000000, 26000000, 18, '우드톤,아일랜드,욕실', '주방+욕실 중심 부분 공사')
ON CONFLICT DO NOTHING;
