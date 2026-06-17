# Network Requirements for GitHub Codespaces in Education

This project lets Computer Science teachers run Python coding exercises entirely in the browser — no installers, no Python versions, it doesn't even need to run on a Windows device. Students open a link, get a fully configured VS Code environment with notebooks and autograded tests, and the teacher controls everything through the repository. This document is for IT network administrators whose school is adopting this approach. It explains why it's worth supporting, how to scope access safely, and exactly what needs to be unblocked.

- [Network Requirements for GitHub Codespaces in Education](#network-requirements-for-github-codespaces-in-education)
  - [Why support this? — It's safer and less work than local Python](#why-support-this--its-safer-and-less-work-than-local-python)
    - [Security isolation](#security-isolation)
    - [Zero configuration burden](#zero-configuration-burden)
    - [Consistent environment](#consistent-environment)
  - [Recommendation: scope access by user group](#recommendation-scope-access-by-user-group)
  - [What to unblock](#what-to-unblock)
    - [Core domains](#core-domains)
    - [Protocols and ports](#protocols-and-ports)
    - [Source references](#source-references)
    - [Verification](#verification)

---

## Why support this? — It's safer and less work than local Python

### Security isolation

**Codespaces run on Microsoft's Azure infrastructure, not on the school network.** When a student opens a Codespace, their browser establishes an encrypted tunnel to a remote virtual machine in Azure. The code they write and run executes inside that cloud container.

This means:

- **Malicious code can't reach the school network.** If a student writes and executes deliberately harmful code (e.g., attempting to scan ports or run cryptominers), it runs inside the isolated cloud container — not on a school-managed device or server.
- **No inbound exposure.** The school firewall only needs to allow *outbound* connections to the listed domains. No ports need to be opened to allow external traffic in.
- **No persistent installation.** No Python interpreters, packages, or IDE binaries are installed on school devices. Everything lives in the cloud and is torn down when the Codespace is stopped.

The security model is analogous to allowing access to any SaaS product (Google Docs, Office 365) — the browser makes a remote connection, and the heavy lifting happens externally.

### Zero configuration burden

With a local Python setup (e.g., Thonny, IDLE, or a manually installed VS Code), IT support is regularly asked to:

- Install or update Python on individual machines
- Install specific library packages (`pip install ...`)
- Resolve version conflicts between classes
- Debug "it works on my machine" issues caused by inconsistent environments
- Handle OS updates that break the Python path
- Install new software when the curriculum changes

With Codespaces, **none of this is your problem.**

- The development environment is defined in a repository config file. Every student gets an identical, pre-configured environment regardless of their local device.
- If a library needs updating, the teacher updates the repository config — students see the change on their next Codespace start.
- If something breaks, the teacher debugs it. IT is not involved unless the network configuration changes.

### Consistent environment

Every student gets the same Python version, the same extensions, the same linter settings, and the same libraries — whether they're using a Windows laptop, a Chromebook, or an iPad. The teacher controls the environment through the repository configuration, not through Group Policy or MDM profile updates.

---

## Recommendation: scope access by user group

We recognise that allowing outbound access to these domains creates a tunnel through the firewall. While the tunnel connects to a tightly restricted cloud container, it is technically possible (with significant difficulty) for a determined student to use it to bypass network restrictions — for example, by running a proxy inside their Codespace that forwards traffic to external sites.

The risk is low and manageable because:

- The Codespace is a disposable container with no persistence between sessions.
- Any attempt to tunnel traffic leaves logs on the student's GitHub account (their Codespace activity is tied to their identity).
- Standard classroom management techniques — line-of-sight teaching, circulating the room, monitoring screens — are sufficient to catch misuse.

**However, to minimise the attack surface, we recommend unblocking these domains only for the computers or student accounts that need them**, rather than opening them for the entire school. This can be done by:

- **By user/group** — applying the firewall rules to a specific Active Directory group or Chromebook organisational unit that contains only Computer Science students.
- **By device** — if specific lab machines or Chromebooks are used for coding, scope the rules to those devices only.
- **By time** — if your firewall supports time-based rules, consider allowing access only during scheduled lesson times.

Keeping the scope limited makes it trivial to identify who is using the tunnel if an issue arises, without impeding the rest of the school.

---

## What to unblock

GitHub Codespaces requires outbound HTTPS and WebSocket connections to the following domains. The browser connects to a cloud-based development environment running on Microsoft Azure infrastructure — no inbound ports need to be opened.

### Core domains

| Domain | Port(s) | Protocol | Purpose |
| --- | --- | --- | --- |
| `github.com` | 443 | HTTPS | Main GitHub website and authentication. |
| `api.github.com` | 443 | HTTPS | GitHub REST and GraphQL APIs (repo access, user data). |
| `classroom.github.com` | 443 | HTTPS | GitHub Classroom interface for managing assignments. |
| `*.githubusercontent.com` | 443 | HTTPS | Content delivery (avatars, raw file downloads, git data). |
| `*.github.dev` | 443 | HTTPS + WSS | Codespaces web editor — the environment students open in their browser. The WebSocket connection maintains the live editor link. |
| `*.visualstudio.com` | 443 | HTTPS + WSS | Codespaces tunnel/connection service — establishes and maintains the secure link between the browser and the cloud environment. |
| `*.vscode-cdn.net` | 443 | HTTPS | VS Code asset downloads (extensions, UI components) that the browser-based editor needs to function. |
| `update.code.visualstudio.com` | 443 | HTTPS | VS Code update checks. |
| `vscode-sync-insiders.trafficmanager.net` | 443 | HTTPS | (Optional) Settings Sync across devices. |

### Protocols and ports

| Protocol | Port | Direction | Used for |
| --- | --- | --- | --- |
| HTTPS | TCP 443 | Outbound | All API calls, git operations, asset downloads, and web UI access. |
| WSS (WebSocket Secure) | TCP 443 | Outbound | Real-time communication between the browser editor and the Codespace container — this is what makes the editor feel responsive. WSS runs over the same HTTPS connection (standard port 443). |

> **ℹ️ Note on IP addresses:** Codespaces IP addresses are dynamically assigned and change regularly. The `gh api meta --jq .domains.codespaces` command returns the most up-to-date list of required domains at any time. Allowlisting by domain (as listed above) is more reliable than trying to maintain a static IP allowlist. If you need a full list of GitHub's IP ranges, they are published at the GitHub Meta API endpoint (`https://api.github.com/meta`).

### Source references

The domain list above is compiled from the following official GitHub documentation sources. If this document becomes stale, these are the authoritative references to check:

| Source | URL | What it covers |
| --- | --- | --- |
| GitHub Docs — Troubleshooting Codespaces connection | [docs.github.com/en/codespaces/troubleshooting/troubleshooting-your-connection-to-github-codespaces](https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-your-connection-to-github-codespaces) | Diagnosing blocked connections; `gh api meta --jq .domains.codespaces` command for live domain list. |
| GitHub Docs — Using github.dev behind a firewall | [docs.github.com/en/codespaces/the-githubdev-web-based-editor](https://docs.github.com/en/codespaces/the-githubdev-web-based-editor#using-githubdev-behind-a-firewall) | Domains required for the browser-based editor (`*.vscode-cdn.net`, `update.code.visualstudio.com`, `api.github.com`). |
| GitHub Docs — Security in Codespaces | [docs.github.com/en/codespaces/reference/security-in-github-codespaces](https://docs.github.com/en/codespaces/reference/security-in-github-codespaces) | Detailed security model — port forwarding, authentication, isolation. |
| GitHub Docs — Connecting to a private network | [docs.github.com/en/codespaces/developing-in-a-codespace/connecting-to-a-private-network](https://docs.github.com/en/codespaces/developing-in-a-codespace/connecting-to-a-private-network) | Networking architecture — dynamically assigned IPs and why IP allowlisting isn't viable for Codespaces. |
| GitHub Meta API | `https://api.github.com/meta` | Returns all current GitHub IP ranges and domains in JSON format. Run `gh api meta --jq .domains.codespaces` for the Codespaces-specific subset. |

### Verification

If the above domains are unblocked, a teacher or student should be able to:

1. Visit `github.com` and log in.
2. Navigate to a repository and click **Code > Codespaces > Create codespace**.
3. See the VS Code interface load in their browser within 60 seconds.
4. Edit a file, commit, and push without errors.

The most common symptom of a blocked domain is a codespace that appears to hang at "Creating codespace..." or a browser error saying "Oh no, it looks like you are offline." If this happens, check the [troubleshooting guide](https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-your-connection-to-github-codespaces) for steps to identify which domain is being blocked.
