import http from 'node:http';
import { pipeline } from 'node:stream';
import express from 'express';

/**
 * Optional, local-only Folha transport. Not an executor, Store, Kernel,
 * authority, parser, or independent memory. Every API request reaches the
 * existing Python nexus.app -> Host -> Store boundary unchanged.
 *
 * Start the Python Nexus server on a fixed local port first, then set
 * NEXUS_BACKEND_PORT and start this gateway. Both bind to 127.0.0.1.
 * The browser supplies the Python-issued X-Nexus-Session. The gateway never
 * reads launch-url.txt or generates its own session/approval tickets.
 */
const app = express();
app.disable('x-powered-by');

function port(name, fallback) {
  const raw = process.env[name] === undefined ? fallback : process.env[name];
  const number = Number(raw);
  if (!Number.isInteger(number) || number < 1 || number > 65535 ||
      String(number) !== String(raw)) {
    throw new Error('Invalid ' + name + ' (expected port 1..65535)');
  }
  return number;
}

const HOST = '127.0.0.1';
const PORT = port('PORT', '3000');
const BACKEND_PORT = port('NEXUS_BACKEND_PORT', '0');
if (BACKEND_PORT === PORT) throw new Error('Gateway and Python backend must use different ports.');

const UI_PATHS = new Set(['/', '/app.js', '/style.css']);
const READ_PATHS = new Set(['/api/runs']);
const WRITE_PATHS = new Set([
  '/api/interpret', '/api/search', '/api/prepare-run', '/api/confirm-run',
  '/api/prepare', '/api/approve',
]);
const ID_PATH = /^\/api\/(?:runs|pdf)\/[0-9a-f]{32}$/;
const MAX_BODY = 3200000;

function reject(res, code, message, outcome) {
  res.writeHead(code, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
  });
  res.end(JSON.stringify({error: message, ...(outcome ? {outcome} : {})}));
}

function allowed(method, url) {
  if (method === 'GET') return UI_PATHS.has(url) || READ_PATHS.has(url) || ID_PATH.test(url);
  if (method === 'POST') return WRITE_PATHS.has(url);
  return false;
}

app.use((req, res) => {
  const gatewayOrigin = 'http://' + HOST + ':' + PORT;
  if (req.headers.host !== HOST + ':' + PORT ||
      (req.headers.origin && req.headers.origin !== gatewayOrigin)) {
    return reject(res, 403, 'Origem inválida. Utiliza apenas a Folha local.');
  }

  const url = req.url;
  if (typeof url !== 'string' || !allowed(req.method, url)) {
    return reject(res, 403, 'Rota não autorizada.');
  }

  // Never silently replace an absent/malformed user session with a gateway
  // secret: Python Host.authorize must make the sole authority decision.
  const session = req.headers['x-nexus-session'];
  if (!UI_PATHS.has(url) &&
      (typeof session !== 'string' || session.length > 512 || !/^[\x21-\x7e]+$/.test(session))) {
    return reject(res, 403, 'Sessão Nexus ausente ou inválida.');
  }

  const upstreamHeaders = {
    Host: HOST + ':' + BACKEND_PORT,
    'X-Nexus-Session': typeof session === 'string' ? session : '',
  };
  if (req.headers.origin) upstreamHeaders.Origin = 'http://' + HOST + ':' + BACKEND_PORT;

  if (req.method === 'POST') {
    const value = req.headers['content-length'];
    const length = typeof value === 'string' && /^[0-9]+$/.test(value) ? Number(value) : NaN;
    if (!Number.isSafeInteger(length) || length <= 0 || length > MAX_BODY ||
        req.headers['content-type']?.split(';')[0] !== 'application/json' ||
        req.headers['transfer-encoding']) {
      return reject(res, 403, 'Pedido inválido ou demasiado grande.');
    }
    upstreamHeaders['Content-Type'] = req.headers['content-type'];
    upstreamHeaders['Content-Length'] = String(length);
  }

  const upstream = http.request({
    hostname: HOST, port: BACKEND_PORT, method: req.method, path: url,
    headers: upstreamHeaders, agent: false, timeout: 30000,
  }, (upstreamResponse) => {
    if (res.headersSent) return upstreamResponse.destroy();
    // Transport only: forward status and bytes verbatim. Never interpret,
    // synthesize, cache, promote, or mutate any result/memory.
    const headers = {};
    for (const [key, value] of Object.entries(upstreamResponse.headers)) {
      if (!['connection', 'keep-alive', 'transfer-encoding', 'upgrade',
             'proxy-connection', 'trailer'].includes(key) && value !== undefined) {
        headers[key] = value;
      }
    }
    res.writeHead(upstreamResponse.statusCode || 502, headers);
    // A broken upstream frame must close the downstream response promptly.
    // The browser then knows delivery failed; it cannot infer no operation ran.
    pipeline(upstreamResponse, res, () => {});
  });

  upstream.on('timeout', () => upstream.destroy(new Error('Backend timed out')));
  upstream.on('error', () => {
    if (res.destroyed) return;
    if (!res.headersSent) return reject(res, 503,
      'Não foi possível confirmar o resultado. Consulta os trabalhos anteriores antes de repetir o pedido.', 'UNKNOWN');
    res.destroy();
  });
  req.on('aborted', () => upstream.destroy());
  // Stop abandoned transport only, never cancel/replay a Host operation.
  res.on('close', () => { if (!res.writableEnded) upstream.destroy(); });
  req.pipe(upstream);
});

app.listen(PORT, HOST, () => {
  console.log('Folha gateway local em http://' + HOST + ':' + PORT);
  console.log('A execução e a memória pertencem exclusivamente ao Host Python na porta ' + BACKEND_PORT);
});
