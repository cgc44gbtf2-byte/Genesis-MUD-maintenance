# Genesis MUD maintenance

Finalized source-only maintenance snapshot for building and hosting on your own Linux server. No deployment has been configured or performed.

## Download

[Genesis-MUD-maintenance-updated.zip](Genesis-MUD-maintenance-updated.zip) contains 153 files, including a MANIFEST.sha256 covering 152 source/data/documentation/test payloads. Compiled programs, object files, player records, backups and runtime logs are excluded.

ZIP SHA-256: 16ec3140b00cfa5cb463b5e1655b3876e28a62ecc2ff22f00b7bb83328518e6b

## Included updates

- Earlier class-ability reconstruction and maintenance, skill, combat and fighting-stance repairs.
- 20 reconstructed legacy spell effects in total, including the final three below.
- Know Alignment reports a visible same-room NPC's alignment; player alignment is not restored.
- Frenzy grants timed hitroll +1 and damroll +1, with battle-rage messaging; it does not initiate combat or modify class rage toggles.
- Darkblessing grants timed hitroll +1, damroll +1 and AC -10 to evil NPCs only.
- Expanded regression tests, source manifest, build instructions and upgrade precautions.

Hybrid functionality and internal hybrid design notes are excluded. Ventriloquate remains disabled. Spell indices, slots and direct-casting eligibility are unchanged; the three newly finalized handlers are not newly assigned to original-area items or class unlocks. Supplied area files are unchanged from the previous verified release.

## Verification

Strict GNU C89 native and AddressSanitizer/UndefinedBehaviorSanitizer builds passed with -Wall -Werror and the existing builtin-declaration compatibility exception. All five native live suites passed: legacy spells, class abilities, maintenance fixes, combat-system runtime and smoke/save/reload. The complete legacy live suite also passed under sanitizers, including real item dispatch, logout/login, dispelling and natural expiry. Both linked sanitizer C probes, the native combat probe, and sanitizer resolve/random regressions passed.

One new live test initially expected the wrong wand-equipping message; the assertion was corrected and both native/sanitized live spell runs passed. The archive CRC, safe paths, every archived byte and all extracted manifest hashes were validated before upload. Sanitizer leak checking was disabled; these results are not a complete security or leak audit.

## Build on Ubuntu or Debian

    sudo apt update
    sudo apt install build-essential libcrypt-dev unzip
    unzip Genesis-MUD-maintenance-updated.zip
    cd genesis-maintenance
    sha256sum --check MANIFEST.sha256
    make -C src
    PORT=4000 ./run.sh

The launcher stays in the foreground. Use an unprivileged account and back up mutable areas and player data before upgrades. See README.md, LEGACY_SPELL_RESTORATION.md and the other maintenance notes inside the archive for test commands and compatibility details.

## Upstream permission and hosting precautions

The source contains an upstream God Wars notice requiring permission to run or redistribute it; the supplied archive did not include the referenced license documents. Verify your permission before publishing or operating a public server. This maintenance does not modernize the legacy password hashing or fully audit networking and memory management. Validate gameplay and saves in a private staging copy before public hosting.
