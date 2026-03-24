#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import textwrap
from pathlib import Path, PurePosixPath


DEFAULT_REMOTE_HOME = "/dev_vepfs/rc_wu"
DEFAULT_REMOTE_BINARY_STORE = f"{DEFAULT_REMOTE_HOME}/bin/codex"
DEFAULT_REMOTE_RUN_ROOT = f"{DEFAULT_REMOTE_HOME}/codex_subagents"
DEFAULT_DEV02_PROXY_HELPER = f"{DEFAULT_REMOTE_HOME}/bin/ensure_codex_proxy.sh"
DEFAULT_DEV02_PROXY_BINARY = f"{DEFAULT_REMOTE_HOME}/software/clash/clash"
DEFAULT_DEV02_PROXY_CONFIG = f"{DEFAULT_REMOTE_HOME}/software/clash/config.yaml"
DEFAULT_DEV02_PROXY_STATE_DIR = f"{DEFAULT_REMOTE_HOME}/cache/tmp"
DEFAULT_DEV02_PROXY_HTTP_PORT = 27890
DEFAULT_DEV02_PROXY_SOCKS_PORT = 27891
DEFAULT_DEV02_PROXY_CONTROLLER_PORT = 29090
SSH_CONNECT_TIMEOUT_SECONDS = 10
SSH_RETRY_ATTEMPTS = 3
SUBPROCESS_NO_WINDOW = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if os.name == "nt" else {}


def run_local(cmd: list[str], *, input_text: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
        capture_output=True,
        **SUBPROCESS_NO_WINDOW,
    )


def write_stream_text(stream, text: str) -> None:
    if not text:
        return
    try:
        stream.write(text)
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "utf-8"
        data = text.encode(encoding, errors="replace")
        buffer = getattr(stream, "buffer", None)
        if buffer is not None:
            buffer.write(data)
        else:
            stream.write(data.decode(encoding, errors="replace"))
    stream.flush()


def choose_local_linux_binary(explicit: Path | None) -> Path:
    if explicit is not None:
        path = explicit.expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        return path

    root = Path.home() / ".vscode" / "extensions"
    candidates = sorted(
        root.glob("openai.chatgpt-*/bin/linux-x86_64/codex"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError("No local linux-x86_64 codex binary found under ~/.vscode/extensions")
    return candidates[0].resolve()


def ssh(host: str, remote_cmd: str, *, input_text: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = ["ssh", "-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT_SECONDS}", host, remote_cmd]
    result = run_local(cmd, input_text=input_text, check=False)
    for _ in range(1, SSH_RETRY_ATTEMPTS):
        if result.returncode == 0:
            break
        result = run_local(cmd, input_text=input_text, check=False)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)
    return result


def scp_legacy(local_path: Path, host: str, remote_path: str) -> subprocess.CompletedProcess[str]:
    return run_local(["scp", "-O", "-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT_SECONDS}", str(local_path), f"{host}:{remote_path}"])


def write_remote_text(host: str, remote_path: str, text: str) -> None:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    cmd = ["ssh", "-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT_SECONDS}", host, f"cat > {shlex.quote(remote_path)}"]
    proc = subprocess.run(
        cmd,
        input=normalized.encode("utf-8"),
        check=False,
        capture_output=True,
        **SUBPROCESS_NO_WINDOW,
    )
    for _ in range(1, SSH_RETRY_ATTEMPTS):
        if proc.returncode == 0:
            break
        proc = subprocess.run(
            cmd,
            input=normalized.encode("utf-8"),
            check=False,
            capture_output=True,
            **SUBPROCESS_NO_WINDOW,
        )
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, proc.args, output=proc.stdout, stderr=proc.stderr)


def should_ensure_dev02_proxy(args: argparse.Namespace) -> bool:
    flag = getattr(args, "ensure_dev02_proxy", None)
    if flag is not None:
        return bool(flag)
    return args.host == "dev-intern-02"


def build_dev02_proxy_env(args: argparse.Namespace) -> dict[str, str]:
    http_proxy = f"http://127.0.0.1:{int(args.proxy_http_port)}"
    all_proxy = f"socks5h://127.0.0.1:{int(args.proxy_socks_port)}"
    no_proxy = "localhost,127.0.0.1,::1"
    return {
        "HTTP_PROXY": http_proxy,
        "HTTPS_PROXY": http_proxy,
        "ALL_PROXY": all_proxy,
        "http_proxy": http_proxy,
        "https_proxy": http_proxy,
        "all_proxy": all_proxy,
        "NO_PROXY": no_proxy,
        "no_proxy": no_proxy,
    }


def effective_sandbox(args: argparse.Namespace) -> str:
    if args.host == "dev-intern-02" and args.sandbox == "workspace-write" and not getattr(
        args, "no_auto_dev02_sandbox_fix", False
    ):
        return "danger-full-access"
    return args.sandbox


def build_provider_override_flags_for_route(route: dict[str, object]) -> list[str]:
    provider_name = str(route.get("provider_name") or "").strip()
    provider_base_url = str(route.get("provider_base_url") or "").strip()
    if not provider_name or not provider_base_url:
        return []

    display_name = str(route.get("provider_display_name") or provider_name).strip()
    requires_openai_auth = "true" if bool(route.get("provider_requires_openai_auth")) else "false"
    return [
        "-c",
        f"model_provider={json.dumps(provider_name)}",
        "-c",
        f"model_providers.{provider_name}.name={json.dumps(display_name)}",
        "-c",
        f"model_providers.{provider_name}.base_url={json.dumps(provider_base_url)}",
        "-c",
        f"model_providers.{provider_name}.wire_api={json.dumps(str(route.get('provider_wire_api') or 'responses'))}",
        "-c",
        f"model_providers.{provider_name}.env_key={json.dumps(str(route.get('provider_env_key') or 'OPENAI_API_KEY'))}",
        "-c",
        f"model_providers.{provider_name}.requires_openai_auth={requires_openai_auth}",
    ]


def build_provider_override_flags(args: argparse.Namespace) -> list[str]:
    return build_provider_override_flags_for_route(
        {
            "provider_name": args.provider_name,
            "provider_display_name": args.provider_display_name or args.provider_name,
            "provider_base_url": args.provider_base_url,
            "provider_wire_api": args.provider_wire_api,
            "provider_env_key": args.provider_env_key,
            "provider_requires_openai_auth": bool(args.provider_requires_openai_auth),
        }
    )


def bool_from_any(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off", ""}:
        return False
    raise ValueError(f"Cannot coerce value to bool: {value!r}")


def slugify_provider_name(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "route"


def load_route_specs_from_path(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError(f"Route spec file must contain a JSON object or list: {path}")
    return [dict(item) for item in payload]


def normalize_route_spec(
    spec: dict[str, object],
    args: argparse.Namespace,
    default_api_key_file: str,
    index: int,
) -> dict[str, object]:
    provider_base_url = str(spec.get("provider_base_url") or spec.get("base_url") or args.provider_base_url or "").strip()
    provider_name = str(spec.get("provider_name") or spec.get("name") or args.provider_name or "").strip()
    if provider_base_url and not provider_name:
        provider_name = slugify_provider_name(provider_base_url)
    provider_display_name = str(
        spec.get("provider_display_name") or spec.get("display_name") or args.provider_display_name or provider_name
    ).strip()
    provider_wire_api = str(spec.get("provider_wire_api") or spec.get("wire_api") or args.provider_wire_api or "responses").strip()
    provider_env_key = str(spec.get("provider_env_key") or spec.get("env_key") or args.provider_env_key or "OPENAI_API_KEY").strip()
    provider_requires_openai_auth = bool_from_any(
        spec.get("provider_requires_openai_auth", spec.get("requires_openai_auth")),
        default=bool(args.provider_requires_openai_auth),
    )
    api_key_file = str(spec.get("api_key_file") or spec.get("key_file") or default_api_key_file).strip()
    model = str(spec.get("model") or args.model or "").strip()
    route_name = str(
        spec.get("route_name")
        or spec.get("label")
        or provider_name
        or (Path(api_key_file).stem if api_key_file else "")
        or f"route_{index + 1}"
    ).strip()
    return {
        "route_name": route_name,
        "provider_name": provider_name,
        "provider_display_name": provider_display_name,
        "provider_base_url": provider_base_url,
        "provider_wire_api": provider_wire_api,
        "provider_env_key": provider_env_key,
        "provider_requires_openai_auth": provider_requires_openai_auth,
        "api_key_file": api_key_file,
        "model": model,
    }


def collect_route_specs(args: argparse.Namespace, default_api_key_file: str) -> list[dict[str, object]]:
    raw_specs: list[dict[str, object]] = []
    for path in args.route_spec_file or []:
        raw_specs.extend(load_route_specs_from_path(path))
    for raw in args.route_spec or []:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            raw_specs.append(dict(payload))
        elif isinstance(payload, list):
            raw_specs.extend(dict(item) for item in payload)
        else:
            raise ValueError(f"Route spec must decode to a JSON object or list: {raw!r}")

    if raw_specs:
        return [normalize_route_spec(spec, args, default_api_key_file, idx) for idx, spec in enumerate(raw_specs)]

    route_key_files = list(dict.fromkeys(path.strip() for path in (args.api_key_file or []) if path.strip()))
    if not route_key_files:
        route_key_files = [default_api_key_file]

    return [
        normalize_route_spec({"api_key_file": key_file}, args, default_api_key_file, idx)
        for idx, key_file in enumerate(route_key_files)
    ]


def build_remote_proxy_helper(args: argparse.Namespace) -> str:
    return textwrap.dedent(
        f"""\
        #!/usr/bin/env bash
        set -euo pipefail
        CLASH_HOME={json.dumps(str(PurePosixPath(args.proxy_binary).parent))}
        CLASH_BIN={json.dumps(args.proxy_binary)}
        SOURCE_CFG={json.dumps(args.proxy_config)}
        STATE_DIR={json.dumps(args.proxy_state_dir)}
        TMP_CFG="$STATE_DIR/codex_proxy_{int(args.proxy_http_port)}.yaml"
        LOG_PATH="$STATE_DIR/codex_proxy_{int(args.proxy_http_port)}.log"
        PID_PATH="$STATE_DIR/codex_proxy_{int(args.proxy_http_port)}.pid"
        HTTP_PORT={int(args.proxy_http_port)}
        SOCKS_PORT={int(args.proxy_socks_port)}
        CONTROLLER_PORT={int(args.proxy_controller_port)}

        listeners_ready() {{
          command -v ss >/dev/null 2>&1 || return 1
          ss -lnt 2>/dev/null | grep -q ":$HTTP_PORT " || return 1
          ss -lnt 2>/dev/null | grep -q ":$SOCKS_PORT " || return 1
        }}

        current_pid() {{
          if [ -f "$PID_PATH" ]; then
            cat "$PID_PATH"
          fi
        }}

        running_pid() {{
          local pid
          pid="$(current_pid)"
          if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            printf '%s\\n' "$pid"
            return 0
          fi
          return 1
        }}

        emit_json() {{
          local status="$1"
          local pid
          pid="$(current_pid || true)"
          python3 - <<'PY' "$status" "$pid" "$HTTP_PORT" "$SOCKS_PORT" "$CONTROLLER_PORT" "$TMP_CFG" "$LOG_PATH" "$PID_PATH"
        import json, sys
        payload = {{
          "status": sys.argv[1],
          "pid": sys.argv[2],
          "http_proxy": f"http://127.0.0.1:{{sys.argv[3]}}",
          "all_proxy": f"socks5h://127.0.0.1:{{sys.argv[4]}}",
          "controller": f"127.0.0.1:{{sys.argv[5]}}",
          "config_path": sys.argv[6],
          "log_path": sys.argv[7],
          "pid_path": sys.argv[8],
        }}
        print(json.dumps(payload, ensure_ascii=False))
        PY
        }}

        if [ ! -x "$CLASH_BIN" ]; then
          echo "Missing clash binary: $CLASH_BIN" >&2
          exit 1
        fi
        if [ ! -f "$SOURCE_CFG" ]; then
          echo "Missing clash config: $SOURCE_CFG" >&2
          exit 1
        fi

        mkdir -p "$STATE_DIR"

        if running_pid >/dev/null && listeners_ready; then
          emit_json running
          exit 0
        fi

        python3 - <<'PY' "$SOURCE_CFG" "$TMP_CFG" "$HTTP_PORT" "$SOCKS_PORT" "$CONTROLLER_PORT"
        from pathlib import Path
        import sys

        src = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore").splitlines()
        out: list[str] = []
        for line in src:
            if line.startswith("port:"):
                out.append(f"port: {{sys.argv[3]}}")
            elif line.startswith("socks-port:"):
                out.append(f"socks-port: {{sys.argv[4]}}")
            elif line.startswith("external-controller:"):
                out.append(f"external-controller: 127.0.0.1:{{sys.argv[5]}}")
            elif line.startswith("allow-lan:"):
                out.append("allow-lan: false")
            else:
                out.append(line)
        Path(sys.argv[2]).write_text("\\n".join(out) + "\\n", encoding="utf-8")
        PY

        "$CLASH_BIN" -d "$CLASH_HOME" -f "$TMP_CFG" -t >/dev/null

        if running_pid >/dev/null; then
          kill "$(current_pid)" || true
          sleep 1
        fi

        nohup "$CLASH_BIN" -d "$CLASH_HOME" -f "$TMP_CFG" > "$LOG_PATH" 2>&1 &
        echo $! > "$PID_PATH"
        sleep 4

        if ! listeners_ready; then
          tail -n 120 "$LOG_PATH" >&2 || true
          exit 1
        fi

        emit_json started
        """
    )


def ensure_remote_codex_proxy(args: argparse.Namespace) -> dict[str, object]:
    helper_parent = str(PurePosixPath(args.proxy_helper_path).parent)
    ssh(args.host, f"mkdir -p {shlex.quote(helper_parent)} {shlex.quote(args.proxy_state_dir)}")
    write_remote_text(args.host, args.proxy_helper_path, build_remote_proxy_helper(args))
    ssh(args.host, f"chmod +x {shlex.quote(args.proxy_helper_path)}")
    proc = ssh(args.host, f"bash {shlex.quote(args.proxy_helper_path)}")
    for line in reversed(proc.stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise RuntimeError(f"Proxy bootstrap returned no JSON payload. stdout={proc.stdout!r}")


def build_prompt(args: argparse.Namespace) -> str:
    parts: list[str] = []
    for path in args.prepend_file or []:
        parts.append(Path(path).read_text(encoding="utf-8"))
    if args.prompt_file is not None:
        parts.append(args.prompt_file.read_text(encoding="utf-8"))
    if args.prompt_text:
        parts.append(args.prompt_text)
    prompt = "\n\n".join(part.strip() for part in parts if part.strip()).strip()
    if not prompt:
        raise ValueError("No prompt content provided.")
    return prompt + "\n"


def install(args: argparse.Namespace) -> int:
    local_binary = choose_local_linux_binary(args.local_linux_binary)
    ssh(args.host, f"mkdir -p {shlex.quote(str(PurePosixPath(args.remote_binary_store).parent))}")
    scp_legacy(local_binary, args.host, args.remote_binary_store)
    ssh(args.host, f"chmod 0644 {shlex.quote(args.remote_binary_store)}")
    payload = {
        "host": args.host,
        "local_binary": str(local_binary),
        "remote_binary_store": args.remote_binary_store,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def ensure_proxy(args: argparse.Namespace) -> int:
    if not should_ensure_dev02_proxy(args):
        payload = {
            "status": "skipped",
            "host": args.host,
            "reason": "Proxy bootstrap is only enabled by default for dev-intern-02. Use --ensure-dev02-proxy to force it.",
        }
    else:
        payload = ensure_remote_codex_proxy(args)
        payload["host"] = args.host
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def launch_v2(args: argparse.Namespace) -> int:
    if not args.skip_install:
        install(args)

    proxy_payload: dict[str, object] | None = None
    if should_ensure_dev02_proxy(args):
        proxy_payload = ensure_remote_codex_proxy(args)

    prompt = build_prompt(args)
    agent_root = f"{args.remote_run_root}/{args.run_id}/{args.agent_name}"
    ssh(args.host, f"mkdir -p {shlex.quote(agent_root)}")

    prompt_path = f"{agent_root}/prompt.md"
    wrapper_path = f"{agent_root}/run_agent.sh"
    pid_path = f"{agent_root}/pid"
    status_path = f"{agent_root}/status.json"
    launch_json = f"{agent_root}/launch.json"
    stdout_log = f"{agent_root}/stdout.log"
    last_message = f"{agent_root}/last_message.txt"
    codex_home = str(PurePosixPath(args.remote_home) / ".codex")

    ssh(args.host, f"mkdir -p {shlex.quote(args.remote_home)} {shlex.quote(codex_home)}")
    write_remote_text(args.host, prompt_path, prompt)

    exec_flags: list[str] = [
        "--skip-git-repo-check",
        "--color",
        "never",
        "--json",
        "--output-last-message",
        last_message,
        "-s",
        effective_sandbox(args),
        "-C",
        args.cwd,
        "-",
    ]
    prefix_flags: list[str] = []
    if args.approval:
        prefix_flags.extend(["-a", args.approval])
    if args.search:
        prefix_flags.append("--search")
    env_setup_lines: list[str] = []
    for item in args.unset_env or []:
        env_setup_lines.append(f"unset {shlex.quote(item)} || true")
    if proxy_payload is not None:
        for key, value in build_dev02_proxy_env(args).items():
            env_setup_lines.append(f"export {key}={shlex.quote(value)}")
    for item in args.env or []:
        if "=" not in item:
            raise ValueError(f"Invalid --env value: {item}")
        key, value = item.split("=", 1)
        env_setup_lines.append(f"export {key}={shlex.quote(value)}")
    for add_dir in args.add_dir or []:
        exec_flags = ["--add-dir", add_dir, *exec_flags]
    env_setup = "\n".join(env_setup_lines)

    api_key_file = str(PurePosixPath(codex_home) / "aris_primary_api_key.txt")
    route_specs = collect_route_specs(args, api_key_file)
    routes_json = json.dumps(route_specs, ensure_ascii=False)
    exec_flags_json = json.dumps(exec_flags, ensure_ascii=False)
    prefix_flags_json = json.dumps(prefix_flags, ensure_ascii=False)

    launch_payload = {
        "host": args.host,
        "run_id": args.run_id,
        "agent_name": args.agent_name,
        "cwd": args.cwd,
        "sandbox_requested": args.sandbox,
        "sandbox_effective": effective_sandbox(args),
        "remote_home": args.remote_home,
        "remote_binary_store": args.remote_binary_store,
        "remote_run_root": args.remote_run_root,
        "prompt_path": prompt_path,
        "stdout_log": stdout_log,
        "last_message": last_message,
        "status_path": status_path,
        "route_specs": route_specs,
    }
    write_remote_text(args.host, launch_json, json.dumps(launch_payload, ensure_ascii=False, indent=2) + "\n")

    wrapper = f"""#!/usr/bin/env bash
set -euo pipefail
BIN_STORE={shlex.quote(args.remote_binary_store)}
TMP_BIN="/tmp/codex_{args.agent_name}_$$"
PROMPT_PATH={shlex.quote(prompt_path)}
STDOUT_LOG={shlex.quote(stdout_log)}
STATUS_PATH={shlex.quote(status_path)}
CODEX_HOME_PATH={shlex.quote(codex_home)}
REMOTE_HOME_PATH={shlex.quote(args.remote_home)}
ROUTES_JSON={shlex.quote(routes_json)}
EXEC_FLAGS_JSON={shlex.quote(exec_flags_json)}
PREFIX_FLAGS_JSON={shlex.quote(prefix_flags_json)}
START_TS="$(date -Is)"
python3 - <<'PY' "$STATUS_PATH" "$ROUTES_JSON"
import json
import pathlib
import sys

payload = {{
  "state": "starting",
  "started_at": "{args.run_id}",
  "agent_name": {json.dumps(args.agent_name)},
  "cwd": {json.dumps(args.cwd)},
  "sandbox_requested": {json.dumps(args.sandbox)},
  "sandbox_effective": {json.dumps(effective_sandbox(args))},
  "route_specs": json.loads(sys.argv[2]),
}}
pathlib.Path(sys.argv[1]).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
PY
cp "$BIN_STORE" "$TMP_BIN"
chmod +x "$TMP_BIN"
{env_setup}
set +e
python3 - <<'PY' "$TMP_BIN" "$PROMPT_PATH" "$STDOUT_LOG" "$STATUS_PATH" "$CODEX_HOME_PATH" "$REMOTE_HOME_PATH" "$ROUTES_JSON" "$EXEC_FLAGS_JSON" "$PREFIX_FLAGS_JSON" "$START_TS"
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys
import time


def build_provider_flags(route):
    provider_name = str(route.get("provider_name") or "").strip()
    provider_base_url = str(route.get("provider_base_url") or "").strip()
    if not provider_name or not provider_base_url:
        return []

    display_name = str(route.get("provider_display_name") or provider_name).strip()
    wire_api = str(route.get("provider_wire_api") or "responses").strip()
    env_key = str(route.get("provider_env_key") or "OPENAI_API_KEY").strip()
    requires_openai_auth = "true" if bool(route.get("provider_requires_openai_auth")) else "false"
    return [
        "-c",
        "model_provider=" + json.dumps(provider_name),
        "-c",
        "model_providers." + provider_name + ".name=" + json.dumps(display_name),
        "-c",
        "model_providers." + provider_name + ".base_url=" + json.dumps(provider_base_url),
        "-c",
        "model_providers." + provider_name + ".wire_api=" + json.dumps(wire_api),
        "-c",
        "model_providers." + provider_name + ".env_key=" + json.dumps(env_key),
        "-c",
        "model_providers." + provider_name + ".requires_openai_auth=" + requires_openai_auth,
    ]


def should_rotate_route(log_path):
    if not log_path.exists():
        return False
    tail = log_path.read_text(encoding="utf-8", errors="ignore")[-30000:]
    pattern = (
        r"unexpected status 401|unexpected status 402|unexpected status 403|unexpected status 429|"
        r"missing bearer|invalid api key|insufficient[_ -]?quota|quota|rate limit|authentication|"
        r"payment_required|missing environment variable:.*openai_api_key|未提供令牌"
    )
    return re.search(pattern, tail, flags=re.IGNORECASE) is not None


tmp_bin, prompt_path, stdout_log, status_path, codex_home_path, remote_home_path, routes_json, exec_flags_json, prefix_flags_json, start_ts = sys.argv[1:]
routes = json.loads(routes_json)
exec_flags = json.loads(exec_flags_json)
prefix_flags = json.loads(prefix_flags_json)
stdout_path = pathlib.Path(stdout_log)
status_path_obj = pathlib.Path(status_path)
prompt_path_obj = pathlib.Path(prompt_path)
return_code = 1
route_attempts = 0
route_index_final = 0
route_key_file_final = ""
route_name_final = ""
provider_name_final = ""

for route_index, route in enumerate(routes):
    route_attempts += 1
    route_name = str(route.get("route_name") or ("route_%d" % (route_index + 1)))
    provider_name = str(route.get("provider_name") or "").strip()
    route_key_file = str(route.get("api_key_file") or "").strip()
    route_env_key = str(route.get("provider_env_key") or "OPENAI_API_KEY").strip()
    route_model = str(route.get("model") or "").strip()
    route_cmd = [tmp_bin] + prefix_flags + build_provider_flags(route)
    if route_model:
        route_cmd.extend(["--model", route_model])
    route_cmd.append("exec")
    route_cmd.extend(exec_flags)

    env = os.environ.copy()
    if route_key_file and pathlib.Path(route_key_file).is_file():
        key_value = pathlib.Path(route_key_file).read_text(encoding="utf-8", errors="ignore").strip()
        if key_value:
            env[route_env_key] = key_value
            env["OPENAI_API_KEY"] = key_value
    else:
        env.pop(route_env_key, None)
    env["HOME"] = remote_home_path
    env["CODEX_HOME"] = codex_home_path

    with prompt_path_obj.open("r", encoding="utf-8", errors="ignore") as fin, stdout_path.open("a", encoding="utf-8", errors="ignore") as fout:
        fout.write(
            "===== %s route_attempt=%s route_index=%s route_name=%s provider_name=%s key_file=%s model=%s =====\\n"
            % (
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
                route_attempts,
                route_index,
                route_name,
                provider_name,
                route_key_file,
                route_model,
            )
        )
        fout.flush()
        proc = subprocess.run(route_cmd, stdin=fin, stdout=fout, stderr=subprocess.STDOUT, text=True, env=env)
        return_code = proc.returncode
        fout.write(
            "===== %s route_attempt_done rc=%s route_index=%s route_name=%s provider_name=%s key_file=%s =====\\n"
            % (
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
                return_code,
                route_index,
                route_name,
                provider_name,
                route_key_file,
            )
        )
        fout.flush()

    route_index_final = route_index
    route_key_file_final = route_key_file
    route_name_final = route_name
    provider_name_final = provider_name
    if return_code == 0:
        break
    if route_index + 1 >= len(routes):
        break
    if not should_rotate_route(stdout_path):
        break
    time.sleep(5)

payload = json.loads(status_path_obj.read_text(encoding="utf-8")) if status_path_obj.exists() else {{}}
payload["state"] = "finished"
payload["returncode"] = int(return_code)
payload["started_at_real"] = start_ts
payload["finished_at_real"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
payload["route_attempts"] = int(route_attempts)
payload["route_index_final"] = int(route_index_final)
payload["route_key_file_final"] = route_key_file_final
payload["route_name_final"] = route_name_final
payload["provider_name_final"] = provider_name_final
status_path_obj.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
raise SystemExit(return_code)
PY
RC=$?
set -e
rm -f "$TMP_BIN"
exit "$RC"
"""
    write_remote_text(args.host, wrapper_path, wrapper)
    ssh(args.host, f"chmod +x {shlex.quote(wrapper_path)}")
    launch_cmd = f"nohup bash {shlex.quote(wrapper_path)} >/dev/null 2>&1 & echo $! > {shlex.quote(pid_path)} && cat {shlex.quote(pid_path)}"
    proc = ssh(args.host, launch_cmd)
    payload = {
        "host": args.host,
        "run_id": args.run_id,
        "agent_name": args.agent_name,
        "pid": proc.stdout.strip(),
        "agent_root": agent_root,
        "prompt_path": prompt_path,
        "stdout_log": stdout_log,
        "last_message": last_message,
        "status_path": status_path,
        "sandbox_requested": args.sandbox,
        "sandbox_effective": effective_sandbox(args),
        "route_specs": route_specs,
    }
    if proxy_payload is not None:
        payload["proxy"] = proxy_payload
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def launch(args: argparse.Namespace) -> int:
    return launch_v2(args)

    if not args.skip_install:
        install(args)

    proxy_payload: dict[str, object] | None = None
    if should_ensure_dev02_proxy(args):
        proxy_payload = ensure_remote_codex_proxy(args)

    prompt = build_prompt(args)
    agent_root = f"{args.remote_run_root}/{args.run_id}/{args.agent_name}"
    ssh(args.host, f"mkdir -p {shlex.quote(agent_root)}")

    prompt_path = f"{agent_root}/prompt.md"
    wrapper_path = f"{agent_root}/run_agent.sh"
    pid_path = f"{agent_root}/pid"
    status_path = f"{agent_root}/status.json"
    launch_json = f"{agent_root}/launch.json"
    stdout_log = f"{agent_root}/stdout.log"
    last_message = f"{agent_root}/last_message.txt"
    codex_home = str(PurePosixPath(args.remote_home) / ".codex")

    ssh(args.host, f"mkdir -p {shlex.quote(args.remote_home)} {shlex.quote(codex_home)}")

    write_remote_text(args.host, prompt_path, prompt)
    launch_payload = {
        "host": args.host,
        "run_id": args.run_id,
        "agent_name": args.agent_name,
        "cwd": args.cwd,
        "sandbox_requested": args.sandbox,
        "sandbox_effective": effective_sandbox(args),
        "remote_home": args.remote_home,
        "remote_binary_store": args.remote_binary_store,
        "remote_run_root": args.remote_run_root,
        "prompt_path": prompt_path,
        "stdout_log": stdout_log,
        "last_message": last_message,
        "status_path": status_path,
        "provider_name": args.provider_name,
        "provider_base_url": args.provider_base_url,
    }
    write_remote_text(args.host, launch_json, json.dumps(launch_payload, ensure_ascii=False, indent=2) + "\n")

    exec_flags: list[str] = [
        "--skip-git-repo-check",
        "--color",
        "never",
        "--json",
        "--output-last-message",
        last_message,
        "-s",
        effective_sandbox(args),
        "-C",
        args.cwd,
        "-",
    ]
    provider_override_flags = build_provider_override_flags(args)
    if args.model:
        exec_flags = ["--model", args.model, *exec_flags]
    prefix_flags: list[str] = []
    if args.approval:
        prefix_flags.extend(["-a", args.approval])
    if args.search:
        prefix_flags.append("--search")
    env_setup_lines: list[str] = []
    for item in args.unset_env or []:
        env_setup_lines.append(f"unset {shlex.quote(item)} || true")
    if proxy_payload is not None:
        for key, value in build_dev02_proxy_env(args).items():
            env_setup_lines.append(f"export {key}={shlex.quote(value)}")
    for item in args.env or []:
        if "=" not in item:
            raise ValueError(f"Invalid --env value: {item}")
        key, value = item.split("=", 1)
        env_setup_lines.append(f"export {key}={shlex.quote(value)}")
    for add_dir in args.add_dir or []:
        exec_flags = ["--add-dir", add_dir, *exec_flags]
    exec_args = " ".join(shlex.quote(flag) for flag in exec_flags)
    prefix_args = " ".join(shlex.quote(flag) for flag in prefix_flags)
    provider_args = " ".join(shlex.quote(flag) for flag in provider_override_flags)
    env_setup = "\n".join(env_setup_lines)

    api_key_file = str(PurePosixPath(codex_home) / "aris_primary_api_key.txt")
    route_key_files = list(dict.fromkeys(path.strip() for path in (args.api_key_file or []) if path.strip()))
    if not route_key_files:
        route_key_files = [api_key_file]
    route_key_files_shell = "\n".join(f"  {shlex.quote(path)}" for path in route_key_files)

    wrapper = f"""#!/usr/bin/env bash
set -euo pipefail
AGENT_ROOT={shlex.quote(agent_root)}
BIN_STORE={shlex.quote(args.remote_binary_store)}
TMP_BIN="/tmp/codex_{args.agent_name}_$$"
PROMPT_PATH={shlex.quote(prompt_path)}
STDOUT_LOG={shlex.quote(stdout_log)}
STATUS_PATH={shlex.quote(status_path)}
LAST_MESSAGE={shlex.quote(last_message)}
CODEX_HOME_PATH={shlex.quote(codex_home)}
API_KEY_FILE={shlex.quote(api_key_file)}
API_KEY_FILES=(
{route_key_files_shell}
)
START_TS="$(date -Is)"
python3 - <<'PY' > "$STATUS_PATH"
import json
print(json.dumps({{
  "state": "starting",
  "started_at": "{args.run_id}",
  "agent_name": {json.dumps(args.agent_name)},
  "cwd": {json.dumps(args.cwd)},
  "sandbox_requested": {json.dumps(args.sandbox)},
  "sandbox_effective": {json.dumps(effective_sandbox(args))},
  "provider_name": {json.dumps(args.provider_name)},
  "provider_base_url": {json.dumps(args.provider_base_url)},
  "route_api_key_files": {json.dumps(route_key_files)}
}}, ensure_ascii=False, indent=2))
PY
cp "$BIN_STORE" "$TMP_BIN"
chmod +x "$TMP_BIN"
{env_setup}
route_key_count="${{#API_KEY_FILES[@]}}"
route_index=0
route_attempts=0
route_key_file=""
should_rotate_route() {{
  grep -Eqi 'unexpected status 401|unexpected status 403|unexpected status 429|missing bearer|invalid api key|insufficient[_ -]?quota|quota|rate limit|authentication|missing environment variable:.*openai_api_key|未提供令牌' "$STDOUT_LOG"
}}
while true; do
  route_attempts=$((route_attempts + 1))
  if [ "$route_key_count" -gt 0 ]; then
    route_key_file="${{API_KEY_FILES[$route_index]}}"
  else
    route_key_file="$API_KEY_FILE"
  fi
  if [ -f "$route_key_file" ]; then
    export OPENAI_API_KEY="$(tr -d '\\r\\n' < "$route_key_file")"
  elif [ -z "${{OPENAI_API_KEY:-}}" ] && [ -f "$API_KEY_FILE" ]; then
    route_key_file="$API_KEY_FILE"
    export OPENAI_API_KEY="$(tr -d '\\r\\n' < "$API_KEY_FILE")"
  else
    unset OPENAI_API_KEY || true
  fi
  printf '===== %s route_attempt=%s route_index=%s key_file=%s =====\\n' "$(date -Is)" "$route_attempts" "$route_index" "$route_key_file" >> "$STDOUT_LOG"
  set +e
  HOME={shlex.quote(args.remote_home)} CODEX_HOME="$CODEX_HOME_PATH" "$TMP_BIN" {provider_args} {prefix_args} exec {exec_args} < "$PROMPT_PATH" >> "$STDOUT_LOG" 2>&1
  RC=$?
  set -e
  printf '===== %s route_attempt_done rc=%s route_index=%s key_file=%s =====\\n' "$(date -Is)" "$RC" "$route_index" "$route_key_file" >> "$STDOUT_LOG"
  if [ "$RC" -eq 0 ]; then
    break
  fi
  if [ "$route_key_count" -le 1 ]; then
    break
  fi
  if ! should_rotate_route; then
    break
  fi
  if [ "$route_attempts" -ge "$route_key_count" ]; then
    break
  fi
  route_index=$((route_index + 1))
  sleep 5
done
END_TS="$(date -Is)"
python3 - <<'PY' "$STATUS_PATH" "$RC" "$START_TS" "$END_TS" "$route_attempts" "$route_index" "$route_key_file"
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {{}}
payload["state"] = "finished"
payload["returncode"] = int(sys.argv[2])
payload["started_at_real"] = sys.argv[3]
payload["finished_at_real"] = sys.argv[4]
payload["route_attempts"] = int(sys.argv[5])
payload["route_index_final"] = int(sys.argv[6])
payload["route_key_file_final"] = sys.argv[7]
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
PY
rm -f "$TMP_BIN"
exit "$RC"
"""
    write_remote_text(args.host, wrapper_path, wrapper)
    ssh(args.host, f"chmod +x {shlex.quote(wrapper_path)}")
    launch_cmd = f"nohup bash {shlex.quote(wrapper_path)} >/dev/null 2>&1 & echo $! > {shlex.quote(pid_path)} && cat {shlex.quote(pid_path)}"
    proc = ssh(args.host, launch_cmd)
    payload = {
        "host": args.host,
        "run_id": args.run_id,
        "agent_name": args.agent_name,
        "pid": proc.stdout.strip(),
        "agent_root": agent_root,
        "prompt_path": prompt_path,
        "stdout_log": stdout_log,
        "last_message": last_message,
        "status_path": status_path,
        "sandbox_requested": args.sandbox,
        "sandbox_effective": effective_sandbox(args),
        "provider_name": args.provider_name,
        "provider_base_url": args.provider_base_url,
        "route_api_key_files": route_key_files,
    }
    if proxy_payload is not None:
        payload["proxy"] = proxy_payload
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def status(args: argparse.Namespace) -> int:
    target = f"{args.remote_run_root}/{args.run_id}"
    list_proc = ssh(args.host, f"find {shlex.quote(target)} -mindepth 1 -maxdepth 1 -type d -printf '%f\\n'", check=False)
    if list_proc.returncode != 0:
        if list_proc.stderr:
            sys.stderr.write(list_proc.stderr)
        return int(list_proc.returncode)
    agent_names = [line.strip() for line in list_proc.stdout.splitlines() if line.strip()]
    for agent_name in agent_names:
        agent_root = f"{target}/{agent_name}"
        status_proc = ssh(args.host, f"cat {shlex.quote(agent_root + '/status.json')}", check=False)
        payload: dict[str, object] = {}
        if status_proc.returncode == 0 and status_proc.stdout.strip():
            payload.update(json.loads(status_proc.stdout))
        pid_proc = ssh(args.host, f"cat {shlex.quote(agent_root + '/pid')}", check=False)
        pid = pid_proc.stdout.strip() if pid_proc.returncode == 0 else ""
        running = False
        if pid:
            running_proc = ssh(args.host, f"ps -p {pid} >/dev/null 2>&1", check=False)
            running = running_proc.returncode == 0
        payload.update(
            {
                "agent_name": agent_name,
                "pid": pid,
                "running": running,
                "agent_root": agent_root,
                "stdout_log": f"{agent_root}/stdout.log",
                "last_message": f"{agent_root}/last_message.txt",
            }
        )
        print(json.dumps(payload, ensure_ascii=False))
    return 0


def tail(args: argparse.Namespace) -> int:
    log_path = f"{args.remote_run_root}/{args.run_id}/{args.agent_name}/stdout.log"
    proc = ssh(args.host, f"tail -n {int(args.lines)} {shlex.quote(log_path)}", check=False)
    write_stream_text(sys.stdout, proc.stdout)
    if proc.stderr:
        write_stream_text(sys.stderr, proc.stderr)
    return int(proc.returncode)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Launch and monitor remote Codex subagents over SSH.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--host", default="dev-intern-02")
    common.add_argument("--remote-home", default=DEFAULT_REMOTE_HOME)
    common.add_argument("--remote-binary-store", default=DEFAULT_REMOTE_BINARY_STORE)
    common.add_argument("--remote-run-root", default=DEFAULT_REMOTE_RUN_ROOT)
    common.add_argument("--local-linux-binary", type=Path, default=None)
    common.add_argument("--env", action="append", default=[])
    common.add_argument("--unset-env", action="append", default=[])
    common.add_argument("--proxy-helper-path", default=DEFAULT_DEV02_PROXY_HELPER)
    common.add_argument("--proxy-binary", default=DEFAULT_DEV02_PROXY_BINARY)
    common.add_argument("--proxy-config", default=DEFAULT_DEV02_PROXY_CONFIG)
    common.add_argument("--proxy-state-dir", default=DEFAULT_DEV02_PROXY_STATE_DIR)
    common.add_argument("--proxy-http-port", type=int, default=DEFAULT_DEV02_PROXY_HTTP_PORT)
    common.add_argument("--proxy-socks-port", type=int, default=DEFAULT_DEV02_PROXY_SOCKS_PORT)
    common.add_argument("--proxy-controller-port", type=int, default=DEFAULT_DEV02_PROXY_CONTROLLER_PORT)
    common.add_argument("--ensure-dev02-proxy", dest="ensure_dev02_proxy", action="store_true", default=None)
    common.add_argument("--no-ensure-dev02-proxy", dest="ensure_dev02_proxy", action="store_false")
    common.add_argument("--no-auto-dev02-sandbox-fix", action="store_true")
    common.add_argument("--provider-name", default="")
    common.add_argument("--provider-display-name", default="")
    common.add_argument("--provider-base-url", default="")
    common.add_argument("--provider-wire-api", default="responses")
    common.add_argument("--provider-env-key", default="OPENAI_API_KEY")
    common.add_argument("--provider-requires-openai-auth", action="store_true")
    common.add_argument("--api-key-file", action="append", default=[])
    common.add_argument("--route-spec", action="append", default=[])
    common.add_argument("--route-spec-file", type=Path, action="append", default=[])

    p_install = sub.add_parser("install", parents=[common])
    p_install.set_defaults(func=install)

    p_proxy = sub.add_parser("ensure-proxy", parents=[common])
    p_proxy.set_defaults(func=ensure_proxy)

    p_launch = sub.add_parser("launch", parents=[common])
    p_launch.add_argument("--run-id", required=True)
    p_launch.add_argument("--agent-name", required=True)
    p_launch.add_argument("--cwd", required=True)
    p_launch.add_argument("--prompt-file", type=Path, default=None)
    p_launch.add_argument("--prepend-file", type=Path, action="append", default=[])
    p_launch.add_argument("--prompt-text", default="")
    p_launch.add_argument("--add-dir", action="append", default=[])
    p_launch.add_argument("--model", default="")
    p_launch.add_argument("--sandbox", default="workspace-write")
    p_launch.add_argument("--approval", default="never")
    p_launch.add_argument("--search", action="store_true")
    p_launch.add_argument("--skip-install", action="store_true")
    p_launch.set_defaults(func=launch)

    p_status = sub.add_parser("status", parents=[common])
    p_status.add_argument("--run-id", required=True)
    p_status.set_defaults(func=status)

    p_tail = sub.add_parser("tail", parents=[common])
    p_tail.add_argument("--run-id", required=True)
    p_tail.add_argument("--agent-name", required=True)
    p_tail.add_argument("--lines", type=int, default=80)
    p_tail.set_defaults(func=tail)

    return ap


def main() -> int:
    ap = build_parser()
    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
