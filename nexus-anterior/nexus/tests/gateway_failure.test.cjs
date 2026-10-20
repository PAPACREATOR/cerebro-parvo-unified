"use strict";
// Real loopback sockets and the original gateway; effects below are synthetic.
// These tests do not call a tool, Host, or Store. Real authority has its own E2E.
const assert = require("node:assert/strict");
const { test } = require("node:test");
const http = require("node:http");
const net = require("node:net");
const path = require("node:path");
const { spawn } = require("node:child_process");
const ROOT = path.resolve(__dirname, "../..");

async function unusedPort() {
  const listener = net.createServer();
  await new Promise(resolve => listener.listen(0, "127.0.0.1", resolve));
  const port = listener.address().port;
  await new Promise(resolve => listener.close(resolve));
  return port;
}

function request(port, route, { method = "GET", payload, timeout = 4000 } = {}) {
  return new Promise((resolve, reject) => {
    const body = payload === undefined ? undefined : Buffer.from(JSON.stringify(payload));
    const req = http.request({ hostname: "127.0.0.1", port, path: route, method,
      headers: { Host: "127.0.0.1:" + port, "X-Nexus-Session": "synthetic-session",
        ...(body ? { "Content-Type": "application/json", "Content-Length": body.length } : {}) },
      timeout,
    }, response => {
      const chunks = [];
      response.on("data", chunk => chunks.push(chunk));
      response.on("error", reject);
      response.on("aborted", () => reject(new Error("response aborted")));
      response.on("end", () => resolve({ status: response.statusCode,
        headers: response.headers, body: Buffer.concat(chunks).toString("utf8") }));
    });
    req.on("error", reject);
    req.on("timeout", () => req.destroy(new Error("client timeout")));
    req.end(body);
  });
}

async function lab(t, handler) {
  const sockets = new Set();
  const effects = [];
  const backend = http.createServer((req, res) => {
    const chunks = [];
    req.on("data", chunk => chunks.push(chunk));
    req.on("end", () => {
      if (req.url === "/") return res.end("SYNTHETIC_UI");
      handler(req, res, Buffer.concat(chunks), effects);
    });
  });
  backend.on("connection", socket => { sockets.add(socket); socket.on("close", () => sockets.delete(socket)); });
  await new Promise(resolve => backend.listen(0, "127.0.0.1", resolve));
  const backendPort = backend.address().port;
  const port = await unusedPort();
  const gateway = spawn(process.execPath, ["server.js"], { cwd: ROOT,
    env: { ...process.env, PORT: String(port), NEXUS_BACKEND_PORT: String(backendPort) },
    stdio: ["ignore", "ignore", "pipe"] });
  let stderr = "";
  gateway.stderr.on("data", data => { stderr += data; });
  t.after(async () => {
    if (gateway.exitCode === null) {
      const closed = new Promise(resolve => gateway.once("exit", resolve));
      gateway.kill(); await closed;
    }
    for (const socket of sockets) socket.destroy();
    if (backend.listening) await new Promise(resolve => backend.close(resolve));
  });
  // Observe cold process startup separately from operation/transport deadlines.
  const startupDeadline = performance.now() + 10000;
  while (performance.now() < startupDeadline) {
    if (gateway.exitCode !== null) throw new Error("Gateway exited: " + stderr);
    try {
      if ((await request(port, "/")).status === 200) return { port, backend, gateway, effects, sockets };
    } catch (_) { /* wait for the listener, never retry an operation */ }
    await new Promise(resolve => setTimeout(resolve, 25));
  }
  throw new Error("Gateway startup timeout: " + stderr);
}

function unknown(response) {
  assert.equal(response.status, 503);
  const value = JSON.parse(response.body);
  assert.equal(value.outcome, "UNKNOWN");
  assert.match(value.error, /confirmar.*resultado/iu);
  assert.match(value.error, /trabalhos anteriores/iu);
  assert.doesNotMatch(value.error, /nenhuma operação|tenta novamente|repetir automaticamente/iu);
  assert.equal(response.headers["cache-control"], "no-store");
}

for (const route of ["/api/confirm-run", "/api/approve"]) {
  test(route + " loses the reply after an effect: UNKNOWN, one dispatch, no replay", async t => {
    const state = await lab(t, (req, _res, body, effects) => {
      effects.push({ route: req.url, body: JSON.parse(body) });
      req.socket.destroy();
    });
    const payload = { ticket: "synthetic-ticket", confirmed: true };
    const response = await request(state.port, route, { method: "POST", payload });
    assert.deepEqual(state.effects, [{ route, body: payload }]);
    unknown(response);
    assert.equal(state.effects.length, 1);
  });
}

test("unreachable backend gives UNKNOWN without an invented success or effect", async t => {
  const state = await lab(t, (_req, res, _body, effects) => { effects.push("unexpected"); res.end("{}"); });
  for (const socket of state.sockets) socket.destroy();
  await new Promise(resolve => state.backend.close(resolve));
  unknown(await request(state.port, "/api/confirm-run", { method: "POST", payload: { confirmed: true } }));
  assert.deepEqual(state.effects, []);
});

test("native 403 denial and later recovery pass through without a second operation", async t => {
  let broken = true;
  const state = await lab(t, (req, res, body, effects) => {
    if (req.headers["x-nexus-session"] !== "synthetic-session") throw new Error("session changed");
    if (req.url === "/api/runs") {
      res.writeHead(200, { "Content-Type": "application/json" });
      return res.end(JSON.stringify(effects));
    }
    const value = JSON.parse(body);
    if (!value.confirmed) {
      res.writeHead(403, { "Content-Type": "application/json" });
      return res.end('{"error":"human denied"}');
    }
    effects.push("one-effect");
    if (broken) { broken = false; return req.socket.destroy(); }
    res.end("{}");
  });
  const denied = await request(state.port, "/api/approve", { method: "POST", payload: { confirmed: false } });
  assert.equal(denied.status, 403);
  assert.deepEqual(JSON.parse(denied.body), { error: "human denied" });
  assert.deepEqual(state.effects, []);
  unknown(await request(state.port, "/api/approve", { method: "POST", payload: { confirmed: true } }));
  const recovered = await request(state.port, "/api/runs");
  assert.equal(recovered.status, 200);
  assert.deepEqual(JSON.parse(recovered.body), ["one-effect"]);
  assert.equal(state.effects.length, 1);
  assert.equal(state.gateway.exitCode, null);
});

test("truncated upstream framing terminates the client response and keeps the gateway alive", async t => {
  const state = await lab(t, (req, res, _body, effects) => {
    if (req.url === "/api/runs") return res.end("[]");
    effects.push("one-effect");
    res.writeHead(202, { "Content-Type": "application/json", "Content-Length": "200" });
    res.write('{"run_id":"');
    res.flushHeaders();
    setTimeout(() => req.socket.destroy(), 20);
  });
  const started = Date.now();
  await assert.rejects(request(state.port, "/api/confirm-run", { method: "POST", payload: { confirmed: true } }));
  assert.ok(Date.now() - started < 2000, "must propagate the broken stream before the client timeout");
  assert.equal(state.effects.length, 1);
  assert.equal((await request(state.port, "/api/runs")).status, 200);
  assert.equal(state.gateway.exitCode, null);
});

test("client cancellation after dispatch does not replay the operation", async t => {
  let recorded;
  const seen = new Promise(resolve => { recorded = resolve; });
  let closed;
  const upstreamClosed = new Promise(resolve => { closed = resolve; });
  const state = await lab(t, (req, res, _body, effects) => {
    if (req.url === "/api/runs") return res.end(JSON.stringify(effects));
    effects.push("one-effect"); req.socket.on("close", () => closed(true)); recorded();
  });
  const req = http.request({ hostname: "127.0.0.1", port: state.port, path: "/api/confirm-run", method: "POST",
    headers: { "X-Nexus-Session": "synthetic-session", "Content-Type": "application/json", "Content-Length": "2" } });
  req.on("error", () => {});
  req.end("{}");
  await seen;
  req.destroy();
  assert.equal(await Promise.race([upstreamClosed, new Promise(resolve => setTimeout(() => resolve(false), 1000))]), true,
    "the abandoned upstream connection must be closed without waiting 30 seconds");
  assert.deepEqual(JSON.parse((await request(state.port, "/api/runs")).body), ["one-effect"]);
  assert.equal(state.gateway.exitCode, null);
});

test("real 30-second upstream timeout after an effect is UNKNOWN, never replayed", { timeout: 45000 }, async t => {
  const state = await lab(t, (req, res, _body, effects) => {
    if (req.url === "/api/runs") return res.end(JSON.stringify(effects));
    effects.push("one-effect"); // deliberately leave the actual socket unanswered
  });
  const response = await request(state.port, "/api/confirm-run", { method: "POST", payload: { confirmed: true }, timeout: 40000 });
  assert.equal(state.effects.length, 1);
  unknown(response);
  assert.deepEqual(JSON.parse((await request(state.port, "/api/runs")).body), ["one-effect"]);
});
