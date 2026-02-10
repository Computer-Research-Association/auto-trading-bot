// import type { IncomingMessage, ServerResponse } from "http";
// import type { Connect } from "vite";
// import { mockData } from "./mockData";

// // 쿼리스트링 파싱용 (선택이지만 편함)
// function getQuery(url: string) {
//   const u = new URL(url, "http://localhost");
//   return Object.fromEntries(u.searchParams.entries());
// }

// export function viteMockApi(): Connect.NextHandleFunction {
//   return (
//     req: IncomingMessage,
//     res: ServerResponse,
//     next: Connect.NextFunction
//   ) => {
//     // 타입 가드
//     if (!req.url || !req.method) {
//       return next();
//     }

//     // ✅ 1) GET /api/strategies
//     if (req.method === "GET" && req.url.startsWith("/api/strategies")) {
//       // 예: /api/strategies?query=rsi 이런 거까지 받을 수 있음
//       const q = getQuery(req.url).query?.toLowerCase() ?? "";

//       const data = !q
//         ? mockData
//         : mockData.filter((s) => s.name.toLowerCase().includes(q));

//       res.statusCode = 200;
//       res.setHeader("Content-Type", "application/json; charset=utf-8");
//       res.end(JSON.stringify(data));
//       return;
//     }

//     // ✅ 2) POST /api/strategies/:id/start
//     if (req.method === "POST" && /^\/api\/strategies\/[^/]+\/start$/.test(req.url)) {
//       res.statusCode = 200;
//       res.setHeader("Content-Type", "application/json; charset=utf-8");
//       res.end(JSON.stringify({ ok: true }));
//       return;
//     }

//     // ✅ 3) POST /api/strategies/:id/stop
//     if (req.method === "POST" && /^\/api\/strategies\/[^/]+\/stop$/.test(req.url)) {
//       res.statusCode = 200;
//       res.setHeader("Content-Type", "application/json; charset=utf-8");
//       res.end(JSON.stringify({ ok: true }));
//       return;
//     }

//     // 그 외 요청은 정상 흐름으로 넘김
//     return next();
//     };
// }
