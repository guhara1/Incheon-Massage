# 인천 세븐 마사지 — 인천 출장마사지·홈타이

인천 전지역(2군 8구) 방문 건강관리(마사지·홈타이) 예약 안내 정적 웹사이트입니다.
순수 HTML + 인라인 CSS/JS로 구성되어 **런타임 의존성이 0개**이며, 빌드 없이 그대로 배포할 수 있습니다.

> 상호: 인천 세븐 마사지 · 예약번호: 0508-202-4743
> 설계 기준: `BLUEPRINT.md`(강서 프로젝트 재사용 플레이북) — 다크 럭스 디자인, 전용 페이지 링크아웃,
> 도어웨이 회피, E-E-A-T, IndexNow 자동 색인.

## 구조 (총 237페이지)

```
/                              홈 (인천 출장마사지·홈타이 허브)
/incheon/                      인천 출장마사지 대표 랜딩
/incheon/hometai|coverage|hours|checklist|safety|faq/   인천 안내 6 (각 2,000자+)
/incheon/area/                 지역별 안내 허브
/incheon/<구·군>/              구·군 10 (강화군·옹진군·중구·동구·미추홀구·연수구·남동구·부평구·계양구·서구)
/incheon/<구·군>/<대표동>/      대표 동 83 (숫자 행정동은 대표 동으로 통합)
/incheon/stations/             지하철역별 안내 허브
/incheon/stations/line/<노선>/ 노선 6 (인천1·2호선, 1·7호선, 수인분당선, 공항철도 인천권)
/incheon/stations/<역>/        역 상세 86 (환승역은 URL 1개로 통합, 출구별 페이지 없음)
/theme/                        테마별 안내 허브
/theme/<테마>/                 테마 14 (스웨디시·로미로미·타이·중국·아로마·홈케어·호텔식·발·스포츠경락·스킨케어·왁싱·커플·24시간·수면)
/course/                       코스안내 허브
/course/<코스>/                코스 8 (fatigue·aroma·sports·hometai·couple·group·price·guide)
/magazine/                     매거진 허브
/magazine/<slug>/              칼럼 10편 (코스 선택·역세권 팁·홈타이·테마 비교·예약·위생·스포츠·커플·수면·요금)
/reservation/ /guide/ /reviews/ /customer/   예약·가이드·후기·고객센터
/privacy/ /terms/ /youth/      정책 3
sitemap.xml robots.txt site.webmanifest _redirects   메타 파일
favicon.svg favicon.ico icon-*.png assets/og-cover.jpg   브랜드 이미지
```

### 도어웨이·중복 방지 (가장 중요)
- **지역+역+테마 조합 페이지를 만들지 않습니다.** 구·군 / 대표 동 / 역 / 테마를 각각 분리해 안내합니다.
- **숫자 행정동 통합**: 주안1~8동 → 주안동, 송도1~5동 → 송도동, 부평1~6동 → 부평동, 구월1~4동 → 구월동,
  청라1~3동 → 청라동 등 대표 동 1페이지로 통합(별도 페이지 금지).
- **역 1개당 1페이지**, 환승역(부평·주안·인천시청·계양·검암·석남·부평구청·원인재·인천)은 URL 1개로 통합. 출구별 페이지 없음.
- **전용 페이지 링크아웃**: 예약 시간·준비물·위생은 동/역 본문에서 반복하지 않고
  `/incheon/hours·checklist·safety/`로 링크만 겁니다(반복 블록 제거 → 유사도 감소).
- **요금표(코스별 기본 요금)는 전 페이지 노출**: 지역·지하철·테마·안내·서비스 페이지에 60·90·120분 요금표를 표시합니다.
  (정책 3종 제외) 구글은 가격표 반복을 명시적으로 허용합니다(BLUEPRINT §4.3).
- **본문 2,000자 미만 자동 Noindex**: `tools/build.py`가 본문 글자수를 측정해 2,000자 미만이면
  `robots noindex`를 부여합니다(현재 전 페이지 2,000자 이상, Noindex 0건).

### 빌드 시 자동 점검 결과 (참고)
- 페이지별 `title`/`description`/`canonical` 100% 고유, JSON-LD 파싱 오류 0, 내부 broken link 0.
- 도어웨이 유사도(4-gram 자카드): 대표 동 **44%**, 역 **48%**.
  전 페이지 공통 요금표·링크아웃 섹션(블루프린트 허용 콘텐츠)이 포함된 수치이며, 각 동/역은
  노선·환승·구·랜드마크·평균 도착·고유 FAQ 등 고유 데이터를 가집니다.
  → **단계적 색인 권장**: 검색 수요가 큰 역(부평·주안·송도·인천시청 등)부터 Search Console에 제출 후 확장하세요.

## 행정체제 개편(2026-07-01) 대비
2026년 7월 1일부터 인천은 **2군 9구**(제물포구·영종구·검단구 신설)로 개편될 예정입니다.
현재는 공식 기준(2군 8구)으로 운영하며, 개편 시 메뉴 변경과 주소 리다이렉트를 적용할 수 있도록
`_redirects`(Cloudflare Pages)에 **주석 처리된 리다이렉트 규칙**을 미리 준비해 두었습니다.

## 빌드 (선택)

배포에는 빌드가 필요 없습니다. 공통 헤더/푸터/SEO/데이터를 일괄 수정할 때만 사용합니다.

```bash
python3 tools/build.py      # 모든 HTML + sitemap/robots/manifest/_redirects + IndexNow 키 파일 생성
python3 tools/gen_icons.py  # 파비콘 / PWA 아이콘 / OG 이미지 생성 (Pillow 필요)
```

## 색인 즉시 통보 (IndexNow / Google / sitemap)

### 1) IndexNow — 빙·네이버·얀덱스 즉시 통보 (권장, 무료·무설정)
- 인증 키 파일은 빌드 시 자동 생성: `a7c41e9b8d2f4a6e9c3b5d7f1a2e4c68.txt`
  → 배포되면 `https://incheon-massage.pages.dev/a7c41e9b8d2f4a6e9c3b5d7f1a2e4c68.txt` 로 노출
- 수동 제출:
  ```bash
  python3 tools/indexnow.py --all        # sitemap 전체
  python3 tools/indexnow.py --changed    # 직전 커밋 대비 바뀐 페이지만
  python3 tools/indexnow.py --all --dry-run   # 전송 없이 목록 확인
  ```
- **자동화**: `.github/workflows/indexnow.yml` 가 `main`에 페이지/사이트맵이 바뀌어 푸시될 때마다
  변경 URL을 IndexNow로 통보합니다. (별도 시크릿 불필요)
- 네이버는 [서치어드바이저](https://searchadvisor.naver.com)에 사이트 등록 + IndexNow 사용 설정을 한 번 해두면 더 확실합니다.

### 2) Google Indexing API (선택, 보조)
- ⚠️ 공식적으로 **JobPosting / BroadcastEvent** 페이지만 지원합니다. 일반 페이지는 무시될 수 있으므로,
  구글은 **Search Console 등록 + sitemap 제출**이 정공법입니다.
- CI 자동화: 서비스계정 JSON을 GitHub 시크릿 `GOOGLE_INDEXING_SA` 로 넣으면 워크플로가 함께 호출합니다.

### 3) sitemap ping
- **Google·Bing의 sitemap ping 엔드포인트는 2023년 폐지**되었습니다. 대신 Search Console / Bing Webmaster에
  sitemap을 한 번 제출하고, 즉시 통보는 위 IndexNow로 대체합니다.

## 배포 전 교체할 항목 (`tools/build.py` 상단 상수)

| 상수 | 현재값 | 설명 |
|---|---|---|
| `BASE_URL` | `https://incheon-massage.pages.dev` | 메인 도메인(Cloudflare Pages) |
| `BRAND` / `PHONE_DISP` | `인천 세븐 마사지` / `0508-202-4743` | 상호 / 예약번호(설정됨) |
| `COMPANY.ceo` / `privacy_officer` | `홍길동` | **대표 / 개인정보보호책임자(실제값으로 교체)** |
| `COMPANY.biz_no` | `000-00-00000` | **사업자등록번호(실제값으로 교체)** |
| `COMPANY.sales_no` | `2026-인천-0000` | **통신판매업신고번호(실제값으로 교체)** |

> `LocalBusiness` 구조화 데이터와 푸터 사업자 정보는 **실제 사업자 정보가 사실일 때만** 게시하세요.
> 값을 바꾼 뒤 `python3 tools/build.py`를 다시 실행하면 전 페이지에 반영됩니다.

## SEO / 적법성
- 페이지별 고유 `title` / `description` / `canonical`(절대 URL), Breadcrumb 전 페이지.
- JSON-LD: Organization · WebSite · LocalBusiness · Service · OfferCatalog · CollectionPage · BreadcrumbList · FAQPage · ItemList.
- 푸터에 사업자 6필드 + 비의료·만 19세 이상 고지 + 정책 3종(개인정보·약관·청소년보호).
- 시스템 폰트·인라인 자원·`content-visibility`로 Core Web Vitals 최적화, 전 페이지 플로팅 전화 버튼.
