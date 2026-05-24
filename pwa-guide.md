# PWA (Progressive Web App) 구현 가이드

아이폰·안드로이드 홈 화면에 앱처럼 추가할 수 있는 웹앱 구현을 위한 실전 가이드입니다.

---

## 목차

1. [개요](#개요)
2. [필수 파일](#필수-파일)
3. [HTML meta 태그](#html-meta-태그)
4. [manifest.json](#manifestjson)
5. [Service Worker](#service-worker)
6. [캐싱 전략](#캐싱-전략)
7. [확장 기능](#확장-기능)
8. [배포 체크리스트](#배포-체크리스트)

---

## 개요

PWA는 웹 기술(HTML, CSS, JS)로 만들어진 앱이 네이티브 앱처럼 동작하도록 하는 기술 모음입니다.

| 기능 | 설명 |
|---|---|
| 홈 화면 추가 | 아이콘으로 설치, 주소창 없이 실행 |
| 오프라인 지원 | 인터넷 없이 캐시된 페이지 접근 |
| 빠른 로딩 | 캐시에서 즉시 제공 |
| 푸시 알림 | 앱처럼 알림 발송 (선택) |

### 핵심 구성 요소

```
프로젝트 루트/
├── index.html        ← meta 태그 + SW 등록 스크립트
├── manifest.json     ← 앱 이름, 아이콘, 색상 정의
└── sw.js             ← Service Worker (캐싱 로직)
```

---

## 필수 파일

### 파일 위치 규칙

- `manifest.json`, `sw.js`는 반드시 **루트 경로**(`/`)에 위치해야 합니다.
- Service Worker는 자신이 위치한 경로의 하위 범위만 제어합니다.
  - `/sw.js` → 전체 사이트 제어 가능
  - `/app/sw.js` → `/app/` 하위만 제어

---

## HTML meta 태그

`index.html`의 `<head>` 안에 추가합니다.

```html
<!-- PWA manifest 연결 -->
<link rel="manifest" href="/manifest.json">

<!-- 브라우저 테마 색상 (주소창 색상) -->
<meta name="theme-color" content="#d95f2b">

<!-- iOS 홈 화면 추가 지원 -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="앱 이름">

<!-- Service Worker 등록 -->
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
  }
</script>
```

### `apple-mobile-web-app-status-bar-style` 값

| 값 | 효과 |
|---|---|
| `default` | 흰색 상태바 |
| `black` | 검정 상태바 |
| `black-translucent` | 투명 상태바 (콘텐츠가 뒤로 밀림) |

---

## manifest.json

웹앱의 이름, 아이콘, 색상, 실행 방식을 정의합니다.

```json
{
  "name": "My App",
  "short_name": "App",
  "description": "앱 설명",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "background_color": "#f5f2ed",
  "theme_color": "#d95f2b",
  "lang": "ko",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### `display` 값

| 값 | 효과 |
|---|---|
| `standalone` | 주소창·탭바 없이 앱처럼 실행 (권장) |
| `fullscreen` | 상태바까지 숨김 |
| `minimal-ui` | 최소한의 브라우저 UI 유지 |
| `browser` | 일반 브라우저와 동일 |

### 아이콘을 이미지 없이 SVG로 인라인 처리하는 방법

이미지 파일 없이 SVG를 data URI로 사용할 수 있습니다.

```json
{
  "src": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 192 192'><rect width='192' height='192' rx='32' fill='%23d95f2b'/><text x='96' y='130' font-size='110' text-anchor='middle' font-family='system-ui' fill='white'>✦</text></svg>",
  "sizes": "192x192",
  "type": "image/svg+xml"
}
```

> ⚠️ iOS는 SVG 아이콘을 지원하지 않습니다. iOS 지원이 필요하면 PNG 파일을 별도 제공해야 합니다.

---

## Service Worker

### 기본 구조

```js
const CACHE = 'my-app-v1'; // 버전을 바꾸면 캐시가 갱신됩니다

// 설치 시: 핵심 파일 미리 캐싱
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll([
      '/',
      '/index.html',
    ])).then(() => self.skipWaiting())
  );
});

// 활성화 시: 이전 버전 캐시 삭제
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// 요청 가로채기
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return; // POST 등은 그냥 통과
  e.respondWith(/* 아래 전략 중 선택 */);
});
```

---

## 캐싱 전략

### 1. Network First (네트워크 우선) — 권장: 콘텐츠가 자주 바뀌는 경우

항상 최신 콘텐츠를 제공하되, 오프라인이면 캐시 사용.

```js
e.respondWith(
  fetch(e.request)
    .then(res => {
      const clone = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, clone));
      return res;
    })
    .catch(() => caches.match(e.request))
);
```

### 2. Cache First (캐시 우선) — 권장: 이미지·폰트 등 정적 자산

캐시가 있으면 즉시 반환, 없으면 네트워크에서 가져와 저장.

```js
e.respondWith(
  caches.match(e.request).then(cached => {
    if (cached) return cached;
    return fetch(e.request).then(res => {
      caches.open(CACHE).then(c => c.put(e.request, res.clone()));
      return res;
    });
  })
);
```

### 3. Stale While Revalidate — 권장: 속도와 최신성 균형

캐시를 즉시 반환하면서 백그라운드에서 갱신.

```js
e.respondWith(
  caches.open(CACHE).then(cache =>
    cache.match(e.request).then(cached => {
      const fetchPromise = fetch(e.request).then(res => {
        cache.put(e.request, res.clone());
        return res;
      });
      return cached || fetchPromise;
    })
  )
);
```

### 전략 선택 가이드

| 콘텐츠 유형 | 권장 전략 |
|---|---|
| HTML 페이지 (자주 업데이트) | Network First |
| 이미지, 폰트, 아이콘 | Cache First |
| API 응답 | Network First 또는 Stale While Revalidate |
| 앱 셸 (index.html) | Cache First + 버전 관리 |

---

## 확장 기능

### 설치 유도 배너 (직접 버튼 표시)

브라우저 기본 "홈 화면에 추가" 프롬프트를 직접 제어합니다.

```js
let deferredPrompt;

window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  deferredPrompt = e;
  document.getElementById('install-btn').style.display = 'block';
});

document.getElementById('install-btn').addEventListener('click', async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  deferredPrompt = null;
  document.getElementById('install-btn').style.display = 'none';
});
```

> ⚠️ iOS Safari는 `beforeinstallprompt`를 지원하지 않습니다. iOS에서는 "공유 → 홈 화면에 추가"를 안내하는 별도 UI가 필요합니다.

### iOS 설치 안내 배너

```js
const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent);
const isStandalone = window.navigator.standalone;

if (isIos && !isStandalone) {
  // "공유 버튼 → 홈 화면에 추가" 안내 UI 표시
}
```

### 캐시 버전 관리

`sw.js`의 CACHE 상수 버전을 올리면 모든 사용자의 캐시가 다음 방문 시 자동 갱신됩니다.

```js
const CACHE = 'my-app-v2'; // v1 → v2로 올리면 v1 캐시 전부 삭제
```

---

## 배포 체크리스트

### 필수

- [ ] `manifest.json`이 루트에 있고 `<link rel="manifest">` 로 연결됨
- [ ] `sw.js`가 루트에 있고 `navigator.serviceWorker.register('/sw.js')` 로 등록됨
- [ ] HTTPS로 서비스됨 (Service Worker는 HTTPS 또는 localhost에서만 작동)
- [ ] `display: standalone` 설정됨
- [ ] 192×192, 512×512 아이콘 제공됨

### iOS 대응

- [ ] `apple-mobile-web-app-capable` meta 태그 추가
- [ ] `apple-mobile-web-app-title` meta 태그 추가
- [ ] PNG 아이콘 제공 (SVG 미지원)
- [ ] `apple-touch-icon` 링크 태그 추가 (선택)
  ```html
  <link rel="apple-touch-icon" href="/icons/icon-192.png">
  ```

### 검증 도구

| 도구 | 방법 |
|---|---|
| Chrome DevTools | F12 → Application 탭 → Manifest / Service Workers |
| Lighthouse | F12 → Lighthouse 탭 → PWA 항목 점수 확인 |
| iOS Safari | 직접 홈 화면 추가 후 동작 확인 |

---

## GitHub Pages 배포 시 주의사항

저장소 이름이 있는 경우(`username.github.io/repo-name/`) `start_url`과 `scope`를 조정해야 합니다.

```json
{
  "start_url": "/repo-name/",
  "scope": "/repo-name/"
}
```

Service Worker도 경로를 맞춰야 합니다.

```js
// sw.js 내부 경로 필터링
if (!url.pathname.startsWith('/repo-name/')) return;
```

Service Worker 등록 경로도 수정합니다.

```html
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/repo-name/sw.js');
  }
</script>
```
