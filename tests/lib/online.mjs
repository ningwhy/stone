/** Where the online checks point, and how they get there.
 *
 *  The site has two addresses:
 *
 *    stone.yan.pub         the public one, behind Cloudflare. Its managed
 *                          bot challenge answers every automated client with a
 *                          403 challenge page — including a headed Chrome. It
 *                          also serves the assets, so a stale bundle or a
 *                          pruned file is still visible through it.
 *
 *    stone-direct.yan.pub  DNS-only, straight to the origin, with its own
 *                          Let's Encrypt certificate. No challenge, no
 *                          certificate mismatch, nothing to work around.
 *
 *  The checks run against the direct address. It is the same deployed bytes —
 *  the origin is behind the tunnel either way — but it answers an automated
 *  client the way a browser answers one, so a run measures the site instead
 *  of measuring the challenge.
 *
 *  Set TEST_URL to point somewhere else (a local dev server, or the public
 *  address when the challenge is lifted). Set ORIGIN_DIRECT=1 to keep the old
 *  behaviour of resolving the public name to the origin IP.
 */
export const DIRECT_HOST='stone-direct.yan.pub';
export const PUBLIC_HOST='stone.yan.pub';
export const ORIGIN_IP='154.8.237.35';

/** The address an online check should visit. */
export function onlineUrl() {
  return process.env.TEST_URL??`https://${DIRECT_HOST}/`;
}

/** A short label for the run's output. */
export function onlineTag() {
  const url=onlineUrl();
  if(url.includes(DIRECT_HOST))return 'direct';
  if(url.includes(PUBLIC_HOST))return 'public';
  return 'online';
}

/** The browser options an online check needs.
 *
 *  `ignoreHTTPSErrors` is only needed for the old trick of resolving the public
 *  name to the origin IP: that address serves the Cloudflare Origin CA
 *  certificate, which does not match the name it was reached by. The direct
 *  address has its own certificate and needs no such allowance. */
export function onlineArgs() {
  const args=['--disable-blink-features=AutomationControlled'];
  if(process.env.ORIGIN_DIRECT==='1')args.push(`--host-resolver-rules=MAP ${PUBLIC_HOST} ${ORIGIN_IP}`);
  return args;
}

/** Whether TLS errors should be tolerated (only for the origin-IP trick). */
export function ignoreTlsErrors() {
  return process.env.ORIGIN_DIRECT==='1'&&!onlineUrl().includes(DIRECT_HOST);
}

/** A profile directory for a run, kept apart per script and per mode. */
export function onlineProfile(name) {
  const custom=process.env.ONLINE_PROFILE;
  if(custom)return custom;
  const suffix=onlineTag()==='direct'?'direct':'online';
  return `/tmp/wb-${suffix}-${name}`;
}
