#!/bin/sh
# Link the real game modules into the focused combat/skill/spell probe.
# Build in isolation so the user's normal server binary and player data stay untouched.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_source="$root/tests/test_combat_system.c"
if [ "$#" -eq 1 ] && [ "${1-}" = legacy ]; then
    test_source="$root/tests/test_legacy_spells.c"
elif [ "$#" -ne 0 ]; then
    echo "Usage: sh tests/test-combat-system.sh [legacy]" >&2
    exit 2
fi
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc=${CC:-cc}
crypt=${CRYPT_LIBRARY:--lcrypt}
flags='-O1 -g -std=gnu89 -Wall -Werror -Wno-builtin-declaration-mismatch -fsanitize=address,undefined -fno-omit-frame-pointer -fno-pie'
cp -a "$root/src" "$tmp/src"
make -C "$tmp/src" clean >/dev/null
make -C "$tmp/src" -j2 CC="$cc" CFLAGS="$flags" \
    LDFLAGS='-fsanitize=address,undefined -no-pie' LDLIBS="$crypt" >/dev/null
"$cc" $flags -DMERC -Dunix -DMEMWATCH -Dmain=genesis_server_main \
    -c "$tmp/src/comm.c" -o "$tmp/comm-probe.o"
set --
for obj in "$tmp/src/"*.o; do
    [ "$obj" = "$tmp/src/comm.o" ] || set -- "$@" "$obj"
done
"$cc" $flags -DMERC -Dunix -DMEMWATCH -no-pie \
    "$test_source" "$tmp/comm-probe.o" "$@" "$crypt" \
    -o "$tmp/probe"
ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=halt_on_error=1 "$tmp/probe"
