#!/usr/bin/env bash
# 鱼塘视觉监控系统 · 树莓派端固件 · 一键安装
#
#   bash install.sh                 # 建 venv + 装依赖 + 写 systemd 单元 + 开机自启
#   bash install.sh --offline       # 不联网：不装任何第三方包，只用系统 python3（纯标准库也能跑）
#   bash install.sh --no-systemd    # 只准备环境，不碰 systemd（手工前台跑）
#   bash install.sh --simulate      # systemd 单元里带 --simulate（无相机联调前端）
#   bash install.sh --port 8080 --user pi
#
# 装完：
#   systemctl status yutang-vision
#   curl -s http://127.0.0.1:8080/api/v1/health | python3 -m json.tool
#   python3 tools/selfcheck.py --base-url http://127.0.0.1:8080
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="yutang-vision"
UNIT_SRC="${PROJECT_DIR}/systemd/${SERVICE_NAME}.service"
UNIT_DST="/etc/systemd/system/${SERVICE_NAME}.service"
VENV_DIR="${PROJECT_DIR}/.venv"
RUN_USER="$(id -un)"
PORT="8080"
USE_SYSTEMD=1
OFFLINE=0
SIMULATE=0
START_NOW=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline)     OFFLINE=1; shift ;;
    --no-systemd)  USE_SYSTEMD=0; shift ;;
    --simulate)    SIMULATE=1; shift ;;
    --no-start)    START_NOW=0; shift ;;
    --port)        PORT="${2:?--port 需要端口号}"; shift 2 ;;
    --user)        RUN_USER="${2:?--user 需要用户名}"; shift 2 ;;
    -h|--help)     sed -n '2,20p' "$0"; exit 0 ;;
    *)             echo "未知参数：$1（用 --help 看用法）" >&2; exit 2 ;;
  esac
done

say()  { printf '\033[1;34m[install]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------------------
say "项目目录：${PROJECT_DIR}"
[[ -f "${PROJECT_DIR}/yutang_vision/__main__.py" ]] || die "没找到 yutang_vision/，请在固件根目录执行本脚本"

PYTHON_BIN="$(command -v python3 || true)"
[[ -n "${PYTHON_BIN}" ]] || die "没有 python3，请先 sudo apt install -y python3 python3-venv"
PY_VER="$("${PYTHON_BIN}" -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
say "系统 Python：${PYTHON_BIN}（${PY_VER}）"
"${PYTHON_BIN}" -c 'import sys;raise SystemExit(0 if sys.version_info>=(3,9) else 1)' \
  || die "需要 Python ≥ 3.9（树莓派 OS Bookworm 自带 3.11）"

# ---------------------------------------------------------------------------
# 1) 虚拟环境
if [[ "${OFFLINE}" == "1" ]]; then
  warn "--offline：跳过 venv 与 pip，直接用系统 python3（纯标准库路径，功能有降级）"
  RUN_PYTHON="${PYTHON_BIN}"
else
  if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    say "创建虚拟环境：${VENV_DIR}"
    if ! "${PYTHON_BIN}" -m venv "${VENV_DIR}" 2>/dev/null; then
      warn "python3-venv 不可用，尝试安装"
      sudo apt-get update -qq && sudo apt-get install -y python3-venv || true
      "${PYTHON_BIN}" -m venv "${VENV_DIR}" || die "venv 创建失败（可改用 --offline）"
    fi
  fi
  RUN_PYTHON="${VENV_DIR}/bin/python"
  say "升级 pip / setuptools"
  "${RUN_PYTHON}" -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || warn "pip 升级失败（离线？继续）"

  # 逐包安装：某个包装不上（比如 arm64 没有 wheel）不能拖垮整件事
  say "安装依赖（缺哪个就降级哪个，不阻塞启动）"
  while read -r pkg; do
    [[ -z "${pkg}" || "${pkg}" == \#* ]] && continue
    if "${RUN_PYTHON}" -m pip install --no-input "${pkg}" >/tmp/yutang-pip.log 2>&1; then
      printf '  \033[1;32m✓\033[0m %s\n' "${pkg}"
    else
      printf '  \033[1;33m✗\033[0m %s（装不上，运行时会自动降级；日志 /tmp/yutang-pip.log）\n' "${pkg}"
    fi
  done < <(grep -vE '^\s*(#|$)' "${PROJECT_DIR}/requirements.txt")
fi

# ---------------------------------------------------------------------------
# 2) 配置文件
if [[ ! -f "${PROJECT_DIR}/config.yaml" ]]; then
  cp "${PROJECT_DIR}/config.example.yaml" "${PROJECT_DIR}/config.yaml"
  say "已生成 config.yaml（记得改相机 IP 与 rtsp_password 占位 CHANGE_ME）"
else
  say "config.yaml 已存在，保留不动"
fi

# ffmpeg：拉流与录像靠它，没有就只能用 OpenCV 兜底
if ! command -v ffmpeg >/dev/null 2>&1; then
  warn "没有 ffmpeg：将用 OpenCV 兜底拉流（更吃 CPU），本地录像不可用。建议：sudo apt install -y ffmpeg"
fi

# ---------------------------------------------------------------------------
# 3) systemd 单元
if [[ "${USE_SYSTEMD}" == "1" ]]; then
  if [[ ! -d /run/systemd/system ]]; then
    warn "本机没有 systemd（容器/开发机？），跳过服务安装；可直接跑："
    warn "  ${RUN_PYTHON} -m yutang_vision --config ${PROJECT_DIR}/config.yaml"
  else
    SIM_FLAG=""
    [[ "${SIMULATE}" == "1" ]] && SIM_FLAG=" --simulate"
    TMP_UNIT="$(mktemp)"
    sed -e "s|__PROJECT_DIR__|${PROJECT_DIR}|g" \
        -e "s|__USER__|${RUN_USER}|g" \
        -e "s|__PYTHON__|${RUN_PYTHON}|g" \
        -e "s|__PORT__|${PORT}|g" \
        "${UNIT_SRC}" > "${TMP_UNIT}"
    if [[ -n "${SIM_FLAG}" ]]; then
      sed -i "s|--port ${PORT}|--port ${PORT}${SIM_FLAG}|" "${TMP_UNIT}"
    fi
    say "安装 systemd 单元：${UNIT_DST}（User=${RUN_USER}, Python=${RUN_PYTHON}, Port=${PORT}${SIM_FLAG}）"
    sudo install -m 0644 "${TMP_UNIT}" "${UNIT_DST}"
    rm -f "${TMP_UNIT}"
    sudo systemctl daemon-reload
    sudo systemctl enable "${SERVICE_NAME}" >/dev/null
    if [[ "${START_NOW}" == "1" ]]; then
      sudo systemctl restart "${SERVICE_NAME}"
      sleep 2
      if systemctl is-active --quiet "${SERVICE_NAME}"; then
        say "服务已启动：systemctl status ${SERVICE_NAME}"
      else
        warn "服务没起来，看日志：journalctl -u ${SERVICE_NAME} -n 50 --no-pager"
      fi
    fi
  fi
else
  say "跳过 systemd（--no-systemd）。前台启动："
  say "  ${RUN_PYTHON} -m yutang_vision --config ${PROJECT_DIR}/config.yaml"
fi

# ---------------------------------------------------------------------------
# 4) 自检
say "跑一次配置校验"
"${RUN_PYTHON}" -m yutang_vision --config "${PROJECT_DIR}/config.yaml" --check >/dev/null \
  && say "配置 OK" || warn "配置有问题，看上面的输出"

cat <<EOF

============================================================
安装完成。下一步：
  1. 改 config.yaml 里的相机 IP / 口令（占位 CHANGE_ME）
  2. 相机端开启 ONVIF（配置 → 网络 → 高级配置 → 集成协议），否则云台只能走 mock
  3. 健康检查：
       curl -s http://127.0.0.1:${PORT}/api/v1/health | python3 -m json.tool
  4. 一键自检（打全部端点，打印通过/失败表）：
       python3 "${PROJECT_DIR}/tools/selfcheck.py" --base-url http://127.0.0.1:${PORT}
  5. 无相机时联调前端：
       "${RUN_PYTHON}" -m yutang_vision --simulate
  6. 日志：journalctl -u ${SERVICE_NAME} -f
============================================================
EOF
