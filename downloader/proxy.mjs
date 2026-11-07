// Proxy helpers removed — CDN downloads use the system VPN.
// Kept as stubs so older import sites fail closed into torrent fallback.

/** @deprecated Always null — connect a system VPN instead of configuring an HTTP proxy. */
export async function fetchCdnWithPaidProxy() {
  return null;
}

/** @deprecated */
export async function fetchCdnWithProxies() {
  throw new Error('HTTP proxies removed. Connect your VPN app, or fall back to torrent.');
}

/** @deprecated */
export async function fetchViaProxy() {
  throw new Error('HTTP proxies removed. Connect your VPN app, or fall back to torrent.');
}
