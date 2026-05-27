# podmania/template

Template for creating new podmania container images. Uses [nix2container](https://github.com/nlewo/nix2container) to build distroless images designed for rootless Podman.

## Usage

Go to **Actions → Create image from template** and fill in the inputs:

| Input | Required | Description |
| --- | --- | --- |
| `name` | Yes | nixpkgs package name (e.g. `sonarr`, `qbittorrent-nox`) |
| `upstream` | Yes | Upstream repo in `owner/repo` format (e.g. `Radarr/Radarr`) |
| `api-url` | No | Forge API base URL (default: `https://api.github.com`) |
| `tag-prefix` | No | Tag prefix to strip (default: `v`) |
| `fetcher` | No | Nix fetcher: `fetchzip` (default) or `fetchurl` |
| `fetch-url` | Yes | Source URL template with `${VERSION}` placeholder |
| `description` | No | Description. Auto-detected from nixpkgs if blank |
| `ports` | No | Comma-separated ports (e.g. `8080,6881`) |
| `volumes` | No | Comma-separated volumes (e.g. `/config,/data`) |
| `env` | No | Comma-separated env vars (e.g. `KEY=value,KEY2=value2`) |
| `cmd_args` | No | Comma-separated extra args (e.g. `-data=/config,-nobrowser`) |

### Examples

**GitHub upstream**:
- `name`: `radarr`
- `upstream`: `Radarr/Radarr`
- `fetch-url`: `https://github.com/Radarr/Radarr/archive/refs/tags/v${VERSION}.tar.gz`

**Forgejo/Codeberg upstream**:
- `name`: `forgejo`
- `upstream`: `forgejo/forgejo`
- `api-url`: `https://codeberg.org/api/v1`
- `fetch-url`: `https://codeberg.org/forgejo/forgejo/archive/v${VERSION}.tar.gz`

**Custom tarball URL** (e.g. MariaDB):
- `name`: `mariadb`
- `upstream`: `MariaDB/server`
- `fetcher`: `fetchurl`
- `fetch-url`: `https://archive.mariadb.org/mariadb-${VERSION}/source/mariadb-${VERSION}.tar.gz`

## What gets generated

```
podmania/<name>/
├── .github/
│   ├── FUNDING.yml
│   └── workflows/
│       ├── build-publish.yml    # Calls shared workflow for multi-arch build + GHCR push + release
│       ├── update-version.yml   # Calls shared workflow for daily upstream version polling
│       └── create-image.yml     # One-time setup (this workflow, harmless to keep)
├── config.json                  # Package config read by workflows (name, upstream, api-url, fetcher, images)
├── flake.nix                    # nix2container image definition with upstream source tracking
├── compose.yml                  # Rootless Podman compose file
├── Dockerfile                   # Local build Dockerfile
├── Dockerfile.debug             # Local build Dockerfile (debug variant)
├── LICENSE
└── README.md
```

## How it works

- `flake.nix` uses `<%= %>` / `<% %>` jinja2 delimiters so templates don't conflict with nix expression syntax
- `render.py` sets `block_start_string="<%"` and `variable_start_string="<%="` to distinguish variables from control flow
- Workflow files (`build-publish.yml`, `update-version.yml`) are static — they read package-specific values from `config.json`
- Build and update workflows use shared reusable workflows from [podmania/actions](https://github.com/podmania/actions)
- `flake.nix` tracks upstream releases with hardcoded `version` and `srcHash`, updated by the `update-flake` composite action
- Supports any forge (GitHub, Codeberg, self-hosted Forgejo/Gitea) via configurable `api-url`
- Uses generic `fetchzip`/`fetchurl` fetchers with a URL template for any source
- Images only rebuild when the upstream version changes
