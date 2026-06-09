# -*- coding: utf-8 -*-
"""
인천 세븐 마사지 — 인천 출장마사지·홈타이 static site generator.

One-time generator that emits PURE static HTML (inline CSS/JS, zero runtime
dependencies). The published site needs no build step or framework; this script
only exists to keep the shared header/footer/SEO blocks consistent across pages.

Run:  python3 tools/build.py
Output: HTML files + sitemap.xml + robots.txt + site.webmanifest + _redirects
        at repo root.

설계 원칙(BLUEPRINT.md):
  순수 HTML + 인라인 CSS/JS + Python 단일 생성기 + 전용 페이지 링크아웃
  → 도어웨이 회피 / 키워드 반복 방지 / E-E-A-T / 빠른 LCP.
"""

import os
import json
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 얇은 콘텐츠/도어웨이 방지: 본문 글자수 임계값(미만이면 Noindex)
THIN_THRESHOLD = 2000
THIN_PAGES = []

# ---------------------------------------------------------------------------
# Brand / business constants  (replace placeholders before going live)
# ---------------------------------------------------------------------------
BASE_URL   = "https://incheon-massage.pages.dev"   # 메인 도메인 (Cloudflare Pages)
BRAND      = "인천 세븐 마사지"                       # 상호
BRAND_KW   = "인천 출장마사지"                        # 핵심 키워드
BRAND_MARK = "7"                                    # 브랜드 로고 글자
PHONE_DISP = "0508-202-4743"                        # 예약번호
PHONE_TEL  = "+825082024743"                        # tel: 링크용
HOURS      = "연중무휴 · 24시간 상담"
INDEXNOW_KEY = "a7c41e9b8d2f4a6e9c3b5d7f1a2e4c68"   # IndexNow(빙·네이버 등) 인증 키
NAVER_VERIFY = "1fdea23ba21b6683e5c9c98e6591f844bc7220b3"  # 네이버 서치어드바이저 사이트 소유확인(메인만)
GOOGLE_VERIFY = ""                                  # (선택) 구글 서치콘솔 소유확인 코드
UPDATED    = "2026-06-09"

COMPANY = {
    "name": "인천 세븐 마사지",
    "ceo": "홍길동",                     # TODO 실제 대표자명
    "biz_no": "000-00-00000",            # TODO 사업자등록번호
    "addr": "인천광역시",
    "sales_no": "2026-인천-0000",        # TODO 통신판매업신고번호
    "privacy_officer": "홍길동",         # TODO 개인정보보호책임자
}

# ===========================================================================
# DATA MODEL — 지역(구·군 → 대표 동)
# 1동·2동·3동 등 숫자 행정동은 대표 동 1개로 통합(도어웨이 회피).
# 각 동의 character/landmarks/arrival 이 페이지 고유성을 만든다.
# ===========================================================================
AREAS = [
    {"slug": "ganghwa-gun", "name": "강화군", "kind": "군",
     "summary": "강화도와 부속 도서로 이루어진 인천 북서부 자연·관광 권역입니다.",
     "dongs": [
        {"slug": "ganghwa-eup", "name": "강화읍", "arrival": 70,
         "landmarks": "강화풍물시장, 고려궁지, 강화터미널 일대",
         "character": "강화군의 행정·생활 중심지로 시장과 관공서가 모인 읍 중심 생활권"},
        {"slug": "seonwon-myeon", "name": "선원면", "arrival": 72,
         "landmarks": "선원사지, 강화남단 농촌 마을 일대",
         "character": "강화읍과 접한 농촌 주거·전원 생활권"},
        {"slug": "bureun-myeon", "name": "불은면", "arrival": 76,
         "landmarks": "광성보, 덕진진 인근 해안 마을",
         "character": "강화 동남부 해안 방어유적과 농촌이 어우러진 권역"},
        {"slug": "gilsang-myeon", "name": "길상면", "arrival": 80,
         "landmarks": "전등사, 정족산성, 온수리 일대",
         "character": "전등사를 낀 관광·전원 생활권"},
        {"slug": "hwado-myeon", "name": "화도면", "arrival": 85,
         "landmarks": "마니산, 동막해변, 화도 중심지",
         "character": "마니산과 해변을 끼고 펜션·전원주택이 모인 관광 권역"},
        {"slug": "yangdo-myeon", "name": "양도면", "arrival": 82,
         "landmarks": "강화나들길, 능내리 일대",
         "character": "강화 중부 내륙 농촌 전원 생활권"},
        {"slug": "naega-myeon", "name": "내가면", "arrival": 84,
         "landmarks": "고려산, 외포리 방향 일대",
         "character": "고려산 자락의 농촌·해안 생활권"},
        {"slug": "hajeom-myeon", "name": "하점면", "arrival": 86,
         "landmarks": "강화고인돌, 봉천산 일대",
         "character": "고인돌 유적과 농경지가 펼쳐진 북부 권역"},
        {"slug": "yangsa-myeon", "name": "양사면", "arrival": 90,
         "landmarks": "강화평화전망대, 북단 해안 마을",
         "character": "한강 하구 북단의 조용한 해안 농촌 권역"},
        {"slug": "songhae-myeon", "name": "송해면", "arrival": 84,
         "landmarks": "숭릉, 강화북부 농촌 일대",
         "character": "강화읍 북측 농촌 전원 생활권"},
        {"slug": "gyodong-myeon", "name": "교동면", "arrival": 105,
         "landmarks": "교동대교, 대룡시장, 교동도",
         "character": "교동대교로 연결된 섬마을 관광·농촌 권역"},
        {"slug": "samsan-myeon", "name": "삼산면", "arrival": 120,
         "landmarks": "석모도, 보문사 일대",
         "character": "석모도 보문사를 낀 섬 관광 권역"},
        {"slug": "seodo-myeon", "name": "서도면", "arrival": 130,
         "landmarks": "주문도, 볼음도 등 서부 도서",
         "character": "주문도·볼음도 등 여객선으로 닿는 도서 권역"},
     ]},
    {"slug": "ongjin-gun", "name": "옹진군", "kind": "군",
     "summary": "서해 도서로 이루어진 인천 최서단 섬 권역입니다.",
     "dongs": [
        {"slug": "bukdo-myeon", "name": "북도면", "arrival": 75,
         "landmarks": "신도·시도·모도, 영종도 삼목선착장",
         "character": "영종도에서 배로 닿는 신도·시도·모도 섬 관광 권역"},
        {"slug": "yeonpyeong-myeon", "name": "연평면", "arrival": 240,
         "landmarks": "연평도, 연평항",
         "character": "서해 최북단 연평도 어촌 권역"},
        {"slug": "baengnyeong-myeon", "name": "백령면", "arrival": 290,
         "landmarks": "백령도, 두무진, 사곶해변",
         "character": "여객선으로 닿는 백령도 관광·어촌 권역"},
        {"slug": "daecheong-myeon", "name": "대청면", "arrival": 280,
         "landmarks": "대청도, 옥죽동 해안사구",
         "character": "백령도 인근 대청도 도서 권역"},
        {"slug": "deokjeok-myeon", "name": "덕적면", "arrival": 150,
         "landmarks": "덕적도, 서포리해변",
         "character": "여객선으로 닿는 덕적도 해변 관광 권역"},
        {"slug": "jawol-myeon", "name": "자월면", "arrival": 140,
         "landmarks": "자월도, 이작도, 승봉도",
         "character": "자월도·이작도 등 서해 휴양 도서 권역"},
        {"slug": "yeongheung-myeon", "name": "영흥면", "arrival": 80,
         "landmarks": "영흥대교, 십리포해변, 선재도",
         "character": "영흥대교로 연결된 영흥도 해변 관광 권역"},
     ]},
    {"slug": "jung-gu", "name": "중구", "kind": "구",
     "summary": "원도심과 영종·용유 공항 지역으로 나뉘는 인천의 관문 권역입니다.",
     "dongs": [
        {"slug": "sinpo-dong", "name": "신포동", "arrival": 33,
         "landmarks": "신포국제시장, 차이나타운, 자유공원",
         "character": "원도심 상권과 근대 거리·시장이 모인 중구 중심 생활권"},
        {"slug": "yeonan-dong", "name": "연안동", "arrival": 35,
         "landmarks": "인천항 연안부두, 종합어시장",
         "character": "연안부두와 어시장을 낀 항만 배후 생활권"},
        {"slug": "sinheung-dong", "name": "신흥동", "arrival": 34,
         "landmarks": "신흥시장, 인천항 인근",
         "character": "항만과 주거가 섞인 원도심 생활권"},
        {"slug": "dowon-dong", "name": "도원동", "arrival": 33,
         "landmarks": "도원역, 제물포 방향 주거지",
         "character": "도원역을 낀 원도심 주거 생활권"},
        {"slug": "yulmok-dong", "name": "율목동", "arrival": 33,
         "landmarks": "율목공원, 신포동 인근",
         "character": "신포동과 이어지는 조용한 원도심 주거지"},
        {"slug": "dongincheon-dong", "name": "동인천동", "arrival": 32,
         "landmarks": "동인천역, 배다리 헌책방거리",
         "character": "동인천역 상권을 중심으로 한 원도심 생활권"},
        {"slug": "gaehang-dong", "name": "개항동", "arrival": 33,
         "landmarks": "개항장 근대건축, 차이나타운, 월미도 방향",
         "character": "개항장 역사문화와 관광이 어우러진 권역"},
        {"slug": "yeongjong-dong", "name": "영종동", "arrival": 40,
         "landmarks": "영종하늘도시, 운서·중산 일대",
         "character": "영종하늘도시 신주거지가 형성된 공항 배후 권역"},
        {"slug": "unseo-dong", "name": "운서동", "arrival": 42,
         "landmarks": "운서역, 공항신도시, 인천공항 인근",
         "character": "인천공항과 공항신도시를 낀 신주거 생활권"},
        {"slug": "yongyu-dong", "name": "용유동", "arrival": 48,
         "landmarks": "을왕리해수욕장, 무의도, 마시안해변",
         "character": "을왕리·무의도 해변 관광이 집중된 권역"},
     ]},
    {"slug": "dong-gu", "name": "동구", "kind": "구",
     "summary": "인천 원도심의 산업·주거가 밀집한 작은 권역입니다.",
     "dongs": [
        {"slug": "manseok-dong", "name": "만석동", "arrival": 33,
         "landmarks": "만석부두, 괭이부리마을",
         "character": "항만 산업과 오래된 주거가 공존하는 권역"},
        {"slug": "hwasu-hwapyeong-dong", "name": "화수·화평동", "arrival": 32,
         "landmarks": "화수부두, 화평동 세숫대야냉면거리",
         "character": "화수부두와 화평동 먹자거리를 낀 원도심 생활권"},
        {"slug": "songhyeon-dong", "name": "송현동", "arrival": 31,
         "landmarks": "송현시장, 동산 일대",
         "character": "전통시장을 낀 주거 밀집 생활권"},
        {"slug": "songnim-dong", "name": "송림동", "arrival": 31,
         "landmarks": "송림오거리, 인천대학교(제물포) 인근",
         "character": "동구 최대 주거지로 재개발이 진행되는 생활권"},
        {"slug": "geumchang-dong", "name": "금창동", "arrival": 32,
         "landmarks": "배다리, 금곡동 헌책방거리",
         "character": "배다리 역사거리를 낀 원도심 주거 생활권"},
     ]},
    {"slug": "michuhol-gu", "name": "미추홀구", "kind": "구",
     "summary": "주안·용현을 중심으로 한 인천 중심부의 대표 주거 권역입니다.",
     "dongs": [
        {"slug": "sungui-dong", "name": "숭의동", "arrival": 31,
         "landmarks": "숭의역, 도원역, 제물포스포츠타운",
         "character": "원도심과 주안을 잇는 주거·상업 혼합 생활권"},
        {"slug": "yonghyeon-dong", "name": "용현동", "arrival": 30,
         "landmarks": "인하대학교, 토지금고, 수봉공원",
         "character": "인하대 학군과 대단지 주거가 모인 생활권"},
        {"slug": "hagik-dong", "name": "학익동", "arrival": 31,
         "landmarks": "학익동 법조타운, 문학산 인근",
         "character": "법원·검찰청과 대단지 아파트가 자리한 주거 권역"},
        {"slug": "dohwa-dong", "name": "도화동", "arrival": 30,
         "landmarks": "도화역, 인천대학교(제물포캠퍼스)",
         "character": "도화역을 낀 학군·주거 생활권"},
        {"slug": "juan-dong", "name": "주안동", "arrival": 28,
         "landmarks": "주안역, 주안역 상권, 석바위시장",
         "character": "주안역을 중심으로 한 미추홀구 최대 상업·주거 밀집 생활권",
         "sub_note": "주안1동~주안8동 일대는 주안동 페이지에서 통합 안내드립니다."},
        {"slug": "gwangyo-dong", "name": "관교동", "arrival": 31,
         "landmarks": "인천종합터미널, 신세계백화점, 문학경기장",
         "character": "터미널·백화점을 낀 교통·상업 중심 생활권"},
        {"slug": "munhak-dong", "name": "문학동", "arrival": 33,
         "landmarks": "문학산, 문학경기장, 인천문학경기장",
         "character": "문학산 자락의 경기장·주거 생활권"},
     ]},
    {"slug": "yeonsu-gu", "name": "연수구", "kind": "구",
     "summary": "송도국제도시와 연수 택지지구를 아우르는 인천 남부 신주거 권역입니다.",
     "dongs": [
        {"slug": "okryeon-dong", "name": "옥련동", "arrival": 33,
         "landmarks": "옥련동, 인천상륙작전기념관, 송도유원지",
         "character": "옛 송도와 연수를 잇는 주거·관광 생활권"},
        {"slug": "seonhak-dong", "name": "선학동", "arrival": 33,
         "landmarks": "선학역, 선학경기장",
         "character": "선학역을 낀 조용한 주거 생활권"},
        {"slug": "yeonsu-dong", "name": "연수동", "arrival": 33,
         "landmarks": "연수역, 원인재, 연수 택지지구",
         "character": "연수 택지지구의 정주형 대단지 주거 생활권"},
        {"slug": "cheonghak-dong", "name": "청학동", "arrival": 34,
         "landmarks": "청학동, 문학산 남측",
         "character": "문학산 자락의 안정적 주거 생활권"},
        {"slug": "dongchun-dong", "name": "동춘동", "arrival": 34,
         "landmarks": "동춘역, 동막역, 연수 남부 주거지",
         "character": "연수구 남부의 대단지 주거 생활권"},
        {"slug": "songdo-dong", "name": "송도동", "arrival": 37,
         "landmarks": "송도센트럴파크, 인천대, 트리플스트리트, 송도국제업무지구",
         "character": "고층 주거·업무·연구시설이 밀집한 송도국제도시 핵심 권역",
         "sub_note": "송도1동~송도5동 일대는 송도동 페이지에서 통합 안내드립니다."},
     ]},
    {"slug": "namdong-gu", "name": "남동구", "kind": "구",
     "summary": "인천시청과 구월동 상권을 낀 인천 행정·상업 중심 권역입니다.",
     "dongs": [
        {"slug": "guwol-dong", "name": "구월동", "arrival": 29,
         "landmarks": "인천시청, 구월동 로데오거리, 모래내시장",
         "character": "인천시청과 최대 번화가를 낀 행정·상업 중심 생활권",
         "sub_note": "구월1동~구월4동 일대는 구월동 페이지에서 통합 안내드립니다."},
        {"slug": "ganseok-dong", "name": "간석동", "arrival": 29,
         "landmarks": "간석오거리역, 간석역, 백운역",
         "character": "교통이 교차하는 주거 밀집 생활권"},
        {"slug": "mansu-dong", "name": "만수동", "arrival": 31,
         "landmarks": "만수역, 인천대공원 인근",
         "character": "대단지 아파트가 모인 정주형 주거 생활권"},
        {"slug": "jangsu-seochang-dong", "name": "장수서창동", "arrival": 34,
         "landmarks": "서창2지구, 인천대공원, 장수동 은행나무",
         "character": "인천대공원과 서창지구를 낀 자연·신주거 생활권"},
        {"slug": "seochang-dong", "name": "서창동", "arrival": 34,
         "landmarks": "서창지구, 서창2지구 택지",
         "character": "서창 택지지구의 신주거 생활권"},
        {"slug": "namchon-dorim-dong", "name": "남촌도림동", "arrival": 32,
         "landmarks": "남촌동, 도림동, 남동공단 인근",
         "character": "남동산단 배후의 주거·물류 혼합 생활권"},
        {"slug": "nonhyeon-dong", "name": "논현동", "arrival": 32,
         "landmarks": "인천논현역, 에코메트로, 논현지구",
         "character": "논현 택지지구의 대단지 신주거 생활권",
         "sub_note": "논현1동·논현2동 일대는 논현동 페이지에서 통합 안내드립니다."},
        {"slug": "nonhyeon-gojan-dong", "name": "논현고잔동", "arrival": 33,
         "landmarks": "소래포구, 호구포역, 고잔동",
         "character": "소래포구와 남동산단을 낀 주거·해안 생활권"},
     ]},
    {"slug": "bupyeong-gu", "name": "부평구", "kind": "구",
     "summary": "부평역 상권을 중심으로 한 인천 동부의 최대 주거·상업 권역입니다.",
     "dongs": [
        {"slug": "bupyeong-dong", "name": "부평동", "arrival": 27,
         "landmarks": "부평역, 부평지하상가, 부평문화의거리",
         "character": "부평역 상권을 낀 인천 동부 최대 상업·주거 밀집 생활권",
         "sub_note": "부평1동~부평6동 일대는 부평동 페이지에서 통합 안내드립니다."},
        {"slug": "sangok-dong", "name": "산곡동", "arrival": 28,
         "landmarks": "산곡역, 부평미군기지(캠프마켓) 인근",
         "character": "재개발이 활발한 대단지 주거 생활권"},
        {"slug": "cheongcheon-dong", "name": "청천동", "arrival": 29,
         "landmarks": "청천동, 부평공단 인근",
         "character": "부평산업단지 배후의 주거 생활권"},
        {"slug": "galsan-dong", "name": "갈산동", "arrival": 29,
         "landmarks": "갈산역, 부평구청 인근",
         "character": "갈산역과 구청을 낀 주거·행정 생활권"},
        {"slug": "samsan-dong", "name": "삼산동", "arrival": 28,
         "landmarks": "삼산체육관역, 홈플러스, 삼산농수산물시장",
         "character": "삼산 택지지구의 대단지 신주거 생활권"},
        {"slug": "bugae-dong", "name": "부개동", "arrival": 28,
         "landmarks": "부개역, 부평삼거리 인근",
         "character": "부개역을 낀 정주형 주거 생활권"},
        {"slug": "ilsin-dong", "name": "일신동", "arrival": 29,
         "landmarks": "일신동, 부영아파트 일대",
         "character": "부평 동남부의 조용한 주거 생활권"},
        {"slug": "sipjeong-dong", "name": "십정동", "arrival": 29,
         "landmarks": "동암역, 백운역, 열우물경기장",
         "character": "동암·백운역을 낀 주거 밀집 생활권"},
     ]},
    {"slug": "gyeyang-gu", "name": "계양구", "kind": "구",
     "summary": "계산·작전 생활권과 계양신도시를 아우르는 인천 북부 권역입니다.",
     "dongs": [
        {"slug": "hyoseong-dong", "name": "효성동", "arrival": 31,
         "landmarks": "효성동, 천마산 인근",
         "character": "천마산 자락의 주거 밀집 생활권"},
        {"slug": "gyesan-dong", "name": "계산동", "arrival": 31,
         "landmarks": "계산역, 경인교대입구역, 계양구청",
         "character": "경인교대와 구청을 낀 계양구 중심 생활권"},
        {"slug": "jakjeon-dong", "name": "작전동", "arrival": 30,
         "landmarks": "작전역, 작전동 상권",
         "character": "작전역 상권을 낀 대단지 주거 생활권"},
        {"slug": "jakjeon-seoun-dong", "name": "작전·서운동", "arrival": 31,
         "landmarks": "서운동, 작전서운 일대, 경인고속도로 인근",
         "character": "작전과 서운을 아우르는 주거·물류 생활권"},
        {"slug": "gyeyang-dong", "name": "계양동", "arrival": 33,
         "landmarks": "계양역, 박촌역, 계양신도시",
         "character": "계양역과 신도시 개발을 낀 북부 신주거 생활권"},
     ]},
    {"slug": "seo-gu", "name": "서구", "kind": "구",
     "summary": "청라국제도시와 검단신도시를 양 축으로 빠르게 성장하는 인천 서부 권역입니다.",
     "dongs": [
        {"slug": "geomam-gyeongseo-dong", "name": "검암경서동", "arrival": 33,
         "landmarks": "검암역, 청라 인근, 경서동 드림파크",
         "character": "검암역 환승과 경서동 자연을 낀 서부 생활권"},
        {"slug": "yeonhui-dong", "name": "연희동", "arrival": 32,
         "landmarks": "아시아드주경기장, 서구청, 연희자연마당",
         "character": "서구청과 경기장을 낀 행정·주거 생활권"},
        {"slug": "cheongna-dong", "name": "청라동", "arrival": 33,
         "landmarks": "청라국제도시, 청라호수공원, 커낼웨이",
         "character": "호수공원을 낀 고층 대단지 신주거 권역",
         "sub_note": "청라1동~청라3동 일대는 청라동 페이지에서 통합 안내드립니다."},
        {"slug": "gajeong-dong", "name": "가정동", "arrival": 31,
         "landmarks": "가정역, 루원시티, 가정중앙시장",
         "character": "루원시티 개발을 낀 신주거·상업 생활권"},
        {"slug": "sinhyeon-wonchang-dong", "name": "신현원창동", "arrival": 31,
         "landmarks": "신현동, 원창동, 청라 인근",
         "character": "주거와 산업단지가 접한 서부 생활권"},
        {"slug": "seoknam-dong", "name": "석남동", "arrival": 30,
         "landmarks": "석남역, 거북시장",
         "character": "석남역 환승을 낀 주거 밀집 생활권"},
        {"slug": "gajwa-dong", "name": "가좌동", "arrival": 30,
         "landmarks": "인천가좌역, 가재울, 가좌산업단지",
         "character": "산업단지와 주거가 섞인 생활권"},
        {"slug": "geomdan-dong", "name": "검단동", "arrival": 36,
         "landmarks": "검단사거리역, 검단신도시 인근",
         "character": "검단신도시와 접한 주거 생활권"},
        {"slug": "bullo-daegok-dong", "name": "불로대곡동", "arrival": 37,
         "landmarks": "불로동, 대곡동, 검단신도시",
         "character": "검단신도시 동측 신주거 생활권"},
        {"slug": "wondang-dong", "name": "원당동", "arrival": 37,
         "landmarks": "원당지구, 검단신도시 중심",
         "character": "검단신도시 원당지구 대단지 신주거 권역"},
        {"slug": "dangha-dong", "name": "당하동", "arrival": 37,
         "landmarks": "신검단중앙역, 당하지구",
         "character": "검단신도시 당하지구의 신주거 생활권"},
        {"slug": "oryu-wanggil-dong", "name": "오류왕길동", "arrival": 39,
         "landmarks": "검단오류역, 왕길역, 검단산업단지",
         "character": "검단 북부의 주거·산업 혼합 생활권"},
        {"slug": "majeon-dong", "name": "마전동", "arrival": 37,
         "landmarks": "마전역, 검단사거리, 마전지구",
         "character": "검단신도시 마전지구의 주거 생활권"},
        {"slug": "ara-dong", "name": "아라동", "arrival": 36,
         "landmarks": "아라역, 검단호수공원, 경인아라뱃길",
         "character": "아라뱃길과 호수공원을 낀 신주거 생활권"},
     ]},
]

# ===========================================================================
# DATA MODEL — 지하철역 (노선 → 역, 환승역은 URL 1개로 통합)
# 메뉴/노선 목록에는 역명만, 역 상세 페이지 H1·Title에서만 키워드 사용.
# ===========================================================================
# 노선 표시 정보
LINES = [
    {"key": "incheon-line-1", "name": "인천1호선", "short": "인천1호선"},
    {"key": "incheon-line-2", "name": "인천2호선", "short": "인천2호선"},
    {"key": "line-1",         "name": "1호선 인천권", "short": "1호선"},
    {"key": "line-7",         "name": "7호선 인천권", "short": "7호선"},
    {"key": "suinbundang",    "name": "수인분당선 인천권", "short": "수인분당선"},
    {"key": "airport",        "name": "공항철도 인천권", "short": "공항철도"},
]
LINE_NAME = {l["key"]: l["name"] for l in LINES}
LINE_SHORT = {l["key"]: l["short"] for l in LINES}

# 노선별 역 순서 (역명 기준 — 환승역은 같은 역명으로 자동 통합)
LINE_STATIONS = {
    "incheon-line-1": ["검단호수공원","신검단중앙","아라","계양","귤현","박촌","임학","계산",
        "경인교대입구","작전","갈산","부평구청","부평시장","부평","동수","부평삼거리","간석오거리",
        "인천시청","예술회관","인천터미널","문학경기장","선학","신연수","원인재","동춘","동막",
        "캠퍼스타운","테크노파크","지식정보단지","인천대입구","센트럴파크","국제업무지구","송도달빛축제공원"],
    "incheon-line-2": ["검단오류","왕길","검단사거리","마전","완정","독정","검암","검바위",
        "아시아드경기장","서구청","가정","가정중앙시장","석남","서부여성회관","인천가좌","가재울",
        "주안국가산단","주안","시민공원","석바위시장","인천시청","석천사거리","모래내시장","만수",
        "남동구청","인천대공원","운연"],
    "line-1": ["인천","동인천","도원","제물포","도화","주안","간석","동암","백운","부평","부개"],
    "line-7": ["삼산체육관","굴포천","부평구청","산곡","석남"],
    "suinbundang": ["인천","신포","숭의","인하대","송도","연수","원인재","남동인더스파크",
        "호구포","인천논현","소래포구"],
    "airport": ["계양","검암","청라국제도시","영종","운서","공항화물청사","인천공항1터미널","인천공항2터미널"],
}

# 역 고유 데이터: 역명 → (slug, 구, 랜드마크, 평균도착(분))
STATION_DATA = {
    # 인천1호선
    "검단호수공원": ("geomdan-lake-park-station", "서구", "검단호수공원, 검단신도시 중심", 38),
    "신검단중앙": ("singeomdan-jungang-station", "서구", "검단신도시 중앙, 당하지구", 38),
    "아라": ("ara-station", "서구", "경인아라뱃길, 검단호수공원", 36),
    "계양": ("gyeyang-station", "계양구", "계양구청, 계양신도시(환승역)", 33),
    "귤현": ("gyulhyeon-station", "계양구", "귤현동, 계양1호선 차량기지", 34),
    "박촌": ("bakchon-station", "계양구", "박촌동, 계양신도시 인근", 33),
    "임학": ("imhak-station", "계양구", "임학동, 계양구 주거지", 32),
    "계산": ("gyesan-station", "계양구", "계산동, 경인교대, 계양구청", 31),
    "경인교대입구": ("gyeongin-edu-station", "계양구", "경인교육대학교, 계산동", 31),
    "작전": ("jakjeon-station", "계양구", "작전동 상권, 작전시장", 30),
    "갈산": ("galsan-station", "부평구", "갈산동, 부평구청 인근", 29),
    "부평구청": ("bupyeong-gu-office-station", "부평구", "부평구청(환승역)", 28),
    "부평시장": ("bupyeong-market-station", "부평구", "부평종합시장, 부평문화의거리", 28),
    "부평": ("bupyeong-station", "부평구", "부평역 상권, 부평지하상가(환승역)", 27),
    "동수": ("dongsu-station", "부평구", "동수동, 부평 주거지", 28),
    "부평삼거리": ("bupyeong-samgeori-station", "부평구", "부평삼거리, 부개동 인근", 29),
    "간석오거리": ("ganseok-ogeori-station", "남동구", "간석오거리, 간석동 상권", 30),
    "인천시청": ("incheon-city-hall-station", "남동구", "인천시청, 구월동 번화가(환승역)", 30),
    "예술회관": ("arts-center-station", "남동구", "인천종합문화예술회관, 구월동", 31),
    "인천터미널": ("incheon-terminal-station", "미추홀구", "인천종합터미널, 신세계백화점", 31),
    "문학경기장": ("munhak-stadium-station", "미추홀구", "인천문학경기장, 문학동", 32),
    "선학": ("seonhak-station", "연수구", "선학동, 선학경기장", 33),
    "신연수": ("sinyeonsu-station", "연수구", "신연수, 연수동 주거지", 33),
    "원인재": ("woninjae-station", "연수구", "원인재, 연수 택지지구(환승역)", 34),
    "동춘": ("dongchun-station", "연수구", "동춘동, 연수 남부 주거지", 34),
    "동막": ("dongmak-station", "연수구", "동막, 송도 입구", 35),
    "캠퍼스타운": ("campus-town-station", "연수구", "송도 캠퍼스타운, 인천대 인근", 35),
    "테크노파크": ("technopark-station", "연수구", "송도테크노파크, 갯벌타워", 36),
    "지식정보단지": ("knowledge-info-station", "연수구", "송도 지식정보단지, 트리플스트리트", 36),
    "인천대입구": ("incheon-univ-station", "연수구", "인천대학교, 송도센트럴파크", 37),
    "센트럴파크": ("central-park-station", "연수구", "송도센트럴파크, 트라이볼", 37),
    "국제업무지구": ("international-business-station", "연수구", "송도국제업무지구, G타워", 38),
    "송도달빛축제공원": ("songdo-moonlight-park-station", "연수구", "송도달빛축제공원, 인천1호선 종점", 39),
    # 인천2호선 (신규)
    "검단오류": ("geomdan-oryu-station", "서구", "검단오류, 검단산업단지", 39),
    "왕길": ("wanggil-station", "서구", "왕길동, 검단 북부", 38),
    "검단사거리": ("geomdan-sageori-station", "서구", "검단사거리, 마전지구", 37),
    "마전": ("majeon-station", "서구", "마전동, 검단신도시", 37),
    "완정": ("wanjeong-station", "서구", "완정, 당하지구", 36),
    "독정": ("dokjeong-station", "서구", "독정, 검단 남부", 35),
    "검암": ("geomam-station", "서구", "검암역, 청라 인근(환승역)", 34),
    "검바위": ("geombawi-station", "서구", "검바위, 검암 주거지", 34),
    "아시아드경기장": ("asiad-stadium-station", "서구", "인천아시아드주경기장, 연희동", 33),
    "서구청": ("seo-gu-office-station", "서구", "서구청, 연희동", 32),
    "가정": ("gajeong-station", "서구", "가정동, 루원시티", 31),
    "가정중앙시장": ("gajeong-market-station", "서구", "가정중앙시장, 가정동", 31),
    "석남": ("seoknam-station", "서구", "석남동, 거북시장(환승역)", 30),
    "서부여성회관": ("seobu-womens-station", "서구", "서부여성회관, 신현동", 31),
    "인천가좌": ("incheon-gajwa-station", "서구", "가좌동, 가좌산업단지", 30),
    "가재울": ("gajaeul-station", "서구", "가재울, 가좌동 주거지", 30),
    "주안국가산단": ("juan-industrial-station", "미추홀구", "주안국가산업단지", 29),
    "주안": ("juan-station", "미추홀구", "주안역 상권, 주안동(환승역)", 28),
    "시민공원": ("citizens-park-station", "미추홀구", "인천시민공원, 주안동", 29),
    "석바위시장": ("seokbawi-market-station", "미추홀구", "석바위시장, 미추홀구청", 30),
    "석천사거리": ("seokcheon-sageori-station", "남동구", "석천사거리, 구월동", 31),
    "모래내시장": ("moraenae-market-station", "남동구", "모래내시장, 만수동", 31),
    "만수": ("mansu-station", "남동구", "만수동, 만수 주거지", 32),
    "남동구청": ("namdong-gu-office-station", "남동구", "남동구청, 만수동", 32),
    "인천대공원": ("incheon-grand-park-station", "남동구", "인천대공원, 장수동", 34),
    "운연": ("unyeon-station", "남동구", "운연동, 인천2호선 종점", 35),
    # 1호선 인천권 (신규)
    "인천": ("incheon-station", "중구", "인천역, 차이나타운, 월미도(환승역)", 33),
    "동인천": ("dongincheon-station", "중구", "동인천역 상권, 신포동", 32),
    "도원": ("dowon-station", "중구", "도원동, 제물포스포츠타운", 32),
    "제물포": ("jemulpo-station", "미추홀구", "제물포역, 인천대 제물포캠퍼스", 30),
    "도화": ("dohwa-station", "미추홀구", "도화동, 도화지구", 30),
    "간석": ("ganseok-station", "남동구", "간석동, 백운 인근", 29),
    "동암": ("dongam-station", "부평구", "동암역, 십정동", 28),
    "백운": ("baegun-station", "부평구", "백운동, 십정동", 28),
    "부개": ("bugae-station", "부평구", "부개동, 부평삼거리 인근", 27),
    # 7호선 인천권 (신규)
    "삼산체육관": ("samsan-gym-station", "부평구", "삼산월드체육관, 삼산동", 28),
    "굴포천": ("gulpocheon-station", "부평구", "굴포천, 삼산동", 28),
    "산곡": ("sangok-station", "부평구", "산곡동, 캠프마켓 인근", 29),
    # 수인분당선 인천권 (신규)
    "신포": ("sinpo-station", "중구", "신포국제시장, 차이나타운", 33),
    "숭의": ("sungui-station", "미추홀구", "숭의동, 제물포스포츠타운", 31),
    "인하대": ("inha-univ-station", "미추홀구", "인하대학교, 용현동", 30),
    "송도": ("songdo-station", "연수구", "송도역, 옥련동", 35),
    "연수": ("yeonsu-station", "연수구", "연수동, 연수 택지지구", 33),
    "남동인더스파크": ("namdong-induspark-station", "남동구", "남동국가산업단지", 32),
    "호구포": ("hogupo-station", "남동구", "호구포, 논현지구", 33),
    "인천논현": ("incheon-nonhyeon-station", "남동구", "논현지구, 에코메트로", 33),
    "소래포구": ("soraepogu-station", "남동구", "소래포구, 소래습지생태공원", 34),
    # 공항철도 인천권 (신규)
    "청라국제도시": ("cheongna-intl-station", "서구", "청라국제도시, 청라호수공원", 33),
    "영종": ("yeongjong-station", "중구", "영종도, 영종하늘도시", 40),
    "운서": ("unseo-station", "중구", "운서동, 공항신도시", 42),
    "공항화물청사": ("cargo-terminal-station", "중구", "인천공항 화물청사", 45),
    "인천공항1터미널": ("airport-t1-station", "중구", "인천국제공항 제1여객터미널", 47),
    "인천공항2터미널": ("airport-t2-station", "중구", "인천국제공항 제2여객터미널", 50),
}

def station_lines(name):
    """역이 속한 모든 노선 key 목록(노선 정의 순서)."""
    return [l["key"] for l in LINES if name in LINE_STATIONS[l["key"]]]

def unique_stations():
    """역명 기준 중복 제거된 역 목록(노선 정의 순서, 최초 등장 순)."""
    seen, out = set(), []
    for l in LINES:
        for nm in LINE_STATIONS[l["key"]]:
            if nm not in seen:
                seen.add(nm)
                out.append(nm)
    return out

# ===========================================================================
# DATA MODEL — 테마
# ===========================================================================
THEMES = [
    {"slug": "swedish", "name": "스웨디시", "kicker": "SWEDISH",
     "summary": "일정한 압과 리듬으로 전신을 부드럽게 이완하는 오일 관리입니다.",
     "intro": "스웨디시는 오일을 사용해 큰 근육을 따라 길게 쓸어주는, 가장 대중적인 전신 이완 관리입니다. 강한 지압보다 일정한 압과 리듬으로 혈행과 이완을 돕는 데 초점을 둡니다.",
     "detail": "스웨디시의 기본 동작은 에플라지(쓸어주기)·페트리사지(반죽하기)·프릭션(마찰)으로 나뉘며, 큰 근육을 따라 일정한 방향으로 이어집니다. 오일을 사용해 마찰을 줄이고 혈행을 도와, 자극보다 순환과 이완에 무게를 둡니다. 압은 중간 정도가 기본이며 부위별로 강약을 조절합니다.",
     "fit": ["하루 종일 앉아 일해 어깨·등이 뭉친 분", "강한 자극보다 부드러운 이완을 원하는 분", "처음 마사지를 받아 무난한 코스를 찾는 분"],
     "diff": "타이마사지가 스트레칭 위주라면 스웨디시는 오일을 사용한 부드러운 쓸어내림 위주입니다. 향까지 더하고 싶다면 아로마테라피를 권해드립니다."},
    {"slug": "lomi", "name": "로미로미", "kicker": "LOMI LOMI",
     "summary": "하와이 전통 기법으로 팔뚝을 활용해 길고 리드미컬하게 이완합니다.",
     "intro": "로미로미는 손바닥과 팔뚝을 함께 사용해 파도처럼 길고 이어지는 동작으로 전신을 감싸듯 풀어주는 하와이 전통 계열 관리입니다.",
     "detail": "로미로미는 손바닥뿐 아니라 팔뚝 전체를 활용해 넓은 면으로 길게 쓸어주는 것이 특징입니다. 동작이 끊기지 않고 파도처럼 이어져, 받는 분의 호흡이 자연스럽게 느려집니다. 리듬감 있는 흐름 속에서 몸 전체를 하나로 감싸듯 이완합니다.",
     "fit": ["깊고 연속적인 이완을 원하는 분", "긴장도가 높아 호흡까지 가라앉히고 싶은 분", "스웨디시보다 더 감각적인 흐름을 원하는 분"],
     "diff": "스웨디시와 비슷한 오일 관리지만, 팔뚝을 활용한 넓고 연속적인 동작이 특징입니다."},
    {"slug": "thai", "name": "타이마사지", "kicker": "THAI",
     "summary": "오일 없이 스트레칭과 지압으로 몸의 유연성과 순환을 돕습니다.",
     "intro": "타이마사지는 오일 없이 손·팔꿈치·무릎을 활용한 지압과 스트레칭으로 관절 가동 범위와 순환을 돕는 전통 관리입니다.",
     "detail": "타이마사지는 시술자가 손·팔꿈치·무릎·발을 이용해 지압점을 누르고, 요가에 가까운 스트레칭으로 관절을 펴줍니다. 오일 없이 옷을 입은 상태로 진행해 몸의 라인(센)을 따라 순환을 돕습니다. 뭉친 근육을 늘여주는 동작이 많아 시원하면서도 개운한 느낌을 줍니다.",
     "fit": ["몸이 뻣뻣하고 유연성이 떨어진다고 느끼는 분", "지압과 스트레칭을 선호하는 분", "오일이 부담스러운 분"],
     "diff": "오일 관리(스웨디시·아로마)와 달리 옷을 입은 상태에서 스트레칭 중심으로 진행됩니다."},
    {"slug": "chinese", "name": "중국마사지", "kicker": "CHINESE",
     "summary": "경혈과 지압을 중심으로 또렷한 압을 사용하는 관리입니다.",
     "intro": "중국식 관리는 경혈과 근육을 따라 또렷한 압으로 눌러주는 지압 중심 관리로, 뭉침이 심한 부위를 시원하게 풀어주는 데 초점을 둡니다.",
     "detail": "중국식 관리는 경혈과 근육을 손가락·손바닥으로 또렷하게 누르는 지압이 중심입니다. 뭉친 부위를 점으로 집중해 풀어, 묵직한 시원함을 선호하는 분께 잘 맞습니다. 압이 또렷한 편이라 강도는 받는 분의 반응을 보며 세밀하게 맞춰 갑니다.",
     "fit": ["뻐근함이 심해 또렷한 압을 원하는 분", "특정 부위 집중 관리를 원하는 분", "지압식 시원함을 선호하는 분"],
     "diff": "부드러운 오일 관리보다 압이 또렷한 편이라, 강도를 선호에 맞춰 조절해 드립니다."},
    {"slug": "aroma", "name": "아로마테라피", "kicker": "AROMATHERAPY",
     "summary": "블렌딩 오일의 향과 촉감으로 심신을 함께 이완하는 관리입니다.",
     "intro": "아로마테라피는 라벤더·시트러스 등 블렌딩 오일의 향을 더해 근육 이완과 심리적 안정을 함께 돕는 관리입니다.",
     "detail": "아로마테라피는 에센셜 오일을 캐리어 오일에 블렌딩해 향과 촉감을 함께 전합니다. 후각을 통한 이완이 더해져, 같은 동작도 더 깊고 차분하게 느껴집니다. 라벤더·시트러스 등 향의 계열에 따라 분위기가 달라져 그날 컨디션에 맞춰 고를 수 있습니다.",
     "fit": ["긴장도가 높거나 예민한 날", "향을 통한 깊은 이완을 원하는 분", "수면의 질을 높이고 싶은 분"],
     "diff": "스웨디시에 향의 이완을 더한 구성입니다. 향 알러지가 있다면 예약 시 알려주세요."},
    {"slug": "homecare", "name": "홈케어", "kicker": "HOME CARE",
     "summary": "자택·숙소로 방문해 익숙한 공간에서 받는 방문 관리입니다.",
     "intro": "홈케어는 관리사가 자택·오피스텔·숙소로 방문해 이동 없이 익숙한 공간에서 받는 방문형 관리입니다. 관리 직후 그대로 휴식할 수 있어 이완이 오래 유지됩니다.",
     "detail": "홈케어는 매장이 아닌 고객의 생활 공간에서 진행되어, 조명·온도·향까지 익숙한 환경에서 받을 수 있습니다. 관리사가 필요한 용품을 가지고 방문하므로 따로 준비하실 것이 적습니다. 받은 직후 이동 없이 바로 잠들거나 쉴 수 있는 것이 가장 큰 장점입니다.",
     "fit": ["외출 없이 집에서 편히 받고 싶은 분", "관리 후 바로 쉬고 싶은 분", "이동 시간을 아끼고 싶은 분"],
     "diff": "매장 방문이 아닌, 고객이 계신 곳으로 찾아가는 방식입니다. 인천 전지역으로 방문합니다."},
    {"slug": "hotel", "name": "호텔식마사지", "kicker": "HOTEL STYLE",
     "summary": "호텔·숙소 객실로 방문하는 격식 있는 프리미엄 관리입니다.",
     "intro": "호텔식 관리는 호텔·레지던스 객실로 방문해 격식 있는 응대와 프리미엄 구성으로 진행하는 방문 관리입니다.",
     "detail": "호텔식 관리는 객실 환경에 맞춰 침구·수건·동선을 정돈하고 격식 있게 진행합니다. 출장·여행으로 숙소에 머무는 분이 이동 없이 받기에 적합합니다. 프런트 출입이나 객실 안내가 필요한 경우 사전에 확인해 매끄럽게 방문합니다.",
     "fit": ["출장·여행 중 숙소에서 받고 싶은 분", "격식 있는 응대를 원하는 분", "공항 인근 숙소 투숙객"],
     "diff": "객실 환경에 맞춰 준비물과 동선을 세심하게 안내드립니다. 프런트 출입 안내가 필요하면 미리 알려주세요."},
    {"slug": "foot", "name": "발마사지", "kicker": "FOOT",
     "summary": "발과 종아리의 반사구를 중심으로 피로를 푸는 관리입니다.",
     "intro": "발마사지는 발바닥 반사구와 종아리를 중심으로 눌러주어 하체 피로와 부기를 정리하는 관리입니다.",
     "detail": "발마사지는 발바닥의 반사구와 발등·발가락, 종아리를 함께 눌러주고 풀어줍니다. 오래 서 있거나 많이 걸어 무거워진 하체의 피로와 부기를 정리하는 데 도움을 줍니다. 전신 관리에 부분 옵션으로 더하거나, 발·다리만 집중해 단독으로 받을 수도 있습니다.",
     "fit": ["오래 서서 일하거나 많이 걷는 분", "다리가 잘 붓는 분", "전신보다 부분 관리를 원하는 분"],
     "diff": "전신 관리와 함께 부분 옵션으로 선택하거나 단독으로 받을 수 있습니다."},
    {"slug": "sports", "name": "스포츠·경락", "kicker": "SPORTS",
     "summary": "운동 후 근육과 경락을 또렷한 압으로 정리하는 관리입니다.",
     "intro": "스포츠·경락 관리는 운동 후 뭉친 근육과 경락을 따라 또렷한 압으로 풀어 컨디션 회복을 돕는 관리입니다.",
     "detail": "스포츠·경락 관리는 근육의 결과 경락을 따라 또렷한 압으로 눌러 운동 후의 묵직함을 정리합니다. 큰 근육은 깊게, 자주 긴장되는 부위는 시간을 더 들여 풀어 갑니다. 통증과 시원함의 경계를 확인하며 강약을 세밀하게 조절합니다.",
     "fit": ["러닝·헬스·등산 등 운동 후 회복이 필요한 분", "또렷한 압을 선호하는 분", "특정 부위가 자주 뭉치는 분"],
     "diff": "부상·급성 통증 부위는 관리 대상이 아니며 의료기관 진료를 권유드립니다."},
    {"slug": "skincare", "name": "스킨케어", "kicker": "SKIN CARE",
     "summary": "얼굴·피부 관리를 더한 케어 옵션입니다.",
     "intro": "스킨케어는 클렌징과 보습 중심의 얼굴·피부 관리로, 전신 관리와 함께 또는 단독으로 선택할 수 있는 옵션입니다.",
     "detail": "스킨케어는 클렌징으로 피부를 정돈한 뒤 보습 중심으로 안색과 피부결을 가다듬습니다. 전신 관리와 함께 마무리 단계로 더하거나, 얼굴·피부만 단독으로 받을 수 있습니다. 사용 제품은 피부 상태에 맞춰 조정하며, 민감성·알러지는 미리 확인합니다.",
     "fit": ["관리와 함께 피부 케어를 받고 싶은 분", "건조함·피로한 안색이 신경 쓰이는 분"],
     "diff": "피부 상태에 따라 사용 제품을 조정하며, 민감성·알러지가 있다면 예약 시 알려주세요."},
    {"slug": "waxing", "name": "왁싱", "kicker": "WAXING",
     "summary": "위생적인 제모 케어 옵션입니다.",
     "intro": "왁싱은 위생 기준에 맞춰 진행하는 제모 케어 옵션으로, 부위와 범위를 사전에 확인해 안내드립니다.",
     "detail": "왁싱은 부위와 범위를 사전에 확인한 뒤 위생 기준에 맞춰 진행하는 제모 케어입니다. 일회용 제품과 도구를 사용해 청결을 우선합니다. 피부가 예민하거나 시술 이력이 있는 경우, 무리하지 않도록 사전 상담으로 방식을 조정합니다. 시술 전후에는 자극이 될 수 있는 활동을 피하고, 진정과 보습에 신경 쓰면 피부 부담을 줄일 수 있습니다.",
     "fit": ["방문 케어와 함께 왁싱을 원하는 분", "위생적인 제모를 선호하는 분", "방문이 편한 환경에서 부담 없이 받고 싶은 분"],
     "diff": "피부가 예민하거나 시술 이력이 있다면 예약 시 미리 상담해 주세요."},
    {"slug": "couple", "name": "커플 관리", "kicker": "COUPLE",
     "summary": "두 분이 같은 공간에서 동시에 받는 동반 관리입니다.",
     "intro": "커플 관리는 관리사 2인이 방문해 두 분이 같은 공간에서 동시에 받는 동반형 관리입니다. 각자 원하는 코스를 다르게 고를 수 있습니다.",
     "detail": "커플 관리는 관리사 2인이 함께 방문해 두 분을 같은 공간에서 동시에 진행합니다. 각자 다른 코스를 골라도 되고, 같은 코스로 나란히 받아도 됩니다. 동시 진행을 위해 두 사람이 누울 공간이 필요하며, 좁은 경우 순차로 안내합니다.",
     "fit": ["기념일을 함께 보내려는 커플", "부모님·가족과 함께 받고 싶은 분", "친구와 동반 예약을 원하는 분"],
     "diff": "두 분이 누울 공간이 필요하며, 공간이 좁으면 순차 진행으로 안내드립니다. 사전 예약을 권장합니다."},
    {"slug": "24h", "name": "24시간", "kicker": "24 HOURS",
     "summary": "심야에도 상담·방문이 가능한 24시간 운영 안내입니다.",
     "intro": "24시간 안내는 연중무휴로 운영되는 예약 상담과 심야 방문 가능 여부에 대한 안내입니다. 늦은 시간에도 연락 주시면 가능 여부를 확인해 드립니다.",
     "detail": "24시간 안내는 시간대에 구애받지 않고 상담과 방문을 운영하는 방식에 대한 것입니다. 퇴근이 늦거나 일정이 갑자기 비는 날에도 연락 주시면 가능 여부를 확인해 드립니다. 다만 심야·새벽은 위치에 따라 도착 시간이 길어질 수 있어 미리 안내드립니다.",
     "fit": ["퇴근·일정이 늦어 심야에 받고 싶은 분", "당일·즉시 예약이 필요한 분"],
     "diff": "상담은 24시간 가능하나, 심야는 위치에 따라 도착 시간이 길어질 수 있어 상담 시 안내드립니다."},
    {"slug": "sleep", "name": "수면 가능", "kicker": "SLEEP",
     "summary": "받다가 잠들어도 편안하도록 진행하는 숙면 지향 관리입니다.",
     "intro": "수면 가능 안내는 받는 중 잠이 들어도 편안하도록 부드러운 압과 조용한 진행으로 이완에 집중하는 관리 방식입니다.",
     "detail": "수면 지향 관리는 강한 자극을 피하고 부드럽고 느린 동작으로 긴장을 천천히 가라앉힙니다. 조명과 소리를 낮춘 조용한 분위기에서 진행해, 받는 도중 잠이 들어도 괜찮습니다. 잠들기 전 루틴으로 활용하면 수면의 질을 높이는 데 도움이 됩니다.",
     "fit": ["잠들기 전 긴장을 풀고 싶은 분", "불면·얕은 잠으로 힘든 분", "조용한 분위기를 원하는 분"],
     "diff": "강한 자극보다 부드러운 이완 위주로 진행하며, 받다가 주무셔도 괜찮습니다."},
]

# ===========================================================================
# DATA MODEL — 코스
# ===========================================================================
COURSES = [
    {"slug": "fatigue", "kicker": "RELAX · 피로 회복", "name": "피로 회복 관리",
     "desc": "전신의 긴장을 부드럽게 풀어주는 스웨디시 계열 기본 관리입니다.",
     "prices": [("60분", "70,000원"), ("90분", "100,000원"), ("120분", "130,000원")]},
    {"slug": "aroma", "kicker": "AROMA · 아로마", "name": "아로마 관리",
     "desc": "블렌딩 오일을 사용해 향과 함께 심신을 이완하는 관리입니다.",
     "prices": [("60분", "80,000원"), ("90분", "110,000원"), ("120분", "140,000원")], "best": True},
    {"slug": "sports", "kicker": "SPORTS · 스포츠", "name": "스포츠 관리",
     "desc": "운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 관리입니다.",
     "prices": [("60분", "90,000원"), ("90분", "120,000원"), ("120분", "150,000원")]},
    {"slug": "hometai", "kicker": "HOME · 홈타이", "name": "홈타이 코스",
     "desc": "자택·숙소로 방문해 받는 타이·스트레칭 계열 방문 관리입니다.",
     "prices": [("60분", "80,000원"), ("90분", "110,000원"), ("120분", "140,000원")]},
    {"slug": "couple", "kicker": "COUPLE · 커플·가족", "name": "커플·가족 방문 관리",
     "desc": "두 분이 함께 같은 공간에서 동시에 받는 동반 관리입니다.",
     "prices": [("60분", "150,000원~"), ("90분", "200,000원~"), ("120분", "250,000원~")]},
    {"slug": "group", "kicker": "GROUP · 기업·단체", "name": "기업·단체 방문 관리",
     "desc": "워크숍·행사 등 단체 인원을 위한 사전 협의형 방문 관리입니다.",
     "prices": [("협의", "별도 견적"), ("협의", "별도 견적"), ("협의", "별도 견적")]},
]

# 코스별 기본 요금 (시간 기준 메뉴 — 메인/허브 공통)
TIME_PRICING = [
    {"name": "60분 코스", "price": "80,000", "dur": "60분", "desc": "기본 컨디션·릴랙스 케어"},
    {"name": "90분 코스", "price": "120,000", "dur": "90분", "desc": "아로마 포함 추천 구성", "best": True},
    {"name": "120분 코스", "price": "150,000", "dur": "120분", "desc": "전신 집중 프리미엄 케어"},
]

# 랜드마크 데이터 정규화 — 각 항목 끝의 '인근'/'일대'를 제거해 본문에서 '인근 인근' 중복 방지.
def _strip_lm(s):
    s = s.strip()
    for suf in (" 인근", " 일대"):
        if s.endswith(suf):
            s = s[:-len(suf)]
    return s.strip()

def _clean_lm(s):
    parts = [_strip_lm(p.strip()) for p in s.split(",")]
    return ", ".join(p for p in parts if p)

for _a in AREAS:
    for _d in _a["dongs"]:
        _d["landmarks"] = _clean_lm(_d["landmarks"])
STATION_DATA = {k: (v[0], v[1], _clean_lm(v[2]), v[3]) for k, v in STATION_DATA.items()}

# ---------------------------------------------------------------------------
# Shared CSS  (design system from BLUEPRINT.md — 다크 럭스 스파)
# ---------------------------------------------------------------------------
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0b0b0e;--surface:#13131a;--surface-2:#1a1a23;--line:rgba(255,255,255,.08);
  --text:#f3f3f5;--muted:#9a9aa3;--dim:#6c6c75;
  --gold:#d6b274;--rose:#e9b8a7;--copper:#c98a6b;
  --grad:linear-gradient(135deg,#f4d29c 0%,#e9b8a7 45%,#c98a6b 100%);
  --grad-soft:linear-gradient(135deg,rgba(244,210,156,.14),rgba(201,138,107,.06));
}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);line-height:1.65;letter-spacing:-.01em;
  font-family:"Pretendard","Apple SD Gothic Neo","Noto Sans KR",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  -webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}
.serif,.note-num,.step .n{font-family:"Cormorant Garamond","Noto Serif KR",Georgia,serif;font-weight:300;font-style:italic}
.grad{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}
section.block{padding:96px 0}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:11.5px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--gold);font-weight:700}
.pulse{width:7px;height:7px;border-radius:50%;background:var(--rose);box-shadow:0 0 0 0 rgba(233,184,167,.6);animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(233,184,167,.55)}70%{box-shadow:0 0 0 9px rgba(233,184,167,0)}100%{box-shadow:0 0 0 0 rgba(233,184,167,0)}}
h2.sec{font-size:clamp(28px,4vw,46px);letter-spacing:-.03em;font-weight:800;margin:14px 0 10px}
.sec-lead{color:var(--muted);max-width:660px;font-size:15px}
header{position:sticky;top:0;z-index:60;backdrop-filter:blur(14px);
  background:rgba(11,11,14,.78);border-bottom:1px solid var(--line)}
.nav{max-width:1240px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;gap:18px}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:18px;letter-spacing:-.02em}
.brand .mark{width:34px;height:34px;border-radius:10px;background:var(--grad);display:grid;place-items:center;
  color:#1a1208;font-weight:800;font-family:"Cormorant Garamond",serif;font-style:italic;font-size:20px}
.brand small{display:block;font-size:10.5px;letter-spacing:.12em;color:var(--gold);font-weight:700}
.menu{list-style:none;display:flex;align-items:center;gap:2px;margin-left:auto}
.menu>li{position:relative}
.menu>li>a{display:block;padding:10px 11px;font-size:13.5px;color:var(--text);border-radius:9px;font-weight:600}
.menu>li>a:hover{background:rgba(255,255,255,.05)}
.menu>li>a.active{color:var(--gold)}
.submenu{position:absolute;top:calc(100% + 6px);left:0;min-width:212px;list-style:none;padding:8px;
  background:linear-gradient(160deg,var(--surface),var(--surface-2));border:1px solid var(--line);
  border-radius:14px;box-shadow:0 20px 48px rgba(0,0,0,.45);opacity:0;visibility:hidden;transform:translateY(6px);
  transition:.22s;z-index:70;max-height:70vh;overflow:auto}
.menu>li:hover>.submenu,.menu>li:focus-within>.submenu{opacity:1;visibility:visible;transform:none}
.submenu li{position:relative}
.submenu li a{display:block;padding:9px 12px;font-size:13.5px;color:var(--muted);border-radius:9px}
.submenu li a:hover{background:rgba(255,255,255,.05);color:var(--text)}
.submenu li.has-sub>a::after{content:"›";float:right;color:var(--dim);font-weight:700}
.submenu .sub2{position:absolute;top:-9px;left:calc(100% + 7px);transform:translateX(6px);max-height:74vh}
.submenu li.has-sub:hover>.sub2,.submenu li.has-sub:focus-within>.sub2{opacity:1;visibility:visible;transform:none}
.cta-pill{margin-left:6px;padding:11px 16px!important;background:var(--grad);color:#1a1208!important;
  border-radius:999px;font-weight:800!important}
.toggle{display:none;margin-left:auto;background:none;border:1px solid var(--line);color:var(--text);
  font-size:20px;width:44px;height:44px;border-radius:11px;cursor:pointer}
.hero{position:relative;overflow:hidden;border-bottom:1px solid var(--line)}
.hero::before{content:"";position:absolute;inset:0;z-index:0;
  background:radial-gradient(60% 70% at 80% 10%,rgba(233,184,167,.16),transparent 60%),
             radial-gradient(50% 60% at 10% 90%,rgba(214,178,116,.12),transparent 60%),
             radial-gradient(40% 50% at 50% 50%,rgba(201,138,107,.08),transparent 70%)}
.hero-inner{position:relative;z-index:1;display:grid;grid-template-columns:1.12fr .88fr;gap:48px;
  align-items:center;max-width:1240px;margin:0 auto;padding:88px 24px}
.hero h1{font-size:clamp(34px,5.4vw,64px);font-weight:800;letter-spacing:-.038em;line-height:1.08;margin:18px 0}
.hero .lead{color:var(--muted);font-size:16px;max-width:520px;margin-bottom:26px}
.actions{display:flex;gap:12px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:8px;padding:14px 22px;border-radius:12px;font-weight:700;
  font-size:14.5px;transition:.25s;border:1px solid transparent}
.btn-primary{background:var(--grad);color:#1a1208}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 14px 34px rgba(201,138,107,.35)}
.btn-ghost{border-color:var(--line);color:var(--text)}
.btn-ghost:hover{border-color:rgba(244,210,156,.4);transform:translateY(-2px)}
.trust{margin-top:24px;display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--muted);font-size:13px}
.trust b{color:var(--text)}
.hero-visual{position:relative}
.glass{position:relative;z-index:2;border-radius:20px;padding:26px;
  background:linear-gradient(160deg,rgba(255,255,255,.06),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.12);backdrop-filter:blur(20px);transform:rotate(1.5deg)}
.glass h3{font-size:13px;color:var(--gold);letter-spacing:.04em;margin-bottom:14px}
.glass h3 b{display:block;font-size:21px;color:var(--text);letter-spacing:-.02em;margin-top:4px}
.book-row{display:flex;justify-content:space-between;padding:11px 0;border-top:1px solid var(--line);font-size:14px}
.book-row span:first-child{color:var(--muted)}
.bk{display:block;text-align:center;margin-top:16px;padding:13px;border-radius:12px;background:var(--grad);color:#1a1208;font-weight:800}
.floating{position:absolute;z-index:3;padding:11px 14px;border-radius:12px;font-size:12px;font-weight:600;
  background:linear-gradient(160deg,var(--surface),var(--surface-2));border:1px solid var(--line);
  box-shadow:0 14px 34px rgba(0,0,0,.4)}
.fl-1{top:-18px;left:-14px;transform:rotate(-4deg)}
.fl-2{bottom:-16px;right:-10px;transform:rotate(3deg)}
.fl-1 .dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#6fe3a1;margin-right:6px}
.marquee{overflow:hidden;border-bottom:1px solid var(--line);background:var(--surface)}
.marquee-track{display:flex;gap:0;white-space:nowrap;width:max-content;animation:scroll 34s linear infinite}
.marquee-track span{padding:14px 26px;color:var(--muted);font-size:13px;letter-spacing:.04em}
.marquee-track span::after{content:"·";margin-left:26px;color:var(--dim)}
@keyframes scroll{to{transform:translateX(-50%)}}
.grid{display:grid;gap:16px}
.g4{grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.g2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.card{padding:24px;border-radius:16px;border:1px solid var(--line);
  background:linear-gradient(135deg,var(--surface),var(--surface-2));transition:.3s}
.card:hover{transform:translateY(-4px);border-color:rgba(244,210,156,.28);box-shadow:0 18px 40px rgba(0,0,0,.3)}
.card .k{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);font-weight:700}
.card h3{margin:10px 0 8px;font-size:19px;font-weight:800}
.card p{color:var(--muted);font-size:14px}
.card .more{display:inline-block;margin-top:14px;color:var(--rose);font-size:13.5px;font-weight:700}
.card:hover .more{transform:translateX(4px)}
.note-card{display:flex;gap:22px;padding:26px 28px;border-radius:18px;position:relative;overflow:hidden;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));border:1px solid var(--line);transition:.3s}
.note-card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--grad);opacity:0;transition:.3s}
.note-card:hover::before{opacity:1}
.note-card:hover{transform:translateY(-2px);box-shadow:0 18px 44px rgba(0,0,0,.32);border-color:rgba(244,210,156,.28)}
.note-num{font-size:44px;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent;flex-shrink:0;line-height:1}
.note-title{font-size:18px;font-weight:800;margin-bottom:10px}
.note-text{max-width:660px}
.note-text p{margin:0 0 9px;color:#c8c8d0;font-size:14.5px;line-height:1.78}
.note-stack{display:flex;flex-direction:column;gap:14px}
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
.chip{padding:9px 14px;border-radius:999px;border:1px solid var(--line);background:var(--surface);
  font-size:12.5px;color:var(--muted)}
.chip b{color:var(--gold)}
.price-card{padding:24px;border-radius:16px;border:1px solid var(--line);position:relative;overflow:hidden;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));transition:.3s}
.price-card::after{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:var(--grad);opacity:.5}
.price-card:hover{transform:translateY(-3px);border-color:rgba(244,210,156,.3)}
.price-card.best{border-color:rgba(244,210,156,.45)}
.best-badge{position:absolute;top:14px;right:14px;font-size:10.5px;font-weight:800;letter-spacing:.1em;
  padding:5px 10px;border-radius:999px;background:var(--grad);color:#1a1208}
.price-card .k{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);font-weight:700}
.price-card h3{margin:8px 0 6px;font-size:20px;font-weight:800}
.price-card>p{color:var(--muted);font-size:13.5px;margin-bottom:14px}
.time-rows>div{display:flex;justify-content:space-between;padding:9px 0;border-top:1px solid var(--line);font-size:14px}
.time-rows span:last-child{font-weight:700}
.pmenu{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:28px}
.pmenu-card{position:relative;text-align:center;padding:36px 24px 26px;border-radius:18px;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));border:1px solid var(--line);transition:.3s}
.pmenu-card:hover{transform:translateY(-4px);border-color:rgba(244,210,156,.3);box-shadow:0 18px 42px rgba(0,0,0,.32)}
.pmenu-card.best{border-color:rgba(244,210,156,.5);box-shadow:0 16px 42px rgba(201,138,107,.2)}
.pmenu-name{font-weight:800;font-size:17px;margin-bottom:16px}
.pmenu-price{font-size:clamp(30px,4vw,40px);font-weight:800;letter-spacing:-.035em;line-height:1}
.pmenu-price span{font-size:15px;font-weight:600;color:var(--muted);margin-left:3px;letter-spacing:0}
.pmenu-dur{color:var(--gold);font-size:13px;font-weight:700;margin-top:10px}
.pmenu-desc{color:var(--muted);font-size:13.5px;margin:8px 0 22px}
.pmenu-btn{display:block;padding:13px;border-radius:11px;border:1px solid var(--line);font-weight:700;font-size:14px;transition:.25s}
.pmenu-btn:hover{border-color:rgba(244,210,156,.5);transform:translateY(-1px)}
.pmenu-card.best .pmenu-btn{background:var(--grad);color:#1a1208;border-color:transparent}
.pmenu-badge{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--grad);color:#1a1208;
  font-size:11.5px;font-weight:800;padding:5px 15px;border-radius:999px;box-shadow:0 6px 16px rgba(201,138,107,.35)}
.pmenu-note{margin-top:20px;color:var(--muted);font-size:13px}
.pmenu-note a{color:var(--gold);font-weight:700;white-space:nowrap}
@media(max-width:760px){.pmenu{grid-template-columns:1fr}}
details{border:1px solid var(--line);border-radius:14px;padding:0;margin-bottom:12px;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));overflow:hidden}
summary{list-style:none;cursor:pointer;padding:18px 22px;font-weight:700;font-size:15px;
  display:flex;justify-content:space-between;align-items:center;gap:14px}
summary::-webkit-details-marker{display:none}
summary span{color:var(--gold);font-size:22px;transition:.25s;flex-shrink:0}
details[open] summary span{transform:rotate(45deg)}
details>div{padding:0 22px 20px;color:var(--muted);font-size:14.5px;line-height:1.78}
.crumb{font-size:12.5px;color:var(--dim);padding:18px 0}
.crumb a{color:var(--muted)}
.crumb a:hover{color:var(--gold)}
.crumb b{color:var(--text)}
.review{padding:22px;border-radius:16px;border:1px solid var(--line);
  background:linear-gradient(135deg,var(--surface),var(--surface-2))}
.review .stars{color:var(--gold);font-size:13px;letter-spacing:2px}
.review p{margin:10px 0;font-size:14px;color:#c8c8d0;line-height:1.7}
.review .who{font-size:12.5px;color:var(--muted)}
.cta-band{position:relative;overflow:hidden;text-align:center;padding:88px 24px;border-top:1px solid var(--line)}
.cta-band::before{content:"";position:absolute;inset:0;background:radial-gradient(50% 80% at 50% 0%,rgba(233,184,167,.16),transparent 60%)}
.cta-band>div{position:relative}
.cta-band h2{font-size:clamp(26px,4vw,42px);font-weight:800;letter-spacing:-.03em}
.cta-band p{color:var(--muted);margin:12px 0 24px}
.site-footer{border-top:1px solid var(--line);background:var(--surface);padding:64px 0 36px;font-size:13.5px}
.footer-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:30px}
.footer-grid h4{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin-bottom:14px}
.footer-grid a{display:block;color:var(--muted);padding:5px 0}
.footer-grid a:hover{color:var(--text)}
.footer-brand b{font-size:17px}
.footer-brand p{color:var(--muted);margin-top:10px;max-width:280px;line-height:1.7}
.footer-ops{margin:34px 0;padding:22px;border-radius:14px;background:var(--grad-soft);
  border:1px solid var(--line);display:flex;flex-wrap:wrap;gap:14px 40px}
.footer-ops div b{color:var(--gold);display:block;font-size:11px;letter-spacing:.12em;margin-bottom:4px}
.company-info{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;color:var(--dim);font-size:12.5px;
  padding-top:24px;border-top:1px solid var(--line)}
.company-info b{color:var(--muted)}
.footer-policies{display:flex;flex-wrap:wrap;gap:8px 18px;margin:22px 0 14px}
.footer-policies a{color:var(--muted);font-size:12.5px}
.footer-bottom{color:var(--dim);font-size:12px;line-height:1.7;border-top:1px solid var(--line);padding-top:18px}
.legal-note{margin-top:8px;color:var(--dim)}
.byline{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:18px;color:var(--dim);font-size:12.5px}
.byline span{display:inline-flex;align-items:center}
.byline span+span::before{content:"·";margin-right:16px;color:var(--dim)}
.byline .au{color:var(--muted);font-weight:700}
.article{max-width:760px}
.data-box{margin:24px 0;padding:20px 22px;border-radius:14px;background:var(--grad-soft);border:1px solid var(--line)}
.data-box b{color:var(--gold);display:block;font-size:11px;letter-spacing:.14em;margin-bottom:8px;text-transform:uppercase}
.data-box p{color:var(--muted);font-size:13.5px;margin:0;line-height:1.8}
.lux-hero{position:relative;overflow:hidden;border-bottom:1px solid rgba(244,210,156,.14);
  background:radial-gradient(70% 120% at 88% -10%,rgba(233,184,167,.14),transparent 60%),
             linear-gradient(180deg,#0d1018,#0b0b0e);padding:54px 0 40px}
.lux-h1{font-size:clamp(28px,4.6vw,50px);font-weight:800;letter-spacing:-.03em;line-height:1.12;margin:14px 0 12px;color:#fff}
.lux-lead{color:#cfd2da;font-size:16.5px;line-height:1.8;max-width:760px}
.lux-body{background:linear-gradient(180deg,#0b0b0e,#0c0e15 40%,#0b0b0e)}
.lux-grid{display:grid;grid-template-columns:240px 1fr;gap:46px;align-items:start}
.toc{position:sticky;top:86px}
.toc-inner{border:1px solid rgba(244,210,156,.2);border-radius:16px;padding:18px 14px;
  background:linear-gradient(165deg,#10131f,#0a0c13);box-shadow:0 18px 40px rgba(0,0,0,.35)}
.toc-label{display:block;font-size:10.5px;letter-spacing:.2em;color:var(--gold);font-weight:800;text-transform:uppercase;margin:0 0 12px 8px}
.toc ul{list-style:none;margin:0;padding:0}
.toc li a{display:block;padding:8px 12px;font-size:13px;line-height:1.4;color:var(--muted);
  border-left:2px solid transparent;border-radius:0 8px 8px 0;transition:.2s}
.toc li a:hover{color:var(--text);background:rgba(255,255,255,.05)}
.toc li a.active{color:var(--gold);border-left-color:var(--gold);background:rgba(244,210,156,.09);font-weight:700}
.lux-main{min-width:0}
.lux-sec{position:relative;overflow:hidden;background:linear-gradient(165deg,#121626,#0c0e16);
  border:1px solid rgba(255,255,255,.08);border-radius:18px;padding:28px 32px;margin-bottom:18px}
.lux-sec::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--grad)}
.lux-sec h2{font-size:clamp(20px,2.5vw,27px);font-weight:800;letter-spacing:-.02em;margin:0 0 14px;color:#fff}
.lux-sec h3{color:var(--gold);font-size:16.5px;font-weight:800;margin:20px 0 7px}
.lux-sec p{color:#e4e5ec;font-size:15.5px;line-height:1.9;margin:0 0 12px}
.lux-sec>ul{margin:6px 0 14px;padding:0;list-style:none}
.lux-sec>ul li{position:relative;padding:8px 0 8px 22px;color:#e4e5ec;font-size:15px;line-height:1.65;
  border-bottom:1px solid rgba(255,255,255,.06)}
.lux-sec>ul li::before{content:"";position:absolute;left:3px;top:15px;width:6px;height:6px;border-radius:50%;background:var(--grad)}
.lux-sec>ul li:last-child{border-bottom:none}
.lux-sec a{color:var(--rose);font-weight:600;border-bottom:1px solid rgba(233,184,167,.4)}
.lux-sec a:hover{color:var(--gold);border-bottom-color:var(--gold)}
.lux-sec strong{color:#fff}
.lux-sec .grid{margin-top:6px}
.lux-main .data-box{margin:4px 0 0;background:linear-gradient(135deg,rgba(244,210,156,.12),rgba(201,138,107,.05));
  border:1px solid rgba(244,210,156,.22)}
@media(max-width:980px){
  .lux-grid{grid-template-columns:1fr;gap:14px}
  .toc{position:static}
  .toc-inner{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:12px 14px}
  .toc-label{margin:0 4px 0 2px}
  .toc ul{display:flex;flex-wrap:wrap;gap:6px}
  .toc li a{border-left:none;border:1px solid var(--line);border-radius:999px;padding:6px 13px;font-size:12px}
  .toc li a.active{background:var(--grad);color:#1a1208;border-color:transparent}
  .lux-sec{padding:22px 20px}
}
.call-fab{position:fixed;right:20px;bottom:20px;z-index:90;display:inline-flex;align-items:center;gap:9px;
  padding:14px 20px 14px 16px;border-radius:999px;color:#fff;font-weight:800;font-size:14.5px;letter-spacing:-.01em;
  background:linear-gradient(135deg,#ffa23c,#ff7a18 55%,#f4600a);
  box-shadow:0 12px 30px rgba(255,122,24,.5);transition:transform .25s,box-shadow .25s}
.call-fab:hover{transform:translateY(-3px);box-shadow:0 16px 38px rgba(255,122,24,.6)}
.call-fab::before{content:"";position:absolute;inset:0;border-radius:999px;border:2px solid #ff7a18;
  animation:fabpulse 1.8s ease-out infinite;pointer-events:none}
.call-fab-ic{position:relative;display:grid;place-items:center;width:26px;height:26px;
  transform-origin:60% 60%;animation:fabring 1.5s ease-in-out infinite}
.call-fab-ic svg{width:21px;height:21px;fill:#fff}
.call-fab-tx{position:relative;white-space:nowrap}
.call-fab-tx small{display:block;font-size:11px;font-weight:700;opacity:.92;letter-spacing:.01em}
@keyframes fabring{0%,62%,100%{transform:rotate(0)}8%,26%{transform:rotate(-15deg)}17%,35%{transform:rotate(15deg)}}
@keyframes fabpulse{0%{transform:scale(1);opacity:.7}100%{transform:scale(1.55);opacity:0}}
@media(max-width:560px){.call-fab{right:14px;bottom:14px;padding:14px}.call-fab-tx{display:none}}
@media(prefers-reduced-motion:reduce){.call-fab-ic,.call-fab::before{animation:none}}
.reveal{opacity:0;transform:translateY(20px);transition:.8s}
.reveal.in{opacity:1;transform:none}
#region,#process,#reviews,#about,#faq,.cta-band,.site-footer{content-visibility:auto;contain-intrinsic-size:auto 700px}
.card,.note-card,.review,.price-card{contain:layout style}
@media(hover:none){.glass,.floating{backdrop-filter:none}}
@media(prefers-reduced-motion:reduce){.marquee-track,.pulse{animation:none}.reveal{opacity:1;transform:none}}
@media(max-width:1100px){
  .toggle{display:block}
  .menu{position:fixed;inset:64px 0 auto 0;flex-direction:column;align-items:stretch;gap:2px;margin:0;
    padding:14px;background:var(--bg);border-bottom:1px solid var(--line);max-height:calc(100vh - 64px);
    overflow:auto;transform:translateY(-12px);opacity:0;visibility:hidden;transition:.25s}
  .menu.open{transform:none;opacity:1;visibility:visible}
  .menu>li>a{padding:13px 12px}
  .submenu,.submenu .sub2{position:static;opacity:1;visibility:visible;transform:none;box-shadow:none;
    background:transparent;border:none;padding:0 0 6px 12px;min-width:0;left:auto;top:auto;max-height:none}
  .submenu .sub2{padding-left:14px}
  .submenu li.has-sub>a::after{content:""}
  .cta-pill{text-align:center}
  .hero-inner{grid-template-columns:1fr;gap:36px}
  .hero-visual{max-width:420px}
  .footer-grid{grid-template-columns:1fr 1fr}
  .company-info{grid-template-columns:1fr 1fr}
}
@media(max-width:560px){
  .footer-grid,.company-info{grid-template-columns:1fr}
  .note-card{flex-direction:column;gap:12px}
  .hero-inner{padding:56px 24px}
}
"""

# ---------------------------------------------------------------------------
# Navigation  (top menu + dropdowns; 3단 중첩: 구·군→동 / 노선→역)
# 상단 메뉴는 핵심 키워드 1회 노출, 하위 메뉴는 지역명/역명만(키워드 반복 금지).
# ---------------------------------------------------------------------------
def menu_html(active):
    def li(key, href, label, sub=None, cta=False):
        cls = ' class="active"' if active == key else ""
        pop = ' aria-haspopup="true"' if sub else ""
        a = f'<a href="{href}"{cls}{pop}>{label}</a>'
        if cta:
            a = f'<a class="cta-pill" href="tel:{PHONE_TEL}">예약문의</a>'
        sub_html = ""
        if sub:
            parts = []
            for item in sub:
                if len(item) == 3:  # 3단(구·군→동 / 노선→역)
                    h, t, kids = item
                    kids_html = "".join(f'<li><a href="{kh}">{kt}</a></li>' for kh, kt in kids)
                    parts.append(
                        f'<li class="has-sub"><a href="{h}" aria-haspopup="true">{t}</a>'
                        f'<ul class="submenu sub2">{kids_html}</ul></li>')
                else:
                    h, t = item
                    parts.append(f'<li><a href="{h}">{t}</a></li>')
            sub_html = f'<ul class="submenu">{"".join(parts)}</ul>'
        return f"<li>{a}{sub_html}</li>"

    incheon_sub = [
        ("/incheon/", "인천 출장마사지 안내"),
        ("/incheon/hometai/", "인천 홈타이 안내"),
        ("/incheon/coverage/", "인천 전지역 방문 가능 안내"),
        ("/incheon/stations/", "인천 지하철역 인근 안내"),
        ("/incheon/hours/", "예약 가능 시간"),
        ("/course/guide/", "코스 선택 안내"),
        ("/incheon/checklist/", "이용 전 확인사항"),
        ("/incheon/safety/", "위생 및 안전 안내"),
        ("/incheon/faq/", "자주 묻는 질문"),
    ]
    area_sub = [("/incheon/area/", "인천 전체")]
    area_sub += [(f"/incheon/{a['slug']}/", a["name"],
                  [(f"/incheon/{a['slug']}/{d['slug']}/", d["name"]) for d in a["dongs"]])
                 for a in AREAS]
    station_sub = [("/incheon/stations/", "인천 지하철역 전체")]
    station_sub += [(f"/incheon/stations/line/{l['key']}/", l["name"],
                     [(f"/incheon/stations/{STATION_DATA[nm][0]}/", f"{nm}역")
                      for nm in LINE_STATIONS[l["key"]]])
                    for l in LINES]
    theme_sub = [("/theme/", "전체 테마")] + [(f"/theme/{t['slug']}/", t["name"]) for t in THEMES]
    course_sub = [("/course/", "전체 코스")] + [(f"/course/{c['slug']}/", c["name"]) for c in COURSES] + [
        ("/course/price/", "가격 안내"), ("/course/guide/", "코스 선택 가이드")]

    items = [
        li("home", "/", "홈"),
        li("incheon", "/incheon/", "인천 출장마사지", incheon_sub),
        li("area", "/incheon/area/", "지역별 안내", area_sub),
        li("stations", "/incheon/stations/", "지하철역별 안내", station_sub),
        li("theme", "/theme/", "테마별 안내", theme_sub),
        li("course", "/course/", "코스안내", course_sub),
        li("reservation", "/reservation/", "예약안내"),
        li("guide", "/guide/", "이용가이드"),
        li("magazine", "/magazine/", "매거진"),
        li("reviews", "/reviews/", "후기"),
        li("customer", "/customer/", "고객센터"),
        li("cta", "#", "", cta=True),
    ]
    return (
        '<header><nav class="nav" aria-label="주 메뉴">'
        f'<a class="brand" href="/" aria-label="{BRAND} 홈">'
        f'<span class="mark">{BRAND_MARK}</span><span>인천 세븐<small>출장마사지·홈타이</small></span></a>'
        '<button class="toggle" aria-expanded="false" aria-controls="primary-menu" aria-label="메뉴 열기">☰</button>'
        f'<ul id="primary-menu" class="menu">{"".join(items)}</ul>'
        "</nav></header>"
    )

# ---------------------------------------------------------------------------
# Footer  (지역명·역명 대량 나열 금지 — 구·군/노선/테마 대표만)
# ---------------------------------------------------------------------------
def footer_html():
    area_links = "".join(f'<a href="/incheon/{a["slug"]}/">{a["name"]}</a>' for a in AREAS)
    line_links = "".join(f'<a href="/incheon/stations/line/{l["key"]}/">{l["name"]}</a>' for l in LINES)
    return f"""<footer class="site-footer"><div class="wrap">
<div class="footer-grid">
  <div class="footer-brand">
    <b class="grad">{BRAND}</b>
    <p>인천 전지역(2군 8구) 출장마사지·홈타이 방문 건강관리 예약 안내입니다. 구·군별 지역과 지하철역 인근, 테마별 관리를 안내합니다.</p>
  </div>
  <div><h4>지역별 안내</h4>{area_links}<a href="/incheon/area/">전체 지역 보기</a></div>
  <div><h4>지하철역별</h4>{line_links}<a href="/incheon/stations/">역 전체 보기</a></div>
  <div><h4>안내</h4>
    <a href="/incheon/">인천 출장마사지</a><a href="/theme/">테마별 안내</a><a href="/course/">코스안내</a>
    <a href="/reservation/">예약안내</a><a href="/guide/">이용가이드</a>
    <a href="/magazine/">매거진</a><a href="/reviews/">후기</a><a href="/customer/">고객센터</a></div>
</div>
<div class="footer-ops">
  <div><b>운영 시간</b>{HOURS}</div>
  <div><b>전화 예약·상담</b><a href="tel:{PHONE_TEL}">{PHONE_DISP}</a></div>
</div>
<div class="company-info">
  <div><b>상호</b> {COMPANY['name']}</div>
  <div><b>대표</b> {COMPANY['ceo']}</div>
  <div><b>사업자등록번호</b> {COMPANY['biz_no']}</div>
  <div><b>주소</b> {COMPANY['addr']}</div>
  <div><b>통신판매업신고</b> {COMPANY['sales_no']}</div>
  <div><b>개인정보보호책임자</b> {COMPANY['privacy_officer']}</div>
</div>
<div class="footer-policies">
  <a href="/customer/#notice">공지사항</a><a href="/customer/#qna">자주 묻는 질문</a>
  <a href="/customer/#inquiry">1:1 문의</a><a href="/privacy/">개인정보처리방침</a>
  <a href="/terms/">이용약관</a><a href="/youth/">청소년보호정책</a>
</div>
<div class="footer-bottom">
  © 2026 {COMPANY['name']}. All rights reserved.
  <div class="legal-note">본 서비스는 의료 행위가 아닌 건강관리(이완·휴식) 목적의 방문 관리 서비스이며, 만 19세 이상 성인을 대상으로 합니다. 불법·퇴폐 행위는 일절 제공하지 않습니다.</div>
</div>
</div></footer>"""

# ---------------------------------------------------------------------------
# Shared JS  (idle-loaded)
# ---------------------------------------------------------------------------
JS = """
(function(){
  var t=document.querySelector('.toggle'),m=document.getElementById('primary-menu');
  if(t&&m){t.addEventListener('click',function(){
    var o=m.classList.toggle('open');t.setAttribute('aria-expanded',o);});}
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&m){m.classList.remove('open');}});
  function idle(fn){if('requestIdleCallback'in window){requestIdleCallback(fn,{timeout:1500});}else{setTimeout(fn,1);}}
  idle(function(){
    if(!('IntersectionObserver'in window)){document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('in');});return;}
    var io=new IntersectionObserver(function(es){es.forEach(function(e){
      if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12,rootMargin:'80px'});
    document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
    var secs=[].slice.call(document.querySelectorAll('.lux-sec')),
        links=[].slice.call(document.querySelectorAll('.toc a'));
    if(secs.length&&links.length){
      var spy=new IntersectionObserver(function(es){es.forEach(function(e){
        if(e.isIntersecting){var id=e.target.id;
          links.forEach(function(a){a.classList.toggle('active',a.getAttribute('href')==='#'+id);});}});
      },{rootMargin:'-35% 0px -55% 0px'});
      secs.forEach(function(s){spy.observe(s);});
    }
  });
})();
"""

# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------
def call_fab():
    phone_svg = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8c1.4 2.8 3.8 5.2 '
                 '6.6 6.6l2.2-2.2c.28-.28.68-.36 1.02-.24 1.12.37 2.33.57 3.58.57.55 0 1 .45 1 '
                 '1V20c0 .55-.45 1-1 1C10.4 21 3 13.6 3 4.4c0-.55.45-1 1-1h3.6c.55 0 1 .45 1 1 0 '
                 '1.25.2 2.46.57 3.58.12.34.04.74-.24 1.02l-2.2 2.2z"/></svg>')
    return (f'<a class="call-fab" href="tel:{PHONE_TEL}" aria-label="전화 예약 {PHONE_DISP}">'
            f'<span class="call-fab-ic">{phone_svg}</span>'
            f'<span class="call-fab-tx">전화 예약<small>{PHONE_DISP}</small></span></a>')

def page(path, title, desc, active, body, jsonld=None, og_type="website", noindex=False):
    canonical = BASE_URL + path
    robots = ("noindex,follow" if noindex else
              "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1")
    gbot = "noindex,follow" if noindex else "index,follow"
    ld = ""
    if jsonld:
        blocks = jsonld if isinstance(jsonld, list) else [jsonld]
        ld = "".join(
            '<script type="application/ld+json">'
            + json.dumps(b, ensure_ascii=False, separators=(",", ":")) + "</script>"
            for b in blocks)
    og_img = BASE_URL + "/assets/og-cover.jpg"
    # 사이트 소유확인 메타는 루트(메인)에만 출력 — 네이버/구글은 루트 URL을 확인
    verify = ""
    if path == "/":
        if NAVER_VERIFY:
            verify += f'\n<meta name="naver-site-verification" content="{NAVER_VERIFY}">'
        if GOOGLE_VERIFY:
            verify += f'\n<meta name="google-site-verification" content="{GOOGLE_VERIFY}">'
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b0b0e">
<meta name="format-detection" content="telephone=no">
<meta name="robots" content="{robots}">
<meta name="googlebot" content="{gbot}">{verify}
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="author" content="{COMPANY['name']} 운영팀">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="ko-KR" href="{canonical}">
<link rel="alternate" hreflang="x-default" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="ko_KR">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_img}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{BRAND} 매거진" href="{BASE_URL}/rss.xml">
<style>{CSS}</style>
{ld}
</head>
<body>
{menu_html(active)}
{body}
{footer_html()}
{call_fab()}
<script>{JS}</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Reusable body builders
# ---------------------------------------------------------------------------
def write(path, html):
    if path == "/":
        out = os.path.join(ROOT, "index.html")
    else:
        d = os.path.join(ROOT, path.strip("/"))
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

def breadcrumb(items):
    parts = []
    for href, label in items:
        parts.append(f'<a href="{href}">{label}</a>' if href else f"<b>{label}</b>")
    return f'<div class="wrap"><nav class="crumb" aria-label="탐색경로">{" › ".join(parts)}</nav></div>'

def bc_ld(trail):
    el = []
    for i, (p, n) in enumerate(trail):
        item = {"@type": "ListItem", "position": i + 1, "name": n}
        if p:
            item["item"] = BASE_URL + p
        el.append(item)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": el}

def faq_block(qas, heading="자주 묻는 질문"):
    rows = "".join(
        f"<details><summary>{q}<span>+</span></summary><div>{a}</div></details>"
        for q, a in qas)
    return f"""<section class="block" id="faq"><div class="wrap">
<span class="eyebrow"><span class="pulse"></span>FAQ</span>
<h2 class="sec">{heading}</h2>
<div style="margin-top:26px;max-width:820px">{rows}</div>
</div></section>"""

def faq_ld(qas):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qas]}

def notes_block(eyebrow, heading, lead, notes, _id="about"):
    cards = "".join(
        f'<div class="note-card reveal"><div class="note-num">{n:02d}</div>'
        f'<div class="note-content"><h3 class="note-title">{t}</h3>'
        f'<div class="note-text">{"".join(f"<p>{p}</p>" for p in ps)}</div></div></div>'
        for n, (t, ps) in enumerate(notes, 1))
    return f"""<section class="block" id="{_id}"><div class="wrap">
<span class="eyebrow"><span class="pulse"></span>{eyebrow}</span>
<h2 class="sec">{heading}</h2>
<p class="sec-lead">{lead}</p>
<div class="note-stack" style="margin-top:30px">{cards}</div>
</div></section>"""

def price_menu_block(anchor="pricing-menu"):
    cards = ""
    for p in TIME_PRICING:
        best = " best" if p.get("best") else ""
        badge = '<span class="pmenu-badge">추천</span>' if p.get("best") else ""
        cards += (f'<div class="pmenu-card{best}">{badge}'
                  f'<div class="pmenu-name">{p["name"]}</div>'
                  f'<div class="pmenu-price">{p["price"]}<span>원</span></div>'
                  f'<div class="pmenu-dur">{p["dur"]}</div>'
                  f'<div class="pmenu-desc">{p["desc"]}</div>'
                  f'<a class="pmenu-btn" href="tel:{PHONE_TEL}">예약 문의</a></div>')
    return (f'<section class="block" id="{anchor}"><div class="wrap">'
            f'<span class="eyebrow"><span class="pulse"></span>요금 안내</span>'
            f'<h2 class="sec">코스별 기본 요금</h2>'
            f'<p class="sec-lead">60·90·120분 코스별 기본 요금입니다. 숨겨진 추가 비용 없이 투명하게 안내합니다.</p>'
            f'<div class="pmenu">{cards}</div>'
            f'<p class="pmenu-note">지역·예약 시간대·이동 거리에 따라 상담 시 최종 확인됩니다. '
            f'<a href="/course/price/">상세 요금 안내 보기 →</a></p>'
            f'</div></section>')

def offer_ld():
    return {"@context": "https://schema.org", "@type": "OfferCatalog", "name": "코스별 기본 요금",
            "itemListElement": [{"@type": "Offer", "name": p["name"],
                                 "price": p["price"].replace(",", ""), "priceCurrency": "KRW",
                                 "description": p["desc"], "url": BASE_URL + "/course/"}
                                for p in TIME_PRICING]}

def cta_band(title="가까운 곳에서 휴식을 예약하세요", sub=None):
    sub = sub or f"{HOURS} · 전화 한 통으로 방문 일정과 코스를 안내드립니다."
    return f"""<section class="cta-band"><div>
<span class="eyebrow"><span class="pulse"></span>RESERVE</span>
<h2>{title}</h2><p>{sub}</p>
<div class="actions" style="justify-content:center">
<a class="btn btn-primary" href="tel:{PHONE_TEL}">{PHONE_DISP} 전화하기 →</a>
<a class="btn btn-ghost" href="/reservation/">예약 안내 보기</a>
</div></div></section>"""

def byline():
    return (f'<div class="byline">'
            f'<span class="au">작성 · {BRAND} 운영팀</span>'
            f'<span>감수 · {COMPANY["ceo"]} ({COMPANY["name"]} 대표)</span>'
            f'<span>최종 업데이트 · {UPDATED.replace("-", ".")}</span></div>')

def article_ld(title, desc, path):
    return {"@context": "https://schema.org", "@type": "Article",
            "headline": title, "description": desc, "inLanguage": "ko-KR",
            "author": {"@type": "Organization", "name": BRAND, "url": BASE_URL + "/incheon/"},
            "publisher": {"@type": "Organization", "name": COMPANY["name"], "url": BASE_URL + "/"},
            "mainEntityOfPage": BASE_URL + path,
            "image": BASE_URL + "/assets/og-cover.jpg",
            "datePublished": UPDATED, "dateModified": UPDATED}

def render_lux(sections):
    """다크 럭스 섹션 패널 + 좌측 고정 목차(TOC).
    sections: [(title,[블록...])] 블록: 문자열(문단)/("ul",[…])/("h3","…")/("html","원본")."""
    toc, panels = [], []
    for i, (title, blocks) in enumerate(sections, 1):
        sid = f"sec-{i}"
        toc.append(f'<li><a href="#{sid}">{title}</a></li>')
        inner = ""
        for b in blocks:
            if isinstance(b, tuple) and b[0] == "ul":
                inner += "<ul>" + "".join(f"<li>{x}</li>" for x in b[1]) + "</ul>"
            elif isinstance(b, tuple) and b[0] == "h3":
                inner += f"<h3>{b[1]}</h3>"
            elif isinstance(b, tuple) and b[0] == "html":
                inner += b[1]
            else:
                inner += f"<p>{b}</p>"
        panels.append(f'<section class="lux-sec reveal" id="{sid}"><h2>{title}</h2>{inner}</section>')
    toc_html = ('<aside class="toc"><div class="toc-inner"><span class="toc-label">목차</span>'
                f'<ul>{"".join(toc)}</ul></div></aside>')
    return toc_html, "".join(panels)

def org_ld():
    return {"@context": "https://schema.org", "@type": "Organization",
            "name": BRAND, "legalName": COMPANY["name"], "url": BASE_URL + "/",
            "telephone": PHONE_DISP,
            "address": {"@type": "PostalAddress", "addressLocality": "인천광역시",
                        "addressRegion": "인천광역시", "addressCountry": "KR"}}

def website_ld():
    return {"@context": "https://schema.org", "@type": "WebSite",
            "name": BRAND, "url": BASE_URL + "/",
            "potentialAction": {"@type": "SearchAction",
                "target": BASE_URL + "/?q={search_term_string}",
                "query-input": "required name=search_term_string"}}

def localbiz_ld(name=None, area="인천광역시", path="/"):
    return {"@context": "https://schema.org", "@type": "HealthAndBeautyBusiness",
            "name": name or BRAND, "url": BASE_URL + path,
            "telephone": PHONE_DISP, "priceRange": "₩₩",
            "areaServed": {"@type": "AdministrativeArea", "name": area},
            "address": {"@type": "PostalAddress", "addressLocality": "인천광역시",
                        "addressRegion": "인천광역시", "addressCountry": "KR"},
            "openingHoursSpecification": {"@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
                "opens": "00:00", "closes": "23:59"}}

def service_ld(name, desc, path):
    return {"@context": "https://schema.org", "@type": "Service",
            "name": name, "description": desc, "serviceType": "방문 건강관리(마사지) 서비스",
            "provider": {"@type": "Organization", "name": BRAND, "url": BASE_URL + "/"},
            "areaServed": {"@type": "AdministrativeArea", "name": "인천광역시"},
            "url": BASE_URL + path}

def content_page(path, active, trail, *, title, desc, eyebrow, h1, lead,
                 sections, faq, data_note=None, service=None, show_price=False,
                 top_links=None, extra_schema=None, cta_title=None):
    """E-E-A-T 기준 개별 콘텐츠 페이지 (다크 럭스 레이아웃 + TOC)."""
    toc_html, panels = render_lux(sections)
    if data_note:
        panels += f'<div class="data-box"><b>현장 운영 메모</b><p>{data_note}</p></div>'
    links_html = ""
    if top_links:
        btns = ""
        for href, label, *rest in top_links:
            primary = rest and rest[0]
            cls = "btn btn-primary" if primary else "btn btn-ghost"
            btns += f'<a class="{cls}" href="{href}">{label}</a>'
        links_html = f'<div class="actions" style="margin-top:22px">{btns}</div>'
    body = (breadcrumb(trail) +
        f'<section class="lux-hero"><div class="wrap">'
        f'<span class="eyebrow"><span class="pulse"></span>{eyebrow}</span>'
        f'<h1 class="lux-h1">{h1}</h1>'
        f'<p class="lux-lead">{lead}</p>{byline()}{links_html}</div></section>'
        f'<section class="block lux-body" style="padding-top:34px"><div class="wrap">'
        f'<div class="lux-grid">{toc_html}<div class="lux-main">{panels}</div></div>'
        f'</div></section>'
        + (price_menu_block() if show_price else "")
        + faq_block(faq) + (cta_band(cta_title) if cta_title else cta_band()))
    jsonld = [bc_ld(trail), article_ld(title, desc, path), faq_ld(faq)]
    if service:
        jsonld.append(service_ld(service[0], service[1], path))
        jsonld.append(offer_ld())
    if extra_schema:
        jsonld += extra_schema
    # 도어웨이/얇은 콘텐츠 방지: 본문 2,000자 미만은 Noindex 처리(전용 규칙)
    import re as _re
    main_txt = _re.sub(r"\s+", " ", _re.sub(r"<[^>]+>", " ", body)).strip()
    noindex = len(main_txt) < THIN_THRESHOLD
    if noindex:
        THIN_PAGES.append((len(main_txt), path))
    write(path, page(path, title, desc, active, body, jsonld, og_type="article", noindex=noindex))

# ---------------------------------------------------------------------------
# 변형 헬퍼 — title/description/본문 섹션을 페이지별로 다양화(중복·복사·유사 방지).
# 슬러그 해시로 결정적 회전 → 빌드마다 동일하지만 페이지마다 다른 변형을 선택.
# ---------------------------------------------------------------------------
def _h(key):
    return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)

def hpick(key, seq):
    return seq[_h(key) % len(seq)]

def hsubset(key, seq, k):
    n = len(seq); start = _h(key) % n
    return [seq[(start + i) % n] for i in range(k)]

def short_lm(landmarks):
    first = landmarks.split(",")[0].strip()
    return first.replace(" 인근", "").replace(" 일대", "")

def station_lm(NM, landmarks):
    """역명 자체와 겹치지 않는 첫 랜드마크(예: 송도역→옥련동)."""
    items = [p.strip() for p in landmarks.split(",") if p.strip()]
    for it in items:
        base = it.replace(" 인근", "").replace(" 일대", "")
        if base not in (NM, NM + "역") and not base.startswith(NM + "역"):
            return base
    return short_lm(landmarks)

# 본문 테마 링크 회전용 풀(마사지 성격 테마 위주)
THEME_LINK_POOL = [(t["slug"], t["name"]) for t in THEMES
                   if t["slug"] in ("swedish", "aroma", "thai", "sports", "homecare",
                                    "hotel", "lomi", "foot", "chinese", "sleep")]

def theme_links_block(key, intro_subject):
    """페이지별로 다른 테마 3개를 노출하는 (인트로문장, ul항목들) 반환."""
    picks = hsubset(key, THEME_LINK_POOL, 3)
    names = "·".join(n for _, n in picks)
    intro = f"{intro_subject}에서는 {names} 등 방문 관리 문의가 많습니다. 원하는 테마와 코스는 아래에서 확인하세요."
    ul = ['<a href="/theme/">전체 테마 보기</a>']
    ul += [f'<a href="/theme/{s}/">{n}</a>' for s, n in picks]
    ul += ['<a href="/course/">코스안내</a>', '<a href="/course/price/">가격 안내</a>']
    return intro, ul

# ---- 구·군 title/desc ----
def gu_title(N):
    return hpick(N, [
        f"{N} 출장마사지·홈타이 | 인천 {N} 방문 마사지 예약",
        f"인천 {N} 출장마사지·홈타이 — {N} 전역 방문 예약 안내",
        f"{N} 홈타이·출장마사지 방문 예약 | 인천 {N} 건강관리",
    ])

def gu_desc(N, dongs, summary):
    names = ", ".join(d["name"] for d in dongs[:5])
    return hpick(N, [
        f"{N} 출장마사지·홈타이 안내 - {names} 등 대표 동 방문 건강관리 예약 안내입니다. {summary}",
        f"인천 {N} 출장마사지·홈타이 예약 안내. {summary} {names} 등 대표 동으로 방문합니다.",
        f"{N} 홈타이·출장마사지 방문 예약 - {summary} {names} 일대를 안내합니다.",
    ])

# ---- 동 title/desc/lead ----
def dong_title(N, G, lm):
    L = short_lm(lm)
    return hpick(N + G, [
        f"{N} 출장마사지·홈타이 | 인천 {G} {N} 방문 예약 안내",
        f"인천 {G} {N} 출장마사지·홈타이 예약 — {N} 방문 마사지",
        f"{N} 홈타이·출장마사지 | 인천 {G} {N} 방문 건강관리",
        f"인천 {N} 출장마사지·홈타이 — {G} {N} 방문 예약",
        f"{L} 인근 {N} 출장마사지·홈타이 | 인천 {G} 방문",
        f"{N} 출장마사지·홈타이 방문 예약 | 인천 {G} {L} 일대",
    ])

def dong_desc(N, G, C, lm, A):
    L = short_lm(lm)
    return hpick(N + lm, [
        f"인천 {G} {N} 출장마사지·홈타이 예약 안내입니다. {N}은 {C}입니다. {L} 인근 자택·숙소로 평균 {A}분 내외 방문하며 코스·요금·예약 시간을 안내합니다.",
        f"{N} 출장마사지·홈타이 — {C}인 {N} 일대를 {L} 중심으로 방문하는 건강관리 예약 안내입니다. 60·90·120분 코스와 도착 시간을 확인해보세요.",
        f"인천 {N}({G}) 출장마사지·홈타이 안내. {N}은 {C}이며, {L} 인근 생활권으로 평균 {A}분 내외 방문합니다.",
        f"{N} 홈타이·출장마사지 방문 예약. {C}인 {N}을 {L} 인근까지 안내하며, 코스 선택과 위생·안전 기준을 확인하실 수 있습니다.",
        f"인천 {G} {L} 인근 {N} 출장마사지·홈타이 방문 예약 안내. {C}인 {N}까지 평균 {A}분 내외로 자택·숙소·오피스텔로 방문합니다.",
    ])

def dong_lead(N, G, C, lm, A):
    L = short_lm(lm)
    return hpick(N, [
        f"인천 {G} {N}({C})에서 출장마사지·홈타이 예약을 찾는 분들을 위한 안내입니다. {N}은 {L} 인근 생활권과 가까워 자택·숙소·오피스텔 방문 문의가 많으며, 평균 {A}분 내외로 도착합니다.",
        f"{C}인 {N}은 {L} 인근을 중심으로 인천 {G} 출장마사지·홈타이를 방문 안내합니다. 평균 {A}분 내외로 도착하며, 코스와 예약 시간을 함께 확인하실 수 있습니다.",
        f"인천 {G} {N} 일대로 방문하는 출장마사지·홈타이 예약 안내입니다. {C}인 {N}을 {L} 인근까지 평균 {A}분 내외로 방문합니다.",
    ])

# ---- 역 title/desc/lead ----
def station_title(NM, G, line_short_list, transfer, lm):
    L = station_lm(NM, lm); LS = line_short_list[0]
    tag = "환승역" if transfer else f"{LS} 역세권"
    return hpick(NM + G, [
        f"{NM}역 출장마사지·홈타이 | 인천 {G} {L} 인근 방문 예약",
        f"인천 {G} {NM}역 출장마사지·홈타이 — {tag} 방문 안내",
        f"{NM}역 홈타이·출장마사지 | 인천 {G} {L} 인근 예약",
        f"인천 {NM}역 출장마사지·홈타이 — {G} 역세권 예약 안내",
        f"{NM}역({tag}) 출장마사지·홈타이 | 인천 {G} 방문",
        f"{L} 인근 {NM}역 출장마사지·홈타이 | 인천 {G} 예약",
    ])

def station_desc(NM, G, line_names, transfer, lm, A):
    L = station_lm(NM, lm); lines = "·".join(line_names)
    tw = " 환승역" if transfer else ""
    return hpick(NM + lm, [
        f"{NM}역 출장마사지·홈타이 안내입니다. {lines}{tw} {NM}역 인근({L}) 자택·숙소로 평균 {A}분 내외 방문하며 코스·예약 시간을 안내합니다.",
        f"인천 {G} {NM}역 출장마사지·홈타이 예약 — {L} 인근 역세권으로 방문합니다. {lines} 인근 방문과 60·90·120분 코스를 확인하세요.",
        f"{NM}역 홈타이·출장마사지 방문 예약 안내. 인천 {G} {NM}역({L}) 생활권으로 평균 {A}분 내외 방문하며 위생·요금 기준을 확인하실 수 있습니다.",
        f"인천 {G} {L} 인근 {NM}역 출장마사지·홈타이 방문 예약. {lines} 역세권 자택·오피스텔·숙소로 평균 {A}분 내외 안내합니다.",
        f"{NM}역세권({L}) 출장마사지·홈타이 안내 — 인천 {G}에서 {lines} {NM}역 인근을 평균 {A}분 내외로 방문합니다.",
    ])

def station_lead(NM, G, line_sentence, lm, A):
    L = station_lm(NM, lm)
    return hpick(NM, [
        f"{NM}역 인근에서 출장마사지·홈타이 예약을 찾는 분들을 위한 안내입니다. {line_sentence} {L} 인근 생활권으로 평균 {A}분 내외로 방문합니다.",
        f"인천 {G} {NM}역세권({L} 일대)으로 방문하는 출장마사지·홈타이 예약 안내입니다. {line_sentence} 평균 {A}분 내외로 도착합니다.",
        f"{line_sentence} {NM}역 인근 {L} 생활권으로 출장마사지·홈타이를 방문 안내하며, 평균 {A}분 내외로 도착합니다.",
    ])

# ---- 노선 title ----
def line_title(LN):
    return hpick(LN, [
        f"{LN} 역세권 | 인천 출장마사지·홈타이 방문 안내",
        f"인천 출장마사지·홈타이 — {LN} 역세권 방문 예약",
        f"{LN} 출장마사지·홈타이 | 역세권 인근 방문 안내",
    ])

# ===========================================================================
# PAGE BUILDERS
# ===========================================================================
HOME_FAQ = [
    ("인천 전지역 어디까지 방문 가능한가요?",
     "강화군·옹진군 2개 군과 중구·동구·미추홀구·연수구·남동구·부평구·계양구·서구 8개 구 등 인천 전지역을 안내드립니다. 도서·외곽 지역은 시간대와 위치에 따라 방문 가능 여부를 상담 시 확인해 드립니다."),
    ("지하철역 근처도 예약할 수 있나요?",
     "인천1호선·인천2호선·1호선·7호선·수인분당선·공항철도 인천권 주요 역 인근으로 방문합니다. 역 인근 위치를 알려주시면 가까운 생활권 기준으로 안내드립니다."),
    ("당일 예약도 가능한가요?",
     "가능합니다. 다만 시간대와 위치에 따라 방문 가능 시간이 달라질 수 있어 상담 시 확인해 드립니다."),
    ("테마는 어떻게 선택하나요?",
     "스웨디시·아로마테라피·타이마사지·스포츠·홈케어 등 원하는 테마를 말씀해 주시면 컨디션과 목적에 맞춰 안내드립니다."),
    ("예약 전 무엇을 준비하면 되나요?",
     "방문 장소의 정확한 주소와 출입 방법, 연락 가능한 번호, 희망 코스와 시간을 미리 정리해 두시면 빠르게 진행됩니다."),
    ("이 서비스는 의료 행위인가요?",
     "아닙니다. 본 서비스는 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상 성인을 대상으로 합니다."),
]

def build_home():
    services = "".join(
        f'<a class="card reveal" href="/course/{c["slug"]}/"><div class="k">{c["kicker"]}</div>'
        f'<h3>{c["name"]}</h3><p>{c["desc"]}</p><span class="more">자세히 →</span></a>'
        for c in COURSES[:4])
    areas = "".join(
        f'<a class="card reveal" href="/incheon/{a["slug"]}/"><div class="k">{a["kind"]}</div>'
        f'<h3>{a["name"]}</h3><p>{a["summary"]}</p><span class="more">지역 보기 →</span></a>'
        for a in AREAS)
    lines = "".join(
        f'<a class="card reveal" href="/incheon/stations/line/{l["key"]}/"><div class="k">LINE</div>'
        f'<h3>{l["name"]}</h3><p>{l["short"]} 인근 역세권 방문 안내</p>'
        f'<span class="more">노선 보기 →</span></a>'
        for l in LINES)
    themes = "".join(
        f'<a class="card reveal" href="/theme/{t["slug"]}/"><div class="k">{t["kicker"]}</div>'
        f'<h3>{t["name"]}</h3><p>{t["summary"]}</p><span class="more">테마 보기 →</span></a>'
        for t in THEMES[:8])
    steps = [
        ("위치 확인", "지역 또는 역 인근 위치를 확인합니다."),
        ("시간 확인", "희망하시는 방문 시간을 확인합니다."),
        ("코스·인원", "원하는 코스와 인원을 확인합니다."),
        ("방문 안내", "방문 가능 여부를 안내하고 예약을 확정합니다."),
    ]
    steps_html = "".join(
        f'<div class="card reveal"><div class="k step"><span class="n serif">{i:02d}</span></div>'
        f'<h3>{t}</h3><p>{d}</p></div>' for i, (t, d) in enumerate(steps, 1))
    reviews = [
        ("부평동 · 30대", "늦은 시간에 연락했는데 도착 시간을 정확히 안내해 주셔서 좋았습니다."),
        ("송도동 · 40대", "아로마 관리 후 컨디션이 한결 가벼워졌어요. 응대가 정중했습니다."),
        ("구월동 · 30대", "예약부터 마무리까지 깔끔했고 위생 안내가 꼼꼼했습니다."),
    ]
    reviews_html = "".join(
        f'<div class="review reveal"><div class="stars">★★★★★</div><p>“{q}”</p>'
        f'<div class="who">{w}</div></div>' for w, q in reviews)
    marquee_items = ["연중무휴 24시간 상담", "인천 전지역 2군 8구", "당일 예약 가능",
                     "역세권 방문", "홈타이·방문 관리", "위생·안전 관리", "정찰 요금 안내"]
    marquee = "".join(f"<span>{x}</span>" for x in marquee_items * 2)
    safety_notes = [
        ("이용 전 확인사항",
         ["방문 장소의 정확한 주소와 공동현관 출입 방법, 주차 가능 여부를 알려주시면 도착이 빨라집니다.",
          "조용히 쉴 수 있는 공간과 예약자 본인 연락 가능 여부를 함께 확인해 주세요."]),
        ("위생 및 안전 안내",
         ["수건·오일 등 용품은 위생 기준에 맞춰 관리하며, 개인정보는 예약 목적으로만 이용합니다.",
          "불법·퇴폐 행위는 일절 제공하지 않으며, 건전한 건강관리 서비스로 운영합니다."]),
    ]
    body = f"""
<section class="hero"><div class="hero-inner">
  <div class="hero-copy">
    <span class="eyebrow"><span class="pulse"></span>INCHEON · 2군 8구 · 24H</span>
    <h1>인천 출장마사지·홈타이,<br><span class="grad">전지역</span> <span class="serif">방문 예약 안내.</span></h1>
    <p class="lead">부평·주안·송도·구월·계양·청라부터 영종·강화까지 — 인천 전지역 방문 건강관리 예약을 연중무휴로 안내드립니다.</p>
    <div class="actions">
      <a class="btn btn-primary" href="tel:{PHONE_TEL}">지금 예약하기 →</a>
      <a class="btn btn-ghost" href="/incheon/area/">지역별 안내</a>
    </div>
    <div class="trust">
      <span>★★★★★ <b>4.9</b> · 후기 다수</span><span>·</span>
      <span><b>{HOURS}</b></span><span>·</span><span>인천 <b>2군 8구</b> 방문</span>
    </div>
  </div>
  <div class="hero-visual">
    <div class="floating fl-1"><span class="dot"></span>LIVE · 방금 송도동 예약</div>
    <div class="glass">
      <h3>SIGNATURE<b>아로마 딥 릴렉스</b></h3>
      <div class="book-row"><span>지역</span><span>인천 전지역</span></div>
      <div class="book-row"><span>코스</span><span>아로마 90분</span></div>
      <div class="book-row"><span>예약</span><span>{HOURS}</span></div>
      <a class="bk" href="tel:{PHONE_TEL}">전화 예약 →</a>
    </div>
    <div class="floating fl-2">CUSTOMER RATING · ★ 4.9</div>
  </div>
</div></section>

<div class="marquee" aria-hidden="true"><div class="marquee-track">{marquee}</div></div>

<section class="block"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>SERVICE</span>
  <h2 class="sec">인천 출장마사지·홈타이 서비스 안내</h2>
  <p class="sec-lead">고객이 계신 곳으로 방문하는 건강관리 예약 서비스입니다. 컨디션과 목적에 맞춰 코스를 고르실 수 있습니다.</p>
  <div class="grid g4" style="margin-top:28px">{services}</div>
</div></section>

{price_menu_block()}

<section class="block" id="region"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>SERVICE AREA</span>
  <h2 class="sec">인천 전지역 방문 가능 안내</h2>
  <p class="sec-lead">현재 2군 8구 기준으로 안내하며, 2026년 7월 행정체제 개편(제물포구·영종구·검단구 출범) 예정도 함께 준비하고 있습니다. 구·군을 눌러 지역별 안내를 확인하세요.</p>
  <div class="grid g3" style="margin-top:28px">{areas}</div>
</div></section>

<section class="block"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>STATION</span>
  <h2 class="sec">지하철역 인근 안내</h2>
  <p class="sec-lead">대표역 — 부평역·주안역·송도역·인천시청역·계양역·검암역·인천공항1터미널역 등 역세권 인근으로 방문합니다.</p>
  <div class="grid g3" style="margin-top:28px">{lines}</div>
</div></section>

<section class="block"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>THEME</span>
  <h2 class="sec">테마별 관리 안내</h2>
  <p class="sec-lead">스웨디시·타이마사지·아로마테라피·홈케어·호텔식·스포츠·경락 등 원하는 테마를 선택하세요.</p>
  <div class="grid g4" style="margin-top:28px">{themes}</div>
  <div class="chips"><span class="chip">지역+역+테마 조합 페이지는 만들지 않습니다 — <b>각 항목을 분리</b>해 안내합니다.</span></div>
</div></section>

<section class="block" id="process"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>HOW IT WORKS</span>
  <h2 class="sec">예약은 이렇게 진행됩니다</h2>
  <div class="grid g4" style="margin-top:28px">{steps_html}</div>
</div></section>

<section class="block" id="reviews"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>CLIENT VOICES</span>
  <h2 class="sec">고객 후기</h2>
  <div class="grid g3" style="margin-top:28px">{reviews_html}</div>
</div></section>

{notes_block("SAFETY", "이용 전 확인 · 위생 및 안전", "안심하고 받으실 수 있도록 미리 확인하고 운영하는 기준입니다.", safety_notes)}

{faq_block(HOME_FAQ)}

{cta_band()}
"""
    jsonld = [org_ld(), website_ld(), localbiz_ld(), offer_ld(), faq_ld(HOME_FAQ)]
    write("/", page("/",
        "인천 출장마사지·홈타이 | 인천 전지역 방문 마사지 예약 안내",
        "인천 출장마사지·홈타이 안내 페이지입니다. 인천 전지역, 구·군별 지역, 지하철역 인근, 테마별 관리와 예약 전 확인사항을 한눈에 확인해보세요.",
        "home", body, jsonld))

# ---- 인천 출장마사지 대표 랜딩 -------------------------------------------
def build_incheon():
    trail = [("/", "홈"), (None, "인천 출장마사지")]
    area_cards = "".join(
        f'<a class="card reveal" href="/incheon/{a["slug"]}/"><div class="k">{a["kind"]}</div>'
        f'<h3>{a["name"]}</h3><p>{a["summary"]}</p><span class="more">지역 보기 →</span></a>'
        for a in AREAS)
    course_cards = "".join(
        f'<a class="card reveal" href="/course/{c["slug"]}/"><div class="k">{c["kicker"]}</div>'
        f'<h3>{c["name"]}</h3><p>{c["desc"]}</p><span class="more">코스 보기 →</span></a>'
        for c in COURSES[:4])
    intro = notes_block("INTRO", "인천 출장마사지·홈타이 안내",
        "인천 전지역을 대상으로 하는 방문 건강관리 예약 안내입니다.",
        [("인천 전지역 방문 안내",
          ["인천 세븐 마사지는 강화군·옹진군 2개 군과 8개 구 등 인천 전지역으로 방문하는 출장마사지·홈타이 예약을 안내합니다.",
           "고객이 계신 자택·오피스텔·숙소로 방문해 이동 없이 받으실 수 있는 방문형 관리입니다."])],
        _id="intro")
    area_section = (
        '<section class="block" id="area"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>SERVICE AREA</span>'
        '<h2 class="sec">인천 전지역 방문 가능 안내</h2>'
        '<p class="sec-lead">2군 8구 기준으로 안내합니다. 구·군을 눌러 대표 동별 안내를 확인하세요.</p>'
        f'<div class="grid g3" style="margin-top:26px">{area_cards}</div></div></section>')
    course_section = (
        '<section class="block" id="course"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>POPULAR COURSE</span>'
        '<h2 class="sec">많이 찾는 관리 코스</h2>'
        '<p class="sec-lead">컨디션과 목적에 맞춰 고를 수 있는 대표 코스입니다.</p>'
        f'<div class="grid g4" style="margin-top:26px">{course_cards}</div></div></section>')
    station_notes = notes_block("STATION", "지하철역 인근 안내",
        "역세권 인근으로도 방문합니다.",
        [("역세권 방문",
          ["인천1호선·인천2호선·1호선·7호선·수인분당선·공항철도 인천권 주요 역 인근으로 방문합니다.",
           "환승역은 여러 노선에 보이더라도 한 페이지로 안내합니다. 자세한 내용은 지하철역별 안내에서 확인하세요."])],
        _id="station")
    safety = notes_block("SAFETY", "위생 및 안전 안내",
        "안심하고 받으실 수 있도록 안내드립니다.",
        [("위생·안전", ["용품 위생 관리와 안전 가이드라인을 준수하며 개인정보는 예약 목적으로만 이용합니다.",
                     "본 서비스는 의료 행위가 아닌 건강관리 서비스이며 만 19세 이상을 대상으로 합니다."])],
        _id="safety")
    incheon_faq = [
        ("인천 출장마사지는 어디까지 가능한가요?", "강화군·옹진군과 8개 구 등 인천 전지역을 안내드립니다. 도서·외곽은 시간대와 위치에 따라 확인해 드립니다."),
        ("당일 예약도 가능한가요?", "가능합니다. 다만 시간대와 위치에 따라 방문 가능 시간이 달라질 수 있어 상담 시 확인해 드립니다."),
        ("주안1동·송도3동처럼 동이 나뉜 곳도 되나요?", "네. 주안1~8동은 주안동, 송도1~5동은 송도동처럼 대표 동 안내 기준으로 통합 안내드립니다."),
    ]
    body = (breadcrumb(trail) +
        f'<section class="hero"><div class="hero-inner"><div class="hero-copy">'
        f'<span class="eyebrow"><span class="pulse"></span>인천 대표</span>'
        f'<h1><span class="grad">인천 출장마사지·홈타이</span><br><span class="serif">예약 안내</span></h1>'
        f'<p class="lead">인천 전지역(2군 8구) 방문 건강관리 예약을 인천 세븐 마사지가 안내합니다.</p>'
        f'<div class="actions"><a class="btn btn-primary" href="tel:{PHONE_TEL}">전화 예약 →</a>'
        f'<a class="btn btn-ghost" href="/incheon/area/">지역별 안내</a></div></div>'
        f'<div class="hero-visual"><div class="glass"><h3>INCHEON<b>인천 전지역</b></h3>'
        f'<div class="book-row"><span>구·군</span><span>2군 8구</span></div>'
        f'<div class="book-row"><span>상담</span><span>{HOURS}</span></div>'
        f'<a class="bk" href="tel:{PHONE_TEL}">예약 문의 →</a></div></div></div></section>' +
        intro + area_section + course_section + station_notes + safety +
        price_menu_block() + faq_block(incheon_faq, "인천 출장마사지 자주 묻는 질문") + cta_band())
    jsonld = [bc_ld(trail), localbiz_ld(name="인천 세븐 마사지", path="/incheon/"),
              service_ld("인천 출장마사지·홈타이", "인천 전지역 방문 건강관리 서비스", "/incheon/"),
              offer_ld(), faq_ld(incheon_faq)]
    write("/incheon/", page("/incheon/",
        "인천 출장마사지 | 인천 전지역 방문 마사지·홈타이 예약 안내",
        "인천 세븐 마사지는 인천 전지역(2군 8구) 출장마사지·홈타이 방문 예약을 안내합니다. 부평·주안·송도·구월·청라 등 구·군별 지역과 역세권 인근, 코스를 확인하세요.",
        "incheon", body, jsonld))


# ---- 인천 안내 개별 페이지 (각 ~2000자, E-E-A-T) -------------------------
def build_incheon_info_pages():
    it = [("/", "홈"), ("/incheon/", "인천 출장마사지")]

    content_page("/incheon/hometai/", "incheon", it + [(None, "인천 홈타이 안내")],
        title="인천 홈타이 | 자택·숙소 방문 타이마사지 예약 안내",
        desc="인천 홈타이 안내 - 자택·오피스텔·숙소로 방문하는 타이·스트레칭 계열 방문 관리입니다. 홈타이 진행 방식, 준비, 방문 관리의 장점과 자주 묻는 질문을 확인하세요.",
        eyebrow="인천 · 홈타이", h1="인천 홈타이 안내",
        show_price=True,
        lead="자택·오피스텔·숙소로 방문해 익숙한 공간에서 받는 타이·스트레칭 계열 방문 관리입니다.",
        sections=[
            ("홈타이란 무엇인가요", [
                "홈타이는 관리사가 고객이 계신 곳으로 방문해 진행하는 방문형 타이·스트레칭 계열 관리입니다.",
                "매장을 찾지 않고 익숙한 공간에서 받기 때문에 긴장이 덜하고, 관리 직후 이동 없이 그대로 휴식할 수 있어 이완 상태가 오래 유지됩니다."]),
            ("이런 분께 권해드립니다", [
                ("ul", ["외출 없이 집에서 편하게 받고 싶은 분",
                        "몸이 뻣뻣해 스트레칭 위주의 이완을 원하는 분",
                        "관리 후 바로 쉬고 싶은 분",
                        "이동 시간을 아끼고 싶은 분"])]),
            ("진행 방식", [
                "홈타이는 보통 옷을 입은 상태에서 스트레칭과 지압 중심으로 진행되며, 원하시면 오일 관리와 함께 구성할 수 있습니다.",
                "60분은 핵심 부위 위주, 90분은 전신을 고르게, 120분은 마무리 케어까지 여유 있게 진행합니다.",
                "압의 세기와 집중 부위는 시작 전과 진행 중 언제든 조절해 드립니다."]),
            ("방문 전 준비", [
                "두 사람이 누울 수 있는 평평한 공간과 조용한 분위기가 있으면 충분합니다.",
                "정확한 주소와 공동현관 출입 방법을 알려주시면 도착이 빨라집니다.",
                "자세한 준비물은 <a href='/incheon/checklist/'>이용 전 확인사항</a>에서 확인하실 수 있습니다."]),
            ("방문 관리이기에 좋은 점", [
                "익숙한 공간에서 받아 긴장이 덜하고, 관리 후 그대로 쉴 수 있습니다.",
                "인천 전지역으로 방문하며, 위치에 따라 평균 도착 시간을 예약 시 안내드립니다."]),
            ("관리 당일 진행 순서", [
                "관리사가 도착하면 가볍게 인사를 나누고 누울 공간을 정돈한 뒤, 선호하는 압과 집중 부위를 확인합니다.",
                "스트레칭과 지압을 중심으로 큰 부위부터 차례로 풀어주며, 관절 가동 범위를 살피며 진행합니다.",
                "마무리 단계에서는 호흡을 고르며 가볍게 이완하고 수분 섭취·휴식을 안내합니다."]),
            ("홈타이와 함께 받기 좋은 관리", [
                "오일을 함께 쓰고 싶다면 스웨디시·아로마테라피와 구성할 수 있고, 발·종아리 피로가 심하면 발마사지를 더할 수 있습니다.",
                "테마별 차이는 <a href='/theme/'>테마별 안내</a>, 코스별 요금은 <a href='/course/price/'>가격 안내</a>에서 확인하세요.",
                "지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 예약 시 위치와 원하시는 구성을 함께 말씀해 주시면 안내드립니다."]),
            ("홈타이 예약 시 참고하세요", [
                "홈타이는 매장 방문이 아닌 고객이 계신 곳으로 찾아가는 방식이라, 정확한 주소와 출입 방법을 미리 알려주시면 방문이 매끄럽습니다.",
                "두 사람이 누울 정도의 공간만 있으면 원룸·오피스텔·숙소에서도 진행 가능합니다.",
                "오일을 함께 쓰고 싶은 경우 예약 시 말씀해 주시면 스웨디시·아로마와 구성해 안내드립니다.",
            ]),
            ("홈타이와 함께 묻는 점", [
                "받는 도중 잠이 들어도 괜찮으며, 조용한 분위기에서 이완에 집중해 드립니다.",
                "압의 세기나 스트레칭 강도는 진행 중 언제든 조절하니 편하게 말씀해 주세요.",
            ]),
        ],
        data_note="홈타이는 평일 밤 시간대 문의가 가장 많습니다. 공간이 좁은 원룸·숙소도 진행 가능하니 예약 시 환경을 알려주시면 알맞게 안내드리며, 오일 관리와 함께 구성하실 수도 있으니 편하게 문의해 주세요.",
        faq=[
            ("홈타이와 매장 마사지는 무엇이 다른가요?", "홈타이는 매장이 아닌 고객이 계신 곳으로 방문해 진행합니다. 이동 없이 받고 바로 쉴 수 있는 점이 가장 큰 차이입니다."),
            ("좁은 공간에서도 가능한가요?", "두 사람이 누울 공간이면 충분하며, 원룸·숙소도 진행 가능합니다. 환경을 미리 알려주세요."),
            ("오일 없이 받을 수 있나요?", "네. 타이·스트레칭 위주로 옷을 입은 상태에서 진행하거나, 원하시면 오일 관리와 함께 구성할 수 있습니다.")],
        service=("인천 홈타이", "인천 전지역 자택·숙소 방문 타이 관리"),
        cta_title="인천 홈타이 방문 예약을 도와드릴까요?")

    content_page("/incheon/coverage/", "incheon", it + [(None, "인천 전지역 방문 가능 안내")],
        title="인천 전지역 방문 안내 | 2군 8구 출장마사지 가능 지역",
        desc="인천 전지역 출장마사지·홈타이 방문 가능 안내 - 강화군·옹진군과 8개 구, 2026년 7월 행정체제 개편(제물포구·영종구·검단구) 예정, 도서·외곽 지역 안내를 확인하세요.",
        eyebrow="인천 · 방문 가능 지역", h1="인천 전지역 방문 가능 안내",
        show_price=True,
        lead="인천 세븐 마사지는 강화군·옹진군 2개 군과 8개 구 등 인천 전지역으로 방문합니다.",
        sections=[
            ("2군 8구 기준 방문 안내", [
                "현재 인천시는 공식 기준으로 강화군·옹진군 2개 군과 중구·동구·미추홀구·연수구·남동구·부평구·계양구·서구 8개 구 체계입니다.",
                "본 사이트는 이 2군 8구 기준으로 지역 안내를 구성하며, 각 구·군의 대표 동 단위로 방문 안내를 제공합니다."]),
            ("구·군별로 살펴보기", [
                "원하시는 구·군을 선택하면 대표 동별 안내로 이동합니다.",
                ("ul", [f'<a href="/incheon/{a["slug"]}/">{a["name"]}</a> — {a["summary"]}' for a in AREAS])]),
            ("2026년 7월 행정체제 개편 예정", [
                "2026년 7월 1일부터 인천시는 2군 9구 체제로 개편되어 <strong>제물포구·영종구·검단구</strong>가 새로 출범할 예정입니다.",
                "중구·동구·서구 일부가 재편되므로, 본 사이트는 현재 구조로 운영하되 7월 이후 메뉴 변경과 주소 리다이렉트를 준비하고 있습니다.",
                "개편 이후에도 같은 생활권으로 동일하게 방문하므로, 이용에는 차이가 없습니다."]),
            ("도서·외곽 지역 안내", [
                "강화군·옹진군의 섬 지역(백령도·연평도·덕적도 등)과 영종·용유 등 외곽 지역도 안내드립니다.",
                "다만 이동 거리와 시간이 길어 방문 가능 여부와 도착 시간은 예약 시 미리 확인해 드립니다."]),
            ("정확한 위치를 알려주세요", [
                "같은 구 안에서도 위치에 따라 도착 시간이 달라집니다. 예약 시 정확한 주소나 가까운 역·랜드마크를 알려주시면 빠르게 안내드립니다.",
                "지하철역 인근이라면 <a href='/incheon/stations/'>지하철역별 안내</a>에서 가까운 역을 확인하실 수 있습니다."]),
            ("지역+역+테마 조합 페이지는 만들지 않습니다", [
                "본 사이트는 '부평역 스웨디시'나 '송도동 24시간'처럼 지역·역·테마를 결합한 조합 페이지를 만들지 않습니다.",
                "대신 구·군별 지역, 역세권, 테마를 각각 분리해 안내하고, 예약 시 위치와 원하시는 관리를 함께 말씀해 주시면 맞춰 드립니다.",
                "이렇게 운영하면 같은 안내가 중복되지 않아, 필요한 정보를 더 빠르고 정확하게 확인하실 수 있습니다."]),
        ],
        data_note="원도심·중심 구(부평·미추홀·남동·계양)는 비교적 도착이 빠르고, 강화·옹진 도서와 영종·용유 등 외곽은 이동 시간이 길어 사전 예약을 권장드립니다.",
        faq=[
            ("인천 어디까지 방문하나요?", "강화군·옹진군과 8개 구 등 인천 전지역을 안내드리며, 도서·외곽은 시간대와 위치에 따라 확인해 드립니다."),
            ("2026년 7월 개편 후에도 이용할 수 있나요?", "네. 제물포구·영종구·검단구 출범 이후에도 같은 생활권으로 동일하게 방문하며, 메뉴·주소는 개편에 맞춰 업데이트합니다."),
            ("섬 지역도 방문되나요?", "백령도·연평도·덕적도 등 도서 지역도 안내드리나, 이동 시간이 길어 방문 가능 여부를 예약 시 확인해 드립니다.")],
        cta_title="인천 어느 지역이든 방문 예약을 도와드릴까요?")

    content_page("/incheon/hours/", "incheon", it + [(None, "예약 가능 시간")],
        title="예약 가능 시간 | 인천 출장마사지 24시간 상담·도착 안내",
        desc="인천 출장마사지·홈타이 예약 가능 시간 안내 - 연중무휴 24시간 상담, 시간대별 특징, 지역별 평균 도착 시간, 도착 시간을 줄이는 방법과 예약 팁을 확인하세요.",
        eyebrow="인천 · 시간", h1="예약 가능 시간",
        show_price=True,
        lead="인천 세븐 마사지는 연중무휴 24시간 예약 상담을 운영합니다.",
        sections=[
            ("운영 시간", [
                "인천 세븐 마사지는 <strong>연중무휴 24시간</strong> 예약 상담을 운영합니다.",
                "전화 상담은 언제든 가능하며, 실제 방문 가능 시간은 시간대와 위치에 따라 안내드립니다."]),
            ("시간대별 특징", [
                ("ul", ["낮~초저녁: 비교적 도착이 빠르고 일정 조율이 수월합니다.",
                        "밤 21~24시: 예약이 가장 많이 몰리는 시간대로, 도착 시간을 넉넉히 안내드립니다.",
                        "심야(자정 이후): 방문 가능하나 위치에 따라 도착 시간이 길어질 수 있습니다."])]),
            ("지역별 평균 도착 시간", [
                "인천은 면적이 넓어 위치에 따라 도착 시간 차이가 큽니다. 부평·주안·구월 등 중심 생활권은 비교적 빠릅니다.",
                "검단·청라·송도 신도시와 영종·강화·옹진 도서·외곽은 이동 시간이 길어질 수 있습니다.",
                "예약 시 정확한 위치를 알려주시면 예상 도착 시간을 안내드립니다."]),
            ("도착 시간을 줄이는 방법", [
                "예약 시 정확한 주소와 공동현관·동·호수 등 출입 정보를 함께 알려주세요.",
                "가까운 지하철역이나 큰 건물 등 기준점을 알려주시면 위치 파악이 빨라집니다.",
                "도착 직전 연락이 닿을 수 있는 번호를 남겨주시면 마지막 동선이 매끄럽습니다."]),
            ("주말·공휴일 운영", [
                "주말과 공휴일에도 동일하게 연중무휴로 상담·방문을 운영합니다.",
                "기념일·연휴 저녁은 문의가 몰리므로 미리 예약하시는 편이 좋습니다."]),
            ("예약 변경·취소", [
                "일정이 바뀌면 가능한 한 빠르게 연락 주세요. 빠를수록 다른 시간으로 조율하기 쉽습니다.",
                "방문 직전 변경은 관리사 동선상 어려울 수 있어, 미리 알려주시면 감사하겠습니다."]),
            ("예약이 몰리는 시간", [
                "평일 밤 21~24시와 주말 저녁은 하루 중 예약이 가장 집중되는 시간대입니다.",
                "이 시간대에는 도착이 평소보다 조금 더 걸릴 수 있어, 여유 있게 예약하시길 권합니다.",
                "기념일·연휴 저녁은 특히 문의가 많으니 미리 예약하시면 원하는 시간으로 안내받기 쉽습니다."]),
            ("당일·즉시 예약", [
                "당일 예약도 가능합니다. 다만 시간대와 위치, 배정 상황에 따라 방문 가능 시간이 달라질 수 있습니다.",
                "급하게 받으셔야 한다면 전화로 연락 주시면 가장 가까운 방문 가능 시간을 안내해 드립니다."]),
            ("지역별 도착 시간 차이", [
                "부평·주안·구월 등 중심 생활권은 비교적 도착이 빠른 편이고, 송도·청라·검단 등 신도시와 영종·강화·옹진 도서·외곽은 이동 시간이 더 걸릴 수 있습니다.",
                "같은 지역이라도 시간대에 따라 차이가 있어, 정확한 예상 도착 시간은 예약 상담에서 위치를 기준으로 안내드립니다.",
                "급하게 받으셔야 한다면 가장 가까운 방문 가능 시간을 우선 안내해 드립니다.",
            ]),
            ("예약 시간 조율 팁", [
                "여러 시간대가 가능하다면 후보 시간을 두세 개 알려주시면 더 빠르게 일정을 확정할 수 있습니다.",
                "정확한 시간이 중요한 일정이라면 여유 있게 미리 예약하시는 것을 권장드립니다.",
            ]),
        ],
        data_note="평일 밤 21~24시는 하루 중 예약이 가장 집중되는 시간대입니다. 신도시·외곽은 이 시간대 도착이 더 걸릴 수 있어 여유 있게 예약하시길 권하며, 가능한 시간을 두세 개 알려주시면 일정이 더 빠르게 확정됩니다.",
        faq=[
            ("새벽에도 예약되나요?", "상담은 24시간 가능합니다. 심야는 위치에 따라 도착 시간이 길어질 수 있어 상담 시 안내드립니다."),
            ("도착까지 얼마나 걸리나요?", "위치에 따라 다르며, 중심 생활권은 비교적 빠르고 신도시·외곽은 더 걸릴 수 있습니다. 예약 시 안내드립니다."),
            ("당일 예약이 가능한가요?", "가능합니다. 시간대와 위치에 따라 가능 시간을 상담으로 확인해 드립니다.")])

    content_page("/incheon/checklist/", "incheon", it + [(None, "이용 전 확인사항")],
        title="이용 전 확인사항 | 인천 출장마사지 방문 준비 안내",
        desc="인천 출장마사지·홈타이 이용 전 확인사항 - 정확한 주소, 공동현관 출입, 주차, 조용한 공간, 예약자 연락 등 방문 준비와 결제·주의사항을 안내합니다.",
        eyebrow="인천 · 확인", h1="이용 전 확인사항",
        show_price=True,
        lead="원활한 방문을 위해 예약 전 아래 사항을 미리 확인해 주세요.",
        sections=[
            ("방문 장소 준비", [
                "편하게 누워 쉴 수 있는 조용한 공간을 확보해 주세요.",
                "자택·숙소 등 방문 장소의 정확한 주소와 공동현관 출입 방법을 알려주시면 도착이 빨라집니다.",
                "주차가 필요한 경우 가능 여부를 함께 알려주시면 좋습니다."]),
            ("예약 정보 확인", [
                ("ul", ["연락 가능한 전화번호(예약자 본인)", "방문 장소의 정확한 주소와 출입 방법",
                        "주차 가능 여부", "희망 코스와 시간(60·90·120분)", "방문 희망 시각"])]),
            ("결제 준비", [
                "코스별 정찰 요금을 사전에 안내드리며, 결제 방법은 예약 시 함께 확인합니다.",
                "지역·시간대 등 변동 요소는 미리 고지해 드립니다."]),
            ("이용 시 주의사항", [
                "본 서비스는 의료 행위가 아닌 건강관리 서비스이며 <strong>만 19세 이상</strong> 성인을 대상으로 합니다.",
                "불법·퇴폐 행위 요구는 일절 제공되지 않으며, 요청 시 서비스가 중단될 수 있습니다.",
                "음주가 심한 경우 안전을 위해 관리가 어려울 수 있습니다."]),
            ("방문 장소별 안내", [
                ("h3", "자택"),
                "공동현관 출입 방법과 동·호수를 알려주시면 도착이 빨라집니다. 반려동물이 있다면 미리 안내해 주세요.",
                ("h3", "숙소·호텔"),
                "건물명과 객실 번호, 프런트 출입 안내가 필요한지 함께 알려주시면 원활합니다."]),
            ("미리 알려주시면 좋은 점", [
                "함께 계신 분이 있거나 특정 향·압을 피하고 싶다면 예약 시 말씀해 주세요.",
                "임신 중이거나 피부·건강상 주의가 필요한 상황은 안전을 위해 사전에 공유해 주세요."]),
            ("결제·영수 안내", [
                "결제 방법은 예약 시 함께 확인하며, 필요하시면 영수 관련 사항도 안내드립니다.",
                "변동 요소(지역·시간대 등)가 있을 경우 관리 전에 미리 설명드리고 진행합니다."]),
            ("방문이 끝나면", [
                "관리 후에는 충분한 수분 섭취와 휴식을 권장드립니다.",
                "사용한 공간은 관리사가 정돈하고 마무리하니 따로 준비하실 것은 없습니다.",
                "다음 방문에 참고할 선호 사항(압·향·부위 등)을 알려주시면 더 잘 맞춰 드립니다."]),
            ("주차·출입 안내", [
                "주차가 필요한 경우 방문 차량 주차가 가능한지, 가능하다면 위치를 함께 알려주시면 도착이 수월합니다.",
                "공동현관 비밀번호나 출입 카드가 필요한 건물은 도착 직전에 안내해 주셔도 됩니다.",
                "엘리베이터 없는 건물이나 복잡한 동선은 미리 알려주시면 방문 시간을 더 정확히 안내드릴 수 있습니다.",
            ]),
            ("반려동물·동거인 안내", [
                "반려동물이 있다면 미리 알려주세요. 안전을 위해 관리 중에는 분리된 공간에 있도록 부탁드립니다.",
                "함께 거주하는 분이 있는 경우에도 사전에 알려주시면 편안한 환경을 준비하는 데 도움이 됩니다.",
            ]),
            ("예약 전 마지막 점검", [
                "방문 직전에는 예약하신 코스·시간·장소가 맞는지 한 번 더 확인해 주시면 착오 없이 진행됩니다.",
                "연락 가능한 번호가 바뀌었다면 미리 알려주시고, 변동이 생기면 가능한 한 빨리 연락 주세요.",
                "준비가 어려운 점이 있어도 부담 갖지 마시고 상담 시 말씀해 주시면 함께 맞춰 안내드립니다.",
            ]),
        ],
        data_note="예약 시 주소와 출입 방법을 함께 남겨주시면 도착 시간이 평균적으로 단축됩니다. 공동현관 비밀번호 등은 도착 직전 안내해 주셔도 됩니다. 준비가 어려운 점이 있어도 상담 시 함께 맞춰 안내드리니 부담 갖지 않으셔도 됩니다.",
        faq=[
            ("무엇을 준비하면 되나요?", "편히 쉴 공간과 연락 가능한 번호, 정확한 주소면 충분합니다."),
            ("출입은 어떻게 하나요?", "공동현관 출입 방법을 미리 알려주시면 도착이 수월합니다. 필요한 안내는 상담 시 도와드립니다."),
            ("예약을 변경할 수 있나요?", "가능한 한 빠르게 연락 주시면 일정 변경을 도와드립니다.")])

    content_page("/incheon/safety/", "incheon", it + [(None, "위생 및 안전 안내")],
        title="위생 및 안전 안내 | 인천 출장마사지 위생·안전 기준",
        desc="인천 출장마사지·홈타이 위생 및 안전 안내 - 용품 위생 관리, 관리사·고객 안전 가이드라인, 개인정보 보호, 비의료 서비스 고지와 건전 운영 원칙을 안내합니다.",
        eyebrow="인천 · 안전", h1="위생 및 안전 안내",
        show_price=True,
        lead="안심하고 받으실 수 있도록 위생과 안전을 운영의 기본 기준으로 둡니다.",
        sections=[
            ("위생 관리 기준", [
                "관리에 사용하는 수건·오일 등 용품은 위생 기준에 맞춰 관리합니다.",
                "방문 시 청결을 우선하며, 관리 종료 후 사용한 공간을 정돈합니다."]),
            ("개인정보 보호", [
                "예약을 위해 수집한 연락처·주소 등은 예약 진행 목적으로만 이용하고, 목적 달성 후 관련 법령에 따라 파기합니다.",
                "자세한 내용은 <a href='/privacy/'>개인정보처리방침</a>에서 확인하실 수 있습니다."]),
            ("예약 정보 확인", [
                "예약 시 안내드린 코스·시간·위치 정보를 방문 전 다시 확인해 정확한 방문이 이루어지도록 합니다.",
                "변동 사항이 있으면 관리 전에 미리 안내드리고 진행합니다."]),
            ("금지행위 안내", [
                "본 서비스는 건전한 건강관리 서비스로, 불법·퇴폐 행위 요구는 일절 제공하지 않습니다.",
                "부적절한 요구가 있을 경우 관리가 중단될 수 있으며, 관리사와 고객 상호 존중을 원칙으로 합니다."]),
            ("비의료·건전 서비스 운영", [
                "본 서비스는 의료 행위가 아닌 <strong>이완·휴식 목적의 건강관리(마사지) 서비스</strong>입니다.",
                "질환의 진단·치료를 목적으로 하지 않으며, 통증·부상은 의료기관 진료를 권유드립니다.",
                "만 19세 이상 성인을 대상으로 하며, 청소년은 이용할 수 없습니다."]),
            ("관리사 응대 기준", [
                "정중한 인사와 설명을 기본으로, 관리 전 선호 사항을 충분히 확인합니다.",
                "관리 중에도 압·온도·자세 등 불편함이 없는지 살피며 진행합니다.",
                "응대 가이드라인을 통해 어느 관리사가 방문하더라도 일관된 경험을 유지합니다."]),
            ("고객님께 부탁드리는 점", [
                ("ul", ["만 19세 이상 본인 확인에 협조해 주세요.",
                        "관리사에 대한 존중과 기본 예의를 지켜주세요.",
                        "불법·퇴폐 행위 요구는 삼가주세요. 요청 시 서비스가 중단됩니다.",
                        "과도한 음주 상태에서는 안전을 위해 관리가 어려울 수 있습니다."])]),
            ("신뢰를 위해 공개합니다", [
                "운영 주체와 연락처, 책임자 정보는 모든 페이지 하단에서 확인하실 수 있습니다.",
                "개인정보 처리 기준은 <a href='/privacy/'>개인정보처리방침</a>, 이용 조건은 <a href='/terms/'>이용약관</a>에 공개되어 있습니다."]),
            ("이런 경우 관리가 어려울 수 있습니다", [
                "과도한 음주 상태이거나 의사소통이 어려운 경우, 안전을 위해 관리가 어려울 수 있습니다.",
                "고열·급성 통증·부상 등 의료적 처치가 필요한 상태에서는 관리 대신 의료기관 진료를 권유드립니다.",
                "관리사에 대한 부적절한 요구나 위협이 있을 경우 관리는 즉시 중단됩니다.",
            ]),
            ("위생·안전을 위한 상호 협조", [
                "고객과 관리사 모두 안심할 수 있도록, 청결한 환경과 상호 존중을 함께 지켜주시면 감사하겠습니다.",
                "안전과 관련해 불편하거나 우려되는 점이 있으면 언제든 말씀해 주세요. 즉시 확인하고 조치합니다.",
            ]),
            ("문의와 신고 안내", [
                "위생·안전과 관련해 궁금하거나 개선이 필요한 점이 있으면 <a href='/customer/'>고객센터</a> 또는 전화로 언제든 말씀해 주세요.",
                "접수된 의견은 운영과 관리사 교육에 반영해, 더 안전한 방문 경험을 만드는 데 활용합니다.",
            ]),
        ],
        data_note="인천 세븐 마사지는 위생·안전을 운영의 기본 기준으로 두며, 관리사 교육과 응대 가이드라인을 통해 일관된 방문 경험을 유지하며, 개선 의견은 고객센터로 언제든 접수받아 운영에 반영합니다.",
        faq=[
            ("위생은 어떻게 관리되나요?", "수건·오일 등 용품을 위생 기준에 맞춰 관리하고, 관리 후 공간을 정돈합니다."),
            ("개인정보는 안전한가요?", "예약 목적으로만 이용하고 목적 달성 후 관련 법령에 따라 파기합니다."),
            ("의료적 효과가 있나요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 치료를 보장하지 않습니다.")])

    content_page("/incheon/faq/", "incheon", it + [(None, "자주 묻는 질문")],
        title="인천 출장마사지 FAQ | 예약·지역·역세권·요금 자주 묻는 질문",
        desc="인천 출장마사지·홈타이 자주 묻는 질문 - 방문 가능 지역, 지하철역 인근 예약, 당일 예약, 테마 선택, 요금과 안전까지 자주 들어오는 질문을 한곳에 정리했습니다.",
        eyebrow="인천 · FAQ", h1="인천 출장마사지 자주 묻는 질문",
        show_price=True,
        lead="예약·지역·역세권·테마·요금 등 자주 들어오는 질문을 한곳에 정리했습니다.",
        sections=[
            ("자주 묻는 질문을 모았습니다", [
                "인천 출장마사지·홈타이를 이용하기 전 자주 들어오는 질문을 주제별로 정리했습니다.",
                "더 궁금한 점은 <a href='/customer/'>고객센터</a> 또는 전화로 언제든 문의해 주세요."]),
            ("지역·역세권 한눈에", [
                ("h3", "어디까지 방문하나요"),
                "강화군·옹진군과 8개 구 등 인천 전지역을 안내드립니다. 도서·외곽은 시간대와 위치에 따라 확인해 드립니다.",
                ("h3", "지하철역 근처도 되나요"),
                "인천1·2호선, 1·7호선, 수인분당선, 공항철도 인천권 주요 역 인근으로 방문합니다."]),
            ("테마·요금 한눈에", [
                ("h3", "어떤 테마가 있나요"),
                "스웨디시·아로마테라피·타이마사지·중국마사지·스포츠·경락·홈케어·호텔식 등 테마별로 안내합니다.",
                ("h3", "요금은 어떻게 안내되나요"),
                "코스별 정찰 요금을 사전에 안내하며, 지역·시간대 등 변동 요소는 예약 시 미리 알려드립니다."]),
            ("안전·신뢰", [
                "본 서비스는 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며, 만 19세 이상 성인을 대상으로 합니다.",
                "위생·안전 가이드라인을 준수하며, 자세한 내용은 <a href='/incheon/safety/'>위생 및 안전 안내</a>에서 확인하실 수 있습니다."]),
            ("도어웨이·중복 없이 안내합니다", [
                "본 사이트는 지역·역·테마를 결합한 조합 페이지나, 지역명·역명만 바꾼 복제 페이지를 만들지 않습니다.",
                "구·군별 지역, 역세권, 테마를 각각 분리해 안내하므로 같은 내용이 중복되지 않습니다.",
                "예약 시 위치와 원하시는 관리를 함께 말씀해 주시면, 별도 페이지 없이도 정확하게 맞춰 안내드립니다."]),
            ("2026년 7월 행정개편 안내", [
                "2026년 7월 1일부터 인천은 제물포구·영종구·검단구가 출범하는 2군 9구 체제로 개편될 예정입니다.",
                "개편 이후에도 같은 생활권으로 동일하게 방문하며, 메뉴와 주소는 개편 일정에 맞춰 업데이트합니다. 자세한 내용은 <a href='/incheon/coverage/'>인천 전지역 방문 가능 안내</a>에서 확인하세요."]),
            ("문의가 많은 추가 질문", [
                ("h3", "여성 관리사가 방문하나요"),
                "요청 사항은 예약 상담에서 확인해 드리며, 배정 상황에 따라 안내가 달라질 수 있습니다.",
                ("h3", "결제는 어떻게 하나요"),
                "코스별 정찰 요금을 사전에 안내드리고, 결제 방법은 예약 시 함께 확인합니다. 자세한 요금은 <a href='/course/price/'>가격 안내</a>에서 확인하세요.",
            ]),
        ],
        data_note="가장 많이 들어오는 문의는 '도착까지 걸리는 시간'과 '테마·요금'입니다. 예약 시 위치와 희망 테마를 함께 알려주시면 빠르게 안내해 드립니다.",
        faq=[
            ("인천 어디까지 방문 가능한가요?", "강화군·옹진군과 8개 구 등 인천 전지역을 안내드립니다."),
            ("주안1동·송도3동처럼 동이 나뉜 곳도 되나요?", "네. 주안1~8동은 주안동, 송도1~5동은 송도동처럼 대표 동 안내 기준으로 통합 안내드립니다."),
            ("지하철역 근처도 예약할 수 있나요?", "인천1·2호선, 1·7호선, 수인분당선, 공항철도 인천권 주요 역 인근으로 방문합니다."),
            ("당일·심야 예약이 가능한가요?", "상담은 24시간 가능합니다. 심야는 위치에 따라 도착 시간이 길어질 수 있습니다."),
            ("테마는 어떻게 선택하나요?", "원하는 테마를 말씀해 주시면 컨디션과 목적에 맞춰 안내드립니다. 자세한 내용은 테마별 안내에서 확인하세요."),
            ("요금은 어떻게 되나요?", "코스별 정찰 요금을 사전에 안내드립니다. 자세한 금액은 가격 안내에서 확인하세요."),
            ("표시 요금 외 추가 비용이 있나요?", "정찰 요금을 원칙으로 하며 지역·시간대 등 변동 요소는 예약 시 미리 안내드립니다."),
            ("이 서비스는 의료 행위인가요?", "아닙니다. 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상을 대상으로 합니다.")])

# ---- 지역 허브 -----------------------------------------------------------
def build_area_hub():
    trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"), (None, "지역별 안내")]
    blocks = ""
    for a in AREAS:
        dong_links = "".join(
            f'<a class="card reveal" href="/incheon/{a["slug"]}/{d["slug"]}/"><div class="k">{a["name"]}</div>'
            f'<h3>{d["name"]}</h3><p>{d["character"]}</p>'
            f'<span class="more">동 안내 보기 →</span></a>' for d in a["dongs"])
        blocks += (
            f'<div style="margin-top:40px"><h3 style="font-size:22px;font-weight:800;margin-bottom:6px">'
            f'<a href="/incheon/{a["slug"]}/" class="grad">{a["name"]}</a></h3>'
            f'<p class="sec-lead">{a["summary"]}</p>'
            f'<div class="grid g3" style="margin-top:18px">{dong_links}</div></div>')
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>AREA GUIDE</span>'
        '<h2 class="sec">지역별 안내</h2>'
        '<p class="sec-lead">인천 2군 8구를 대표 동 단위로 나누어 방문 안내를 제공합니다. 주안1~8동·송도1~5동 등 숫자 행정동은 대표 동으로 통합 안내합니다.</p>'
        + blocks + '</div></section>' + price_menu_block() + cta_band())
    item_list = {"@context": "https://schema.org", "@type": "CollectionPage",
        "name": "인천 출장마사지 지역별 안내", "url": BASE_URL + "/incheon/area/",
        "hasPart": [{"@type": "WebPage", "name": a["name"],
                     "url": BASE_URL + f"/incheon/{a['slug']}/"} for a in AREAS]}
    write("/incheon/area/", page("/incheon/area/",
        "인천 지역별 안내 | 2군 8구 출장마사지·홈타이 방문 지역",
        "인천 출장마사지·홈타이 지역별 안내 - 강화군·옹진군과 중구·동구·미추홀구·연수구·남동구·부평구·계양구·서구 등 구·군별 대표 동 방문 안내를 제공합니다.",
        "area", body, [bc_ld(trail), item_list, offer_ld()]))


# ---- 구·군 페이지 --------------------------------------------------------
def build_gu_pages():
    for a in AREAS:
        trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"),
                 ("/incheon/area/", "지역별 안내"), (None, a["name"])]
        dong_cards = "".join(
            f'<a class="card reveal" href="/incheon/{a["slug"]}/{d["slug"]}/"><div class="k">동 안내</div>'
            f'<h3>{d["name"]}</h3><p>{d["landmarks"]}</p>'
            f'<span class="more">자세히 →</span></a>' for d in a["dongs"])
        dong_lines = [f'<a href="/incheon/{a["slug"]}/{d["slug"]}/">{d["name"]}</a>은 {d["character"]}으로, {d["landmarks"]} 인근을 평균 {d["arrival"]}분 내외로 방문합니다. 자택·오피스텔·숙소 방문 문의가 고르게 들어옵니다.'
                      for d in a["dongs"]]
        sub_notes = [d.get("sub_note") for d in a["dongs"] if d.get("sub_note")]
        chips = "".join(f'<span class="chip"><b>{d["name"]}</b></span>' for d in a["dongs"])
        gu_faq = [
            (f"{a['name']}은 어디까지 방문 가능한가요?",
             "대표 동 기준 " + "·".join(d["name"] for d in a["dongs"]) + " 일대를 안내드리며, 정확한 가능 여부는 예약 시간과 위치에 따라 확인해 드립니다."),
            (f"{a['name']} 예약은 어떻게 하나요?",
             "전화 또는 문의로 동·시간·코스를 말씀해 주시면 방문 가능 시간을 확정해 드립니다."),
            (f"{a['name']}에서 숫자로 나뉜 동도 되나요?",
             "네. 1동·2동·3동 등으로 나뉜 행정동은 대표 동 안내 기준으로 통합 안내드립니다."),
        ]
        sections = [
            (f"{a['name']} 출장마사지·홈타이 안내", [
                f"{a['name']}은 {a['summary']} 인천 세븐 마사지는 {a['name']} 전역으로 방문해 자택·오피스텔·숙소에서 받으실 수 있는 출장마사지·홈타이 예약을 안내합니다.",
                f"{a['name']}은 1동·2동·3동처럼 숫자로 나뉜 행정동이 있어도 대표 동 하나로 통합해 안내합니다. 아래에서 원하시는 대표 동을 선택하면 상세 안내로 이동합니다.",
                '예약 방법은 <a href="/reservation/">예약안내</a>, 처음 이용 시 흐름은 <a href="/guide/">이용가이드</a>에서 확인하실 수 있습니다.']),
            (f"{a['name']} 방문 가능 대표 동", [
                f"{a['name']}은 " + "·".join(d["name"] for d in a["dongs"]) + " 등 대표 동을 포함합니다. 원하는 동을 눌러 상세 안내를 확인하세요.",
                ("html", f'<div class="chips" style="margin-bottom:18px">{chips}</div>'
                         f'<div class="grid g3">{dong_cards}</div>')]),
            ("대표 동별 방문 안내", dong_lines),
            (f"{a['name']} 방문·도착 안내", [
                f"{a['name']} 안에서도 위치에 따라 도착 시간이 달라집니다. 예약 시 정확한 주소나 가까운 역·랜드마크를 알려주시면 가까운 동선으로 안내드립니다.",
                f"{a['name']} 인근 지하철역으로 방문 위치를 알려주셔도 됩니다. 역세권 안내는 <a href='/incheon/stations/'>지하철역별 안내</a>에서 확인하실 수 있습니다.",
                "저녁·주말은 문의가 몰릴 수 있어 사전 예약을 권장드리며, 예약 가능 시간은 연중무휴 24시간 상담으로 확인해 드립니다."]),
        ]
        if sub_notes:
            sections.append(("숫자 행정동 통합 안내", sub_notes))
        sections.append((f"{a['name']}에서 많이 찾는 관리", [
            f"{a['name']}에서는 스웨디시·아로마테라피·홈케어·스포츠 관리 문의가 고르게 들어옵니다. 컨디션과 목적에 맞춰 테마와 코스를 선택하실 수 있습니다.",
            ("ul", ['<a href="/theme/swedish/">스웨디시</a>', '<a href="/theme/aroma/">아로마테라피</a>',
                    '<a href="/theme/homecare/">홈케어</a>', '<a href="/theme/thai/">타이마사지</a>',
                    '<a href="/course/">코스안내</a>', '<a href="/course/price/">가격 안내</a>'])]))
        sections.append(("예약·코스·위생은 전용 안내에서", [
            f"{a['name']} 내 예약 가능 시간·준비물·위생 기준·코스 요금은 페이지마다 반복하지 않고 전용 안내에서 확인하실 수 있습니다.",
            ("ul", ['<a href="/incheon/hours/">예약 가능 시간 안내</a>',
                    '<a href="/incheon/checklist/">이용 전 확인사항(준비물)</a>',
                    '<a href="/incheon/safety/">위생 및 안전 안내</a>',
                    '<a href="/theme/">테마별 안내</a>',
                    '<a href="/course/price/">코스안내 · 가격</a>'])]))
        top_links = [("tel:" + PHONE_TEL, "예약문의", True), ("/incheon/area/", "지역별 안내"),
                     ("/incheon/", "인천 출장마사지 대표"), ("/incheon/stations/", "지하철역별 안내")]
        content_page(f"/incheon/{a['slug']}/", "area", trail,
            title=gu_title(a['name']),
            desc=gu_desc(a['name'], a['dongs'], a['summary']),
            eyebrow=f"인천 · {a['name']}", h1=f"{a['name']} 출장마사지·홈타이", lead=a["summary"],
            sections=sections, faq=gu_faq, top_links=top_links, show_price=True,
            cta_title=f"{a['name']} 방문 예약을 도와드릴까요?",
            service=(f"{a['name']} 출장마사지", a["summary"]),
            extra_schema=[localbiz_ld(name=f"인천 세븐 마사지 {a['name']}",
                                      area=f"인천광역시 {a['name']}", path=f"/incheon/{a['slug']}/")])


# ---- 동 페이지 -----------------------------------------------------------
def build_dong_pages():
    for a in AREAS:
        for idx, d in enumerate(a["dongs"]):
            name, slug = d["name"], d["slug"]
            path = f"/incheon/{a['slug']}/{slug}/"
            trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"),
                     ("/incheon/area/", "지역별 안내"),
                     (f"/incheon/{a['slug']}/", a["name"]),
                     (None, f"{name} 출장마사지")]
            siblings = [x for x in a["dongs"] if x["slug"] != slug]
            lm_list = [s.strip() for s in d["landmarks"].split(",")]
            first_lm = lm_list[0]
            top_links = [("tel:" + PHONE_TEL, "예약문의", True), ("/theme/", "테마별 안내"),
                         ("/incheon/", "인천 출장마사지 대표")]
            if siblings:
                top_links.append((f"/incheon/{a['slug']}/{siblings[0]['slug']}/", f"{siblings[0]['name']}"))

            # 생활권 블록(H3) — 동 고유 콘텐츠
            zone_blocks = [
                f"{name}은 {d['landmarks']}를 중심으로 인근 생활권과 연결됩니다. {d['character']}이라 자택·오피스텔·숙소 방문 문의가 고르게 들어오며, 세부 방문 가능 여부는 정확한 위치·예약 시간·배정 상황에 따라 달라질 수 있습니다.",
                f"{name} 일대는 평균 {d['arrival']}분 내외로 도착하며(예약 데이터 기준), 같은 {name} 안에서도 위치에 따라 도착 시간이 달라집니다."]
            for i, lm in enumerate(lm_list[:3]):
                zone_blocks += [("h3", f"{lm} 인근"),
                                f"{lm} 방향은 {name}의 주요 생활 포인트로, 인근 자택·숙소 방문 문의가 많습니다. 정확한 위치를 알려주시면 가까운 동선으로 안내드립니다."]
            zone_blocks += [("h3", "주거지·숙소 방문 안내"),
                            f"{name}에서는 {first_lm} 인근 자택·오피스텔·숙소로 방문하며, 공동현관 출입 방법과 정확한 주소를 알려주시면 도착이 빨라집니다."]

            region_links = ['<a href="/incheon/">인천 출장마사지</a>',
                            '<a href="/incheon/area/">인천 전지역 안내</a>',
                            f'<a href="/incheon/{a["slug"]}/">{a["name"]}</a>']
            region_links += [f'<a href="/incheon/{a["slug"]}/{s["slug"]}/">{s["name"]}</a>' for s in siblings[:6]]
            region_tail = d["sub_note"] if d.get("sub_note") else \
                f"{a['name']}은 생활권이 이어져 있어 인근 동과 함께 안내드리는 경우가 많습니다."
            dong_theme_intro, dong_theme_ul = theme_links_block(slug, f"{name}({d['character']})")

            sections = [
                (f"{name} 출장마사지·홈타이 이용 안내", [
                    f"{name}은 {d['character']}입니다. 주요 위치는 {d['landmarks']} 일대로, 이 생활권을 중심으로 자택·오피스텔·숙소 방문 문의가 많습니다.",
                    f"{name} 출장마사지·홈타이는 {first_lm} 등 {name} 내 원하시는 장소로 방문해 피로 회복과 컨디션 관리를 돕는 방문형 관리 서비스입니다. 예약 시 위치·희망 시간·코스·인원을 확인한 뒤 방문 가능 여부를 안내드립니다.",
                    '예약 방법·결제 절차는 <a href="/reservation/">예약안내</a>, 처음 이용 시 진행 흐름은 <a href="/guide/">이용가이드</a>에서 확인하실 수 있습니다.']),
                (f"{name} 방문 가능 생활권", zone_blocks),
                (f"{a['name']} 함께 보기", [
                    f"{name}과 가까운 같은 {a['name']} 대표 동도 함께 확인할 수 있습니다.",
                    ("ul", region_links), region_tail]),
                (f"{name}에서 많이 찾는 관리", [
                    dong_theme_intro,
                    ("ul", dong_theme_ul)]),
                (f"{name} 예약·준비·위생 안내", [
                    f"{name} 방문 예약은 시간대와 배정 상황에 따라 가능 여부가 달라지며, 평균 {d['arrival']}분 내외로 도착합니다. 저녁·주말은 문의가 몰릴 수 있어 사전 예약을 권장드립니다.",
                    "예약 가능 시간, 방문 전 준비물, 위생·안전 기준은 페이지마다 반복하지 않고 전용 안내에서 자세히 확인하실 수 있습니다.",
                    ("ul", ['<a href="/incheon/hours/">예약 가능 시간 안내</a>',
                            '<a href="/incheon/checklist/">이용 전 확인사항(준비물)</a>',
                            '<a href="/incheon/safety/">위생 및 안전 안내</a>',
                            '<a href="/course/price/">가격 안내</a>'])]),
            ]
            dong_faq = [
                (f"{name} 전 지역 방문이 가능한가요?",
                 f"예약 시간, 정확한 위치, 배정 상황에 따라 가능 여부가 달라질 수 있습니다. {d['landmarks']} 인근 등 세부 위치를 기준으로 안내드립니다."),
                (f"{first_lm} 근처도 예약할 수 있나요?",
                 f"{first_lm} 인근은 {name} 주요 생활권으로 함께 안내할 수 있습니다. 정확한 방문 가능 여부는 예약 시 위치를 기준으로 확인합니다."),
                (f"{name}은 어떤 지역인가요?",
                 f"{name}은 {d['character']}입니다. {d['landmarks']} 인근을 중심으로 자택·숙소·오피스텔 방문 문의가 많은 편입니다."),
                (f"{name} 도착까지 얼마나 걸리나요?",
                 f"평균 {d['arrival']}분 내외이며, 시간대와 정확한 위치에 따라 달라질 수 있습니다."),
                (f"{name}에서는 어떤 관리가 인기인가요?",
                 f"{name}에서는 스웨디시·아로마테라피·홈케어 관리 문의가 많습니다. 목적과 컨디션에 따라 선택하시면 되며, 자세한 내용은 테마별 안내에서 확인하실 수 있습니다."),
            ]
            lead = dong_lead(name, a['name'], d['character'], d['landmarks'], d['arrival'])
            content_page(path, "area", trail,
                title=dong_title(name, a['name'], d['landmarks']),
                desc=dong_desc(name, a['name'], d['character'], d['landmarks'], d['arrival']),
                eyebrow=f"{a['name']} · {name}", h1=f"{name} 출장마사지·홈타이 예약 안내", lead=lead,
                sections=sections, faq=dong_faq,
                data_note=f"{name} 일대는 평균 {d['arrival']}분 내외로 도착합니다(예약 데이터 기준). 저녁·주말은 문의가 몰려 도착이 다소 길어질 수 있어 사전 예약을 권장드립니다.",
                service=(f"{name} 출장마사지", f"인천 {a['name']} {name} 일대 방문 건강관리 서비스"),
                top_links=top_links, show_price=True,
                cta_title=f"{name} 방문 예약, 지금 도와드릴까요?",
                extra_schema=[localbiz_ld(name=f"인천 세븐 마사지 {name}",
                                          area=f"인천광역시 {a['name']} {name}", path=path)])

# ---- 지하철역 허브 -------------------------------------------------------
def build_station_hub():
    trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"), (None, "지하철역별 안내")]
    blocks = ""
    for l in LINES:
        chips = "".join(
            f'<a class="chip" href="/incheon/stations/{STATION_DATA[nm][0]}/"><b>{nm}</b></a>'
            for nm in LINE_STATIONS[l["key"]])
        blocks += (
            f'<div style="margin-top:36px"><h3 style="font-size:21px;font-weight:800;margin-bottom:6px">'
            f'<a href="/incheon/stations/line/{l["key"]}/" class="grad">{l["name"]}</a></h3>'
            f'<p class="sec-lead">{l["short"]} 인근 역세권 방문 안내입니다. 역을 눌러 상세 안내를 확인하세요.</p>'
            f'<div class="chips" style="margin-top:14px">{chips}</div></div>')
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>STATION GUIDE</span>'
        '<h2 class="sec">지하철역별 안내</h2>'
        '<p class="sec-lead">인천1·2호선, 1·7호선, 수인분당선, 공항철도 인천권 노선별 역세권 방문 안내입니다. '
        '환승역은 여러 노선에 보이더라도 한 페이지로 안내합니다.</p>'
        + blocks + '</div></section>' + price_menu_block() + cta_band())
    item_list = {"@context": "https://schema.org", "@type": "CollectionPage",
        "name": "인천 지하철역별 출장마사지 안내", "url": BASE_URL + "/incheon/stations/",
        "hasPart": [{"@type": "WebPage", "name": l["name"],
                     "url": BASE_URL + f"/incheon/stations/line/{l['key']}/"} for l in LINES]}
    write("/incheon/stations/", page("/incheon/stations/",
        "인천 지하철역별 안내 | 역세권 출장마사지·홈타이 방문",
        "인천 지하철역별 출장마사지·홈타이 안내 - 인천1·2호선, 1·7호선, 수인분당선, 공항철도 인천권 주요 역 인근 방문 안내입니다. 부평·주안·송도·계양·검암역 등을 확인하세요.",
        "stations", body, [bc_ld(trail), item_list]))


# ---- 노선별 페이지 -------------------------------------------------------
def build_line_pages():
    for l in LINES:
        key = l["key"]
        trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"),
                 ("/incheon/stations/", "지하철역별 안내"), (None, l["name"])]
        st_cards = "".join(
            f'<a class="card reveal" href="/incheon/stations/{STATION_DATA[nm][0]}/"><div class="k">{STATION_DATA[nm][1]}</div>'
            f'<h3>{nm}역</h3><p>{STATION_DATA[nm][2]}</p><span class="more">역 안내 보기 →</span></a>'
            for nm in LINE_STATIONS[key])
        body = (breadcrumb(trail) +
            '<section class="block"><div class="wrap">'
            f'<span class="eyebrow"><span class="pulse"></span>{l["short"].upper()}</span>'
            f'<h2 class="sec">{l["name"]} 역세권 안내</h2>'
            f'<p class="sec-lead">{l["name"]} 인근 역세권으로 방문하는 출장마사지·홈타이 안내입니다. '
            f'환승역은 여러 노선에 보이더라도 URL은 하나만 사용합니다.</p>'
            f'<div class="grid g3" style="margin-top:26px">{st_cards}</div>'
            '</div></section>' + price_menu_block() + cta_band())
        item_list = {"@context": "https://schema.org", "@type": "CollectionPage",
            "name": f"{l['name']} 역세권 출장마사지 안내",
            "url": BASE_URL + f"/incheon/stations/line/{key}/",
            "hasPart": [{"@type": "WebPage", "name": f"{nm}역",
                         "url": BASE_URL + f"/incheon/stations/{STATION_DATA[nm][0]}/"}
                        for nm in LINE_STATIONS[key]]}
        write(f"/incheon/stations/line/{key}/", page(f"/incheon/stations/line/{key}/",
            line_title(l['name']),
            f"{l['name']} 역세권 출장마사지·홈타이 안내 - " + "·".join(LINE_STATIONS[key][:6]) +
            "역 등 인근 방문 안내를 제공합니다.",
            "stations", body, [bc_ld(trail), item_list]))


# ---- 역 상세 페이지 (역 1개당 1페이지, 환승역 통합) -----------------------
def build_station_pages():
    for nm in unique_stations():
        slug, gu, landmark, arr = STATION_DATA[nm]
        path = f"/incheon/stations/{slug}/"
        keys = station_lines(nm)
        line_names = [LINE_NAME[k] for k in keys]
        transfer = len(keys) > 1
        trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"),
                 ("/incheon/stations/", "지하철역별 안내"), (None, f"{nm}역 출장마사지")]
        gu_slug = next((a["slug"] for a in AREAS if a["name"] == gu), None)
        lm_list = [s.strip() for s in landmark.split(",")]
        first_lm = lm_list[0]

        line_sentence = (f"{nm}역은 " + "·".join(line_names) + " 환승역으로, 여러 노선이 만나는 거점입니다."
                         if transfer else f"{nm}역은 {line_names[0]} 역입니다.")
        other_lines = ""
        if transfer:
            other_lines = f"환승역이라 여러 노선에서 보이지만, {nm}역 안내는 이 한 페이지로 통합되어 있습니다."

        nearby = ""
        if gu_slug:
            nearby = f'{nm}역은 인천 {gu}에 위치합니다. {gu} 지역 전체 안내는 <a href="/incheon/{gu_slug}/">{gu} 출장마사지</a>에서 확인하실 수 있습니다.'
        else:
            nearby = f'{nm}역은 인천 {gu}에 위치합니다.'

        zone_blocks = [
            f"{nm}역 인근은 {landmark} 일대로 이어지는 생활권입니다. {line_sentence} 역세권 자택·오피스텔·숙소로 방문 문의가 고르게 들어오며, 세부 방문 가능 여부는 정확한 위치와 예약 시간, 배정 상황에 따라 안내드립니다.",
            f"{nm}역 인근은 평균 {arr}분 내외로 도착하며(예약 데이터 기준), 같은 역세권 안에서도 출구·위치에 따라 도착 시간이 달라집니다. 출구별로 페이지를 따로 만들지 않으며, 정확한 주소를 알려주시면 가까운 동선으로 안내드립니다."]
        for li_i, lm in enumerate(lm_list):
            zone_blocks += [("h3", f"{lm} 인근"),
                            f"{lm} 방향은 {nm}역세권의 주요 생활 포인트입니다. 인근 주거지·숙소·오피스텔에서 방문 문의가 많으며, {nm}역에서 가까워 방문 동선이 비교적 빠른 편입니다."]
        if other_lines:
            zone_blocks += [("h3", "환승역 안내"), other_lines]
        zone_blocks += [("h3", "주거지·숙소 방문 안내"),
            f"{nm}역 인근에서는 {first_lm} 등 역세권 자택·오피스텔·숙소로 방문합니다. 공동현관 출입 방법과 정확한 주소, 동·호수를 함께 알려주시면 도착이 한결 빨라집니다."]
        st_theme_intro, st_theme_ul = theme_links_block(slug, f"{nm}역 인근")

        sections = [
            (f"{nm}역 출장마사지·홈타이 이용 안내", [
                f"{nm}역 출장마사지·홈타이는 {nm}역세권({landmark} 일대)으로 방문하는 방문형 건강관리 서비스입니다. {line_sentence}",
                f"{nm}역 인근 자택·오피스텔·숙소로 방문해 이동 없이 받으실 수 있으며, 예약 시 위치·희망 시간·코스·인원을 확인한 뒤 방문 가능 여부를 안내드립니다.",
                '예약 방법은 <a href="/reservation/">예약안내</a>, 처음 이용 시 흐름은 <a href="/guide/">이용가이드</a>에서 확인하실 수 있습니다.']),
            (f"{nm}역 인근 방문 안내", zone_blocks),
            (f"{gu} 함께 보기", [
                nearby,
                f"가까운 노선 정보는 " + "·".join(f'<a href="/incheon/stations/line/{k}/">{LINE_SHORT[k]}</a>' for k in keys) + " 노선 안내에서도 확인하실 수 있습니다."]),
            (f"{nm}역 인근에서 많이 찾는 관리", [
                st_theme_intro,
                ("ul", st_theme_ul)]),
            (f"{nm}역 방문 팁", [
                f"{nm}역 인근은 {gu} 생활권에 속해, 저녁·주말 시간대에 방문 문의가 몰리는 편입니다. 원하는 시간이 정해져 있다면 미리 예약하실수록 일정 조율이 수월합니다.",
                f"예약 시 {nm}역 몇 번 출구 방향인지, 가까운 건물이나 랜드마크가 무엇인지 함께 알려주시면 위치 파악이 빨라져 도착 시간을 줄일 수 있습니다."]),
            (f"{nm}역 예약·준비·위생 안내", [
                f"{nm}역 인근 방문 예약은 시간대와 배정 상황에 따라 가능 여부가 달라지며, 평균 {arr}분 내외로 도착합니다. 저녁·주말은 문의가 몰릴 수 있어 사전 예약을 권장드립니다.",
                "예약 가능 시간, 방문 전 준비물, 위생·안전 기준은 페이지마다 반복하지 않고 전용 안내에서 자세히 확인하실 수 있습니다.",
                ("ul", ['<a href="/incheon/hours/">예약 가능 시간 안내</a>',
                        '<a href="/incheon/checklist/">이용 전 확인사항(준비물)</a>',
                        '<a href="/incheon/safety/">위생 및 안전 안내</a>',
                        '<a href="/course/price/">가격 안내</a>'])]),
        ]
        st_faq = [
            (f"{nm}역 어느 출구든 방문 가능한가요?",
             f"네. 출구별로 페이지를 나누지 않고 {nm}역세권 전체를 기준으로 안내합니다. 정확한 주소를 알려주시면 가까운 동선으로 방문합니다."),
            (f"{nm}역은 어느 노선인가요?",
             ("·".join(line_names) + f" 환승역입니다." if transfer else f"{line_names[0]} 역입니다.") + f" 인천 {gu}에 위치합니다."),
            (f"{nm}역 근처 어디까지 방문하나요?",
             f"{landmark} 인근 생활권을 중심으로 자택·숙소·오피스텔로 방문합니다. 세부 위치에 따라 가능 여부를 예약 시 확인합니다."),
            (f"{nm}역 도착까지 얼마나 걸리나요?",
             f"평균 {arr}분 내외이며, 시간대와 정확한 위치에 따라 달라질 수 있습니다."),
            (f"{nm}역 인근 당일 예약이 되나요?",
             "가능합니다. 시간대와 위치에 따라 방문 가능 시간이 달라질 수 있어 상담 시 확인해 드립니다."),
        ]
        lead = station_lead(nm, gu, line_sentence, landmark, arr)
        content_page(path, "stations", trail,
            title=station_title(nm, gu, [LINE_SHORT[k] for k in keys], transfer, landmark),
            desc=station_desc(nm, gu, line_names, transfer, landmark, arr),
            eyebrow=f"인천 {gu} · {nm}역", h1=f"{nm}역 출장마사지·홈타이", lead=lead,
            sections=sections, faq=st_faq,
            data_note=f"{nm}역 인근은 평균 {arr}분 내외로 도착합니다(예약 데이터 기준). 출구·정확한 위치에 따라 달라지니 예약 시 주소를 알려주시면 빠르게 안내해 드립니다.",
            service=(f"{nm}역 출장마사지", f"인천 {gu} {nm}역세권 방문 건강관리 서비스"),
            show_price=True,
            cta_title=f"{nm}역 인근 방문 예약을 도와드릴까요?",
            extra_schema=[localbiz_ld(name=f"인천 세븐 마사지 {nm}역",
                                      area=f"인천광역시 {gu}", path=path)])

# ---- 테마 허브 + 테마 페이지 ---------------------------------------------
def build_theme_hub():
    trail = [("/", "홈"), (None, "테마별 안내")]
    cards = "".join(
        f'<a class="card reveal" href="/theme/{t["slug"]}/"><div class="k">{t["kicker"]}</div>'
        f'<h3>{t["name"]}</h3><p>{t["summary"]}</p><span class="more">테마 보기 →</span></a>'
        for t in THEMES)
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>THEME</span>'
        '<h2 class="sec">테마별 안내</h2>'
        '<p class="sec-lead">스웨디시·로미로미·타이마사지·중국마사지·아로마테라피·홈케어·호텔식·발마사지·스포츠경락·스킨케어·왁싱·커플·24시간·수면 등 테마별 관리를 안내합니다. '
        '지역+역+테마 조합 페이지는 만들지 않고, 각 테마를 분리해 안내합니다.</p>'
        f'<div class="grid g3" style="margin-top:26px">{cards}</div></div></section>'
        + price_menu_block() + cta_band())
    item_list = {"@context": "https://schema.org", "@type": "CollectionPage",
        "name": "인천 출장마사지 테마별 안내", "url": BASE_URL + "/theme/",
        "hasPart": [{"@type": "WebPage", "name": t["name"],
                     "url": BASE_URL + f"/theme/{t['slug']}/"} for t in THEMES]}
    write("/theme/", page("/theme/",
        "테마별 안내 | 인천 출장마사지 스웨디시·아로마·타이·홈케어",
        "인천 출장마사지·홈타이 테마별 안내 - 스웨디시, 아로마테라피, 타이마사지, 중국마사지, 홈케어, 호텔식, 발마사지, 스포츠·경락, 커플, 24시간, 수면 가능 등 테마별 관리를 확인하세요.",
        "theme", body, [bc_ld(trail), item_list, offer_ld()]))

def build_theme_pages():
    tt = [("/", "홈"), ("/theme/", "테마별 안내")]
    others = {t["slug"]: t["name"] for t in THEMES}
    for t in THEMES:
        slug = t["slug"]
        rel = [(s, n) for s, n in others.items() if s != slug][:5]
        sections = [
            (f"{t['name']}란 무엇인가요", [t["intro"]]),
            (f"{t['name']}의 기법과 특징", [t["detail"]]),
            ("이런 분께 권해드립니다", [
                f"{t['name']}는 아래와 같은 분께 특히 잘 맞습니다.",
                ("ul", t["fit"])]),
            ("다른 테마와 무엇이 다른가요", [
                t["diff"],
                "관리는 의료 행위가 아닌 이완·휴식 목적의 건강관리이며, 통증·부상은 의료기관 진료를 권유드립니다.",
                ("ul", [f'<a href="/theme/{s}/">{n}</a>' for s, n in rel])]),
            ("시간 구성과 요금", [
                f"{t['name']}는 60·90·120분 구성으로 운영하며, 90분이 전신을 고르게 받기 좋아 가장 많이 선택됩니다.",
                "압의 세기와 집중 부위는 시작 전과 진행 중 언제든 조절해 드립니다. 코스별 요금은 <a href='/course/price/'>가격 안내</a>에서 확인하실 수 있습니다."]),
            (f"{t['name']} 관리 당일 순서", [
                f"관리사가 도착하면 가볍게 인사를 나누고 편히 쉴 수 있도록 공간을 정돈한 뒤, {t['name']}에 맞춰 그날의 컨디션과 선호를 확인합니다.",
                f"본격적인 관리는 {t['summary'].rstrip('.다')} 흐름으로 큰 부위부터 차례로 진행하며, 뭉친 부위나 신경 쓰이는 곳에 시간을 더 들입니다.",
                "마무리 단계에서는 가볍게 정돈하고 수분 섭취·휴식을 안내하며 관리를 마칩니다. 받는 동안 불편한 점이 있으면 언제든 말씀해 주세요."]),
            ("방문 전 준비와 예약 안내", [
                f"편안한 복장과 조용히 쉴 수 있는 공간이 있으면 {t['name']}를 받기에 충분합니다. 정확한 주소와 출입 방법은 <a href='/incheon/checklist/'>이용 전 확인사항</a>에서 확인하실 수 있습니다.",
                f"예약 시 방문 위치(지역 또는 가까운 역), 희망 시간, 코스(60·90·120분), 인원을 함께 말씀해 주시면 빠르게 안내드립니다.",
                "임신 중이거나 피부·건강상 주의가 필요한 상황, 피하고 싶은 향·부위가 있으면 미리 알려주시면 무리하지 않도록 진행합니다."]),
            (f"{t['name']}, 어디서 받을 수 있나요", [
                f"{t['name']}는 인천 전지역(2군 8구)으로 방문합니다. 자택·오피스텔·숙소 등 원하시는 곳에서 받으실 수 있습니다.",
                "지역별 안내는 <a href='/incheon/area/'>지역별 안내</a>, 역세권은 <a href='/incheon/stations/'>지하철역별 안내</a>에서 확인하세요.",
                "지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 예약 시 위치와 테마를 함께 말씀해 주시면 안내드립니다."]),
        ]
        faq = [
            (f"{t['name']}는 어떤 관리인가요?", t["intro"]),
            (f"{t['name']}는 다른 관리와 무엇이 다른가요?", t["diff"]),
            (f"{t['name']}는 누구에게 잘 맞나요?", "· ".join(t["fit"]) + " 등에게 권해드립니다."),
            ("어디까지 방문하나요?", "인천 전지역(2군 8구)으로 방문하며, 위치에 따라 도착 시간을 예약 시 안내드립니다."),
        ]
        content_page(f"/theme/{slug}/", "theme", tt + [(None, t["name"])],
            title=f"{t['name']} | 인천 출장마사지·홈타이 {t['name']} 방문 안내",
            desc=f"인천 출장마사지·홈타이 {t['name']} 안내 - {t['summary']} 진행 방식, 적합한 분, 다른 테마와의 차이와 방문 안내를 확인하세요.",
            eyebrow=f"THEME · {t['kicker']}", h1=f"{t['name']} 출장마사지·홈타이", lead=t["summary"],
            show_price=True,
            sections=sections, faq=faq,
            data_note=f"{t['name']}는 인천 전지역 방문으로 운영되며, 90분 구성 선택 비율이 가장 높습니다. 예약 시 선호 압·집중 부위를 알려주시면 방문이 매끄럽습니다.",
            service=(f"{t['name']}", f"인천 전지역 방문 {t['name']} 관리"),
            cta_title=f"{t['name']} 방문 예약을 도와드릴까요?")


# ---- 코스 허브 + 코스 페이지 ---------------------------------------------
def build_course():
    trail = [("/", "홈"), (None, "코스안내")]
    course_faq = [
        ("코스는 어떻게 선택하나요?", "컨디션과 목적을 말씀해 주시면 피로 회복·아로마·스포츠·홈타이 중 적합한 코스를 안내드립니다."),
        ("커플·가족 관리는 어떻게 진행되나요?", "두 분이 같은 공간에서 동시에 받는 동반 관리이며, 인원과 시간에 따라 요금이 달라집니다."),
        ("기업·단체 관리도 되나요?", "워크숍·행사 등 단체 인원은 사전 협의 후 별도 견적으로 안내드립니다."),
        ("표시된 요금 외 추가 비용이 있나요?", "정찰 요금을 원칙으로 하며, 변동 사항은 예약 시 사전에 안내드립니다."),
    ]
    course_cards = "".join(
        f'<a class="card reveal" href="/course/{c["slug"]}/"><div class="k">{c["kicker"]}</div>'
        f'<h3>{c["name"]}</h3><p>{c["desc"]}</p><span class="more">코스 보기 →</span></a>'
        for c in COURSES)
    more_cards = (
        '<a class="card reveal" href="/course/price/"><div class="k">PRICE</div>'
        '<h3>가격 안내</h3><p>코스별 60·90·120분 정찰 요금과 변동 요소를 안내합니다.</p>'
        '<span class="more">가격 보기 →</span></a>'
        '<a class="card reveal" href="/course/guide/"><div class="k">GUIDE</div>'
        '<h3>코스 선택 가이드</h3><p>목적·상황별 추천과 시간 선택 기준을 안내합니다.</p>'
        '<span class="more">가이드 보기 →</span></a>')
    body = (breadcrumb(trail) +
        '<section class="block" id="all"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>COURSE</span>'
        '<h2 class="sec">전체 코스</h2>'
        '<p class="sec-lead">목적과 컨디션에 맞춰 고를 수 있는 인천 세븐 마사지의 방문 관리 코스입니다. 코스를 눌러 상세 안내를 확인하세요.</p>'
        f'<div class="grid g3" style="margin-top:26px">{course_cards}</div></div></section>' +
        price_menu_block() +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>MORE</span>'
        '<h2 class="sec">가격과 코스 선택</h2>'
        f'<div class="grid g2" style="margin-top:24px">{more_cards}</div></div></section>' +
        faq_block(course_faq) + cta_band())
    jsonld = [bc_ld(trail),
              service_ld("방문 마사지 코스", "피로 회복·아로마·스포츠·홈타이·커플·가족·기업·단체 방문 관리 코스", "/course/"),
              offer_ld(), faq_ld(course_faq)]
    write("/course/", page("/course/",
        "코스안내 | 인천 출장마사지 피로회복·아로마·스포츠·홈타이 요금",
        "인천 출장마사지·홈타이 코스안내 - 피로 회복, 아로마, 스포츠, 홈타이, 커플·가족, 기업·단체 관리의 코스 설명과 정찰 요금을 안내합니다.",
        "course", body, jsonld))

def build_course_pages():
    ct = [("/", "홈"), ("/course/", "코스안내")]

    content_page("/course/fatigue/", "course", ct + [(None, "피로 회복 관리")],
        title="피로 회복 관리 | 인천 출장마사지 스웨디시 계열 방문 관리",
        desc="인천 출장마사지 피로 회복 관리 안내 - 전신 긴장을 부드럽게 풀어주는 스웨디시 계열 방문 관리입니다. 대상, 60·90·120분 진행 방식, 방문 관리의 장점과 FAQ를 확인하세요.",
        eyebrow="COURSE · 피로 회복", h1="피로 회복 관리",
        lead="전신의 근육 긴장을 부드럽게 풀어주는 스웨디시 계열 기본 방문 관리입니다.",
        sections=[
            ("피로 회복 관리란 무엇인가요", [
                "피로 회복 관리는 전신의 근육 긴장을 부드럽게 풀어주는 스웨디시 계열의 기본 방문 관리입니다.",
                "강한 자극보다 일정한 압과 리듬으로 혈행과 이완을 돕는 데 초점을 둡니다.",
                "의료적 치료가 아니라, 하루의 피로를 정리하고 휴식의 질을 높이기 위한 <strong>건강관리 목적</strong>의 관리입니다."]),
            ("이런 분께 권해드립니다", [
                ("ul", ["장시간 앉아 일해 어깨·목·허리가 자주 뭉치는 분",
                        "잠들기 전 몸의 긴장을 풀고 수면의 질을 높이고 싶은 분",
                        "강한 지압보다 부드럽고 편안한 이완을 선호하는 분",
                        "출장·야근으로 마사지숍을 방문할 시간을 내기 어려운 분"])]),
            ("60·90·120분 진행 방식", [
                "60분은 어깨·등·다리 등 피로가 집중된 부위를 중심으로 전신을 한 차례 정리합니다.",
                "90분은 가장 많이 선택되는 구성으로, 전신을 고르게 풀고 뭉친 부위에 시간을 더 배분합니다.",
                "120분은 전신을 충분히 이완한 뒤 두피·발 등 마무리 케어까지 여유 있게 진행합니다.",
                "관리 시작 전 선호하는 압의 세기와 집중 부위를 확인하고, 진행 중에도 조절해 드립니다."]),
            ("방문 관리이기에 더 좋은 점", [
                "관리 직후 이동 없이 그대로 쉴 수 있어 이완 상태가 오래 유지됩니다.",
                "익숙한 공간에서 받기 때문에 긴장이 덜하고 편안합니다.",
                "인천 전지역으로 방문하며, 위치에 따라 평균 도착 시간을 예약 시 안내드립니다."]),
            ("관리 당일, 이렇게 진행됩니다", [
                "관리사가 도착하면 가볍게 인사를 나누고, 편히 누우실 수 있도록 공간을 정돈합니다.",
                "본격적인 관리 전에 선호하는 압의 세기와 특히 풀고 싶은 부위를 확인합니다.",
                "관리는 호흡을 고르며 큰 근육부터 차례로 이완하고, 뭉친 부위는 시간을 더 들여 풀어드립니다.",
                "마지막에는 마무리 정돈과 함께 수분 섭취·휴식을 안내하며 관리를 마칩니다."]),
            ("이렇게 준비하면 더 좋습니다", [
                "관리 전 가벼운 샤워로 몸을 따뜻하게 하면 이완이 한결 수월합니다.",
                "과식 직후보다는 식사 후 어느 정도 시간이 지난 뒤가 편안합니다.",
                "편안한 복장과 조용한 분위기를 준비해 두시면 휴식의 질이 높아집니다.",
                "받고 난 뒤 좋았던 압·부위를 기억해 두면 다음 방문 때 더 잘 맞춰 드릴 수 있습니다."]),
            ("피로 회복 관리, 어디서 받을 수 있나요", [
                "피로 회복 관리는 인천 전지역(2군 8구)으로 방문합니다. 부평·주안·송도·구월·청라 등 구·군과 역세권 인근 어디서든 받으실 수 있습니다.",
                "지역별 안내는 <a href='/incheon/area/'>지역별 안내</a>, 역세권은 <a href='/incheon/stations/'>지하철역별 안내</a>에서 확인하실 수 있습니다.",
                "예약 시 위치와 희망 시간·인원을 함께 말씀해 주시면 방문 가능 여부를 빠르게 안내드립니다. 예약 흐름은 <a href='/reservation/'>예약안내</a>, 처음이시라면 <a href='/guide/'>이용가이드</a>에서 확인하세요.",
                "방문 가능 지역과 도착 시간은 <a href='/incheon/coverage/'>인천 전지역 방문 가능 안내</a>와 <a href='/incheon/hours/'>예약 가능 시간</a>에서, 위생·안전 기준은 <a href='/incheon/safety/'>위생 및 안전 안내</a>에서 확인하실 수 있습니다.",
                "지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 같은 안내를 중복하지 않도록 코스·지역·역·테마를 각각 분리해 안내합니다."]),
        ],
        data_note="피로 회복 관리는 90분 구성 선택 비율이 가장 높습니다. 주중 21~24시 예약이 가장 많아, 해당 시간대는 도착 시간을 넉넉히 안내드립니다.",
        faq=[
            ("피로 회복 관리와 아로마 관리는 어떻게 다른가요?", "피로 회복 관리는 전신 이완에, 아로마 관리는 블렌딩 오일의 향을 더한 이완에 중점을 둡니다. 향에 민감하지 않다면 피로 회복 관리로 시작하셔도 좋습니다."),
            ("압이 너무 세거나 약하면 조절되나요?", "네. 시작 전과 진행 중 언제든 압의 세기를 말씀해 주시면 맞춰 드립니다."),
            ("관리 후 주의할 점이 있나요?", "충분한 수분 섭취와 휴식을 권장드립니다. 통증·부상이 있는 부위는 무리하지 않습니다.")],
        service=("피로 회복 관리", "인천 전지역 방문 스웨디시 계열 전신 이완 관리"))

    content_page("/course/aroma/", "course", ct + [(None, "아로마 관리")],
        title="아로마 관리 | 인천 출장마사지 아로마 오일 방문 관리",
        desc="인천 출장마사지 아로마 관리 안내 - 블렌딩 오일의 향과 촉감으로 심신을 이완하는 방문 관리입니다. 사용 오일, 사전 확인사항, 진행 방식과 피로 회복 관리와의 차이를 확인하세요.",
        eyebrow="COURSE · 아로마", h1="아로마 관리",
        lead="블렌딩한 관리용 오일을 사용해 향과 촉감으로 심신을 함께 이완하는 방문 관리입니다.",
        sections=[
            ("아로마 관리의 특징", [
                "아로마 관리는 블렌딩한 관리용 오일을 사용해 향과 촉감으로 심신을 함께 이완하는 방문 관리입니다.",
                "오일이 피부 위에서 부드럽게 미끄러지며 마찰을 줄여, 더 유연하고 감각적인 이완을 돕습니다.",
                "향을 통한 심리적 이완이 더해져, 긴장도가 높거나 예민한 날에 특히 선호됩니다."]),
            ("사용 오일과 사전 확인", [
                "라벤더 계열의 차분한 향, 시트러스 계열의 가벼운 향 등 그날의 컨디션에 맞춰 안내드립니다.",
                "피부가 민감하거나 특정 향·성분에 알러지가 있다면 예약 시 미리 알려주세요.",
                "임신 중이거나 피부 질환이 있는 경우, 무리하지 않도록 사전에 상담드립니다."]),
            ("진행 방식", [
                "60분은 어깨·등을 중심으로 오일 관리를 진행합니다.",
                "90분은 전신을 고르게 아우르는 가장 표준적인 구성입니다.",
                "120분은 전신 이완 후 두피·발 마무리까지 포함해 여유 있게 진행합니다."]),
            ("피로 회복 관리와의 차이", [
                "피로 회복 관리가 근육 이완 자체에 집중한다면, 아로마 관리는 여기에 향의 이완을 더합니다.",
                "오일을 사용하므로 마무리 단계에서 수건으로 가볍게 정돈해 과도한 잔여감을 줄입니다."]),
            ("오일이 만드는 차이", [
                "오일을 사용하면 손과 피부 사이의 마찰이 줄어, 같은 동작도 더 부드럽고 깊게 전달됩니다.",
                "끊김 없이 이어지는 긴 동작이 가능해 호흡이 느려지고 긴장이 천천히 가라앉습니다.",
                "건식 관리에서 자극이 부담스러웠던 분도 비교적 편안하게 받을 수 있습니다."]),
            ("관리 당일 진행 순서", [
                "도착 후 그날의 컨디션과 선호 향을 확인하고 오일을 준비합니다.",
                "어깨·등 등 넓은 부위부터 오일을 펴 바르며 이완을 시작합니다.",
                "전신을 고르게 아우른 뒤, 마무리 단계에서 수건으로 정돈해 잔여감을 줄입니다."]),
            ("관리 후 이렇게 케어하세요", [
                "관리 후에는 따뜻한 물을 충분히 마시고 무리한 활동을 피해 휴식을 권장드립니다.",
                "오일 잔여감이 신경 쓰이면 가벼운 샤워로 마무리하셔도 좋습니다."]),
            ("아로마 관리, 어디서 받을 수 있나요", [
                "아로마 관리는 인천 전지역(2군 8구)으로 방문합니다. 부평·주안·송도·구월·청라 등 구·군과 역세권 인근 어디서든 받으실 수 있습니다.",
                "지역별 안내는 <a href='/incheon/area/'>지역별 안내</a>, 역세권은 <a href='/incheon/stations/'>지하철역별 안내</a>에서 확인하실 수 있습니다.",
                "예약 시 위치와 희망 시간·인원을 함께 말씀해 주시면 방문 가능 여부를 빠르게 안내드립니다. 예약 흐름은 <a href='/reservation/'>예약안내</a>, 처음이시라면 <a href='/guide/'>이용가이드</a>에서 확인하세요.",
                "방문 가능 지역과 도착 시간은 <a href='/incheon/coverage/'>인천 전지역 방문 가능 안내</a>와 <a href='/incheon/hours/'>예약 가능 시간</a>에서, 위생·안전 기준은 <a href='/incheon/safety/'>위생 및 안전 안내</a>에서 확인하실 수 있습니다.",
                "지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 같은 안내를 중복하지 않도록 코스·지역·역·테마를 각각 분리해 안내합니다."]),
            ("향과 컨디션에 맞춘 선택", [
                "차분한 휴식을 원하면 라벤더 계열, 가볍고 산뜻한 기분을 원하면 시트러스 계열을 권해드립니다.",
                "특별히 선호하는 향이 없으시면 그날의 컨디션을 듣고 알맞은 향을 추천드립니다.",
                "향에 민감하거나 알러지가 있으면 예약 시 알려주시면 무리하지 않도록 조정합니다.",
            ]),
        ],
        data_note="아로마 관리는 금요일·주말 저녁 예약 비율이 평일보다 높습니다. 향 선호가 뚜렷한 고객이 많아, 예약 시 선호 향을 함께 받아두면 방문이 매끄럽습니다.",
        faq=[
            ("향을 선택할 수 있나요?", "네. 라벤더·시트러스 등 계열을 안내드리며, 선호가 없으시면 컨디션에 맞춰 추천드립니다."),
            ("오일 알러지가 걱정됩니다.", "민감성 피부나 알러지가 있으면 예약 시 알려주세요. 무리하지 않도록 조정합니다."),
            ("관리 후 끈적임이 남지 않나요?", "마무리 단계에서 수건으로 정돈해 드려 과도한 잔여감을 줄입니다.")],
        service=("아로마 관리", "인천 전지역 방문 아로마 오일 이완 관리"))

    content_page("/course/sports/", "course", ct + [(None, "스포츠 관리")],
        title="스포츠 관리 | 인천 출장마사지 운동 후 근육 방문 관리",
        desc="인천 출장마사지 스포츠 관리 안내 - 운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 방문 관리입니다. 적합한 상황, 진행 방식, 주의사항을 확인하세요.",
        eyebrow="COURSE · 스포츠", h1="스포츠 관리",
        lead="운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 방문 관리입니다.",
        sections=[
            ("스포츠 관리란", [
                "스포츠 관리는 운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 방문 관리입니다.",
                "근육 부위를 따라 비교적 또렷한 압으로 풀어, 운동으로 누적된 피로를 정리하는 데 도움을 줍니다.",
                "전문 재활·치료가 아닌, 일상 운동 후의 컨디션 관리 목적임을 안내드립니다."]),
            ("이런 상황에 잘 맞습니다", [
                ("ul", ["러닝·헬스·등산 등 운동 후 다리·등 근육이 무거운 날",
                        "주말 과한 활동으로 다음 날 컨디션을 빠르게 정리하고 싶을 때",
                        "평소보다 또렷한 압의 관리를 선호하는 분"])]),
            ("진행 방식", [
                "관리 전 운동 종류와 뭉친 부위를 확인해 시간을 집중 배분합니다.",
                "60분은 하체 또는 상체 등 특정 부위 중심, 90·120분은 전신을 고르게 풀며 집중 부위를 추가합니다.",
                "압이 강하게 느껴지면 즉시 조절하니 편하게 말씀해 주세요."]),
            ("주의사항 (꼭 읽어주세요)", [
                "부상·염좌·심한 통증이 있는 부위는 관리 대상이 아니며, 해당 증상은 의료기관 진료를 권유드립니다.",
                "본 관리는 의료 행위가 아닌 건강관리 서비스이며, 통증 완화·치료를 보장하지 않습니다."]),
            ("부위별 접근 방식", [
                "하체는 허벅지·종아리 등 큰 근육을 따라 또렷한 압으로 무거움을 정리합니다.",
                "등·어깨는 운동 자세로 자주 긴장되는 부위라 시간을 더 배분합니다.",
                "관리 중 통증과 시원함의 경계를 확인하며 강약을 세밀하게 조절합니다."]),
            ("관리 당일 진행 순서", [
                "도착 후 어떤 운동을 했는지, 어느 부위가 무거운지 확인합니다.",
                "근육을 데우듯 가볍게 시작해 점차 압을 높이며 집중 부위를 풀어드립니다.",
                "마무리 단계에서는 가볍게 이완하며 호흡을 고르고 관리를 마칩니다."]),
            ("운동 루틴과 함께하면 좋은 점", [
                "규칙적으로 운동하는 분은 무리한 날 컨디션을 빠르게 정리하는 용도로 활용하기 좋습니다.",
                "다만 통증이 반복되거나 심해지면 관리보다 의료기관 진료를 먼저 권유드립니다."]),
            ("스포츠 관리, 어디서 받을 수 있나요", [
                "스포츠 관리는 인천 전지역(2군 8구)으로 방문합니다. 부평·주안·송도·구월·청라 등 구·군과 역세권 인근 어디서든 받으실 수 있습니다.",
                "지역별 안내는 <a href='/incheon/area/'>지역별 안내</a>, 역세권은 <a href='/incheon/stations/'>지하철역별 안내</a>에서 확인하실 수 있습니다.",
                "예약 시 위치와 희망 시간·인원을 함께 말씀해 주시면 방문 가능 여부를 빠르게 안내드립니다. 예약 흐름은 <a href='/reservation/'>예약안내</a>, 처음이시라면 <a href='/guide/'>이용가이드</a>에서 확인하세요.",
                "방문 가능 지역과 도착 시간은 <a href='/incheon/coverage/'>인천 전지역 방문 가능 안내</a>와 <a href='/incheon/hours/'>예약 가능 시간</a>에서, 위생·안전 기준은 <a href='/incheon/safety/'>위생 및 안전 안내</a>에서 확인하실 수 있습니다.",
                "지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 같은 안내를 중복하지 않도록 코스·지역·역·테마를 각각 분리해 안내합니다."]),
            ("스포츠 관리 전후 안내", [
                "운동 직후보다는 1~2시간 휴식 후 받는 것이 근육 회복에 도움이 됩니다.",
                "관리 후에는 충분한 수분 섭취와 가벼운 스트레칭, 휴식을 권장드립니다.",
                "통증이 반복되거나 부기·열감이 있는 부위는 관리보다 의료기관 진료를 먼저 권유드립니다.",
            ]),
        ],
        data_note="스포츠 관리는 주말(토·일) 오전~오후 예약 비율이 다른 코스보다 높습니다. 운동 직후보다는 1~2시간 휴식 후 관리를 권장드립니다.",
        faq=[
            ("운동 직후 바로 받아도 되나요?", "가벼운 휴식 후 받는 것을 권장드립니다. 심한 통증이 있다면 무리하지 않습니다."),
            ("강도가 센 편인가요?", "근육 부위에 또렷한 압을 사용하지만, 선호에 맞춰 강약을 조절합니다."),
            ("부상이 있어도 받을 수 있나요?", "부상·급성 통증 부위는 관리 대상이 아니며 의료기관 진료를 권유드립니다.")],
        service=("스포츠 관리", "인천 전지역 방문 운동 후 근육 컨디션 관리"))

    content_page("/course/hometai/", "course", ct + [(None, "홈타이 코스")],
        title="홈타이 코스 | 인천 출장마사지 자택·숙소 방문 타이 관리",
        desc="인천 출장마사지 홈타이 코스 안내 - 자택·오피스텔·숙소로 방문하는 타이·스트레칭 계열 관리입니다. 진행 방식, 준비, 방문 관리의 장점을 확인하세요.",
        eyebrow="COURSE · 홈타이", h1="홈타이 코스",
        lead="자택·숙소로 방문해 받는 타이·스트레칭 계열 방문 관리입니다.",
        sections=[
            ("홈타이 코스란", [
                "홈타이 코스는 관리사가 고객이 계신 곳으로 방문해 옷을 입은 상태에서 스트레칭과 지압 중심으로 진행하는 타이 계열 관리입니다.",
                "오일 없이 몸의 유연성과 순환을 돕는 데 초점을 두며, 원하시면 오일 관리와 함께 구성할 수 있습니다."]),
            ("이런 분께 권해드립니다", [
                ("ul", ["몸이 뻣뻣하고 유연성이 떨어진다고 느끼는 분",
                        "지압과 스트레칭을 선호하는 분",
                        "집에서 편하게 받고 바로 쉬고 싶은 분"])]),
            ("진행 방식", [
                "60분은 핵심 부위 위주, 90분은 전신을 고르게, 120분은 마무리 케어까지 여유 있게 진행합니다.",
                "스트레칭 동작이 포함되므로 편안한 복장과 누울 공간을 준비해 주세요."]),
            ("방문 전 준비", [
                "두 사람이 누울 수 있는 평평한 공간이면 충분합니다.",
                "정확한 주소와 출입 방법은 <a href='/incheon/checklist/'>이용 전 확인사항</a>에서 확인하실 수 있습니다."]),
            ("방문 관리이기에 더 좋은 점", [
                "매장을 찾지 않고 익숙한 공간에서 받기 때문에 긴장이 덜하고 편안합니다.",
                "관리 직후 이동 없이 그대로 쉴 수 있어 이완 상태가 오래 유지됩니다.",
                "인천 전지역으로 방문하며, 위치에 따라 평균 도착 시간을 예약 시 안내드립니다."]),
            ("관리 당일 진행 순서", [
                "관리사가 도착하면 가볍게 인사를 나누고 누울 공간을 정돈한 뒤, 선호하는 압과 집중 부위를 확인합니다.",
                "스트레칭과 지압을 중심으로 큰 부위부터 차례로 풀어주며, 관절 가동 범위를 살피며 진행합니다.",
                "마무리 단계에서는 호흡을 고르며 가볍게 이완하고 수분 섭취·휴식을 안내합니다."]),
            ("홈타이 코스, 어디서 받을 수 있나요", [
                "홈타이 코스는 인천 전지역(2군 8구)으로 방문합니다. 부평·주안·송도·구월·청라 등 구·군과 역세권 인근 어디서든 받으실 수 있습니다.",
                "지역별 안내는 <a href='/incheon/area/'>지역별 안내</a>, 역세권은 <a href='/incheon/stations/'>지하철역별 안내</a>에서 확인하실 수 있습니다.",
                "예약 시 위치와 희망 시간·인원을 함께 말씀해 주시면 방문 가능 여부를 빠르게 안내드립니다. 예약 흐름은 <a href='/reservation/'>예약안내</a>, 처음이시라면 <a href='/guide/'>이용가이드</a>에서 확인하세요.",
                "방문 가능 지역과 도착 시간은 <a href='/incheon/coverage/'>인천 전지역 방문 가능 안내</a>와 <a href='/incheon/hours/'>예약 가능 시간</a>에서, 위생·안전 기준은 <a href='/incheon/safety/'>위생 및 안전 안내</a>에서 확인하실 수 있습니다.",
                "지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 같은 안내를 중복하지 않도록 코스·지역·역·테마를 각각 분리해 안내합니다."]),
            ("홈타이와 일반 출장마사지의 차이", [
                "홈타이는 옷을 입은 상태에서 스트레칭과 지압을 중심으로 진행하는 타이 계열 관리이고, 오일 관리(스웨디시·아로마)는 오일을 사용한 부드러운 쓸어내림이 중심입니다.",
                "두 방식은 목적이 다르며, 몸이 뻣뻣해 가동 범위를 넓히고 싶다면 홈타이가, 향과 함께 깊게 이완하고 싶다면 오일 관리가 잘 맞습니다.",
                "원하시면 타이와 오일 관리를 함께 구성할 수 있으니, 예약 시 선호하는 방식을 말씀해 주세요.",
            ]),
            ("홈타이 코스 예약 안내", [
                "예약 시 방문 위치(지역 또는 가까운 역), 희망 시간, 코스 시간(60·90·120분)을 함께 말씀해 주시면 빠르게 안내드립니다.",
                "처음이시라면 90분 구성으로 전신을 고르게 받아보시길 권합니다.",
            ]),
        ],
        data_note="홈타이 코스는 평일 밤 시간대 문의가 가장 많습니다. 원룸·숙소도 진행 가능하니 예약 시 환경을 알려주시면 알맞게 안내드립니다.",
        faq=[
            ("홈타이와 일반 마사지는 무엇이 다른가요?", "홈타이는 스트레칭과 지압 중심의 타이 계열 관리로, 오일 관리(스웨디시·아로마)와 방식이 다릅니다."),
            ("오일도 함께 받을 수 있나요?", "네. 원하시면 타이와 오일 관리를 함께 구성할 수 있습니다."),
            ("좁은 공간도 가능한가요?", "두 사람이 누울 공간이면 충분하며, 원룸·숙소도 진행 가능합니다.")],
        service=("홈타이 코스", "인천 전지역 자택·숙소 방문 타이 관리"))

    content_page("/course/couple/", "course", ct + [(None, "커플·가족 방문 관리")],
        title="커플·가족 방문 관리 | 인천 출장마사지 2인 동반 관리",
        desc="인천 출장마사지 커플·가족 방문 관리 안내 - 두 분이 같은 공간에서 동시에 받는 동반형 방문 관리입니다. 공간·인원 조건, 예약 방법, 요금 구조를 확인하세요.",
        eyebrow="COURSE · 커플·가족", h1="커플·가족 방문 관리",
        lead="두 분이 같은 공간에서 동시에 관리를 받는 동반형 방문 관리입니다.",
        sections=[
            ("커플·가족 방문 관리란", [
                "두 분이 같은 공간에서 동시에 관리를 받는 동반형 방문 관리입니다.",
                "커플은 물론, 부모님과 함께 등 가족 단위로도 이용하실 수 있습니다.",
                "각자 원하는 코스(피로 회복·아로마 등)를 다르게 선택할 수 있습니다."]),
            ("공간과 인원 조건", [
                "동시에 관리가 진행되므로 관리사 2인이 방문하며, 두 사람이 누울 수 있는 공간이 필요합니다.",
                "공간이 협소한 경우 순차 진행으로 안내드릴 수 있어, 예약 시 환경을 알려주세요."]),
            ("예약 방법", [
                "동반 관리는 일정 조율이 필요해 사전 협의 예약을 권장드립니다.",
                "희망 코스, 인원, 시간, 방문 장소를 말씀해 주시면 가능한 시간을 확정해 드립니다."]),
            ("요금 안내", [
                "커플·가족 방문 관리는 인원과 시간에 따라 요금이 책정됩니다.",
                "기본 요금은 <a href='/course/price/'>가격 안내</a>에서 확인하실 수 있으며, 정확한 금액은 상담 시 안내드립니다."]),
            ("어떤 분들이 함께 받나요", [
                "기념일을 함께 보내려는 커플, 부모님께 휴식을 선물하려는 가족, 오랜만에 만난 친구 등 다양합니다.",
                "두 분이 같은 시간에 나란히 이완할 수 있어, 혼자 받을 때와는 다른 편안함이 있습니다.",
                "각자 컨디션이 다르면 한 분은 피로 회복, 다른 한 분은 아로마처럼 다르게 선택하셔도 됩니다."]),
            ("공간 준비 가이드", [
                "두 사람이 동시에 누울 수 있는 평평한 공간이 있으면 동시 진행이 가능합니다.",
                "원룸·호텔 등 공간이 좁다면 한 분씩 순차로 진행하는 방식으로 안내드립니다.",
                "예약 시 방의 크기나 환경을 알려주시면 알맞은 방식을 미리 정해 드립니다."]),
            ("관리 당일 진행 순서", [
                "관리사 2인이 함께 도착해 각자 담당을 정하고 공간을 준비합니다.",
                "두 분의 선호 압·코스를 각각 확인한 뒤 동시에 관리를 시작합니다.",
                "마무리도 함께 정돈하여 두 분이 비슷한 시점에 휴식에 들어가도록 합니다."]),
            ("커플·가족 방문 관리, 어디서 받을 수 있나요", [
                "커플·가족 방문 관리는 인천 전지역(2군 8구)으로 방문합니다. 부평·주안·송도·구월·청라 등 구·군과 역세권 인근 어디서든 받으실 수 있습니다.",
                "지역별 안내는 <a href='/incheon/area/'>지역별 안내</a>, 역세권은 <a href='/incheon/stations/'>지하철역별 안내</a>에서 확인하실 수 있습니다.",
                "예약 시 위치와 희망 시간·인원을 함께 말씀해 주시면 방문 가능 여부를 빠르게 안내드립니다. 예약 흐름은 <a href='/reservation/'>예약안내</a>, 처음이시라면 <a href='/guide/'>이용가이드</a>에서 확인하세요.",
                "방문 가능 지역과 도착 시간은 <a href='/incheon/coverage/'>인천 전지역 방문 가능 안내</a>와 <a href='/incheon/hours/'>예약 가능 시간</a>에서, 위생·안전 기준은 <a href='/incheon/safety/'>위생 및 안전 안내</a>에서 확인하실 수 있습니다.",
                "지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 같은 안내를 중복하지 않도록 코스·지역·역·테마를 각각 분리해 안내합니다."]),
            ("예약 전 알아두면 좋은 점", [
                "동반 관리는 관리사 2인의 일정을 함께 맞춰야 해, 원하는 시간이 있다면 1~2일 전 예약을 권장드립니다.",
                "두 분의 코스·시간을 다르게 구성할 수 있어, 한 분은 60분·다른 한 분은 90분처럼 맞추는 것도 가능합니다.",
                "공간이 좁아 동시 진행이 어려우면 순차 진행으로 안내드리니, 예약 시 방의 환경을 알려주세요.",
            ]),
        ],
        data_note="동반 관리는 기념일·주말 저녁 문의가 집중됩니다. 관리사 2인 일정 조율이 필요하므로 가급적 1~2일 전 예약을 권장드립니다.",
        faq=[
            ("두 사람이 다른 코스를 받을 수 있나요?", "네. 각자 원하는 코스를 선택하실 수 있습니다."),
            ("좁은 공간에서도 가능한가요?", "두 분이 동시에 누울 공간이 어려우면 순차 진행으로 안내드립니다."),
            ("당일 예약도 되나요?", "관리사 2인 일정상 사전 예약을 권장드립니다. 당일은 가능 여부를 상담으로 확인해 드립니다.")],
        service=("커플·가족 방문 관리", "인천 전지역 2인 동반 방문 관리"))

    content_page("/course/group/", "course", ct + [(None, "기업·단체 방문 관리")],
        title="기업·단체 방문 관리 | 인천 출장마사지 단체·행사 관리",
        desc="인천 출장마사지 기업·단체 방문 관리 안내 - 워크숍·행사·사내 복지 등 단체 인원을 위한 사전 협의형 방문 관리입니다. 진행 방식, 견적·결제, 사전 준비를 확인하세요.",
        eyebrow="COURSE · 기업·단체", h1="기업·단체 방문 관리",
        lead="워크숍·행사·사내 복지 등 단체 인원을 대상으로 하는 사전 협의형 방문 관리입니다.",
        sections=[
            ("기업·단체 방문 관리란", [
                "워크숍·행사·사내 복지 등 단체 인원을 대상으로 하는 사전 협의형 방문 관리입니다.",
                "여러 명이 순차 또는 동시에 관리를 받을 수 있도록 일정을 구성합니다."]),
            ("진행 방식", [
                "인원수, 1인당 관리 시간, 희망 날짜와 장소를 먼저 확인합니다.",
                "행사 성격에 맞춰 짧은 의자형 케어부터 표준 코스까지 구성할 수 있습니다.",
                "관리사 인원과 진행 순서를 사전에 설계해 현장 운영을 매끄럽게 합니다."]),
            ("견적과 결제", [
                "단체 관리는 인원·시간·장소에 따라 별도 견적으로 안내드립니다.",
                "세금계산서 등 결제 방식은 사전에 협의해 드립니다."]),
            ("사전 준비", [
                "관리에 적합한 공간(조용한 회의실·라운지 등)과 콘센트, 대기 동선을 확인해 주세요.",
                "행사 일정이 정해지면 가급적 여유 있게 문의해 주시면 원활합니다."]),
            ("어떤 행사에 적합한가요", [
                "사내 워크숍이나 단합 행사에서 직원 복지 프로그램으로 활용하기 좋습니다.",
                "장시간 행사 중간의 휴식 코너, 야유회·연수 등의 부대 프로그램으로도 구성할 수 있습니다.",
                "인원과 시간을 고려해 짧고 가벼운 케어부터 표준 코스까지 유연하게 맞춰 드립니다."]),
            ("현장 운영 순서", [
                "행사 전 인원·시간표·동선을 협의해 관리사 수와 진행 순서를 설계합니다.",
                "당일에는 안내 동선을 미리 잡아 대기 시간을 줄이고 순환이 매끄럽도록 운영합니다.",
                "여러 명이 동시에 받을 경우 관리사를 늘려 전체 진행 시간을 단축합니다.",
                "행사 종료 후에는 사용 공간을 정돈하고 마무리합니다."]),
            ("사전 준비 체크리스트", [
                ("ul", ["참여 인원과 1인당 희망 시간", "행사 날짜·시간과 장소(주소)",
                        "관리 진행이 가능한 공간(회의실·라운지 등)", "콘센트·대기 동선 등 현장 여건"])]),
            ("기업·단체 방문 관리, 어디서 받을 수 있나요", [
                "기업·단체 방문 관리는 인천 전지역(2군 8구)으로 방문합니다. 부평·주안·송도·구월·청라 등 구·군과 역세권 인근 어디서든 받으실 수 있습니다.",
                "지역별 안내는 <a href='/incheon/area/'>지역별 안내</a>, 역세권은 <a href='/incheon/stations/'>지하철역별 안내</a>에서 확인하실 수 있습니다.",
                "예약 시 위치와 희망 시간·인원을 함께 말씀해 주시면 방문 가능 여부를 빠르게 안내드립니다. 예약 흐름은 <a href='/reservation/'>예약안내</a>, 처음이시라면 <a href='/guide/'>이용가이드</a>에서 확인하세요.",
                "방문 가능 지역과 도착 시간은 <a href='/incheon/coverage/'>인천 전지역 방문 가능 안내</a>와 <a href='/incheon/hours/'>예약 가능 시간</a>에서, 위생·안전 기준은 <a href='/incheon/safety/'>위생 및 안전 안내</a>에서 확인하실 수 있습니다.",
                "지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 같은 안내를 중복하지 않도록 코스·지역·역·테마를 각각 분리해 안내합니다."]),
            ("행사 후 마무리", [
                "행사 종료 후 사용한 공간을 정돈하고, 진행 결과를 간단히 정리해 전달드릴 수 있습니다.",
                "정기적인 사내 복지로 운영하실 경우, 다음 일정 협의도 함께 도와드립니다.",
                "인원·시간·장소가 정해지면 가능한 한 빨리 문의해 주실수록 관리사 배치와 동선 설계가 수월합니다.",
            ]),
            ("문의는 이렇게 주세요", [
                "참여 인원과 1인당 희망 시간, 행사 날짜·장소, 현장 여건(공간·콘센트 등)을 함께 알려주시면 견적과 진행안을 빠르게 안내드립니다.",
                "정기 복지 프로그램으로 운영을 검토 중이시라면 장기 일정 협의도 도와드립니다.",
            ]),
        ],
        data_note="기업·단체 관리는 분기 말·연말 사내 행사 시즌에 문의가 늘어납니다. 관리사 배치를 위해 최소 며칠 전 협의를 권장드립니다.",
        faq=[
            ("최소 인원 제한이 있나요?", "인원에 맞춰 구성하며, 정확한 기준은 문의 시 안내드립니다."),
            ("세금계산서 발행이 되나요?", "네. 결제 방식은 사전 협의로 안내드립니다."),
            ("행사 장소로 방문하나요?", "네. 인천 및 인근 행사 장소로 방문 가능하며 위치를 확인해 드립니다.")],
        service=("기업·단체 방문 관리", "인천 전지역 단체·행사 방문 관리"))

    content_page("/course/price/", "course", ct + [(None, "가격 안내")],
        title="가격 안내 | 인천 출장마사지 코스별 정찰 요금",
        desc="인천 출장마사지·홈타이 가격 안내 - 코스별 60·90·120분 기본 요금과 정찰 요금 원칙, 변동 요소, 결제 안내를 제공합니다. 숨겨진 추가 비용 없이 투명하게 안내합니다.",
        eyebrow="COURSE · 가격", h1="가격 안내",
        lead="코스별 기본 요금을 사전에 안내하는 정찰 요금을 원칙으로 합니다.",
        sections=[
            ("정찰 요금 원칙", [
                "인천 세븐 마사지는 코스별 기본 요금을 사전에 안내하는 <strong>정찰 요금</strong>을 원칙으로 합니다.",
                "현장에서 임의로 금액을 올리거나 숨겨진 추가 비용을 청구하지 않습니다."]),
            ("코스별 기본 요금", [
                "아래 60·90·120분 기본 요금을 참고하시고, 코스 종류(피로 회복·아로마·스포츠·홈타이 등)에 따라 세부 금액이 달라질 수 있습니다."]),
            ("변동될 수 있는 요소", [
                ("ul", ["방문 지역과 이동 거리(신도시·도서·외곽 등)", "예약 시간대(심야 등)",
                        "커플·가족 등 인원 구성", "기업·단체 등 별도 견적 대상"])]),
            ("결제 안내", [
                "결제 방법은 예약 시 함께 안내드리며, 변동 사항이 있으면 사전에 고지합니다.",
                "정확한 최종 금액은 예약 상담에서 확인해 드립니다."]),
            ("요금은 이렇게 구성됩니다", [
                "기본 요금은 코스(피로 회복·아로마·스포츠·홈타이 등)와 시간(60·90·120분)의 조합으로 정해집니다.",
                "커플·가족처럼 인원이 늘어나는 경우, 관리사 수와 시간에 따라 요금이 책정됩니다.",
                "기업·단체는 인원·장소·시간 편차가 커서 별도 견적으로 안내드립니다."]),
            ("예약 시 함께 안내드리는 것", [
                "예약 상담에서는 코스 기본 요금과 함께 아래 사항을 미리 확인해 드립니다.",
                ("ul", ["선택한 코스·시간의 최종 금액", "지역·시간대에 따른 변동 여부",
                        "결제 방법과 가능한 결제 수단"])]),
            ("투명한 요금을 위한 약속", [
                "현장에서 사전 안내와 다른 금액을 요구하지 않습니다.",
                "변동이 필요한 경우 반드시 관리 전에 설명드리고 동의를 받은 뒤 진행합니다."]),
            ("가격 안내, 어디서 받을 수 있나요", [
                "가격 안내는 인천 전지역(2군 8구)으로 방문합니다. 부평·주안·송도·구월·청라 등 구·군과 역세권 인근 어디서든 받으실 수 있습니다.",
                "지역별 안내는 <a href='/incheon/area/'>지역별 안내</a>, 역세권은 <a href='/incheon/stations/'>지하철역별 안내</a>에서 확인하실 수 있습니다.",
                "예약 시 위치와 희망 시간·인원을 함께 말씀해 주시면 방문 가능 여부를 빠르게 안내드립니다. 예약 흐름은 <a href='/reservation/'>예약안내</a>, 처음이시라면 <a href='/guide/'>이용가이드</a>에서 확인하세요.",
                "방문 가능 지역과 도착 시간은 <a href='/incheon/coverage/'>인천 전지역 방문 가능 안내</a>와 <a href='/incheon/hours/'>예약 가능 시간</a>에서, 위생·안전 기준은 <a href='/incheon/safety/'>위생 및 안전 안내</a>에서 확인하실 수 있습니다.",
                "지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 같은 안내를 중복하지 않도록 코스·지역·역·테마를 각각 분리해 안내합니다."]),
            ("요금 관련 자주 묻는 점", [
                "도서·외곽(강화·옹진·영종 등)이나 심야 시간대는 이동·운영 여건에 따라 변동 요소가 더해질 수 있어, 예약 시 미리 안내드립니다.",
                "커플·가족·기업 단체는 인원과 시간에 따라 별도로 책정되며, 최종 금액은 상담에서 확정해 드립니다.",
                "표시된 기본 요금 외에 현장에서 임의로 추가되는 비용은 없습니다.",
            ]),
        ],
        data_note="가장 많이 선택되는 구성은 90분입니다. 심야(자정 이후) 예약과 도서·외곽 지역은 도착 시간과 함께 변동 요소를 미리 안내드립니다.",
        faq=[
            ("표시 요금 외에 추가 비용이 있나요?", "정찰 요금을 원칙으로 하며, 지역·시간대 등 변동 요소는 예약 시 미리 안내드립니다."),
            ("결제는 어떻게 하나요?", "결제 방법은 예약 시 안내드립니다."),
            ("코스마다 가격이 다른가요?", "네. 코스 종류에 따라 세부 금액이 달라질 수 있어 상담 시 확정해 드립니다.")],
        show_price=True,
        service=("인천 출장마사지 요금", "인천 전지역 방문 관리 정찰 요금 안내"))

    content_page("/course/guide/", "course", ct + [(None, "코스 선택 가이드")],
        title="코스 선택 가이드 | 인천 출장마사지 상황별 추천",
        desc="인천 출장마사지 코스 선택 가이드 - 목적과 상황에 맞는 코스 추천, 60·90·120분 시간 선택 기준, 처음 이용하는 분을 위한 안내를 제공합니다.",
        eyebrow="COURSE · 선택 가이드", h1="코스 선택 가이드",
        lead="어떤 코스를 골라야 할지 모르겠다면, 목적을 기준으로 선택하면 쉽습니다.",
        sections=[
            ("코스, 이렇게 고르세요", [
                "어떤 코스를 골라야 할지 모르겠다면, '무엇을 위해 받는가'라는 목적을 기준으로 선택하면 쉽습니다."]),
            ("상황별 추천", [
                ("ul", ["전신이 무겁고 푹 쉬고 싶다 → <strong>피로 회복 관리</strong>",
                        "향과 함께 깊게 이완하고 싶다 → <strong>아로마 관리</strong>",
                        "운동 후 근육을 풀고 싶다 → <strong>스포츠 관리</strong>",
                        "집에서 스트레칭 위주로 받고 싶다 → <strong>홈타이 코스</strong>",
                        "둘이 함께 받고 싶다 → <strong>커플·가족 방문 관리</strong>",
                        "행사·단체로 진행하고 싶다 → <strong>기업·단체 방문 관리</strong>"])]),
            ("시간(60·90·120분) 선택", [
                "60분은 핵심 부위 위주로 빠르게 정리하고 싶을 때 적합합니다.",
                "90분은 전신을 고르게 풀 수 있어 가장 무난하며 많이 선택됩니다.",
                "120분은 전신 이완과 마무리 케어까지 여유 있게 받고 싶을 때 좋습니다."]),
            ("처음 이용하신다면", [
                "첫 방문이라면 90분 피로 회복 관리로 시작해 보시길 권합니다.",
                "받아본 뒤 선호하는 압·향·집중 부위를 알려주시면 다음 방문이 더 잘 맞습니다.",
                "테마가 궁금하다면 <a href='/theme/'>테마별 안내</a>에서 스웨디시·아로마·타이 등을 비교해 보세요."]),
            ("목적별로 조금 더 자세히", [
                ("h3", "푹 쉬고 싶다면"),
                "특별히 아픈 곳은 없지만 전반적으로 무겁고 피곤하다면 피로 회복 관리가 가장 무난합니다.",
                ("h3", "향까지 즐기고 싶다면"),
                "긴장도가 높거나 예민한 날에는 향이 더해진 아로마 관리가 이완에 도움이 됩니다.",
                ("h3", "운동 후라면"),
                "다리·등 근육이 무거운 날에는 또렷한 압의 스포츠 관리가 잘 맞습니다."]),
            ("시간 선택이 고민될 때", [
                "처음이거나 시간이 넉넉지 않다면 60분으로 핵심 부위만 정리해도 충분히 도움이 됩니다.",
                "온전히 쉬고 싶은 날에는 90분 이상을 권하며, 마무리 케어까지 원하면 120분이 적합합니다.",
                "정하기 어렵다면 예약 상담에서 컨디션을 말씀해 주시면 알맞은 시간을 추천드립니다."]),
            ("코스 선택 가이드, 어디서 받을 수 있나요", [
                "코스 선택 가이드는 인천 전지역(2군 8구)으로 방문합니다. 부평·주안·송도·구월·청라 등 구·군과 역세권 인근 어디서든 받으실 수 있습니다.",
                "지역별 안내는 <a href='/incheon/area/'>지역별 안내</a>, 역세권은 <a href='/incheon/stations/'>지하철역별 안내</a>에서 확인하실 수 있습니다.",
                "예약 시 위치와 희망 시간·인원을 함께 말씀해 주시면 방문 가능 여부를 빠르게 안내드립니다. 예약 흐름은 <a href='/reservation/'>예약안내</a>, 처음이시라면 <a href='/guide/'>이용가이드</a>에서 확인하세요.",
                "방문 가능 지역과 도착 시간은 <a href='/incheon/coverage/'>인천 전지역 방문 가능 안내</a>와 <a href='/incheon/hours/'>예약 가능 시간</a>에서, 위생·안전 기준은 <a href='/incheon/safety/'>위생 및 안전 안내</a>에서 확인하실 수 있습니다.",
                "지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 같은 안내를 중복하지 않도록 코스·지역·역·테마를 각각 분리해 안내합니다."]),
            ("재방문 시 팁", [
                "한 번 받아본 뒤 좋았던 압·향·집중 부위를 메모해 두면 다음 예약이 훨씬 수월합니다.",
                "컨디션에 따라 코스를 바꿔가며 받는 것도 좋은 방법이며, 처음에는 피로 회복으로 시작해 아로마·스포츠로 넓혀가는 분이 많습니다.",
                "어떤 코스가 맞을지 고민된다면 예약 상담에서 그날의 컨디션을 말씀해 주시면 알맞게 추천드립니다.",
            ]),
        ],
        data_note="처음 이용하는 고객의 다수가 90분 구성을 선택하며, 재방문 시 아로마·스포츠로 옮겨가는 경우가 많습니다.",
        faq=[
            ("처음인데 무엇이 좋을까요?", "90분 피로 회복 관리를 권장드립니다. 무난하게 전신을 풀 수 있습니다."),
            ("커플로 다른 코스도 가능한가요?", "네. 동반 관리에서 각자 다른 코스를 선택할 수 있습니다."),
            ("시간을 늘리면 더 좋은가요?", "집중 부위가 많거나 마무리 케어까지 원하면 90~120분이 적합합니다.")],
        service=("코스 선택 가이드", "인천 전지역 방문 관리 코스 선택 안내"))

# ---- 예약안내 ------------------------------------------------------------
def build_reservation():
    trail = [("/", "홈"), (None, "예약안내")]
    notes = [
        ("예약 방법", ["전화 또는 문의로 지역·역 인근 위치·희망 시간·코스를 말씀해 주세요.", "디스패처가 방문 가능 시간을 확정해 안내드립니다."]),
        ("예약 가능 시간", ["연중무휴 24시간 상담을 운영합니다.", "방문 가능 시간은 시간대와 위치에 따라 안내드립니다."]),
        ("방문 가능 장소", ["자택, 오피스텔, 숙소 등 방문 가능한 장소와 정확한 주소를 알려주세요."]),
        ("결제 안내", ["코스별 정찰 요금을 사전에 안내드리며, 결제 방법은 예약 시 함께 안내합니다."]),
        ("변경·취소 안내", ["일정 변경이나 취소는 가능한 한 빠르게 연락 주시면 도와드립니다."]),
        ("예약 전 체크사항", ["방문 장소·연락처·희망 코스·시간을 미리 정리해 두시면 빠르게 진행됩니다."]),
    ]
    res_faq = [
        ("당일 예약이 가능한가요?", "가능합니다. 다만 시간대와 위치에 따라 방문 가능 시간이 달라질 수 있어 상담 시 확인해 드립니다."),
        ("예약을 변경하고 싶어요.", "확정된 일정 변경은 가능한 한 빠르게 연락 주시면 조정을 도와드립니다."),
        ("결제는 어떻게 하나요?", "정찰 요금을 사전에 안내드리며 결제 방법은 예약 시 함께 안내합니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>RESERVATION</span>'
        '<h2 class="sec">예약안내</h2>'
        '<p class="sec-lead">예약 방법부터 결제·변경까지 한눈에 안내드립니다.</p>'
        '</div></section>' +
        notes_block("HOW TO BOOK", "예약 진행 안내", "아래 순서대로 진행됩니다.", notes, _id="about") +
        price_menu_block() + faq_block(res_faq) + cta_band())
    write("/reservation/", page("/reservation/",
        "예약안내 | 인천 출장마사지 예약 방법·결제 안내",
        "인천 출장마사지·홈타이 예약안내 - 예약 방법, 예약 가능 시간, 방문 가능 장소, 결제와 변경·취소 안내를 제공합니다. 연중무휴 24시간 상담.",
        "reservation", body, [bc_ld(trail), faq_ld(res_faq)]))

# ---- 이용가이드 ----------------------------------------------------------
def build_guide():
    trail = [("/", "홈"), (None, "이용가이드")]
    notes = [
        ("처음 이용하시는 분", ["예약 시 지역·역 인근 위치·시간·코스만 말씀해 주시면 나머지는 안내해 드립니다."]),
        ("방문 전 준비사항", ["편하게 쉴 수 있는 공간과 연락 가능한 번호를 준비해 주세요."]),
        ("위생 및 안전 기준", ["용품 위생 관리와 안전 가이드라인을 준수합니다."]),
        ("관리 후 주의사항", ["관리 후에는 충분한 수분 섭취와 휴식을 권장드립니다."]),
        ("금지행위 안내", ["불법·퇴폐 행위 요구는 일절 제공하지 않으며, 요청 시 서비스가 중단될 수 있습니다."]),
        ("이용 FAQ", ["자주 묻는 질문은 아래 FAQ와 고객센터에서 확인하실 수 있습니다."]),
    ]
    guide_faq = [
        ("처음인데 무엇을 준비하나요?", "편히 쉴 수 있는 공간과 연락 가능한 번호만 있으면 됩니다."),
        ("관리 후 주의할 점이 있나요?", "충분한 수분 섭취와 휴식을 권장드립니다."),
        ("이 서비스는 의료 행위인가요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상을 대상으로 합니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>GUIDE</span>'
        '<h2 class="sec">이용가이드</h2>'
        '<p class="sec-lead">처음 이용하시는 분도 안심할 수 있도록 안내드립니다.</p>'
        '</div></section>' +
        notes_block("USER GUIDE", "이용 안내", "방문 전후 확인하세요.", notes, _id="about") +
        price_menu_block() + faq_block(guide_faq) + cta_band())
    write("/guide/", page("/guide/",
        "이용가이드 | 인천 출장마사지 방문 전 준비·주의사항",
        "인천 출장마사지·홈타이 이용가이드 - 처음 이용하시는 분을 위한 방문 전 준비사항, 위생·안전 기준, 관리 후 주의사항과 금지행위 안내입니다.",
        "guide", body, [bc_ld(trail), faq_ld(guide_faq)]))

# ---- 후기 ----------------------------------------------------------------
def build_reviews():
    trail = [("/", "홈"), (None, "후기")]
    sample = [
        ("부평동 · 30대", "아로마", "늦은 시간 연락에도 도착 안내가 정확했습니다."),
        ("송도동 · 40대", "스포츠", "운동 후 받았는데 컨디션이 한결 가벼워졌어요."),
        ("구월동 · 30대", "피로회복", "예약부터 마무리까지 깔끔하고 정중했습니다."),
        ("청라동 · 50대", "아로마", "위생 안내가 꼼꼼해서 안심하고 받았습니다."),
        ("주안동 · 40대", "홈타이", "도착 시간을 미리 알려주셔서 좋았습니다."),
        ("계산동 · 30대", "커플", "둘이 함께 받았는데 응대가 친절했습니다."),
    ]
    cards = "".join(
        f'<div class="review reveal"><div class="stars">★★★★★</div>'
        f'<p>“{q}”</p><div class="who">{w} · {c} 코스</div></div>' for w, c, q in sample)
    area_links = "".join(f'<a class="chip" href="/incheon/{a["slug"]}/"><b>{a["name"]}</b></a>' for a in AREAS)
    body = (breadcrumb(trail) +
        '<section class="block" id="reviews"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>REVIEWS</span>'
        '<h2 class="sec">후기</h2>'
        '<p class="sec-lead">인천 세븐 마사지를 이용하신 고객들의 후기입니다. 지역별·역세권 후기는 각 지역 페이지에서 확인하세요.</p>'
        f'<div class="grid g3" style="margin-top:26px">{cards}</div>'
        f'<div class="chips" style="margin-top:24px">{area_links}</div>'
        '<p class="sec-lead" style="margin-top:24px">후기는 실제 이용 고객의 동의 하에 게시되며, 개인을 특정할 수 있는 정보는 표시하지 않습니다.</p>'
        '</div></section>' + price_menu_block() + cta_band())
    item_list = {"@context": "https://schema.org", "@type": "ItemList",
        "name": "인천 세븐 마사지 고객후기",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "Review", "reviewRating": {"@type": "Rating", "ratingValue": "5"},
                      "author": {"@type": "Person", "name": w}, "reviewBody": q}}
            for i, (w, c, q) in enumerate(sample)]}
    write("/reviews/", page("/reviews/",
        "후기 | 인천 출장마사지 인천 세븐 마사지 방문 후기",
        "인천 출장마사지·홈타이 후기 - 부평·송도·구월·청라·주안 등 인천 전지역 방문 건강관리 이용 후기를 모았습니다.",
        "reviews", body, [bc_ld(trail), item_list]))

# ---- 고객센터 ------------------------------------------------------------
def build_customer():
    trail = [("/", "홈"), (None, "고객센터")]
    notes = [
        ("공지사항", ["서비스 운영과 관련된 안내를 이곳에 게시합니다."]),
        ("1:1 문의", [f"전화 {PHONE_DISP}로 문의해 주세요. 연중무휴 24시간 상담을 운영합니다."]),
        ("제휴·기업 문의", ["기업·단체 방문 관리 및 제휴 문의도 전화로 접수받습니다."]),
    ]
    cust_faq = [
        ("문의는 어디로 하나요?", f"전화 {PHONE_DISP}로 문의하실 수 있습니다. 연중무휴 24시간 상담을 운영합니다."),
        ("운영 시간이 어떻게 되나요?", "연중무휴 24시간 상담을 운영합니다."),
        ("개인정보는 어떻게 관리되나요?", "개인정보처리방침에 따라 안전하게 관리되며, 자세한 내용은 해당 페이지에서 확인하실 수 있습니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block" id="notice"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>CUSTOMER</span>'
        '<h2 class="sec">고객센터</h2>'
        f'<p class="sec-lead">전화 {PHONE_DISP} · {HOURS}</p>'
        '</div></section>' +
        notes_block("HELP", "문의 안내", "궁금한 점은 언제든 문의해 주세요.", notes, _id="inquiry") +
        price_menu_block() + faq_block(cust_faq, "자주 묻는 질문") + cta_band())
    write("/customer/", page("/customer/",
        "고객센터 | 인천 출장마사지 인천 세븐 마사지 문의·공지",
        "인천 출장마사지·홈타이 고객센터 - 공지사항, 자주 묻는 질문, 1:1 문의, 제휴·기업 문의 안내입니다. 연중무휴 24시간 상담.",
        "customer", body, [bc_ld(trail), faq_ld(cust_faq)]))

# ---- 정책 페이지 ---------------------------------------------------------
def policy_page(path, title, heading, sections, desc):
    trail = [("/", "홈"), (None, heading)]
    secs = "".join(
        f'<div class="note-card"><div class="note-content"><h3 class="note-title">{t}</h3>'
        f'<div class="note-text">{"".join(f"<p>{p}</p>" for p in ps)}</div></div></div>'
        for t, ps in sections)
    body = (breadcrumb(trail) +
        f'<section class="block"><div class="wrap">'
        f'<span class="eyebrow"><span class="pulse"></span>POLICY</span>'
        f'<h2 class="sec">{heading}</h2>'
        f'<div class="note-stack" style="margin-top:26px;max-width:820px">{secs}</div>'
        f'</div></section>')
    write(path, page(path, title, desc, "customer", body, [bc_ld(trail)]))

def build_policies():
    policy_page("/privacy/", "개인정보처리방침 | 인천 세븐 마사지", "개인정보처리방침",
        [("수집하는 개인정보", ["예약 진행을 위해 연락처, 방문 장소 등 최소한의 정보를 수집합니다."]),
         ("이용 목적", ["수집한 정보는 예약 확정과 방문 안내 목적으로만 이용합니다."]),
         ("보유 및 파기", ["목적 달성 후에는 관련 법령에 따라 지체 없이 파기합니다."]),
         ("개인정보보호책임자", [f"{COMPANY['privacy_officer']} · 전화 {PHONE_DISP}"])],
        "인천 세븐 마사지 개인정보처리방침 - 수집 항목, 이용 목적, 보유 및 파기, 개인정보보호책임자 안내입니다.")
    policy_page("/terms/", "이용약관 | 인천 세븐 마사지", "이용약관",
        [("목적", ["본 약관은 인천 세븐 마사지 예약 서비스 이용 조건을 규정합니다."]),
         ("서비스 내용", ["본 서비스는 의료 행위가 아닌 이완·휴식 목적의 방문 건강관리 예약 서비스입니다."]),
         ("이용 자격", ["본 서비스는 만 19세 이상 성인만 이용할 수 있습니다."]),
         ("금지행위", ["불법·퇴폐 행위 요구 등은 금지되며, 위반 시 서비스가 중단될 수 있습니다."])],
        "인천 세븐 마사지 이용약관 - 서비스 내용, 이용 자격, 금지행위 등 이용 조건을 안내합니다.")
    policy_page("/youth/", "청소년보호정책 | 인천 세븐 마사지", "청소년보호정책",
        [("청소년 이용 제한", ["본 서비스는 만 19세 이상 성인을 대상으로 하며 청소년은 이용할 수 없습니다."]),
         ("건전한 운영", ["인천 세븐 마사지는 불법·퇴폐 행위를 일절 제공하지 않으며 건전한 건강관리 서비스를 지향합니다."]),
         ("책임자", [f"청소년보호 책임자 · {COMPANY['privacy_officer']} · 전화 {PHONE_DISP}"])],
        "인천 세븐 마사지 청소년보호정책 - 만 19세 이상 이용 제한과 건전한 운영 원칙을 안내합니다.")


# ---- 매거진(칼럼) --------------------------------------------------------
# 주제별 고유 콘텐츠 칼럼. 각 글은 2,000자+ 본문 + 관련 페이지 내부링크.
MAGAZINE = [
    {"slug": "how-to-choose-course",
     "cat": "코스 가이드",
     "title": "인천 출장마사지 코스, 목적별로 고르는 법 | 인천 세븐 마사지 매거진",
     "desc": "전신 피로·향 이완·운동 후 회복 등 목적에 맞춰 인천 출장마사지 코스를 고르는 방법과 60·90·120분 시간 선택 기준을 정리했습니다.",
     "h1": "인천 출장마사지 코스, 목적별로 고르는 법",
     "lead": "처음 예약하면 어떤 코스를 골라야 할지 막막합니다. '무엇을 위해 받는가'라는 목적을 기준으로 잡으면 선택이 한결 쉬워집니다.",
     "sections": [
        ("코스는 '목적'으로 고르면 쉽습니다", [
            "마사지 코스를 고를 때 가장 단순한 기준은 '오늘 무엇을 풀고 싶은가'입니다. 전신이 무겁다면 피로 회복, 향과 함께 깊게 쉬고 싶다면 아로마, 운동 후라면 스포츠 관리가 기본 출발점이 됩니다.",
            "코스 이름보다 내 컨디션과 목적을 먼저 떠올리면, 상담에서도 원하는 관리를 빠르게 안내받을 수 있습니다."]),
        ("상황별 추천", [
            "각 상황에 맞는 코스를 정리하면 다음과 같습니다.",
            ("ul", ["전신이 무겁고 푹 쉬고 싶다 → <a href='/course/fatigue/'>피로 회복 관리</a>",
                    "향과 함께 깊게 이완하고 싶다 → <a href='/course/aroma/'>아로마 관리</a>",
                    "운동 후 근육을 풀고 싶다 → <a href='/course/sports/'>스포츠 관리</a>",
                    "집에서 스트레칭 위주로 받고 싶다 → <a href='/course/hometai/'>홈타이 코스</a>",
                    "둘이 함께 받고 싶다 → <a href='/course/couple/'>커플·가족 방문 관리</a>"])]),
        ("60·90·120분, 시간은 이렇게", [
            "60분은 어깨·등·다리 등 피로가 집중된 핵심 부위를 빠르게 정리하기 좋습니다.",
            "90분은 전신을 고르게 풀 수 있어 가장 무난하며 많이 선택되는 구성입니다.",
            "120분은 전신 이완에 더해 두피·발 등 마무리 케어까지 여유 있게 받고 싶을 때 적합합니다."]),
        ("처음이라면 90분 피로 회복부터", [
            "첫 방문이고 특별히 아픈 곳이 없다면, 90분 피로 회복 관리로 시작해 보길 권합니다. 전신을 고르게 풀면서 내 몸이 어떤 압과 부위를 선호하는지 파악하기 좋기 때문입니다.",
            "한 번 받아본 뒤 좋았던 압·향·집중 부위를 기억해 두면, 다음 예약에서 더 잘 맞는 코스를 고를 수 있습니다."]),
        ("테마까지 함께 보면 선택이 또렷해집니다", [
            "코스와 별개로 스웨디시·타이마사지·아로마테라피 같은 <a href='/theme/'>테마</a>를 함께 살펴보면 원하는 결이 더 분명해집니다.",
            "예약 시에는 방문 위치, 희망 시간, 인원과 함께 '오늘의 목적'을 한마디만 알려주셔도 알맞은 코스를 추천드립니다."]),
     ],
     "faq": [
        ("처음인데 무엇이 좋을까요?", "90분 피로 회복 관리를 권장합니다. 전신을 무난하게 풀 수 있어 첫 방문에 적합합니다."),
        ("시간을 늘리면 더 좋은가요?", "집중 부위가 많거나 마무리 케어까지 원하면 90~120분이 적합합니다. 시간보다 목적이 우선입니다."),
        ("코스마다 가격이 다른가요?", "네. 코스 종류와 시간에 따라 달라지며, 자세한 내용은 가격 안내에서 확인하실 수 있습니다.")],
     "data_note": "처음 이용하는 분의 다수가 90분 구성을 선택하며, 재방문 시 아로마·스포츠로 옮겨가는 경우가 많습니다.",
     "related": [("/course/", "코스안내"), ("/course/guide/", "코스 선택 가이드"), ("/theme/", "테마별 안내")]},

    {"slug": "station-visit-tips",
     "cat": "이용 팁",
     "title": "역세권에서 출장마사지 받을 때 알아두면 좋은 점 | 인천 세븐 마사지 매거진",
     "desc": "부평역·주안역·송도역 등 인천 역세권에서 방문 마사지를 받을 때 위치 안내, 도착 시간 단축, 출구 안내 팁을 정리했습니다.",
     "h1": "역세권에서 출장마사지 받을 때 알아두면 좋은 점",
     "lead": "부평역·주안역·송도역 같은 역세권은 방문 위치를 알려주기 쉬워 예약이 빠릅니다. 다만 같은 역이라도 출구·위치에 따라 도착 시간이 달라집니다.",
     "sections": [
        ("역 이름만으로도 위치 안내가 빠릅니다", [
            "정확한 주소가 기억나지 않을 때, 가까운 지하철역을 알려주는 것만으로도 위치 파악이 빨라집니다. 인천1·2호선, 1·7호선, 수인분당선, 공항철도 인천권 주요 역 인근으로 방문합니다.",
            "역세권 안내는 <a href='/incheon/stations/'>지하철역별 안내</a>에서 노선별로 확인하실 수 있습니다."]),
        ("같은 역도 출구·방향에 따라 다릅니다", [
            "역은 넓어서 1번 출구와 반대편 출구는 도보로 10분 이상 차이가 나기도 합니다. 그래서 출구별로 페이지를 따로 만들지 않고, 예약 시 정확한 위치를 기준으로 안내합니다.",
            "예약할 때 '몇 번 출구 방향', '가까운 건물이나 랜드마크'를 함께 알려주시면 도착 시간을 줄일 수 있습니다."]),
        ("환승역은 한 곳으로 안내합니다", [
            "부평역·주안역·인천시청역·계양역·검암역처럼 여러 노선이 만나는 환승역은, 여러 노선에 보이더라도 한 페이지로 통합해 안내합니다.",
            "어느 노선을 이용하시든 같은 역세권 기준으로 방문하므로 헷갈릴 일이 없습니다."]),
        ("도착 시간을 줄이는 방법", [
            "예약 시 정확한 주소와 공동현관 출입 방법(동·호수, 비밀번호 등)을 함께 알려주시면 마지막 동선이 매끄럽습니다.",
            "도착 직전 연락이 닿을 수 있는 번호를 남겨주시면, 건물 입구에서 헤매지 않고 바로 방문할 수 있습니다.",
            "자세한 준비 사항은 <a href='/incheon/checklist/'>이용 전 확인사항</a>에서 확인하세요."]),
        ("역세권별 생활권도 함께 보세요", [
            "부평·주안은 상권 밀집 생활권, 송도·청라는 신도시 대단지, 계양·검암은 북부 생활권 등 역마다 성격이 다릅니다.",
            "내가 있는 곳과 가까운 역을 <a href='/incheon/stations/'>지하철역별 안내</a>에서 찾아 두면 다음 예약이 더 빨라집니다."]),
     ],
     "faq": [
        ("역 근처면 어디든 방문하나요?", "역세권 생활권을 기준으로 자택·숙소·오피스텔로 방문합니다. 세부 위치에 따라 가능 여부를 예약 시 확인합니다."),
        ("출구별로 예약이 다른가요?", "아니요. 출구별 페이지는 없으며 역세권 전체 기준으로 안내합니다. 정확한 주소를 알려주시면 가까운 동선으로 방문합니다."),
        ("환승역은 어떻게 찾나요?", "환승역도 한 페이지로 안내합니다. 지하철역별 안내에서 역 이름으로 찾으시면 됩니다.")],
     "data_note": "역세권 문의는 정확한 출구·주소를 함께 주실 때 도착 시간이 평균적으로 단축됩니다.",
     "related": [("/incheon/stations/", "지하철역별 안내"), ("/incheon/hours/", "예약 가능 시간"), ("/incheon/checklist/", "이용 전 확인사항")]},

    {"slug": "first-hometai",
     "cat": "홈타이",
     "title": "홈타이 처음이세요? 방문 전 준비 가이드 | 인천 세븐 마사지 매거진",
     "desc": "홈타이를 처음 받을 때 필요한 공간 준비, 복장, 출입 안내 등 방문 전 준비 사항과 진행 흐름을 알기 쉽게 정리했습니다.",
     "h1": "홈타이 처음이세요? 방문 전 준비 가이드",
     "lead": "홈타이는 매장이 아니라 집·숙소로 방문해 받는 관리입니다. 처음이라면 무엇을 준비해야 할지 막막할 수 있어, 꼭 필요한 것만 정리했습니다.",
     "sections": [
        ("홈타이가 뭔가요", [
            "홈타이는 관리사가 고객이 계신 곳으로 방문해 옷을 입은 상태에서 스트레칭과 지압 중심으로 진행하는 타이 계열 방문 관리입니다.",
            "매장을 찾지 않아 이동이 없고, 관리 직후 그대로 쉴 수 있어 이완 상태가 오래 유지됩니다. 자세한 설명은 <a href='/course/hometai/'>홈타이 코스</a>에서 확인하세요."]),
        ("공간은 이 정도면 충분합니다", [
            "두 사람이 누울 정도의 평평한 자리만 있으면 됩니다. 원룸·오피스텔·숙소에서도 진행 가능합니다.",
            "바닥이 너무 딱딱하면 매트나 이불을 한 겹 깔아두면 더 편안합니다. 조용한 분위기를 만들어 두면 이완에 도움이 됩니다."]),
        ("복장과 준비물", [
            "스트레칭 동작이 포함되므로 편안하고 신축성 있는 복장이 좋습니다.",
            "관리에 필요한 용품은 관리사가 가지고 방문하므로 따로 준비하실 것은 거의 없습니다. 관리 전 가벼운 샤워를 해두면 한결 개운합니다."]),
        ("방문 전 알려주면 좋은 것", [
            "정확한 주소와 공동현관 출입 방법(동·호수, 비밀번호 등)을 미리 알려주시면 도착이 빨라집니다.",
            "반려동물이 있거나 함께 계신 분이 있으면 미리 안내해 주세요. 자세한 체크리스트는 <a href='/incheon/checklist/'>이용 전 확인사항</a>에 있습니다."]),
        ("관리 당일 진행 흐름", [
            "관리사가 도착하면 가볍게 인사를 나누고 누울 공간을 정돈한 뒤, 선호하는 압과 집중 부위를 확인합니다.",
            "스트레칭과 지압을 중심으로 큰 부위부터 차례로 풀어주며, 관리 후에는 충분한 수분 섭취와 휴식을 권합니다."]),
     ],
     "faq": [
        ("좁은 집도 가능한가요?", "두 사람이 누울 공간이면 충분하며 원룸·숙소도 진행 가능합니다. 환경을 미리 알려주세요."),
        ("오일도 받을 수 있나요?", "원하시면 타이와 오일 관리를 함께 구성할 수 있습니다. 예약 시 말씀해 주세요."),
        ("무엇을 준비하나요?", "편히 누울 공간과 연락 가능한 번호, 정확한 주소면 충분합니다.")],
     "data_note": "홈타이는 평일 밤 시간대 문의가 가장 많습니다. 공간이 좁아도 진행 가능하니 환경을 알려주시면 알맞게 안내드립니다.",
     "related": [("/course/hometai/", "홈타이 코스"), ("/theme/homecare/", "홈케어"), ("/incheon/checklist/", "이용 전 확인사항")]},

    {"slug": "theme-compare",
     "cat": "테마 비교",
     "title": "스웨디시·아로마·타이마사지, 무엇이 다를까 | 인천 세븐 마사지 매거진",
     "desc": "스웨디시, 아로마테라피, 타이마사지의 기법과 느낌 차이를 비교하고, 내 컨디션에 맞는 테마를 고르는 기준을 정리했습니다.",
     "h1": "스웨디시·아로마·타이마사지, 무엇이 다를까",
     "lead": "이름은 들어봤지만 막상 고르려면 헷갈리는 대표 테마 셋. 기법과 느낌의 차이를 비교해 보면 선택이 쉬워집니다.",
     "sections": [
        ("스웨디시 — 오일로 부드럽게 쓸어주는 기본", [
            "스웨디시는 오일을 사용해 큰 근육을 따라 길게 쓸어주는 가장 대중적인 전신 이완 관리입니다. 강한 지압보다 일정한 압과 리듬으로 순환과 이완을 돕습니다.",
            "처음 마사지를 받거나 부드러운 이완을 원한다면 무난한 출발점입니다. 자세히는 <a href='/theme/swedish/'>스웨디시</a>에서 확인하세요."]),
        ("아로마테라피 — 향까지 더한 깊은 이완", [
            "아로마테라피는 스웨디시에 블렌딩 오일의 향을 더한 구성입니다. 후각을 통한 이완이 더해져, 긴장도가 높거나 예민한 날에 특히 선호됩니다.",
            "라벤더·시트러스 등 향의 계열에 따라 분위기가 달라집니다. 자세히는 <a href='/theme/aroma/'>아로마테라피</a>에서 확인하세요."]),
        ("타이마사지 — 오일 없이 스트레칭과 지압", [
            "타이마사지는 오일 없이 손·팔꿈치·무릎을 활용한 지압과 스트레칭으로 관절 가동 범위와 순환을 돕습니다. 옷을 입은 상태로 진행합니다.",
            "몸이 뻣뻣하거나 스트레칭을 선호한다면 잘 맞습니다. 자세히는 <a href='/theme/thai/'>타이마사지</a>에서 확인하세요."]),
        ("한눈에 비교하면", [
            ("ul", ["오일 사용: 스웨디시·아로마 O / 타이마사지 X",
                    "향 이완: 아로마 ◎ / 스웨디시·타이 △",
                    "스트레칭: 타이 ◎ / 스웨디시·아로마 △",
                    "처음 추천: 스웨디시 또는 90분 피로 회복"])]),
        ("내 컨디션에 맞추는 법", [
            "전반적으로 무겁고 피곤하면 스웨디시, 긴장과 예민함이 크면 아로마, 몸이 굳고 뻣뻣하면 타이마사지가 잘 맞습니다.",
            "더 많은 테마는 <a href='/theme/'>테마별 안내</a>에서 비교해 보고, 예약 시 원하는 결을 한마디만 알려주셔도 추천드립니다."]),
     ],
     "faq": [
        ("향이 부담스러우면요?", "향에 민감하면 스웨디시나 타이마사지를 권합니다. 아로마는 향 계열을 조절할 수 있습니다."),
        ("오일이 싫은데요?", "타이마사지는 오일 없이 진행합니다. 옷을 입은 상태에서 스트레칭 위주로 받습니다."),
        ("뭐가 제일 무난한가요?", "처음이라면 스웨디시 계열(90분 피로 회복)이 가장 무난합니다.")],
     "data_note": "세 테마 모두 90분 구성 선택 비율이 가장 높습니다. 예약 시 선호 압·향을 알려주면 방문이 매끄럽습니다.",
     "related": [("/theme/swedish/", "스웨디시"), ("/theme/aroma/", "아로마테라피"), ("/theme/thai/", "타이마사지")]},

    {"slug": "booking-timing",
     "cat": "예약 팁",
     "title": "출장마사지 예약, 시간대별 특징과 도착 시간 줄이는 법 | 인천 세븐 마사지 매거진",
     "desc": "낮·저녁·심야 시간대별 특징과 예약이 몰리는 시간, 도착 시간을 줄이는 위치 안내 방법까지 출장마사지 예약 팁을 정리했습니다.",
     "h1": "출장마사지 예약, 시간대별 특징과 도착 시간 줄이는 법",
     "lead": "같은 코스라도 언제 예약하느냐에 따라 도착 시간과 일정 조율이 달라집니다. 시간대별 특징을 알아두면 예약이 수월합니다.",
     "sections": [
        ("시간대별 특징", [
            "낮~초저녁은 비교적 도착이 빠르고 일정 조율이 수월합니다. 여유 있게 받고 싶다면 이 시간대를 권합니다.",
            "밤 21~24시는 예약이 가장 많이 몰리는 시간대로, 도착 시간을 넉넉히 보는 것이 좋습니다.",
            "심야(자정 이후)는 방문 가능하지만 위치에 따라 도착이 길어질 수 있습니다."]),
        ("예약이 몰리는 시간은 미리", [
            "평일 밤과 주말 저녁, 기념일·연휴는 문의가 집중됩니다. 원하는 시간이 정해져 있다면 미리 예약할수록 그 시간으로 안내받기 쉽습니다.",
            "운영은 연중무휴 24시간 상담이며, 자세한 내용은 <a href='/incheon/hours/'>예약 가능 시간</a>에서 확인하세요."]),
        ("도착 시간을 줄이는 위치 안내", [
            "정확한 주소와 공동현관 출입 방법을 함께 알려주시면 마지막 동선이 매끄럽습니다.",
            "가까운 지하철역이나 큰 건물 등 기준점을 알려주시면 위치 파악이 빨라집니다. 도착 직전 연락 가능한 번호도 도움이 됩니다."]),
        ("지역에 따라 도착 시간이 다릅니다", [
            "부평·주안·구월 등 중심 생활권은 비교적 빠르고, 송도·청라·검단 신도시와 영종·강화·옹진 도서·외곽은 이동 시간이 더 걸릴 수 있습니다.",
            "방문 가능 범위는 <a href='/incheon/coverage/'>인천 전지역 방문 가능 안내</a>에서 확인하세요."]),
        ("예약 변경이 필요하면", [
            "일정이 바뀌면 가능한 한 빠르게 연락 주세요. 빠를수록 다른 시간으로 조율하기 쉽습니다.",
            "방문 직전 변경은 관리사 동선상 어려울 수 있어, 미리 알려주시면 감사하겠습니다."]),
     ],
     "faq": [
        ("당일 예약이 되나요?", "가능합니다. 시간대와 위치에 따라 가능 시간이 달라질 수 있어 상담 시 확인합니다."),
        ("새벽에도 되나요?", "상담은 24시간 가능합니다. 심야는 위치에 따라 도착이 길어질 수 있습니다."),
        ("도착까지 얼마나 걸리나요?", "위치에 따라 다르며 중심 생활권은 빠르고 신도시·외곽은 더 걸릴 수 있습니다.")],
     "data_note": "평일 밤 21~24시가 하루 중 예약이 가장 집중되는 시간대입니다. 신도시·외곽은 이 시간대 도착이 더 걸릴 수 있습니다.",
     "related": [("/incheon/hours/", "예약 가능 시간"), ("/reservation/", "예약안내"), ("/incheon/coverage/", "전지역 방문 안내")]},

    {"slug": "hygiene-safety",
     "cat": "위생·안전",
     "title": "방문 마사지 위생·안전 체크리스트 | 인천 세븐 마사지 매거진",
     "desc": "방문 마사지를 안심하고 받기 위한 위생 관리, 개인정보 보호, 안전 가이드라인과 이용자가 확인하면 좋은 체크리스트를 정리했습니다.",
     "h1": "방문 마사지, 안심하고 받기 위한 위생·안전 체크리스트",
     "lead": "낯선 사람이 집으로 방문하는 만큼, 위생과 안전은 가장 먼저 챙겨야 할 부분입니다. 이용자와 운영자가 함께 확인하면 좋은 기준을 정리했습니다.",
     "sections": [
        ("용품 위생은 기본입니다", [
            "관리에 사용하는 수건·오일 등 용품은 위생 기준에 맞춰 관리되어야 합니다. 방문 시 청결을 우선하고, 관리 종료 후 사용한 공간을 정돈하는지 살펴보세요.",
            "운영 기준은 <a href='/incheon/safety/'>위생 및 안전 안내</a>에 공개되어 있습니다."]),
        ("개인정보는 예약 목적으로만", [
            "예약을 위해 받은 연락처·주소 등은 예약 진행 목적으로만 이용하고, 목적 달성 후 관련 법령에 따라 파기하는 것이 원칙입니다.",
            "처리 기준은 <a href='/privacy/'>개인정보처리방침</a>에서 확인할 수 있습니다."]),
        ("안전을 위한 상호 존중", [
            "관리사와 고객 모두의 안전을 위한 가이드라인을 운영하며, 상호 존중을 원칙으로 합니다.",
            "불법·퇴폐 행위 요구는 일절 제공되지 않으며, 부적절한 요구가 있을 경우 관리가 중단될 수 있습니다."]),
        ("이용자가 확인하면 좋은 것", [
            ("ul", ["운영 주체·연락처·책임자 정보가 공개되어 있는가",
                    "비의료(이완·휴식 목적) 안내가 명확한가",
                    "정찰 요금이 사전에 안내되는가",
                    "개인정보 처리 기준이 공개되어 있는가"])]),
        ("비의료 서비스라는 점", [
            "방문 마사지는 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며, 만 19세 이상 성인을 대상으로 합니다.",
            "통증·부상은 관리 대상이 아니며 의료기관 진료를 권합니다."]),
     ],
     "faq": [
        ("위생은 어떻게 관리되나요?", "수건·오일 등 용품을 위생 기준에 맞춰 관리하고, 관리 후 공간을 정돈합니다."),
        ("개인정보는 안전한가요?", "예약 목적으로만 이용하고 목적 달성 후 관련 법령에 따라 파기합니다."),
        ("의료적 효과가 있나요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 치료를 보장하지 않습니다.")],
     "data_note": "운영 주체·연락처·책임자 정보 공개와 정찰 요금, 비의료 고지는 신뢰할 수 있는 업체를 가르는 기본 기준입니다.",
     "related": [("/incheon/safety/", "위생 및 안전 안내"), ("/privacy/", "개인정보처리방침"), ("/guide/", "이용가이드")]},

    {"slug": "sports-recovery",
     "cat": "스포츠",
     "title": "운동 후 회복을 위한 스포츠·경락 마사지 활용법 | 인천 세븐 마사지 매거진",
     "desc": "러닝·헬스·등산 후 뭉친 근육을 정리하는 스포츠·경락 마사지의 적합한 타이밍과 부위별 접근, 주의사항을 정리했습니다.",
     "h1": "운동 후 회복을 위한 스포츠·경락 마사지 활용법",
     "lead": "열심히 운동한 다음 날의 묵직함, 마사지로 정리하면 회복이 한결 수월합니다. 다만 타이밍과 주의점을 알아두는 게 좋습니다.",
     "sections": [
        ("스포츠·경락 마사지란", [
            "스포츠·경락 관리는 운동 후 뭉친 근육과 경락을 따라 또렷한 압으로 풀어 컨디션 회복을 돕는 관리입니다. 전문 재활·치료가 아닌 일상 운동 후의 컨디션 관리 목적입니다.",
            "자세한 내용은 <a href='/course/sports/'>스포츠 관리</a>와 <a href='/theme/sports/'>스포츠·경락</a>에서 확인하세요."]),
        ("언제 받는 게 좋을까", [
            "운동 직후보다는 1~2시간 휴식 후 받는 것이 근육 회복에 도움이 됩니다.",
            "주말 과한 활동으로 다음 날 컨디션이 무겁다면, 그 사이에 한 번 정리해 주면 회복이 빨라집니다."]),
        ("부위별 접근", [
            "하체는 허벅지·종아리 등 큰 근육을 따라 또렷한 압으로 무거움을 정리합니다.",
            "등·어깨는 운동 자세로 자주 긴장되는 부위라 시간을 더 배분합니다. 통증과 시원함의 경계를 확인하며 강약을 조절합니다."]),
        ("이것만은 주의하세요", [
            "부상·염좌·심한 통증이 있는 부위는 관리 대상이 아닙니다. 해당 증상은 의료기관 진료를 권합니다.",
            "본 관리는 의료 행위가 아닌 건강관리 서비스이며, 통증 완화·치료를 보장하지 않습니다."]),
        ("운동 루틴과 함께", [
            "규칙적으로 운동하는 분은 무리한 날 컨디션을 빠르게 정리하는 용도로 활용하기 좋습니다.",
            "다만 통증이 반복되거나 심해지면 관리보다 진료를 먼저 권합니다."]),
     ],
     "faq": [
        ("운동 직후 바로 받아도 되나요?", "가벼운 휴식 후 받는 것을 권합니다. 심한 통증이 있다면 무리하지 않습니다."),
        ("강도가 센 편인가요?", "근육에 또렷한 압을 쓰지만 선호에 맞춰 강약을 조절합니다."),
        ("부상이 있어도 되나요?", "부상·급성 통증 부위는 관리 대상이 아니며 진료를 권합니다.")],
     "data_note": "스포츠 관리는 주말 오전~오후 예약 비율이 다른 코스보다 높습니다. 운동 후 1~2시간 휴식 뒤를 권장합니다.",
     "related": [("/course/sports/", "스포츠 관리"), ("/theme/sports/", "스포츠·경락"), ("/theme/foot/", "발마사지")]},

    {"slug": "couple-care",
     "cat": "커플·가족",
     "title": "커플·가족이 함께 받는 동반 관리, 이렇게 준비하세요 | 인천 세븐 마사지 매거진",
     "desc": "두 분이 같은 공간에서 동시에 받는 커플·가족 동반 관리의 공간·인원 조건과 예약 방법, 준비 가이드를 정리했습니다.",
     "h1": "커플·가족이 함께 받는 동반 관리, 이렇게 준비하세요",
     "lead": "기념일이나 오랜만의 만남에 함께 받는 동반 관리. 두 분이 같은 시간에 나란히 이완할 수 있어, 혼자 받을 때와는 다른 편안함이 있습니다.",
     "sections": [
        ("동반 관리란", [
            "커플·가족 방문 관리는 관리사 2인이 방문해 두 분이 같은 공간에서 동시에 받는 동반형 관리입니다. 각자 원하는 코스를 다르게 고를 수도 있습니다.",
            "자세한 내용은 <a href='/course/couple/'>커플·가족 방문 관리</a>와 <a href='/theme/couple/'>커플 관리</a>에서 확인하세요."]),
        ("공간과 인원 조건", [
            "동시에 진행하려면 두 사람이 누울 수 있는 공간이 필요합니다. 평평한 자리가 둘 있으면 됩니다.",
            "공간이 좁으면 한 분씩 순차로 진행하는 방식으로 안내할 수 있어, 예약 시 환경을 알려주세요."]),
        ("예약은 미리", [
            "동반 관리는 관리사 2인의 일정을 함께 맞춰야 해, 원하는 시간이 있다면 1~2일 전 예약을 권장합니다.",
            "희망 코스, 인원, 시간, 방문 장소를 말씀해 주시면 가능한 시간을 확정해 드립니다."]),
        ("각자 다른 코스도 가능", [
            "한 분은 피로 회복, 다른 한 분은 아로마처럼 컨디션에 따라 다르게 고를 수 있습니다.",
            "코스 비교는 <a href='/course/'>코스안내</a>에서, 향·기법은 <a href='/theme/'>테마별 안내</a>에서 살펴보세요."]),
        ("요금은 인원·시간 기준", [
            "동반 관리는 인원과 시간에 따라 요금이 책정됩니다. 기본 요금은 <a href='/course/price/'>가격 안내</a>에서 확인할 수 있으며, 정확한 금액은 상담에서 안내드립니다."]),
     ],
     "faq": [
        ("다른 코스를 받을 수 있나요?", "네. 각자 원하는 코스를 선택할 수 있습니다."),
        ("좁은 공간도 되나요?", "동시 진행이 어려우면 순차 진행으로 안내합니다. 환경을 알려주세요."),
        ("당일도 되나요?", "관리사 2인 일정상 사전 예약을 권장합니다. 당일은 상담으로 확인합니다.")],
     "data_note": "동반 관리는 기념일·주말 저녁 문의가 집중됩니다. 관리사 2인 조율을 위해 1~2일 전 예약을 권장합니다.",
     "related": [("/course/couple/", "커플·가족 방문 관리"), ("/theme/couple/", "커플 관리"), ("/course/price/", "가격 안내")]},

    {"slug": "sleep-care",
     "cat": "수면",
     "title": "잠이 안 올 때, 숙면을 돕는 마사지와 생활 습관 | 인천 세븐 마사지 매거진",
     "desc": "잠들기 전 긴장을 풀어 숙면을 돕는 마사지 방식과 함께 실천하면 좋은 생활 습관을 정리했습니다.",
     "h1": "잠이 안 올 때, 숙면을 돕는 마사지와 생활 습관",
     "lead": "몸은 피곤한데 정작 잠은 얕은 날이 있습니다. 잠들기 전 긴장을 부드럽게 풀어주면 수면의 질을 높이는 데 도움이 됩니다.",
     "sections": [
        ("수면을 돕는 마사지란", [
            "수면 지향 관리는 강한 자극을 피하고 부드럽고 느린 동작으로 긴장을 천천히 가라앉히는 방식입니다. 조명과 소리를 낮춘 조용한 분위기에서 진행해, 받는 도중 잠이 들어도 괜찮습니다.",
            "자세한 내용은 <a href='/theme/sleep/'>수면 가능</a> 안내에서 확인하세요."]),
        ("왜 잠들기 전이 좋을까", [
            "잠들기 전 몸의 긴장이 풀리면 들숨·날숨이 느려지고 마음도 가라앉아, 잠으로 자연스럽게 이어지기 쉽습니다.",
            "방문 관리는 받은 직후 이동 없이 그대로 누울 수 있어, 이완 상태가 흐트러지지 않는 장점이 있습니다."]),
        ("향을 더하면", [
            "라벤더 계열의 차분한 향을 더한 <a href='/theme/aroma/'>아로마테라피</a>는 심리적 이완에 도움이 됩니다.",
            "향에 민감하다면 향 없이 <a href='/course/fatigue/'>피로 회복 관리</a>로 부드럽게 받아도 좋습니다."]),
        ("함께 실천하면 좋은 습관", [
            ("ul", ["잠들기 1시간 전 스마트폰·강한 조명 줄이기",
                    "미지근한 물로 가볍게 샤워해 체온 살짝 올리기",
                    "카페인은 오후 늦게 피하기",
                    "취침·기상 시간을 일정하게 유지하기"])]),
        ("무리하지 않는 선에서", [
            "마사지는 이완과 휴식을 돕는 건강관리이며 불면증 등 질환의 치료를 보장하지 않습니다.",
            "수면 문제가 오래 지속되면 전문의 상담을 함께 권합니다."]),
     ],
     "faq": [
        ("받다가 잠들어도 되나요?", "네. 부드러운 이완 위주로 진행하니 주무셔도 괜찮습니다."),
        ("향이 부담되면요?", "향 없이 피로 회복 관리로 부드럽게 받을 수 있습니다."),
        ("불면증도 좋아지나요?", "이완에 도움이 될 수 있으나 치료를 보장하지는 않습니다. 지속되면 전문의 상담을 권합니다.")],
     "data_note": "수면 지향 관리는 늦은 저녁~밤 예약이 많습니다. 조용한 환경을 준비해 두면 이완 효과가 높아집니다.",
     "related": [("/theme/sleep/", "수면 가능"), ("/theme/aroma/", "아로마테라피"), ("/course/fatigue/", "피로 회복 관리")]},

    {"slug": "pricing-transparency",
     "cat": "요금",
     "title": "출장마사지 요금, 정찰제가 중요한 이유 | 인천 세븐 마사지 매거진",
     "desc": "출장마사지에서 정찰 요금이 왜 중요한지, 요금이 어떻게 구성되고 어떤 요소로 변동되는지, 안심하고 예약하는 기준을 정리했습니다.",
     "h1": "출장마사지 요금, 정찰제가 중요한 이유",
     "lead": "방문 서비스일수록 '얼마인지 미리 아는 것'이 중요합니다. 정찰 요금이 왜 신뢰의 기준이 되는지 정리했습니다.",
     "sections": [
        ("정찰 요금이 신뢰의 기준입니다", [
            "정찰 요금은 코스별 기본 요금을 사전에 명확히 안내하고, 현장에서 임의로 금액을 올리거나 숨겨진 비용을 청구하지 않는 원칙입니다.",
            "예약 전에 금액을 알 수 있어야 안심하고 부를 수 있습니다. 요금 기준은 <a href='/course/price/'>가격 안내</a>에 공개되어 있습니다."]),
        ("요금은 이렇게 구성됩니다", [
            "기본 요금은 코스(피로 회복·아로마·스포츠·홈타이 등)와 시간(60·90·120분)의 조합으로 정해집니다.",
            "커플·가족처럼 인원이 늘면 관리사 수와 시간에 따라 책정되고, 기업·단체는 별도 견적으로 안내합니다."]),
        ("변동될 수 있는 요소", [
            ("ul", ["방문 지역과 이동 거리(신도시·도서·외곽 등)",
                    "예약 시간대(심야 등)",
                    "커플·가족 등 인원 구성",
                    "기업·단체 등 별도 견적 대상"])]),
        ("이런 안내가 있으면 안심", [
            "표시 요금 외 추가가 있는지, 변동 요소가 무엇인지 예약 시 미리 설명하는지 확인하세요.",
            "변동이 필요한 경우 관리 전에 설명하고 동의를 받은 뒤 진행하는 것이 정상입니다."]),
        ("예약 상담에서 확정합니다", [
            "선택한 코스·시간의 최종 금액, 지역·시간대에 따른 변동 여부, 결제 방법은 예약 상담에서 확인해 드립니다.",
            "결제·예약 절차는 <a href='/reservation/'>예약안내</a>에서 확인할 수 있습니다."]),
     ],
     "faq": [
        ("표시 요금 외 추가가 있나요?", "정찰 요금을 원칙으로 하며, 지역·시간대 등 변동 요소는 예약 시 미리 안내합니다."),
        ("결제는 어떻게 하나요?", "결제 방법은 예약 시 함께 안내합니다."),
        ("코스마다 가격이 다른가요?", "네. 코스 종류와 시간에 따라 달라지며 상담에서 확정합니다.")],
     "data_note": "가장 많이 선택되는 구성은 90분입니다. 심야·도서·외곽은 변동 요소를 도착 시간과 함께 미리 안내합니다.",
     "related": [("/course/price/", "가격 안내"), ("/reservation/", "예약안내"), ("/course/", "코스안내")]},
]


# 매거진 보강 섹션(각 글 2,000자+ 확보용 고유 콘텐츠)
MAGAZINE_EXTRA = {
    "how-to-choose-course": [
        ("자주 하는 실수", [
            "압이 셀수록 좋다고 생각해 무리하게 강한 압을 요청하는 경우가 있는데, 압은 '시원하다'고 느껴지는 정도가 적당합니다. 통증을 참을 필요는 없습니다.",
            "시간이 길수록 무조건 좋은 것도 아닙니다. 목적과 컨디션에 맞는 구성이 가장 만족도가 높습니다."]),
        ("재방문할수록 잘 맞습니다", [
            "한 번 받아본 뒤 좋았던 압·향·집중 부위를 메모해 두면 다음 예약이 훨씬 수월합니다.",
            "컨디션에 따라 코스를 바꿔가며 받는 것도 좋은 방법입니다. 평소 피로 회복을 받다가 운동한 날엔 스포츠로 바꾸는 식입니다."]),
    ],
    "station-visit-tips": [
        ("숙소·호텔에서 받을 때", [
            "출장·여행 중 숙소에서 받는다면 건물명과 객실 번호, 프런트 출입 안내가 필요한지 미리 알려주세요.",
            "객실 환경에 맞춘 <a href='/theme/hotel/'>호텔식마사지</a>도 가능하며, 동선을 세심하게 안내합니다."]),
        ("역세권이라도 주소가 가장 빠릅니다", [
            "역 이름은 위치를 좁히는 데 유용하지만, 최종적으로는 정확한 주소가 가장 빠릅니다.",
            "역세권과 상세 주소를 함께 주시면 도착 안내가 가장 매끄럽습니다."]),
    ],
    "first-hometai": [
        ("관리 후 이렇게 하면 효과가 오래갑니다", [
            "관리 후에는 따뜻한 물을 충분히 마시고 무리한 활동을 피해 휴식을 권합니다.",
            "받은 직후 바로 잠들거나 쉬면 이완 상태가 오래 유지됩니다. 홈타이는 이동이 없어 이 점이 특히 좋습니다."]),
        ("이런 분께 특히 잘 맞습니다", [
            ("ul", ["외출 없이 집에서 편하게 받고 싶은 분",
                    "몸이 뻣뻣해 스트레칭 위주의 이완을 원하는 분",
                    "관리 후 바로 쉬고 싶은 분",
                    "이동 시간을 아끼고 싶은 분"])]),
    ],
    "theme-compare": [
        ("그 외 어떤 테마가 있을까", [
            "스웨디시·아로마·타이 외에도 로미로미, 중국마사지, 발마사지, 스포츠·경락, 호텔식 등 다양한 테마가 있습니다.",
            "전체 목록과 차이는 <a href='/theme/'>테마별 안내</a>에서 비교해 보세요."]),
        ("테마와 코스는 함께 봅니다", [
            "테마가 '어떤 결로 받을까'라면, 코스는 '무슨 목적으로 받을까'에 가깝습니다.",
            "예약 시 둘을 함께 알려주시면 가장 잘 맞는 구성을 안내드립니다."]),
    ],
    "booking-timing": [
        ("주말·공휴일도 운영합니다", [
            "주말과 공휴일에도 동일하게 연중무휴로 상담·방문을 운영합니다.",
            "다만 기념일·연휴 저녁은 문의가 몰리므로 미리 예약하시는 편이 좋습니다."]),
        ("후보 시간을 두세 개 주시면", [
            "가능한 시간이 여러 개라면 후보 시간을 두세 개 알려주시면 더 빠르게 확정됩니다.",
            "정확한 시간이 중요한 일정이라면 여유 있게 미리 예약하시는 것을 권합니다."]),
    ],
    "hygiene-safety": [
        ("관리사 응대도 위생의 일부", [
            "정중한 인사와 설명, 단정한 복장과 청결은 위생·안전의 기본입니다.",
            "관리 중에도 압·온도·자세 등 불편함이 없는지 살피며 진행하는지 살펴보세요."]),
        ("이용자가 지켜주면 좋은 점", [
            ("ul", ["만 19세 이상 본인 확인에 협조",
                    "관리사에 대한 존중과 기본 예의",
                    "불법·퇴폐 행위 요구 삼가기",
                    "과도한 음주 상태에서는 안전상 관리가 어려울 수 있음"])]),
        ("문제가 있으면 바로 알리세요", [
            "안전과 관련해 불편하거나 우려되는 점이 있으면 언제든 <a href='/customer/'>고객센터</a>로 알려주세요. 즉시 확인하고 조치합니다."]),
    ],
    "sports-recovery": [
        ("관리 당일 진행 순서", [
            "도착 후 어떤 운동을 했는지, 어느 부위가 무거운지 확인합니다.",
            "근육을 데우듯 가볍게 시작해 점차 압을 높이며 집중 부위를 풀어줍니다.",
            "마무리 단계에서는 가볍게 이완하며 호흡을 고르고 관리를 마칩니다."]),
        ("발·종아리 피로가 심하다면", [
            "많이 걷거나 서서 일한 날에는 발과 종아리 피로가 큽니다. <a href='/theme/foot/'>발마사지</a>를 더하면 하체 부기 정리에 도움이 됩니다."]),
        ("관리 후 케어", [
            "관리 후에는 충분한 수분 섭취와 가벼운 스트레칭, 휴식을 권합니다.",
            "다음 날까지 묵직함이 남으면 무리한 운동은 잠시 미루는 것이 좋습니다."]),
    ],
    "couple-care": [
        ("어떤 분들이 함께 받나요", [
            "기념일을 보내려는 커플, 부모님께 휴식을 선물하려는 가족, 오랜만에 만난 친구 등 다양합니다.",
            "두 분이 같은 시간에 나란히 이완할 수 있어 혼자 받을 때와는 다른 편안함이 있습니다."]),
        ("공간 준비 가이드", [
            "두 사람이 동시에 누울 평평한 공간이 있으면 동시 진행이 가능합니다.",
            "원룸·호텔 등 좁은 경우 한 분씩 순차로 진행하는 방식으로 안내합니다. 예약 시 방 환경을 알려주세요."]),
        ("관리 당일 진행 순서", [
            "관리사 2인이 함께 도착해 각자 담당을 정하고 공간을 준비합니다.",
            "두 분의 선호 압·코스를 각각 확인한 뒤 동시에 시작하고, 마무리도 비슷한 시점에 들어가도록 합니다."]),
    ],
    "sleep-care": [
        ("받는 동안 이렇게", [
            "받는 도중 잠이 들어도 괜찮습니다. 부드러운 압과 조용한 진행으로 이완에 집중해 드립니다.",
            "말을 많이 하지 않아도 되니 편하게 몸을 맡기시면 됩니다."]),
        ("어떤 부위를 풀면 좋을까", [
            "목·어깨·등의 긴장은 수면을 방해하기 쉬운 부위입니다. 이 부위를 부드럽게 풀면 한결 편해집니다.",
            "발과 종아리의 피로를 정리하면 다리가 무거워 잠을 설치는 느낌을 줄이는 데 도움이 됩니다."]),
        ("생활 습관과 함께", [
            "마사지만으로 모든 수면 문제가 해결되지는 않습니다. 규칙적인 수면 시간과 함께할 때 효과가 큽니다.",
            "낮잠을 너무 길게 자지 않고, 잠들기 전 과식을 피하는 것도 도움이 됩니다."]),
    ],
    "pricing-transparency": [
        ("왜 '미리 아는 것'이 중요할까", [
            "방문 서비스는 현장에서 금액이 바뀌면 거절하기 어려운 상황이 생길 수 있습니다.",
            "그래서 예약 전에 기본 요금과 변동 요소를 명확히 아는 것이 안심의 핵심입니다."]),
        ("정찰제가 지켜지는지 확인하는 법", [
            ("ul", ["기본 요금이 사전에 공개되어 있는가",
                    "추가 비용·변동 요소를 미리 설명하는가",
                    "현장에서 사전 안내와 다른 금액을 요구하지 않는가",
                    "결제 방법을 투명하게 안내하는가"])]),
        ("예약 상담에서 최종 확인", [
            "선택한 코스·시간의 최종 금액과 결제 방법은 예약 상담에서 확인해 드립니다.",
            "변동이 필요하면 관리 전에 설명하고 동의를 받은 뒤 진행합니다."]),
    ],
}


MAGAZINE_EXTRA2 = {
    "booking-timing": [("도착 직전 연락이 닿게", [
        "관리사가 건물 근처에 도착하면 마지막 위치 확인을 위해 연락드릴 수 있습니다. 연락이 닿는 번호를 남겨주시면 입구에서 헤매지 않고 바로 방문합니다.",
        "특히 큰 단지나 복잡한 건물은 도착 직전 안내가 큰 도움이 됩니다."])],
    "couple-care": [("예약 전 체크", [
        "인원과 각자의 희망 코스·시간, 방문 장소와 공간 환경을 미리 정리해 두면 상담이 빠릅니다.",
        "두 분 모두 만 19세 이상 성인이어야 이용할 수 있습니다. 좁은 공간이라면 순차 진행으로도 충분히 편안하게 받으실 수 있으니 부담 갖지 않으셔도 됩니다."])],
    "first-hometai": [("이런 점이 궁금하실 거예요", [
        "향이 부담스러우면 오일 없이 진행할 수 있고, 압이 세거나 약하면 진행 중 언제든 조절합니다.",
        "처음이라 어색해도 괜찮습니다. 관리 전 선호와 피하고 싶은 점만 알려주시면 맞춰 드립니다."])],
    "hygiene-safety": [("후기와 운영 정보도 참고하세요", [
        "다른 이용자의 <a href='/reviews/'>후기</a>와 운영 기준은 업체를 고르는 데 도움이 됩니다.",
        "처음 이용한다면 <a href='/guide/'>이용가이드</a>에서 전체 흐름을 먼저 확인해 보세요."])],
    "pricing-transparency": [("결제 전 마지막 점검", [
        "관리 시작 전, 안내받은 금액과 코스·시간이 맞는지 한 번 더 확인하면 착오를 줄일 수 있습니다.",
        "영수 관련 사항이 필요하면 예약 시 함께 요청해 두세요."])],
    "sleep-care": [("낮의 컨디션에도 영향을 줍니다", [
        "잘 자고 나면 다음 날 피로감과 집중력이 달라집니다. 잠들기 전 이완은 결국 낮의 컨디션까지 이어집니다.",
        "무리한 자극보다 꾸준한 이완 습관이 더 도움이 됩니다. 받는 날에는 조용하고 어두운 환경을 미리 만들어 두면 이완 효과가 한층 높아집니다."])],
    "sports-recovery": [("얼마나 자주 받으면 좋을까", [
        "운동 강도와 빈도에 따라 다르지만, 무리한 날 한 번 정리해 주는 것만으로도 회복에 도움이 됩니다.",
        "통증이 반복되면 빈도를 늘리기보다 진료를 먼저 권합니다. 가벼운 스트레칭과 충분한 수분 섭취를 병행하면 회복에 더 도움이 됩니다."])],
    "theme-compare": [("처음이라면 이렇게 시작하세요", [
        "고르기 어렵다면 90분 스웨디시 계열로 시작해 보세요. 받아본 뒤 더 강한 압을 원하면 타이·스포츠, 더 깊은 이완을 원하면 아로마로 넓혀가면 됩니다.",
        "예약 상담에서 컨디션을 말씀해 주시면 알맞은 테마를 추천드립니다."])],
}

def build_magazine():
    # 허브
    trail = [("/", "홈"), (None, "매거진")]
    cards = "".join(
        f'<a class="card reveal" href="/magazine/{m["slug"]}/"><div class="k">{m["cat"]}</div>'
        f'<h3>{m["h1"]}</h3><p>{m["lead"]}</p><span class="more">읽어보기 →</span></a>'
        for m in MAGAZINE)
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>MAGAZINE</span>'
        '<h2 class="sec">매거진</h2>'
        '<p class="sec-lead">인천 출장마사지·홈타이를 더 잘 이용하는 방법을 칼럼으로 정리했습니다. 코스 선택, 역세권 이용, 위생·안전, 요금까지 주제별로 확인하세요.</p>'
        f'<div class="grid g3" style="margin-top:26px">{cards}</div></div></section>'
        + cta_band())
    blog_ld = {"@context": "https://schema.org", "@type": "Blog",
        "name": "인천 세븐 마사지 매거진", "url": BASE_URL + "/magazine/",
        "blogPost": [{"@type": "BlogPosting", "headline": m["h1"],
                      "url": BASE_URL + f"/magazine/{m['slug']}/"} for m in MAGAZINE]}
    write("/magazine/", page("/magazine/",
        "매거진 | 인천 출장마사지·홈타이 이용 가이드 칼럼",
        "인천 세븐 마사지 매거진 - 코스 선택, 역세권 이용 팁, 홈타이 준비, 위생·안전, 요금 등 인천 출장마사지·홈타이를 더 잘 이용하는 칼럼을 모았습니다.",
        "magazine", body, [bc_ld(trail), blog_ld]))

    # 개별 칼럼
    mt = [("/", "홈"), ("/magazine/", "매거진")]
    for m in MAGAZINE:
        sections = list(m["sections"]) + MAGAZINE_EXTRA.get(m["slug"], []) + MAGAZINE_EXTRA2.get(m["slug"], [])
        rel_ul = [f'<a href="{href}">{label}</a>' for href, label in m["related"]]
        sections.append(("함께 보면 좋은 안내", [
            "이 글과 관련해 더 자세한 안내는 아래에서 확인하실 수 있습니다.",
            ("ul", rel_ul),
            "예약은 연중무휴 24시간 상담으로 진행되며, 방문 위치와 희망 시간을 알려주시면 빠르게 안내드립니다."]))
        content_page(f"/magazine/{m['slug']}/", "magazine",
            mt + [(None, m["cat"])],
            title=m["title"], desc=m["desc"],
            eyebrow=f"MAGAZINE · {m['cat']}", h1=m["h1"], lead=m["lead"],
            sections=sections, faq=m["faq"], data_note=m.get("data_note"),
            show_price=True, cta_title="방문 예약을 도와드릴까요?")


# ---- robots / sitemap / manifest / favicon / redirects -------------------
def all_urls():
    urls = ["/", "/incheon/", "/incheon/hometai/", "/incheon/coverage/", "/incheon/hours/",
            "/incheon/checklist/", "/incheon/safety/", "/incheon/faq/", "/incheon/area/",
            "/incheon/stations/", "/theme/", "/course/",
            "/reservation/", "/guide/", "/reviews/", "/customer/", "/magazine/",
            "/privacy/", "/terms/", "/youth/"]
    urls += [f"/magazine/{m['slug']}/" for m in MAGAZINE]
    urls += [f"/course/{c['slug']}/" for c in COURSES] + ["/course/price/", "/course/guide/"]
    urls += [f"/theme/{t['slug']}/" for t in THEMES]
    for a in AREAS:
        urls.append(f"/incheon/{a['slug']}/")
        for d in a["dongs"]:
            urls.append(f"/incheon/{a['slug']}/{d['slug']}/")
    for l in LINES:
        urls.append(f"/incheon/stations/line/{l['key']}/")
    for nm in unique_stations():
        urls.append(f"/incheon/stations/{STATION_DATA[nm][0]}/")
    # 중복 제거(순서 유지)
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return out

def build_meta_files():
    import datetime as _dt
    def xml_esc(s):
        return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                 .replace('"', "&quot;").replace("'", "&apos;"))
    WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    MO = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    base_date = _dt.date.fromisoformat(UPDATED)
    def rfc822(d, mm=0):
        return f"{WD[d.weekday()]}, {d.day:02d} {MO[d.month-1]} {d.year} 09:{mm:02d}:00 +0900"

    # ---- sitemap.xml (lastmod 포함 → 구글 신선도 판단) ----
    urls = all_urls()
    prio = {"/": "1.0"}
    items = ""
    for u in urls:
        p = prio.get(u, "0.9" if u.count("/") <= 2 else ("0.8" if u.count("/") <= 3 else "0.75"))
        freq = "daily" if u in ("/", "/magazine/") else "weekly"
        items += (f"  <url><loc>{BASE_URL}{u}</loc>"
                  f"<lastmod>{UPDATED}</lastmod>"
                  f"<changefreq>{freq}</changefreq><priority>{p}</priority></url>\n")
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + items + "</urlset>\n")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    # ---- rss.xml (매거진 피드 — 네이버 RSS 제출/콘텐츠 발견용) ----
    rss_items = ""
    for i, m in enumerate(MAGAZINE):
        link = f"{BASE_URL}/magazine/{m['slug']}/"
        rss_items += (
            "  <item>\n"
            f"    <title>{xml_esc(m['h1'])}</title>\n"
            f"    <link>{link}</link>\n"
            f'    <guid isPermaLink="true">{link}</guid>\n'
            f"    <category>{xml_esc(m['cat'])}</category>\n"
            f"    <description>{xml_esc(m['desc'])}</description>\n"
            f"    <pubDate>{rfc822(base_date, 59 - i)}</pubDate>\n"
            "  </item>\n")
    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "<channel>\n"
        f"  <title>{xml_esc(BRAND)} 매거진</title>\n"
        f"  <link>{BASE_URL}/magazine/</link>\n"
        f'  <atom:link href="{BASE_URL}/rss.xml" rel="self" type="application/rss+xml"/>\n'
        "  <description>인천 출장마사지·홈타이를 더 잘 이용하는 가이드 칼럼</description>\n"
        "  <language>ko-KR</language>\n"
        f"  <lastBuildDate>{rfc822(base_date, 0)}</lastBuildDate>\n"
        f"  <pubDate>{rfc822(base_date, 0)}</pubDate>\n"
        "  <ttl>1440</ttl>\n"
        + rss_items + "</channel>\n</rss>\n")
    with open(os.path.join(ROOT, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss)

    # ---- robots.txt (네이버 Yeti·다음 Daumoa 등 명시 허용 + 사이트맵/RSS) ----
    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /tools/\n\n"
        "# 검색엔진 크롤러 (명시 허용)\n"
        "User-agent: Googlebot\nAllow: /\n"
        "User-agent: bingbot\nAllow: /\n"
        "User-agent: Yeti\nAllow: /\n"            # 네이버
        "User-agent: Daumoa\nAllow: /\n"          # 다음(카카오)
        "User-agent: Yandex\nAllow: /\n\n"
        "# AI 크롤러\n"
        "User-agent: GPTBot\nAllow: /\n"
        "User-agent: ClaudeBot\nAllow: /\n"
        "User-agent: Google-Extended\nAllow: /\n\n"
        f"Sitemap: {BASE_URL}/sitemap.xml\n"
        f"Sitemap: {BASE_URL}/rss.xml\n"
        f"Host: {BASE_URL.replace('https://', '')}\n")
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)

    manifest = {
        "name": BRAND, "short_name": "인천세븐", "description": "인천 전지역 출장마사지·홈타이 방문 예약 안내",
        "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#0b0b0e", "theme_color": "#0b0b0e",
        "lang": "ko-KR", "orientation": "portrait",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ]}
    with open(os.path.join(ROOT, "site.webmanifest"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    favicon = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
               '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
               '<stop offset="0" stop-color="#f4d29c"/><stop offset=".5" stop-color="#e9b8a7"/>'
               '<stop offset="1" stop-color="#c98a6b"/></linearGradient></defs>'
               '<rect width="64" height="64" rx="16" fill="#0b0b0e"/>'
               '<rect x="8" y="8" width="48" height="48" rx="13" fill="url(#g)"/>'
               '<text x="32" y="45" font-family="Georgia,serif" font-style="italic" '
               'font-size="34" font-weight="700" text-anchor="middle" fill="#1a1208">7</text></svg>')
    with open(os.path.join(ROOT, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(favicon)

    # IndexNow 인증 키 파일 — https://<도메인>/<KEY>.txt 로 노출되어야 함
    with open(os.path.join(ROOT, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)

    # Cloudflare Pages _redirects — 2026-07-01 행정개편(제물포구·영종구·검단구) 대비
    # 개편 시 아래 주석(#)을 해제하면 신규 구 경로로 301 리다이렉트됩니다.
    redirects = (
        "# 인천 행정체제 개편(2026-07-01) 대비 리다이렉트 준비\n"
        "# 제물포구: 중구 원도심 + 동구 통합 예정\n"
        "# 영종구: 중구 영종·운서·용유 분리 예정\n"
        "# 검단구: 서구 검단 일대 분리 예정\n"
        "# 개편 확정 후 아래 규칙의 주석을 해제하세요.\n"
        "# /incheon/jung-gu/yeongjong-dong/   /incheon/yeongjong-gu/yeongjong-dong/   301\n"
        "# /incheon/jung-gu/unseo-dong/        /incheon/yeongjong-gu/unseo-dong/        301\n"
        "# /incheon/jung-gu/yongyu-dong/       /incheon/yeongjong-gu/yongyu-dong/       301\n"
        "# /incheon/seo-gu/geomdan-dong/       /incheon/geomdan-gu/geomdan-dong/        301\n"
    )
    with open(os.path.join(ROOT, "_redirects"), "w", encoding="utf-8") as f:
        f.write(redirects)


# ---------------------------------------------------------------------------
def main():
    build_home()
    build_incheon()
    build_incheon_info_pages()
    build_area_hub()
    build_gu_pages()
    build_dong_pages()
    build_station_hub()
    build_line_pages()
    build_station_pages()
    build_theme_hub()
    build_theme_pages()
    build_course()
    build_course_pages()
    build_reservation()
    build_guide()
    build_reviews()
    build_customer()
    build_magazine()
    build_policies()
    build_meta_files()
    print(f"Build complete. {len(all_urls())} pages.")
    if THIN_PAGES:
        print(f"Noindex(본문 {THIN_THRESHOLD}자 미만) {len(THIN_PAGES)}건:")
        for n, p in sorted(THIN_PAGES):
            print(f"  {n:>5}  {p}")


if __name__ == "__main__":
    main()
