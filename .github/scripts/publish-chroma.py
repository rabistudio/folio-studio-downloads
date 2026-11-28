"""Publish the verified Folio Chroma 1.4.2 draft at the official Rome launch."""
import json
import os
import subprocess
import time
from datetime import datetime, timezone

REPOSITORY = "rabistudio/folio-studio-downloads"
RELEASE_ID = 461478260
LAUNCH = int(datetime(2027, 1, 10, 9, 0, tzinfo=timezone.utc).timestamp())
FILES = {'FolioChroma-1.4.2-mac-universal.dmg': (23736968, '0d949fac4c4078cf9806a6185d480078ee6eff2adabafc1443b999321d8b7287'), 'FolioChroma-Setup-1.4.2.exe': (172788808, 'e91747ff6792e54af3322c3a7c5aaea25d9fb7aaa2218370986010611edb4776')}


def github(method="GET", body=None):
    cmd = ["gh", "api", "--method", method, f"repos/{REPOSITORY}/releases/{RELEASE_ID}"]
    if body is not None:
        cmd.extend(["--input", "-"])
    return json.loads(subprocess.check_output(cmd, input=json.dumps(body).encode() if body else None))


def verified_release():
    release = github()
    if release["id"] != RELEASE_ID or release["tag_name"] != "chroma-v1.4.2" or release["prerelease"]:
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
        published = github("PATCH", {"tag_name": "chroma-v1.4.2", "draft": False, "prerelease": False, "make_latest": "false"})
        if published["draft"] or published["id"] != RELEASE_ID or published["tag_name"] != "chroma-v1.4.2" or published["prerelease"]:
            raise RuntimeError("Publication was not confirmed")
    print("Folio Chroma 1.4.2 is public.")


if __name__ == "__main__":
    main()

