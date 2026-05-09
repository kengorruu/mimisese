# -*- coding: utf-8 -*-
"""
미세먼지 경보 발령 현황 데이터 수집 스크립트
공공데이터포털 API (한국환경공단_에어코리아)를 활용하여
미세먼지/초미세먼지 경보 데이터를 수집하고 JSON 파일로 저장합니다.

사용법:
1. 공공데이터포털(data.go.kr)에서 API 인증키를 발급받습니다.
2. 아래 SERVICE_KEY 변수에 발급받은 인증키(Decoding)를 입력합니다.
3. 터미널에서 실행: python fetch_data.py
4. 실행 결과로 data.json 파일이 생성됩니다.
"""

import requests
import json
import sys
from urllib.parse import quote_plus

# ============================================================
# ★ 여기에 공공데이터포털에서 발급받은 인증키를 입력하세요 ★
SERVICE_KEY = "3b319f0f81c122e74ac5c3043cfb941639aabcdad152bba6932f0e5c30fe12c6"
# ============================================================

# API 기본 정보
BASE_URL = "http://apis.data.go.kr/B552584/UlfptcaAlarmInqireSvc/getUlfptcaAlarmInfo"

def fetch_alarm_data(year, item_code=None):
    """
    미세먼지 경보 발령 현황 데이터를 API에서 가져옵니다.
    
    Parameters:
        year (str): 조회 연도 (예: '2024')
        item_code (str, optional): 항목 코드 ('PM10' 또는 'PM25', None이면 전체)
    
    Returns:
        list: 경보 발령 데이터 목록
    """
    params = {
        "serviceKey": SERVICE_KEY,
        "returnType": "json",
        "numOfRows": "500",
        "pageNo": "1",
        "year": year,
    }
    
    if item_code:
        params["itemCode"] = item_code
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 응답 구조 확인
        if "response" in data:
            header = data["response"]["header"]
            if header["resultCode"] == "00":
                body = data["response"]["body"]
                total_count = body.get("totalCount", 0)
                print(f"  → {year}년 데이터: 총 {total_count}건 조회 성공")
                
                if total_count == 0:
                    return []
                
                items = body.get("items", [])
                
                # items가 리스트가 아닌 경우 처리
                if isinstance(items, dict):
                    items = [items]
                
                # 페이징 처리 (500건 이상인 경우)
                all_items = list(items)
                total_pages = (total_count // 500) + (1 if total_count % 500 != 0 else 0)
                
                for page in range(2, total_pages + 1):
                    params["pageNo"] = str(page)
                    resp = requests.get(BASE_URL, params=params, timeout=10)
                    resp.raise_for_status()
                    page_data = resp.json()
                    page_items = page_data["response"]["body"].get("items", [])
                    if isinstance(page_items, dict):
                        page_items = [page_items]
                    all_items.extend(page_items)
                    print(f"    페이지 {page}/{total_pages} 로드 완료")
                
                return all_items
            else:
                print(f"  → API 오류: {header['resultCode']} - {header['resultMsg']}")
                return []
        else:
            print(f"  → 응답 형식 오류")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"  → 네트워크 오류: {e}")
        return []
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  → 데이터 파싱 오류: {e}")
        return []


def main():
    """
    여러 연도의 데이터를 수집하여 data.json으로 저장합니다.
    """
    if SERVICE_KEY == "여기에_인증키_입력":
        print("=" * 60)
        print("⚠️  인증키를 먼저 설정해주세요!")
        print("fetch_data.py 파일을 열어 SERVICE_KEY 변수에")
        print("공공데이터포털에서 발급받은 인증키를 입력하세요.")
        print("=" * 60)
        
        # 인증키가 없으면 샘플 데이터 생성
        print("\n📋 샘플 데이터로 data.json을 생성합니다...")
        sample_data = generate_sample_data()
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        print(f"✅ data.json 생성 완료 (샘플 데이터 {len(sample_data)}건)")
        return
    
    print("=" * 60)
    print("🌫️  미세먼지 경보 발령 현황 데이터 수집 시작")
    print("=" * 60)
    
    # 수집할 연도 설정 (최근 3년)
    years = ["2024", "2025", "2026"]
    all_data = []
    
    for year in years:
        print(f"\n📅 {year}년 데이터 수집 중...")
        items = fetch_alarm_data(year)
        all_data.extend(items)
    
    if not all_data:
        print("\n⚠️  수집된 데이터가 없습니다. 샘플 데이터를 생성합니다.")
        all_data = generate_sample_data()
    
    # JSON 파일로 저장
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"✅ 데이터 수집 완료!")
    print(f"   총 {len(all_data)}건의 경보 데이터가 data.json에 저장되었습니다.")
    print(f"{'=' * 60}")


def generate_sample_data():
    """
    API 키가 없거나 데이터가 없을 때 사용할 샘플 데이터를 생성합니다.
    실제 데이터 구조와 동일한 형식으로 만듭니다.
    """
    import random
    
    regions = [
        ("서울", ["도심권", "동북권", "서북권", "서남권", "동남권"]),
        ("경기", ["북부권", "남부권", "동부권", "서부권"]),
        ("인천", ["시내권", "서부권", "남부권"]),
        ("부산", ["시내권", "서부권", "동부권"]),
        ("대구", ["시내권", "북부권"]),
        ("광주", ["시내권", "남부권"]),
        ("대전", ["시내권", "서부권"]),
        ("울산", ["시내권", "남부권"]),
        ("세종", ["시내권"]),
        ("강원", ["영서권", "영동권"]),
        ("충북", ["북부권", "남부권"]),
        ("충남", ["북부권", "남부권"]),
        ("전북", ["북부권", "남부권"]),
        ("전남", ["동부권", "서부권"]),
        ("경북", ["북부권", "남부권"]),
        ("경남", ["서부권", "동부권"]),
        ("제주", ["시내권"]),
    ]
    
    sample = []
    sn = 1
    
    for year in [2024, 2025, 2026]:
        # 각 연도별 경보 횟수 (봄철에 집중)
        months_weights = {1: 2, 2: 3, 3: 8, 4: 6, 5: 4, 6: 2, 7: 1, 8: 1, 9: 1, 10: 3, 11: 4, 12: 3}
        
        for month, weight in months_weights.items():
            if year == 2026 and month > 5:
                continue
            
            num_events = random.randint(0, weight)
            
            for _ in range(num_events):
                region, areas = random.choice(regions)
                area = random.choice(areas)
                item = random.choice(["PM10", "PM25"])
                level = random.choices(["주의보", "경보"], weights=[85, 15])[0]
                
                day = random.randint(1, 28)
                issue_hour = random.randint(6, 18)
                clear_hour = min(issue_hour + random.randint(2, 8), 23)
                
                if level == "주의보":
                    issue_val = random.randint(75, 150) if item == "PM10" else random.randint(36, 75)
                else:
                    issue_val = random.randint(150, 300) if item == "PM10" else random.randint(75, 150)
                
                clear_val = random.randint(20, 60) if item == "PM10" else random.randint(10, 30)
                
                date_str = f"{year}-{month:02d}-{day:02d}"
                
                sample.append({
                    "sn": str(sn),
                    "dataDate": date_str,
                    "districtName": region,
                    "moveName": area,
                    "itemCode": item,
                    "issueGbn": level,
                    "issueDate": date_str,
                    "issueTime": f"{issue_hour:02d}:00",
                    "issueVal": str(issue_val),
                    "clearDate": date_str,
                    "clearTime": f"{clear_hour:02d}:00",
                    "clearVal": str(clear_val),
                })
                sn += 1
    
    return sample


if __name__ == "__main__":
    main()
