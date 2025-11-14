import httpx
import re
import math
from typing import List, Dict, Optional, Any
from bot_body import consts

_session_id: Optional[str] = None

# Регулярное выражение для валидации магнет-ссылки
# Обязательно: magnet:?xt=urn:btih:<40-HEX или 32-BASE32>
_MAGNET_REGEX = re.compile(
    r"^magnet:\?[^#]*xt=urn:btih:([a-fA-F0-9]{40}|[A-Z2-7]{32})(?:&[^#]*)?(?:#.*)?$"
)


def validate_magnet_uri(magnet_uri: str) -> None:
    """
    Валидирует магнет-ссылку.
  
    """
    if not isinstance(magnet_uri, str):
        raise ValueError("Magnet URI must be a string")

    magnet_uri = magnet_uri.strip()
    if not magnet_uri:
        raise ValueError("Magnet URI is empty")

    if not magnet_uri.startswith("magnet:?"):
        raise ValueError("Magnet URI must start with 'magnet:?'")

    if not _MAGNET_REGEX.match(magnet_uri):
        raise ValueError(
            "Invalid magnet URI: must contain 'xt=urn:btih:<40-hex or 32-base32-hash>'"
        )


async def _ensure_session_id(client: httpx.AsyncClient) -> str:
    global _session_id
    if _session_id:
        return _session_id

    try:
        response = await client.post(
            consts.TRANSMISSION_URL,
            json={"method": "session-get"},
            timeout=10.0
        )
        if response.status_code == 409:
            _session_id = response.headers.get("X-Transmission-Session-Id", "")
            if not _session_id:
                raise RuntimeError("X-Transmission-Session-Id missing in 409 response")
        elif response.is_success:
            _session_id = response.headers.get("X-Transmission-Session-Id", "")
        else:
            response.raise_for_status()
        return _session_id
    except Exception as e:
        raise RuntimeError(f"Failed to get session ID: {e}")


async def add_torrent_from_magnet(magnet_uri: str) -> dict:
    """
    Добавляет торрент по магнет-ссылке в Transmission.

    """
    # Валидация перед отправкой
    validate_magnet_uri(magnet_uri)

    global _session_id
    auth = (consts.TRANSMISSION_USER, consts.TRANSMISSION_PASSWORD)

    async with httpx.AsyncClient(auth=auth, timeout=30.0) as client:
        session_id = await _ensure_session_id(client)
        headers = {"X-Transmission-Session-Id": session_id}

        payload = {
            "method": "torrent-add",
            "arguments": {"filename": magnet_uri}
        }

        try:
            response = await client.post(
                consts.TRANSMISSION_URL,
                json=payload,
                headers=headers
            )

            if response.status_code == 409:
                _session_id = response.headers.get("X-Transmission-Session-Id", "")
                if _session_id:
                    headers["X-Transmission-Session-Id"] = _session_id
                    response = await client.post(
                        consts.TRANSMISSION_URL,
                        json=payload,
                        headers=headers
                    )

            if not response.is_success:
                raise RuntimeError(
                    f"Transmission RPC error {response.status_code}: {response.text}"
                )

            data = response.json()
            if data.get("result") != "success":
                raise RuntimeError(f"API error: {data.get('result')}")

            return data

        except httpx.RequestError as e:
            raise RuntimeError(f"Network error: {e}")
        except ValueError as e:
            if "Invalid JSON" in str(e):
                raise RuntimeError(f"Invalid JSON response: {e}")
            else:
                raise  # пробрасываем ValueError от validate_magnet_uri

async def get_torrents(
    fields: Optional[List[str]] = None,
    ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Получает список торрентов из Transmission.
    
    Args:
        fields: список полей для возврата (например: ["id", "name", "percentDone", "status"])
    

    """
    global _session_id
    auth = (consts.TRANSMISSION_USER, consts.TRANSMISSION_PASSWORD)

    async with httpx.AsyncClient(auth=auth, timeout=30.0) as client:
        session_id = await _ensure_session_id(client)
        headers = {"X-Transmission-Session-Id": session_id}

        # Формируем аргументы
        args: Dict[str, Any] = {}
        if fields:
            args["fields"] = fields
        if ids is not None:
            args["ids"] = ids

        payload = {
            "method": "torrent-get",
            "arguments": args
        }

        try:
            response = await client.post(
                consts.TRANSMISSION_URL,
                json=payload,
                headers=headers
            )

            # Повтор при 409 (устаревший session-id)
            if response.status_code == 409:
                _session_id = response.headers.get("X-Transmission-Session-Id", "")
                if _session_id:
                    headers["X-Transmission-Session-Id"] = _session_id
                    response = await client.post(
                        consts.TRANSMISSION_URL,
                        json=payload,
                        headers=headers
                    )

            if not response.is_success:
                raise RuntimeError(
                    f"Transmission RPC error {response.status_code}: {response.text}"
                )

            data = response.json()
            if data.get("result") != "success":
                raise RuntimeError(f"API error: {data.get('result')}")

            torrents = data["arguments"].get("torrents", [])
            return torrents

        except httpx.RequestError as e:
            raise RuntimeError(f"Network error: {e}")
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON response: {e}")

async def format_torrents_for_telegram(torrents: List[Dict[str, Any]]) -> List[str]:
    """
    Форматирует список торрентов для Telegram: добавляет ID, убирает ETA.
    """
    if not torrents:
        return ["📭 Нет активных торрентов."]

    STATUS_ICONS = {
        0: "🛑",  # stopped
        1: "⏳",  # check pending
        2: "🔍",  # checking
        3: "📥",  # download pending
        4: "⬇️",  # downloading
        5: "📤",  # seed pending
        6: "⬆️",  # seeding
    }
    STATUS_NAMES = {
        0: "остановлен",
        1: "проверка (очередь)",
        2: "проверка",
        3: "загрузка (очередь)",
        4: "загрузка",
        5: "раздача (очередь)",
        6: "раздача",
    }

    def _make_progress_bar(percent: float) -> str:
        filled = int(percent * 10)
        bar = "█" * filled + "░" * (10 - filled)
        return f"`[{bar}]`"

    lines = ["📦 *Активные торренты:*\n"]
    for t in torrents:
        torrent_id = t.get("id", "?")
        name = t.get("name", "???")[:40]  # обрезаем до 40 символов
        status_code = t.get("status", 0)
        percent = t.get("percentDone", 0.0)
        rate_down = t.get("rateDownload", 0)
        rate_up = t.get("rateUpload", 0)

        icon = STATUS_ICONS.get(status_code, "❓")
        status_name = STATUS_NAMES.get(status_code, f"stat {status_code}")

        # Скорость (в KB/s)
        down_str = f" ↓{rate_down/1024:.1f}KB/s" if rate_down > 0 else ""
        up_str = f" ↑{rate_up/1024:.1f}KB/s" if rate_up > 0 else ""

        # Прогресс
        progress_bar = _make_progress_bar(percent)
        progress_pct = f"{percent*100:.1f}%"

        # Формат: мелкий ID + имя и детали
        lines.append(
            f"`#{torrent_id}` {icon} *{name}*\n"
            f"{progress_bar} {progress_pct} | {status_name}{down_str}{up_str}\n"
        )

    full_text = "".join(lines)
    MAX_LEN = 4096

    if len(full_text) <= MAX_LEN:
        return [full_text.strip()]

    # Разбивка на части (сохраняя торренты целыми)
    messages = []
    current = ["📦 *Активные торренты (часть 1):*\n"]
    part_num = 1

    for line in lines[1:]:
        test_msg = "".join(current) + line
        if len(test_msg) > MAX_LEN:
            messages.append("".join(current).strip())
            part_num += 1
            current = [f"📦 *Активные торренты (часть {part_num}):*\n"]
        current.append(line)

    if current:
        messages.append("".join(current).strip())

    return messages