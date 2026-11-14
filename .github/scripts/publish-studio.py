"""Publish the verified Folio 1.9.10 draft at the official Rome launch."""
import json
import os
import subprocess
import time
from datetime import datetime, timezone

REPOSITORY = "rabistudio/folio-studio-downloads"
RELEASE_ID = 444304801
LAUNCH = int(datetime(2027, 1, 9, 23, 0, tzinfo=timezone.utc).timestamp())
FILES = {
    "FolioStudio-1.9.10-mac-arm64.dmg": (
        147608747, "92a855eb9c0b5b83733bf1afa7f13dc399bfe2691357e367be9ce7e988e12702"
    ),
    "FolioStudio-Setup-1.9.10.exe": (
        129192175, "f224ab4f262087b0e3261d7bc00bd9e83912711211d4f4fe4540d96fa3acd24d"
    ),
}


def github(method="GET", body=None):
    cmd = ["gh", "api", "--method", method, f"repos/{REPOSITORY}/releases/{RELEASE_ID}"]
    if body is not None:
        cmd.extend(["--input", "-"])
    return json.loads(subprocess.check_output(cmd, input=json.dumps(body).encode() if body else None))


def verified_release():
    release = github()
    if release["id"] != RELEASE_ID or release["tag_name"] != "v1.9.10" or release["prerelease"]:
        raise RuntimeError("Unexpected release identity or channel")
    assets = release["assets"]
    if len(assets) != len(FILES) or {a["name"] for a in assets} != set(FILES):
        raise RuntimeError("Published files would differ from the verified manifest")
    for asset in assets:
        size, sha = FILES[asset["name"]]
        if (asset["state"], asset["size"], asset["digest"]) != ("uploaded", size, "sha256:" + sha):
            raise RuntimeError("Unexpected asset state, size or digest")
    return release


def main():
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise RuntimeError("Wrong repository")
    remaining = LAUNCH - time.time()
    if not verified_release()["draft"]:
        if remaining > 0:
            raise RuntimeError("The release is already public before launch")
        print("The verified release is already public.")
        return
    if remaining > 3600 or (remaining > 0 and os.environ.get("GITHUB_EVENT_NAME") != "schedule"):
        print("Verified both private installers. The launch is still embargoed.")
        return
    while time.time() < LAUNCH:
        time.sleep(max(0, min(30, LAUNCH - time.time())))
    if verified_release()["draft"]:
        published = github("PATCH", {"draft": False, "make_latest": "true"})
        if published["draft"] or published["id"] != RELEASE_ID:
            raise RuntimeError("Publication was not confirmed")
    print("Folio Studio 1.9.10 is public.")


if __name__ == "__main__":
    main()
