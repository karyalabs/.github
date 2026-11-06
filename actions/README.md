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
