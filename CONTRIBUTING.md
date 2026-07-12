# Contributing

Thank you for helping improve Koinome. This project’s positioning, terminology, and honest-scope rules live in [docs/STRATEGY.md](docs/STRATEGY.md); read that before large doc or product changes.

## License and inbound contributions

- **Outbound:** The Koinome CLI, template, and repository code are licensed under the [Apache License 2.0](LICENSE).
- **Inbound:** By contributing, you agree that your contributions are licensed under Apache-2.0 on the same terms.

## Developer Certificate of Origin (DCO)

We use the [Developer Certificate of Origin](https://developercertificate.org/) (DCO). **There is no contributor licence agreement (CLA).** That is intentional: copyright stays distributed across contributors, which is a structural guarantee against relicensing the community’s work (see strategy §5 and decision D6).

Sign off every commit:

```bash
git commit -s -m "Your message"
```

The `-s` line (`Signed-off-by: Name <email>`) certifies the DCO text.

## How to contribute

1. Fork and branch from an up-to-date `master` (see [AGENTS.md](AGENTS.md) for branch naming).
2. Run `uv sync --group dev` and `bash scripts/check_repo.sh` before opening a pull request.
3. Keep changes focused; match existing style in touched files.
4. Open a pull request against `master` with a clear description and test plan.

## Response expectations

Koinome is a solo, part-time project. Reviews and fixes happen as capacity allows; there is no SLA. Critical security reports are prioritised — see [SECURITY.md](SECURITY.md).
