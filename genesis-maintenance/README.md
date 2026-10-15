# Genesis MUD maintenance copy

This is a legacy C/telnet MUD server and its area data. It is not a web app.
This maintenance copy intentionally excludes the original compiled binary,
object files, server logs, player backups, and private notes.

## Build

On Linux, install a C compiler, GNU Make, and the system development package
that provides `crypt(3)` (commonly `libcrypt-dev` on Debian/Ubuntu).

```sh
make -C src
```

The source uses GNU C89 extensions to retain compatibility with its original
style. The build is incremental; `make -C src clean` removes generated build
files.

## Runtime maintenance checks

This pass fixes wide-range random-number overflow, caps mob health before
narrowing squared levels, and corrects an out-of-bounds value copy in forging.
Character saves now use a temporary file and replace the destination only after
a successful write. Save failures no longer double-close a reserved file handle,
and the `save` command no longer claims success for failures or ineligible
sleeper characters. The existing awakening requirement is unchanged.

Run the random-number regression tests with GCC's sanitizers:

```sh
sh tests/test-random.sh
```

For the runtime smoke test, first build the server, then run:

```sh
python3 tests/smoke_runtime.py
```

The smoke test uses temporary copies of the area data and disposable characters;
it does not use your player or backup directories. It covers character creation,
common information commands, saving/reloading, and unavailable save directories.
It requires Python 3 and the system crypt library. If the library is installed
outside the normal loader search path, set `CRYPT_LIBRARY` to its absolute path.

To run it with AddressSanitizer and UndefinedBehaviorSanitizer enabled:

```sh
make -C src clean
make -C src \
  CFLAGS="-O2 -g -std=gnu89 -Wall -Werror -Wno-builtin-declaration-mismatch -fsanitize=address,undefined -fno-omit-frame-pointer" \
  LDFLAGS="-fsanitize=address,undefined"
python3 tests/smoke_runtime.py
```

Clean again before switching back to a normal build. These are focused regression
checks, not a complete gameplay or security audit.

## Class ability restoration

The recoverable class abilities have been repaired and connected to the
interpreter. See `ABILITY_RESTORATION.md` for the changes, safety restrictions,
and the newly reconstructed mechanics. In game, use `help abilitystatus` and
`help reconstructedabilities`. The eight reconstructed powers use new rules,
not recovered original balance; see `ABILITY_RECONSTRUCTION.md`.
This is not a claim that all class abilities or combat balance have been tested.

With the server built, run the isolated class-ability regression test:

```sh
python3 tests/class_abilities.py
python3 tests/maintenance_fixes.py
sh tests/test-resolve.sh
```

Like the runtime smoke test, this needs Python 3 and the system crypt library
and accepts `CRYPT_LIBRARY`. It creates disposable characters and a temporary
copy of the area data, including temporary changes to a room's safety flags.
It never changes your live area or player files.
The class suite can take several minutes while combat timers and normal effect
expiry run. The resolve test requires GCC-compatible sanitizer and linker flags.

The nine-finding repair batch is documented in `MAINTENANCE_FIXES.md`,
including Mage cost rules, saved-status migration, shared stat/save changes
and external upgrade precautions. The maintenance regression test exercises
the fixes with disposable accounts, including a real save/restart/expiry cycle.

`COMBAT_SYSTEM_FIXES.md` documents the follow-up skill, spell and stance
repairs, including newly active item procs and intentionally deferred legacy
item spells at that point in the maintenance history. Run its isolated C
and live-server regressions with:

```sh
sh tests/test-combat-system.sh
python3 tests/system_fixes.py
```

The subsequent `LEGACY_SPELL_RESTORATION.md` documents 20 reconstructed
item/NPC spell effects, restored spell-pill activation, green-potion
targeting, and saved door-barrier loading. The final three are NPC-only
Know Alignment, a small timed Frenzy offensive buff, and Darkblessing for evil
NPCs only. Ventriloquate remains disabled; spell indices, slots and level-99
casting restrictions are unchanged. No hybrid-class feature is included.
Run its focused sanitizer and disposable live-server tests with:

```sh
sh tests/test-combat-system.sh legacy
python3 tests/legacy_spells.py
```

## Run locally

```sh
PORT=4000 ./run.sh
```

The server stays in the foreground so a process manager can supervise it.
The launcher creates the player, backup, and log directories if they are missing.
It loads area files relative to `area/` and stores player records in `player/`.
The default port is 4000; choose an unprivileged port above 1024. Back up
player records and mutable area files before upgrades.

## Before public hosting

The source contains an upstream God Wars notice stating that running or
redistributing the code requires permission. The archive did not include the
referenced license documents, so verify that you have permission before
publishing or operating a public server. This cleanup does not modernize the
game's password hashing or audit the legacy networking and memory-management
code for production security.
