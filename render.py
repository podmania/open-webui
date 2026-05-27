#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys

from jinja2 import Environment, FileSystemLoader

TEMPLATES = [
    "flake.nix",
    "compose.yml",
    "Dockerfile",
    "Dockerfile.debug",
]

STATIC_FILES = [
    "LICENSE",
    ".github/FUNDING.yml",
    ".github/workflows/build-publish.yml",
    ".github/workflows/update-version.yml",
]


def nix_eval(attr):
    try:
        result = subprocess.run(
            [
                "nix",
                "--extra-experimental-features",
                "nix-command flakes",
                "eval",
                f"nixpkgs#{attr}",
                "--raw",
                "--impure",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return None


def main():
    name = os.environ.get("INPUT_NAME", "").strip()
    if not name:
        print("::error::name is required")
        sys.exit(1)

    upstream = os.environ.get("INPUT_UPSTREAM", "").strip()
    api_url = os.environ.get("INPUT_API_URL", "https://api.github.com").strip()
    tag_prefix = os.environ.get("INPUT_TAG_PREFIX", "v").strip()
    fetcher = os.environ.get("INPUT_FETCHER", "fetchzip").strip()
    fetch_url = os.environ.get("INPUT_FETCH_URL", "").strip()

    if not upstream:
        print("::error::upstream is required (e.g. Radarr/Radarr)")
        sys.exit(1)

    if not fetch_url:
        print("::error::fetch-url is required (e.g. https://github.com/Radarr/Radarr/archive/refs/tags/v${VERSION}.tar.gz)")
        sys.exit(1)

    description = os.environ.get("INPUT_DESCRIPTION", "").strip()
    ports_raw = os.environ.get("INPUT_PORTS", "").strip()
    volumes_raw = os.environ.get("INPUT_VOLUMES", "").strip()
    env_raw = os.environ.get("INPUT_ENV", "").strip()
    cmd_args_raw = os.environ.get("INPUT_CMD_ARGS", "").strip()

    if not description:
        description = nix_eval(f"{name}.meta.description") or ""

    main_program = nix_eval(f"{name}.meta.mainProgram")

    ports = [p.strip() for p in ports_raw.split(",") if p.strip()] if ports_raw else []
    volumes = [v.strip() for v in volumes_raw.split(",") if v.strip()] if volumes_raw else []
    env = [e.strip() for e in env_raw.split(",") if e.strip()] if env_raw else []
    cmd_args = [a.strip() for a in cmd_args_raw.split(",") if a.strip()] if cmd_args_raw else []

    print(f"Package: {name}")
    print(f"Upstream: {upstream}")
    print(f"API URL: {api_url}")
    print(f"Tag prefix: {tag_prefix}")
    print(f"Fetcher: {fetcher}")
    print(f"Fetch URL: {fetch_url}")
    print(f"Description: {description}")
    print(f"Main program: {main_program}")
    print(f"Ports: {ports}")
    print(f"Volumes: {volumes}")
    print(f"Env: {env}")
    print(f"Cmd args: {cmd_args}")

    template_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.environ.get("OUTPUT_DIR", "").strip() or template_dir

    jinja_env = Environment(
        loader=FileSystemLoader(template_dir),
        keep_trailing_newline=True,
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="<%=",
        variable_end_string="%>",
    )

    context = dict(
        name=name,
        description=description,
        upstream=upstream,
        tag_prefix=tag_prefix,
        fetcher=fetcher,
        fetch_url=fetch_url,
        ports=ports,
        volumes=volumes,
        env=env,
        cmd_args=cmd_args,
        main_program=main_program,
    )

    for template_name in TEMPLATES:
        tmpl = jinja_env.get_template(template_name)
        rendered = tmpl.render(**context)
        output_path = os.path.join(output_dir, template_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(rendered)
        print(f"Rendered {template_name}")

    for static_file in STATIC_FILES:
        src = os.path.join(template_dir, static_file)
        dst = os.path.join(output_dir, static_file)
        if os.path.exists(src) and os.path.abspath(src) != os.path.abspath(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            print(f"Copied {static_file}")

    config = {
        "name": name,
        "upstream": upstream,
        "apiUrl": api_url,
        "tagPrefix": tag_prefix,
        "fetcher": fetcher,
        "fetchUrl": fetch_url,
        "versionOutput": f"{name}Version",
        "images": [{"name": name, "package": f"{name}-image"}],
    }
    config_path = os.path.join(output_dir, "config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
    print("Generated config.json")

    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write(f"# {name}\n\n{description}\n\n")
        f.write(f"Upstream: [{upstream}](https://github.com/{upstream})\n")
        if ports:
            f.write("\n## Ports\n\n")
            for port in ports:
                f.write(f"- `{port}`\n")
        if volumes:
            f.write("\n## Volumes\n\n")
            for volume in volumes:
                f.write(f"- `{volume}`\n")
        f.write(
            '\n<a href="https://www.buymeacoffee.com/bhoehn"'
            ' target="_blank">'
            '<img src="https://cdn.buymeacoffee.com/buttons/'
            'default-orange.png" alt="Buy Me A Coffee"'
            ' height="41" width="174"></a>\n'
        )
    print("Generated README.md")


if __name__ == "__main__":
    main()
