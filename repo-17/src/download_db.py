"""Скачивает AUDITS_DB.sqlite из релиза GitHub и проверяет SHA-256.

Автор: Davyd Kochuhur (Zero Azimuth Vivifactor)
Использование:  python src/download_db.py [куда/сохранить.sqlite]
"""
import hashlib
import os
import sys
import urllib.request

RELEASE_URL = "https://github.com/Daothecreator/17/releases/download/v1.0.0/AUDITS_DB.sqlite"
EXPECTED_SHA256 = "4570eaec8c720988d82532cc2ec05bf033bd73274e6ef4233a0e8fa5822b67e8"
EXPECTED_SIZE = 1_280_032_768  # точный размер в байтах; подлинность подтверждает SHA-256

DEST_DEFAULT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDITS_DB.sqlite")
)


def download(url: str, dest: str) -> None:
    tmp = dest + ".part"
    with urllib.request.urlopen(url) as resp, open(tmp, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                pct = done * 100 // total
                print(f"\r{pct:3d}%  {done / 2**20:.0f}/{total / 2**20:.0f} MiB", end="", flush=True)
    print()
    os.replace(tmp, dest)


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    dest = sys.argv[1] if len(sys.argv) > 1 else DEST_DEFAULT
    if os.path.isfile(dest):
        print("Проверяю существующий файл…")
        if sha256_of(dest) == EXPECTED_SHA256:
            print("OK: база уже на месте, контрольная сумма совпадает.")
            return 0
        print("Контрольная сумма не совпала — скачиваю заново.")
    print(f"Загрузка {RELEASE_URL}\n -> {dest}")
    download(RELEASE_URL, dest)
    size = os.path.getsize(dest)
    digest = sha256_of(dest)
    if size != EXPECTED_SIZE or digest != EXPECTED_SHA256:
        print(f"ОШИБКА: size={size}, SHA-256 {digest} != {EXPECTED_SHA256}")
        return 1
    print("Готово. Размер и SHA-256 подтверждены:", digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
