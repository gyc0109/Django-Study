#!/usr/bin/env bash
# ============================================================================
# dev.sh —— Django-Study 一键启停脚本
# ============================================================================
# 管了什么：
#   2 个 Docker 容器  MySQL(3307) / Redis(6380)
#   6 个本地进程      project1 的 Django(8000) + Celery + Vite(5173)
#                     practice 的 Django(8001) + Celery + Vite(5174)
#
# 用法：
#   ./dev.sh start      启动全部（容器 → 后端 → Celery → 前端）
#   ./dev.sh stop       停止全部（前端 → Celery → 后端 → 容器）
#   ./dev.sh restart    先 stop 再 start
#   ./dev.sh status     查看每个服务的状态 + 健康检查
#   ./dev.sh logs NAME  实时跟踪某个服务的日志，NAME 见 ./dev.sh status
#
# 文件：
#   .run/<服务名>.pid   进程号
#   logs/<服务名>.log   标准输出 + 错误输出
#
# 说明：
#   - 本脚本不修改 Docker 容器的 restart policy，容器仍是 --restart=no，
#     机器重启后不会自己起来，需要你手动执行 ./dev.sh start。
#   - 停止时先发 TERM（让 Django/Celery 优雅退出），15 秒内没退再 KILL。
#   - 只会杀自己 pid 文件里记录的进程，并且在杀之前校验命令行，
#     避免 pid 被系统复用后误杀别的程序。
# ============================================================================

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$RUN_DIR" "$LOG_DIR"

MYSQL_CONTAINER="django-study-mysql"
REDIS_CONTAINER="django-study-redis"
MYSQL_PORT=3307
REDIS_PORT=6380

# ---------------------------------------------------------------------------
# 服务清单（顺序 = 启动顺序）
# ---------------------------------------------------------------------------
SERVICES=(backend celery frontend practice-backend practice-celery practice-frontend)

declare -A SVC_DIR SVC_PORT SVC_CMD SVC_MARK SVC_DESC

SVC_DIR[backend]="$ROOT_DIR/backend"
SVC_PORT[backend]=8000
SVC_CMD[backend]="$ROOT_DIR/backend/.venv/bin/python manage.py runserver 127.0.0.1:8000"
SVC_MARK[backend]="manage.py runserver"
SVC_DESC[backend]="project1 后端 Django"

SVC_DIR[celery]="$ROOT_DIR/backend"
SVC_PORT[celery]=""
SVC_CMD[celery]="$ROOT_DIR/backend/.venv/bin/celery -A config worker -l info"
SVC_MARK[celery]="celery -A config worker"
SVC_DESC[celery]="project1 Celery worker（实例名 django_study）"

SVC_DIR[frontend]="$ROOT_DIR/frontend"
SVC_PORT[frontend]=5173
SVC_CMD[frontend]="npm run dev -- --strictPort"
SVC_MARK[frontend]="run dev"
SVC_DESC[frontend]="project1 前端 Vite"

SVC_DIR[practice-backend]="$ROOT_DIR/practice/backend"
SVC_PORT[practice-backend]=8001
SVC_CMD[practice-backend]="$ROOT_DIR/practice/backend/.venv/bin/python manage.py runserver 127.0.0.1:8001"
SVC_MARK[practice-backend]="manage.py runserver"
SVC_DESC[practice-backend]="practice 后端 Django"

SVC_DIR[practice-celery]="$ROOT_DIR/practice/backend"
SVC_PORT[practice-celery]=""
SVC_CMD[practice-celery]="$ROOT_DIR/practice/backend/.venv/bin/celery -A config worker -l info"
SVC_MARK[practice-celery]="celery -A config worker"
SVC_DESC[practice-celery]="practice Celery worker（实例名 library_practice）"

SVC_DIR[practice-frontend]="$ROOT_DIR/practice/frontend"
SVC_PORT[practice-frontend]=5174
SVC_CMD[practice-frontend]="npm run dev -- --strictPort"
SVC_MARK[practice-frontend]="run dev"
SVC_DESC[practice-frontend]="practice 前端 Vite"

# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------
say()  { printf '%s\n' "$*"; }
ok()   { printf '  [OK]   %s\n' "$*"; }
warn() { printf '  [警告] %s\n' "$*"; }
fail() { printf '  [失败] %s\n' "$*"; }

# 端口是否已被监听
port_busy() {
    local port="$1"
    [[ -n "$port" ]] || return 1
    ss -ltnH "sport = :$port" 2>/dev/null | grep -q .
}

# 等端口出现，默认最多等 30 秒
wait_port() {
    local port="$1" timeout="${2:-30}" i=0
    while (( i < timeout )); do
        port_busy "$port" && return 0
        sleep 1
        (( i++ ))
    done
    return 1
}

svc_pid_file() { printf '%s/%s.pid' "$RUN_DIR" "$1"; }
svc_log_file() { printf '%s/%s.log' "$LOG_DIR" "$1"; }

# pid 还活着，且 pid 文件存在
service_running() {
    local name="$1" pidfile
    pidfile="$(svc_pid_file "$name")"
    [[ -f "$pidfile" ]] || return 1
    local pid
    pid="$(cat "$pidfile" 2>/dev/null)"
    [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

# 校验 pid 对应的命令行确实是这个服务（防 pid 复用误杀）
pid_matches() {
    local name="$1" pid="$2"
    [[ -r "/proc/$pid/cmdline" ]] || return 1
    tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null | grep -q -- "${SVC_MARK[$name]}"
}

# 递归杀进程树：npm → sh → node，Django 自动重载 → 子进程
kill_tree() {
    local pid="$1" sig="${2:-TERM}" child
    for child in $(pgrep -P "$pid" 2>/dev/null); do
        kill_tree "$child" "$sig"
    done
    kill -"$sig" "$pid" 2>/dev/null || true
}

# 启动前置检查：可执行文件/依赖在不在
check_prereqs() {
    local missing=0
    if ! command -v docker >/dev/null 2>&1; then
        fail "找不到 docker 命令"; missing=1
    fi
    if ! command -v npm >/dev/null 2>&1; then
        fail "找不到 npm 命令（需要 Node.js）"; missing=1
    fi
    if [[ ! -x "$ROOT_DIR/backend/.venv/bin/python" ]]; then
        fail "缺少 backend/.venv（先按文档创建虚拟环境并安装依赖）"; missing=1
    fi
    if [[ ! -x "$ROOT_DIR/practice/backend/.venv/bin/python" ]]; then
        fail "缺少 practice/backend/.venv"; missing=1
    fi
    if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
        fail "缺少 frontend/node_modules（先执行 npm install）"; missing=1
    fi
    if [[ ! -d "$ROOT_DIR/practice/frontend/node_modules" ]]; then
        fail "缺少 practice/frontend/node_modules（先执行 npm install）"; missing=1
    fi
    if [[ ! -f "$ROOT_DIR/backend/.env" ]]; then
        warn "backend/.env 不存在，将使用 settings.py 里的默认值"
    fi
    if [[ ! -f "$ROOT_DIR/practice/backend/.env" ]]; then
        warn "practice/backend/.env 不存在，将使用 settings.py 里的默认值"
    fi
    return $missing
}

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------
container_running() {
    [[ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" == "true" ]]
}

start_containers() {
    say "==> 启动容器"
    local name
    for name in "$MYSQL_CONTAINER" "$REDIS_CONTAINER"; do
        if ! docker inspect "$name" >/dev/null 2>&1; then
            fail "容器 $name 不存在，请先按 docs/启动说明.md 里的 docker run 命令创建"
            return 1
        fi
        if container_running "$name"; then
            ok "$name 已在运行"
        else
            docker start "$name" >/dev/null && ok "$name 已启动" || { fail "$name 启动失败"; return 1; }
        fi
    done

    say "==> 等待 MySQL($MYSQL_PORT) / Redis($REDIS_PORT) 就绪（最多 60 秒）"
    if wait_port "$MYSQL_PORT" 60; then ok "MySQL 端口已就绪"; else fail "MySQL 60 秒内没起来，看：docker logs --tail 50 $MYSQL_CONTAINER"; return 1; fi
    if wait_port "$REDIS_PORT" 20; then ok "Redis 端口已就绪"; else fail "Redis 没起来，看：docker logs --tail 50 $REDIS_CONTAINER"; return 1; fi
    return 0
}

stop_containers() {
    say "==> 停止容器"
    local name
    for name in "$MYSQL_CONTAINER" "$REDIS_CONTAINER"; do
        if ! docker inspect "$name" >/dev/null 2>&1; then
            warn "容器 $name 不存在，跳过"
            continue
        fi
        if container_running "$name"; then
            docker stop "$name" >/dev/null && ok "$name 已停止" || fail "$name 停止失败"
        else
            ok "$name 本来就是停止状态"
        fi
    done
}

# ---------------------------------------------------------------------------
# 本地进程
# ---------------------------------------------------------------------------
start_service() {
    local name="$1"
    local pidfile logfile
    pidfile="$(svc_pid_file "$name")"
    logfile="$(svc_log_file "$name")"

    if service_running "$name"; then
        ok "$name 已在运行（pid $(cat "$pidfile")），跳过"
        return 0
    fi
    rm -f "$pidfile"

    local port="${SVC_PORT[$name]}"
    if [[ -n "$port" ]] && port_busy "$port"; then
        fail "$name 的端口 $port 已被别的程序占用，先排查：ss -ltnp \"sport = :$port\""
        return 1
    fi

    local cmd="${SVC_CMD[$name]}"
    local exe="${cmd%% *}"
    if [[ "$exe" == "npm" ]]; then
        command -v npm >/dev/null 2>&1 || { fail "$name 需要 npm"; return 1; }
    elif [[ ! -x "$exe" ]]; then
        fail "$name 的可执行文件不存在：$exe"
        return 1
    fi

    # 在服务自己的工作目录里启动，输出重定向到日志
    (
        cd "${SVC_DIR[$name]}" || exit 1
        nohup $cmd > "$logfile" 2>&1 &
        echo $! > "$pidfile"
    )

    sleep 1
    if ! service_running "$name"; then
        fail "$name 启动后立刻退出，日志最后几行："
        tail -n 15 "$logfile" 2>/dev/null | sed 's/^/         /'
        rm -f "$pidfile"
        return 1
    fi

    if [[ -n "$port" ]]; then
        if wait_port "$port" 30; then
            ok "$name 已启动（pid $(cat "$pidfile")，端口 $port）"
        else
            fail "$name 进程在，但端口 $port 30 秒内没监听，日志最后几行："
            tail -n 15 "$logfile" 2>/dev/null | sed 's/^/         /'
            return 1
        fi
    else
        ok "$name 已启动（pid $(cat "$pidfile")，日志 logs/$name.log）"
    fi
    return 0
}

stop_service() {
    local name="$1"
    local pidfile pid
    pidfile="$(svc_pid_file "$name")"

    if [[ ! -f "$pidfile" ]]; then
        ok "$name 没有 pid 文件（可能本来就没启动）"
        return 0
    fi

    pid="$(cat "$pidfile" 2>/dev/null)"
    if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
        rm -f "$pidfile"
        ok "$name 已经是停止状态"
        return 0
    fi

    if ! pid_matches "$name" "$pid"; then
        warn "$name 的 pid $pid 命令行不匹配，可能被系统复用，跳过不杀"
        rm -f "$pidfile"
        return 0
    fi

    say "  -> 停止 $name（pid $pid）"
    kill_tree "$pid" TERM

    local i
    for i in {1..15}; do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.4
    done

    if kill -0 "$pid" 2>/dev/null; then
        warn "$name 15 秒内没退出，强制结束"
        kill_tree "$pid" KILL
        sleep 0.3
    fi

    rm -f "$pidfile"
    ok "$name 已停止"
    return 0
}

# ---------------------------------------------------------------------------
# 命令
# ---------------------------------------------------------------------------
cmd_start() {
    say "==> 检查环境"
    if ! check_prereqs; then
        say "环境不完整，先看 docs/启动说明.md 的「首次准备」一节"
        return 1
    fi
    ok "环境检查通过"

    start_containers || return 1

    say "==> 启动本地服务"
    local name failed=0
    for name in "${SERVICES[@]}"; do
        start_service "$name" || failed=1
    done

    say ""
    if (( failed == 0 )); then
        say "全部服务已启动："
    else
        say "有服务启动失败，当前状态如下："
    fi
    cmd_status
    say ""
    say "日志目录：$LOG_DIR"
    say "停止全部：./dev.sh stop"
    return $failed
}

cmd_stop() {
    local i name
    say "==> 停止本地服务"
    for (( i=${#SERVICES[@]}-1; i>=0; i-- )); do
        stop_service "${SERVICES[$i]}"
    done

    stop_containers

    say ""
    say "全部已停止。提醒：容器 restart policy = no，机器重启后不会自动启动。"
    return 0
}

cmd_restart() {
    cmd_stop
    say ""
    cmd_start
}

cmd_status() {
    say ""
    say "Docker 容器"
    local name state
    for name in "$MYSQL_CONTAINER" "$REDIS_CONTAINER"; do
        state="$(docker inspect -f '{{.State.Status}}' "$name" 2>/dev/null || echo "不存在")"
        printf '  %-22s %s\n' "$name" "$state"
    done

    say ""
    say "本地服务"
    printf '  %-20s %-8s %-10s %s\n' "服务名" "端口" "状态" "说明"
    local pidfile pid
    for name in "${SERVICES[@]}"; do
        pidfile="$(svc_pid_file "$name")"
        local st="未运行"
        local port="${SVC_PORT[$name]}"
        port="${port:--}"
        if service_running "$name"; then
            pid="$(cat "$pidfile")"
            if [[ "$port" != "-" ]] && port_busy "$port"; then
                st="运行中 pid=$pid"
            elif [[ "$port" == "-" ]]; then
                st="运行中 pid=$pid"
            else
                st="进程在，端口未监听"
            fi
        fi
        printf '  %-20s %-8s %-10s %s\n' "$name" "$port" "$st" "${SVC_DESC[$name]}"
    done

    say ""
    say "健康检查（MySQL + Redis）"
    local url body code
    for url in "http://127.0.0.1:8000/api/health/" "http://127.0.0.1:8001/api/health/"; do
        body="$(curl -s -m 3 "$url" 2>/dev/null)"
        code=$?
        if [[ $code -eq 0 && -n "$body" ]]; then
            printf '  %-40s %s\n' "$url" "$body"
        else
            printf '  %-40s %s\n' "$url" "无响应"
        fi
    done
}

cmd_logs() {
    local name="${1:-}"
    if [[ -z "$name" ]]; then
        fail "用法：./dev.sh logs <服务名>，可选：${SERVICES[*]}"
        return 1
    fi
    local logfile
    logfile="$(svc_log_file "$name")"
    if [[ ! -f "$logfile" ]]; then
        fail "日志不存在：$logfile"
        return 1
    fi
    tail -n 50 -f "$logfile"
}

usage() {
    cat <<EOF
用法：./dev.sh <命令>

  start          启动全部（容器 → 后端 → Celery → 前端）
  stop           停止全部（前端 → Celery → 后端 → 容器）
  restart        先 stop 再 start
  status         查看服务状态 + 健康检查
  logs <服务名>  实时跟踪日志

服务名：${SERVICES[*]}
EOF
}

case "${1:-}" in
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    restart) cmd_restart ;;
    status)  cmd_status ;;
    logs)    shift; cmd_logs "${1:-}" ;;
    *)       usage; exit 1 ;;
esac
