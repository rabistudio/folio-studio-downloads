"""Publish the verified Folio 1.9.16 draft at the official Rome launch."""
import json
import os
import subprocess
import time
from datetime import datetime, timezone

REPOSITORY = "rabistudio/folio-studio-downloads"
RELEASE_ID = 453233858
LAUNCH = int(datetime(2026, 12, 10, 9, 0, tzinfo=timezone.utc).timestamp())
FILES = {
    "FolioStudio-1.9.16-mac-arm64.dmg": (
        147646611, "bf0bb6b73b06fc079ef4388e3c453922f2084cb59552034d353d26008f2f7da6"
    ),
    "FolioStudio-Setup-1.9.16.exe": (
        129356220, "34a76e84a66df2e899d3c950ea87956f6f5387dcec50e98a22077e850007e169"
    ),
}


def github(method="GET", body=None):
    cmd = ["gh", "api", "--method", method, f"repos/{REPOSITORY}/releases/{RELEASE_ID}"]
    if body is not None:
        cmd.extend(["--input", "-"])
    return json.loads(subprocess.check_output(cmd, input=json.dumps(body).encode() if body else None))


def verified_release():
    release = github()
    if release["id"] != RELEASE_ID or release["tag_name"] != "v1.9.16" or release["prerelease"]:
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
    if remaining < -24 * 3600:
        print("The launch publication window has ended.")
        return
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
    print("Folio Studio 1.9.16 is public.")


if __name__ == "__main__":
    main()
