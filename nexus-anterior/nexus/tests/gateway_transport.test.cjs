"use strict";
const assert = require("node:assert/strict");
const { before, after, test } = require("node:test");
const http = require("node:http");
const net = require("node:net");
const path = require("node:path");
const { spawn } = require("node:child_process");

const ROOT = path.resolve(__dirname, "../..");
let backend, gateway, backendPort, gatewayPort;
const calls = [];

function makeRequest(port, target, options = {}) {
  const { method = "GET", headers = {}, body } = options;
  return new Promise((resolve, reject) => {
    const request = http.request({
      hostname: "127.0.0.1", port, method, path: target,
      headers: { Host: "127.0.0.1:" + port, ...headers },
      timeout: 4000,
    }, response => {
      const chunks = [];
      response.on("data", part => chunks.push(part));
      response.on("end", () => resolve({
        status: response.statusCode,
        headers: response.headers,
        body: Buffer.concat(chunks),
      }));
    });
    request.on("error", reject);
    request.on("timeout", () => request.destroy(new Error("request timeout")));
    if (body !== undefined) request.write(body);
    request.end();
  });
}

async function reservePort() {
  const server = net.createServer();
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}

before(async () => {
  backend = http.createServer((req, res) => {
    const chunks = [];
    req.on("data", chunk => chunks.push(chunk));
    req.on("end", () => {
      const raw = Buffer.concat(chunks);
      calls.push({
        url: req.url, method: req.method, session: req.headers["x-nexus-session"],
        host: req.headers.host, origin: req.headers.origin, body: raw,
      });
      if (req.headers.host !== "127.0.0.1:" + backendPort) {
        res.writeHead(403); return res.end("wrong upstream host");
      }
      if (req.url === "/" || req.url === "/app.js" || req.url === "/style.css") {
        res.writeHead(200, { "Content-Type": "text/html", "Cache-Control": "no-store" });
        return res.end("PYTHON_HOST_UI");
      }
      if (req.headers["x-nexus-session"] !== "python-session") {
        res.writeHead(403, { "Content-Type": "application/json" });
        return res.end('{"error":"Python Host rejects invalid session"}');
      }
      if (req.url === "/api/approve" || req.url === "/api/confirm-run") {
        res.writeHead(403, { "Content-Type": "application/json" });
        return res.end('{"error":"Python Host denies unconfirmed operation"}');
      }
      if (req.url === "/api/runs") {
        res.writeHead(200, { "Content-Type": "application/json" });
        return res.end('[{"run_id":"from-python-store","status":"HUMAN_REQUIRED"}]');
      }
      if (req.url === "/api/pdf/" + "a".repeat(32)) {
        res.writeHead(200, { "Content-Type": "application/pdf" });
        return res.end(Buffer.from("%PDF-python-store"));
      }
      res.writeHead(202, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ source: "python", request: raw.toString("utf8") }));
    });
  });
  await new Promise(resolve => backend.listen(0, "127.0.0.1", resolve));
  backendPort = backend.address().port;
  gatewayPort = await reservePort();
  gateway = spawn(process.execPath, ["server.js"], {
    cwd: ROOT,
    env: { ...process.env, PORT: String(gatewayPort),
      NEXUS_BACKEND_PORT: String(backendPort) },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const errors = [];
  gateway.stderr.on("data", value => errors.push(value.toString("utf8")));
  for (let i = 0; i < 60; i++) {
    if (gateway.exitCode !== null) throw new Error("Gateway exited: " + errors.join(""));
    try {
      const response = await makeRequest(gatewayPort, "/");
      if (response.status === 200) return;
    } catch (_) { /* wait for bound loopback listener */ }
    await new Promise(resolve => setTimeout(resolve, 75));
  }
  throw new Error("Gateway did not start: " + errors.join(""));
});

after(async () => {
  if (gateway && gateway.exitCode === null) {
    gateway.kill();
    await new Promise(resolve => gateway.once("exit", resolve));
  }
  if (backend?.listening) await new Promise(resolve => backend.close(resolve));
});

test("serves exactly the Python Folha bytes; no independently generated UI", async () => {
  const response = await makeRequest(gatewayPort, "/");
  assert.equal(response.status, 200);
  assert.equal(response.body.toString(), "PYTHON_HOST_UI");
});

test("rejects absent sessions, hostile Host/Origin and unknown routes before backend", async () => {
  const count = calls.length;
  const sessionless = await makeRequest(gatewayPort, "/api/runs");
  assert.equal(sessionless.status, 403);
  const hostileHost = await makeRequest(gatewayPort, "/api/runs", {
    headers: { Host: "attacker.example", "X-Nexus-Session": "python-session" },
  });
  assert.equal(hostileHost.status, 403);
  const hostileOrigin = await makeRequest(gatewayPort, "/api/runs", {
    headers: { Origin: "https://attacker.example", "X-Nexus-Session": "python-session" },
  });
  assert.equal(hostileOrigin.status, 403);
  const ARCHIVE_REDACTED_04 = await makeRequest(gatewayPort, "/api/run", {
    method: "POST", headers: { "X-Nexus-Session": "python-session" },
  });
  assert.equal(ARCHIVE_REDACTED_04.status, 403);
  assert.equal(calls.length, count);
});

test("returns only backend Store records and preserves Python session", async () => {
  const response = await makeRequest(gatewayPort, "/api/runs", {
    headers: { "X-Nexus-Session": "python-session" },
  });
  assert.equal(response.status, 200);
  assert.deepEqual(JSON.parse(response.body.toString()), [
    { run_id: "from-python-store", status: "HUMAN_REQUIRED" },
  ]);
  const last = calls.at(-1);
  assert.equal(last.host, "127.0.0.1:" + backendPort);
  assert.equal(last.session, "python-session");
});

test("passes original request bytes unchanged; Python controls approval", async () => {
  const payload = Buffer.from(JSON.stringify({
    ticket: "human-ticket", confirmed: true,
    text: "Olá, memória não é autoridade", filename: "original.txt",
    attachment: Buffer.from("abc").toString("base64"),
  }), "utf8");
  const response = await makeRequest(gatewayPort, "/api/confirm-run", {
    method: "POST",
    headers: {
      "X-Nexus-Session": "python-session",
      "Content-Type": "application/json",
      "Content-Length": String(payload.length),
      Origin: "http://127.0.0.1:" + gatewayPort,
    },
    body: payload,
  });
  assert.equal(response.status, 403);
  assert.match(response.body.toString(), /Python Host denies/);
  const last = calls.at(-1);
  assert.equal(last.method, "POST");
  assert.equal(last.origin, "http://127.0.0.1:" + backendPort);
  assert.deepEqual(last.body, payload);

  const rejectedPromotion = await makeRequest(gatewayPort, "/api/approve", {
    method: "POST",
    headers: {
      "X-Nexus-Session": "python-session",
      "Content-Type": "application/json",
      "Content-Length": "2",
    },
    body: Buffer.from("{}"),
  });
  assert.equal(rejectedPromotion.status, 403);
});

test("forwards PDF bytes from the Store without synthetic conversion", async () => {
  const response = await makeRequest(gatewayPort, "/api/pdf/" + "a".repeat(32), {
    headers: { "X-Nexus-Session": "python-session" },
  });
  assert.equal(response.status, 200);
  assert.deepEqual(response.body, Buffer.from("%PDF-python-store"));
  assert.equal(response.headers["content-type"], "application/pdf");
});

test("does not accept malformed POST framing", async () => {
  const count = calls.length;
  const response = await makeRequest(gatewayPort, "/api/prepare-run", {
    method: "POST",
    headers: { "X-Nexus-Session": "python-session", "Content-Type": "text/plain" },
    body: Buffer.from("bad"),
  });
  assert.equal(response.status, 403);
  assert.equal(calls.length, count);
});
