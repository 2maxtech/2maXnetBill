import asyncio
import subprocess


async def accel_cmd(command: str) -> str:
    """Execute a command via accel-ppp telnet CLI."""
    proc = await asyncio.create_subprocess_exec(
        "accel-cmd", command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"accel-cmd failed: {stderr.decode()}")
    return stdout.decode()


async def get_sessions() -> list[dict]:
    """Get all active PPPoE sessions from accel-ppp."""
    output = await accel_cmd("show sessions")
    sessions = []
    lines = output.strip().split("\n")
    if len(lines) < 2:
        return sessions

    header = lines[0]
    columns = header.split("|")
    col_names = [c.strip().lower() for c in columns]

    for line in lines[1:]:
        if line.startswith("-") or not line.strip():
            continue
        values = line.split("|")
        if len(values) != len(col_names):
            continue
        row = {col_names[i]: values[i].strip() for i in range(len(col_names))}
        sessions.append(row)

    return sessions


async def find_session_by_username(username: str) -> dict | None:
    """Find an active session by PPPoE username."""
    sessions = await get_sessions()
    for s in sessions:
        if s.get("username") == username:
            return s
    return None


def send_radius_packet(packet_type: str, attributes: dict, secret: str, server: str, port: int) -> str:
    """Send a RADIUS CoA or Disconnect packet using radclient."""
    attr_lines = "\n".join(f"{k} = {v}" for k, v in attributes.items())
    result = subprocess.run(
        ["radclient", "-x", f"{server}:{port}", packet_type, secret],
        input=attr_lines,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"radclient failed: {result.stderr}")
    return result.stdout
