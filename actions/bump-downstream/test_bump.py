"""Checks bump.py on the manifest shapes Karya Labs repositories use.

Run with `python3 -I actions/bump-downstream/test_bump.py`.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

MANIFEST = """\
[workspace.dependencies]
gpuicn = "=0.10.6"
gpui-kit = { version = "=0.9.0", default-features = false, features = ["component"] }
gpui_platform = { package = "gpui-pre-platform", version = "=0.3.11", features = ["font-kit"] }
gpui-icons = "=0.8.0"
serde = "1"

[dependencies.extra]
version = "0.3.11"
package = "gpui-pre-platform"

[profile.release.package.gpui-kit]
opt-level = 3
"""

EXPECTED = """\
[workspace.dependencies]
gpuicn = "=0.11.0"
gpui-kit = { version = "=0.9.1", default-features = false, features = ["component"] }
gpui_platform = { package = "gpui-pre-platform", version = "=0.3.12", features = ["font-kit"] }
gpui-icons = "=0.8.0"
serde = "1"

[dependencies.extra]
version = "0.3.12"
package = "gpui-pre-platform"

[profile.release.package.gpui-kit]
opt-level = 3
"""

DEPS = {
    "dependencies": [
        {"crate_id": "gpui-kit", "req": "=0.9.1", "kind": "normal"},
        {"crate_id": "gpui-pre-platform", "req": "=0.3.12", "kind": "normal"},
        # Older than the downstream's: never moved back.
        {"crate_id": "gpui-icons", "req": "^0.7.0", "kind": "normal"},
        {"crate_id": "serde", "req": "^2.0", "kind": "dev"},
    ]
}


def run(*args):
    return subprocess.run(
        [sys.executable, "-I", os.path.join(HERE, "bump.py"), *args],
        capture_output=True,
        text=True,
    )


def main():
    with tempfile.TemporaryDirectory() as tmp:
        manifest = os.path.join(tmp, "Cargo.toml")
        deps = os.path.join(tmp, "deps.json")
        open(manifest, "w").write(MANIFEST)
        json.dump(DEPS, open(deps, "w"))

        result = run(manifest, "gpuicn", "0.11.0", deps)
        assert result.returncode == 0, result.stderr
        assert open(manifest).read() == EXPECTED, open(manifest).read()
        assert result.stdout.split() == ["gpuicn", "gpui-kit", "gpui-pre-platform"], result.stdout

        result = run(manifest, "gpuicn", "0.11.0", deps)
        assert result.returncode == 0 and result.stdout == "", "a second run moves nothing"

        result = run(manifest, "missing", "1.0.0")
        assert result.returncode != 0 and "No requirement on missing" in result.stderr
    print("ok bump.py")


if __name__ == "__main__":
    main()
