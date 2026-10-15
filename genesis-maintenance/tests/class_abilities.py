#!/usr/bin/env python3
"""Exercise restored class commands against disposable accounts and area data.

Build src/merc first. No production player files or area files are modified.
"""
import ctypes
import ctypes.util
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import tempfile
import time

from smoke_runtime import receive

ROOT = Path(__file__).resolve().parents[1]
HEADER = (ROOT / "src/merc.h").read_text()


def constant(name):
    match = re.search(r"^#define\s+" + name + r"\s+(\d+)", HEADER, re.M)
    if not match:
        raise AssertionError("Missing numeric constant: " + name)
    return int(match[1])


def command(client, text, expected):
    alternatives = expected if isinstance(expected, tuple) else (expected,)
    client.sendall(text.encode("ascii") + b"\r\n")
    data = bytearray()
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        client.settimeout(0.3)
        try:
            chunk = client.recv(65536)
        except socket.timeout:
            continue
        if not chunk:
            break
        data.extend(chunk)
        if any(value.lower() in data.lower() for value in alternatives):
            return bytes(data)
    raise AssertionError(f"{text!r}: expected {expected!r}, got {bytes(data)[-1500:]!r}")


def main():
    # Verify every compatibility alias points at the canonical handler, and
    # prevent reintroducing silent duplicate command-name shadowing.
    table = (ROOT / "src/interp.c").read_text()
    table = re.sub(r"/\*.*?\*/|//[^\n]*", "", table, flags=re.S)
    entries = re.findall(r'\{\s*"([^"]+)"\s*,\s*(do_\w+)', table)
    registry = dict(entries)
    assert len(registry) == len(entries), "Duplicate command name"
    for alias, canonical in {
        "frictioncurse": "friction", "sorcheal": "mageheal",
        "sorcbetterbody": "betterbody", "sorcalterweight": "alterweight",
        "sorcinvis": "mageinvis", "sorcenchant": "mageenchant",
        "spiritsence": "spiritsense", "spiritfriend": "spiritguardian",
        "illusionaryform": "formillusion", "changeling": "malleable",
    }.items():
        assert registry[alias] == registry[canonical], alias

    crypt = ctypes.CDLL(os.environ.get("CRYPT_LIBRARY")
                        or ctypes.util.find_library("crypt") or "libcrypt.so.1")
    crypt.crypt.argtypes = (ctypes.c_char_p, ctypes.c_char_p)
    crypt.crypt.restype = ctypes.c_char_p
    password = secrets.token_hex(12)
    hashed = crypt.crypt(password.encode("ascii"), b"Classprobe")
    if not hashed:
        raise RuntimeError("Could not hash disposable fixture password")
    powers = "Powers " + " ".join(["7"] * 20) + "\n"
    tribes = "Tribes " + " ".join(["5"] * 20) + "\n"
    fixtures = {
        "Adminprobe": (2, "Level 7\nRank 1\n"),
        "Noneprobe": (0, "Flag 0\nAffectedBy "
                      + str(constant("AFF_SHADOWPLANE")) + "\n"),
        "Mageprobe": (32, "Spheres " + " ".join(["5"] * 9) + "\n"),
        "Magenovice": (32, "Spheres " + " ".join(["0"] * 9) + "\n"),
        "Wolfprobe": (2, "Breed 5 5 5\nAuspice 0 0 0 0 0\n"
                      + tribes + "Rank 5\nAffectedBy "
                      + str(constant("AFF_SHADOWSIGHT") | constant("AFF_INFRARED")) + "\n"),
        "Wolfcub": (2, "Breed 0 0 0\nRank 1\nStats 1 1 1 1 1\nAffectedBy "
                    + str(constant("AFF_SHADOWPLANE")) + "\n"),
        "Vampprobe": (1, powers + "Blood 1000 1000\nBeast 50\n"),
        "Monkprobe": (256, "Monk 8 8 8 0\n"),
        "Monknovice": (256, "Monk 6 0 0 0\n"),
        "Drywolf": (2, "Breed 5 5 5\n" + tribes
                    + "HpMana 1000000 1000000 1 1\n"),
        "Dryvamp": (1, powers + "Beast 0\nHpMana 1000000 1000000 1 1\n"),
        "Dragprobe": (64, "DSkills " + str(constant("DRAG_WINGS"))
                      + "\nPolyaff " + str(constant("POLY_DRAGONFORM"))
                      + "\nAffectedBy " + str(constant("AFF_POLYMORPH"))
                      + "\nVampaff " + str(constant("VAM_DISGUISED")) + "\n"),
    }
    with tempfile.TemporaryDirectory(prefix="genesis-abilities-") as work:
        work = Path(work)
        shutil.copytree(ROOT / "area", work / "area")
        shutil.copy2(ROOT / "run.sh", work / "run.sh")
        (work / "src").mkdir()
        (work / "src/merc").symlink_to(ROOT / "src/merc")
        (work / "player").mkdir()
        for name, (kind, fields) in fixtures.items():
            record = (
                "#PLAYER\nName " + name + "~\nPassword " + hashed.decode("ascii")
                + "~\nLevel 2\nClass " + str(kind)
                + "\nRoom 3001\nHpMana 1000000 1000000 100000 100000\nFlag 2\n"
                + "AffectedBy " + str(constant("AFF_INFRARED")) + "\n"
                + fields + "End\n"
            )
            if name == "Mageprobe":
                record += ("#OBJECT\nVnum 3000\nNest 0\nName barrel beer~\n"
                           "ShortDescr an audit barrel~\nItemType 17\nEnd\n")
            (work / "player" / name).write_text(record + "#END\n")
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        env = os.environ.copy()
        env.update(PORT=str(port), ASAN_OPTIONS="detect_leaks=0:abort_on_error=1",
                   UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")
        clients = {}
        log_path = work / "server.log"
        with log_path.open("w") as log:
            proc = subprocess.Popen(["sh", str(work / "run.sh")],
                                    cwd=work / "area", env=env,
                                    stdout=log, stderr=subprocess.STDOUT)
            try:
                for _ in range(120):
                    if proc.poll() is not None:
                        raise RuntimeError("Server exited during startup")
                    try:
                        probe = socket.create_connection(("127.0.0.1", port), timeout=1)
                        probe.close()
                        break
                    except OSError:
                        time.sleep(0.25)
                else:
                    raise RuntimeError("Server did not start")
                for name in fixtures:
                    client = socket.create_connection(("127.0.0.1", port), timeout=2)
                    clients[name] = client
                    receive(client)
                    command(client, name, b"password")
                    client.sendall(password.encode("ascii") + b"\r\n")
                    receive(client)
                    if name == "Adminprobe":
                        client.sendall(b"n\r\n")
                        receive(client)
                        command(client, "look", b"Temple of Maraden")
                    else:
                        command(client, "", b"Welcome to Godwars: Genesis")

                def run(name, text, expected):
                    assert proc.poll() is None
                    return command(clients[name], text, expected)

                def snapshot(name):
                    run(name, "save", b"Saved.")
                    return (work / "player" / name).read_text()

                def number(name, field, index=0):
                    text = snapshot(name)
                    match = re.search(r"^" + field + r"\s+([^\n]+)", text, re.M)
                    return int(match[1].split()[index]) if match else 0

                def room_flags(flags):
                    clients["Adminprobe"].sendall(
                        f"rset 3001 flags {flags}\r\n".encode("ascii"))
                    run("Adminprobe", "look", b"Temple of Maraden")

                # Both classes retain the same historical ward spelling.
                run("Wolfprobe", "ward", b"ward yourself")
                assert number("Wolfprobe", "More") & constant("MORE_SHIELDED")
                run("Wolfprobe", "ward", b"stop warding")
                assert not number("Wolfprobe", "More") & constant("MORE_SHIELDED")
                run("Mageprobe", "ward", b"How much quintessense")
                run("Wolfcub", "ward", b"require Homid 5")
                run("Adminprobe", "disable ward", b"Command disabled.")
                run("Wolfprobe", "ward", b"temporarily disabled")
                run("Mageprobe", "ward", b"temporarily disabled")
                run("Adminprobe", "disable ward", b"Command enabled.")
                run("Adminprobe", "disable mageheal", b"Command disabled.")
                run("Mageprobe", "sorcheal Nobodyhere", b"temporarily disabled")
                run("Adminprobe", "disable mageheal", b"Command enabled.")

                # Exact short names win, while ordinary abbreviations still work.
                run("Vampprobe", "step", b"Who do you wish to shadowstep")
                run("Vampprobe", "shadowstep", b"Who do you wish to shadowstep")
                run("Magenovice", "l", b"Temple of Maraden")
                run("Noneprobe", "missingability", b"Huh?")
                run("Wolfprobe", "help abilitystatus", b"Restored commands:")

                run("Magenovice", "analyze", b"require Matter 1")
                run("Mageprobe", "analyze", b"Analyze which carried object")
                run("Mageprobe", "analyze barrel", b"Object")
                run("Mageprobe", "frictioncurse Nobodyhere 0", b"aren't here")
                run("Mageprobe", "sorcheal Nobodyhere", b"aren't here")
                run("Mageprobe", "spiritsence", b"see between planes")
                run("Mageprobe", "spiritsense", b"no longer see between planes")
                run("Wolfprobe", "spiritfriend", b"call your Spirit Guardian")
                run("Vampprobe", "changeling", b"Change to look like whom")
                run("Wolfprobe", "illusionaryform", b"Who")

                menu = run("Wolfprobe", "wwpowers", b"Wendigos:")
                assert b" Aeolus Bodywrack" in menu
                assert b"Bone Gnawers: Friend Infest" in menu

                run("Dragprobe", "wings", b"grow wings")
                assert number("Dragprobe", "DSkills") & constant("DRAG_WINGSOUT")
                run("Dragprobe", "wings", b"slide back")
                assert not number("Dragprobe", "DSkills") & constant("DRAG_WINGSOUT")
                run("Noneprobe", "wings", b"Huh?")
                run("Wolfcub", "invisibility", b"level 4 power")

                # Cross-plane targeting respects protection, then succeeds in PK.
                room_flags(1036)
                run("Wolfprobe", "reach Wolfcub", b"must permit summoning")
                assert number("Wolfcub", "AffectedBy") & constant("AFF_SHADOWPLANE")
                room_flags(12)
                run("Wolfprobe", "reach Noneprobe", b"must permit summoning")
                assert number("Noneprobe", "AffectedBy") & constant("AFF_SHADOWPLANE")
                run("Wolfprobe", "reach Wolfcub", b"pull")
                assert not number("Wolfcub", "AffectedBy") & constant("AFF_SHADOWPLANE")

                run("Wolfcub", "mastery Wolfprobe say hello", b"Silver Fangs 5")
                run("Wolfprobe", "mastery Wolfcub quit", b"permits movement")
                run("Wolfprobe", "mastery Wolfcub mastery Wolfprobe look",
                    b"permits movement")
                run("Wolfprobe", "mastery Wolfcub say obeyed", b"compel")
                assert b"obeyed" in receive(clients["Wolfcub"])
                run("Wolfprobe", "mastery Wolfcub", b"Syntax:")
                run("Wolfprobe", "mastery Adminprobe look", b"higher authority")

                run("Monknovice", "stunfist Wolfcub", b"Tech 7")
                room_flags(1036)
                mana = number("Monkprobe", "HpMana", 2)
                run("Monkprobe", "stunfist Wolfcub", b"prevents you from attacking")
                assert number("Monkprobe", "HpMana", 2) == mana
                room_flags(12)
                run("Monkprobe", "stunfist Wolfcub", b"punch")
                run("Adminprobe", "peace", b"Ok")
                saved = snapshot("Monkprobe")
                hp = re.search(r"^HpMana\s+(\d+) (\d+) (\d+) (\d+)", saved, re.M)
                assert hp and 94000 <= int(hp[3]) <= 96000, hp
                from reconstructed_abilities import check_reconstruction
                check_reconstruction(run, snapshot, room_flags, clients, work,
                                     password, command)
                # Run Fear after other combat scenarios: a feared caster may
                # legitimately flee during a later combat pulse.
                room_flags(1036)
                run("Wolfprobe", "wrath", b"start to howl")
                assert not number("Vampprobe", "AffectedBy") & constant("AFF_FEAR")
                room_flags(12)
                run("Wolfprobe", "wrath", b"start to howl")
                assert number("Vampprobe", "AffectedBy") & constant("AFF_FEAR")
                run("Vampprobe", "shadowplay", b"deep into the shadows")
                assert number("Vampprobe", "AffectedBy") & constant("AFF_HIDE")
                run("Wolfprobe", "invisibility", b"fade out")
                assert number("Wolfprobe", "AffectedBy") & constant("AFF_INVISIBLE")
                assert proc.poll() is None
            except BaseException:
                log.flush()
                print(log_path.read_text()[-6000:])
                raise
            finally:
                for client in clients.values():
                    client.close()
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
        log_text = log_path.read_text()
        if "AddressSanitizer" in log_text or "runtime error:" in log_text:
            raise AssertionError(log_text[-6000:])
    print("Class ability regressions passed: routing, effects, costs, prerequisites, PK protection")


if __name__ == "__main__":
    main()
