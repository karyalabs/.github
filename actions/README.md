# Shared actions

The building blocks every Karya Labs repository's workflows use, so a pin
or a setup step is fixed in one place. The process they serve is
[docs/engineering-process.md](https://github.com/karyalabs/matty/blob/master/docs/engineering-process.md)
in matty (section 7).

Use them by the major version branch `v1`:

```yaml
- uses: karyalabs/.github/actions/rust-toolchain@v1
```

| Action | What it does |
| --- | --- |
| [`pick-runners`](pick-runners/action.yml) | Turns `vars.KARYA_LINUX_RUNNER` / `vars.KARYA_MACOS_RUNNER` into `runs-on` values; GitHub's runners when unset or for fork PRs |
| [`self-hosted-prep`](self-hosted-prep/action.yml) | Cleans a reused self-hosted checkout but keeps `target/` warm |
| [`rust-toolchain`](rust-toolchain/action.yml) | Installs the toolchain in `rust-toolchain.toml` (or an MSRV / nightly) with rustup |
| [`gpui-deps`](gpui-deps/action.yml) | The Debian packages GPUI needs on Linux, only those missing |
| [`release-plan`](release-plan/action.yml) | Is this push a release? Version, tag and the commit to release from; finishes a half-done release |
| [`crates-publish`](crates-publish/action.yml) | Publishes crates in order with Trusted Publishing, skipping published ones |
| [`downstream-canary`](downstream-canary/action.yml) | Builds a consumer repository against this checkout through `[patch.crates-io]` |
| [`bump-downstream`](bump-downstream/action.yml) | After a release, opens the consumer's pin bump PR (needs the Karya bot app) |

Publishing stays in each repository's own workflow file: crates.io Trusted
Publishing trusts the calling workflow, and composite actions keep it so.

## Changing an action

1. Open a PR here; `ci` runs the actions that need no secrets.
2. After merging, a compatible change moves the `v1` branch to the new
   commit (`git push origin <sha>:refs/heads/v1`); a breaking change starts
   a `v2` branch, and each repository moves when it is ready. `v1` is a
   branch, not a tag, because cloud sessions cannot push tags here; actions
   resolve either.

## Runner upkeep (macOS)

`self-hosted-prep` keeps each checkout's own `target/` under its limit, but
a Mac with several runners and repositories still fills up across them, and
nothing else on the machine cleans the Rust caches, old toolchains or old
runner versions. [`runner/macos`](../runner/macos) has a LaunchAgent for
that. On the Mac, as the user the runners run as:

```sh
git clone --depth 1 https://github.com/karyalabs/.github /tmp/karya-github
/tmp/karya-github/runner/macos/install
```

It runs at login and every 6 hours, keeps 100 GB free by dropping unused
and then the largest `target/` folders when no job is running, and logs to
`~/Library/Logs/karya-runner-cleanup.log`. `karya-runner-cleanup --report`
shows where the space is; the header of
[`karya-runner-cleanup`](../runner/macos/karya-runner-cleanup) lists what it
removes and its settings. When a job starts with less than 30 GB free,
`self-hosted-prep` drops that checkout's `target/` and the run shows a
"Runner disk low" warning.
