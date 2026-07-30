import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


USERNAME = "zaidnayaz"
README = Path("README.md")
START = "<!-- AUTO-GENERATED-START -->"
END = "<!-- AUTO-GENERATED-END -->"


def github_get(path):
    request = urllib.request.Request(f"https://api.github.com/{path}")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fmt_date(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%d %b %Y")
    except Exception:
        return value[:10]


def render():
    user = github_get(f"users/{USERNAME}")
    repos = github_get(f"users/{USERNAME}/repos?sort=updated&per_page=100")
    visible_repos = [repo for repo in repos if not repo.get("private")]
    updated_repos = sorted(
        visible_repos,
        key=lambda repo: repo.get("pushed_at") or repo.get("updated_at") or "",
        reverse=True,
    )[:5]

    total_stars = sum(repo.get("stargazers_count", 0) for repo in visible_repos)
    total_forks = sum(repo.get("forks_count", 0) for repo in visible_repos)
    languages = {}
    for repo in visible_repos:
        language = repo.get("language") or "Documentation"
        languages[language] = languages.get(language, 0) + 1
    top_languages = ", ".join(
        f"{language} ({count})"
        for language, count in sorted(languages.items(), key=lambda item: (-item[1], item[0]))[:5]
    )

    lines = [
        f"_Last refreshed: {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}_",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Public repositories | {user.get('public_repos', len(visible_repos))} |",
        f"| Total stars | {total_stars} |",
        f"| Total forks | {total_forks} |",
        f"| Top repository languages | {top_languages or 'Building'} |",
        "",
        "### Recently Updated Repositories",
        "",
    ]

    for repo in updated_repos:
        description = repo.get("description") or "Project repository and documentation."
        if len(description) > 150:
            description = description[:147].rstrip() + "..."
        lines.append(
            f"- [{repo['name']}]({repo['html_url']}) - {description} "
            f"`updated {fmt_date(repo.get('pushed_at') or repo.get('updated_at') or '')}`"
        )

    return "\n".join(lines).strip()


def main():
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise SystemExit("README markers not found.")
    before, rest = readme.split(START, 1)
    _, after = rest.split(END, 1)
    generated = f"{START}\n{render()}\n{END}"
    README.write_text(before + generated + after, encoding="utf-8")


if __name__ == "__main__":
    main()
