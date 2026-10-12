#!/usr/bin/env python3
# mask_build_id_r7.py -- P05-S4 R7 cont9 ADD2 (U87, new file).
#
# Zero the NT_GNU_BUILD_ID descriptor of ELF files, ONLY in copies named *.masked (never in the originals).
# The descriptor offset and length are read from the ELF file itself (section headers and note headers), not assumed:
#   1. find the section named .note.gnu.build-id (section header table, read directly);
#   2. walk its note records (namesz, descsz, type; name padded to 4; desc padded to 4);
#   3. the record with type 3 (NT_GNU_BUILD_ID) and name "GNU" gives desc_off (file offset) and desc_len.
# Then the desc_len bytes at desc_off are set to 0 and the file is written back (same length, no layout change).
# objcopy --remove-section is NOT used (it would change the file layout).
#
# Usage: python3 -I -B mask_build_id_r7.py FILE.masked [FILE.masked ...]
#   Refuses any name that does not end in ".masked", and refuses to run on a file that is not an ELF64 little-endian file.
#   Prints one line per file: path, section offset, desc_off, desc_len, build-id before (hex), after (zeros).
import struct
import sys


def mask(path):
    if not path.endswith(".masked"):
        raise SystemExit("REFUSED: %s does not end in .masked" % path)
    with open(path, "rb") as fh:
        data = bytearray(fh.read())
    if data[:4] != b"\x7fELF" or data[4] != 2 or data[5] != 1:
        raise SystemExit("REFUSED: %s is not ELF64 little-endian" % path)
    shoff = struct.unpack_from("<Q", data, 0x28)[0]
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", data, 0x3A)
    str_off = struct.unpack_from("<Q", data, shoff + shstrndx * shentsize + 0x18)[0]

    def sec_name(idx):
        p = str_off + idx
        return bytes(data[p:data.index(b"\0", p)]).decode()

    found = None
    for i in range(shnum):
        base = shoff + i * shentsize
        name = sec_name(struct.unpack_from("<I", data, base)[0])
        if name == ".note.gnu.build-id":
            found = (struct.unpack_from("<Q", data, base + 0x18)[0], struct.unpack_from("<Q", data, base + 0x20)[0])
            break
    if found is None:
        raise SystemExit("REFUSED: %s has no .note.gnu.build-id section" % path)
    sec_off, sec_size = found

    desc = None
    p = sec_off
    end = sec_off + sec_size
    while p + 12 <= end:
        namesz, descsz, ntype = struct.unpack_from("<III", data, p)
        name_off = p + 12
        desc_off = name_off + ((namesz + 3) & ~3)
        name = bytes(data[name_off:name_off + namesz]).rstrip(b"\0")
        if ntype == 3 and name == b"GNU":
            desc = (desc_off, descsz)
            break
        p = desc_off + ((descsz + 3) & ~3)
    if desc is None:
        raise SystemExit("REFUSED: %s: no NT_GNU_BUILD_ID note in the section" % path)
    d_off, d_len = desc
    if d_len != 20:
        raise SystemExit("REFUSED: %s: build-id length %d (expected 20 for SHA1)" % (path, d_len))
    before = bytes(data[d_off:d_off + d_len]).hex()
    data[d_off:d_off + d_len] = b"\0" * d_len
    with open(path, "r+b") as fh:
        fh.write(bytes(data))
    print("%s section_off=%d desc_off=%d desc_len=%d before=%s after=%s" % (
        path, sec_off, d_off, d_len, before, "00" * d_len))
    return 0


def main(argv):
    if len(argv) < 2:
        raise SystemExit("usage: mask_build_id_r7.py FILE.masked [...]")
    for p in argv[1:]:
        mask(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
