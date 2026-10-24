# Standing engineering and publication requirements

These instructions apply to all future work in this repository. They record the owner's requirement to repeat privacy, secrets, and publication audits for every project and subsequent change.

## Before committing or pushing

- Review the exact staged files and diff. Confirm the changes are within the requested scope and that existing projects are unchanged unless explicitly authorized.
- Check for personal home-directory paths, private email addresses, phone numbers, account identifiers, internal URLs, hostnames, private business information, and copied customer data. Review matches in context; public repository identity and explicitly documented benchmark metadata are permitted, but disclose what remains public.
- Check tracked files for passwords, tokens, API keys, private keys, credential files, connection strings containing credentials, and other secrets. Never print discovered secret values in reports or tool output.
- Confirm generated datasets, raw runtime logs, local environments, caches, editor files, and credential directories are excluded. Only intentional, reviewed, appropriately sized result artifacts belong in version control.
- Confirm sample/customer records are synthetic and that committed evidence contains no real customer information.
- Review commit author/committer metadata. Use the owner's established public identity and GitHub noreply email; flag any private mailbox exposure.
- Run the relevant tests, artifact checks, and Git whitespace checks for the change. Report failures and unexecuted checks accurately.

## Before each authorized publication or push

- Run a dedicated secret scanner such as Gitleaks against every commit being published, with findings redacted. Also review final tracked artifacts for personal information; a secret scanner alone is not a privacy audit.
- Use the intended target branch as the comparison base. Include previously unpublished commits and any fix commits. If the comparison base is unavailable, establish the correct scope rather than silently scanning a smaller range.
- If a dedicated scanner cannot run, explicitly report that limitation and resolve it before publication; do not claim a clean scanner result from pattern searches alone.
- Resolve unintended sensitive content before pushing. If a secret was already published, stop further publication, report the exposure without repeating the secret, and coordinate credential revocation/rotation and history cleanup with the owner. Do not rewrite shared history without authorization.
- Report the audit scope, tools/checks used, findings, intentionally retained public metadata, and limitations. Do not present a project-only scan as a full-repository historical audit.
- Verify the destination repository, branch, and visibility. Verify the remote commit after pushing.
- Push, publish, merge, or create releases only within explicit user authorization. Authorization to push a feature branch does not authorize merging it into the default branch.

## Evidence integrity

Use actual executed results, preserve relevant variability and confounders, distinguish measured metrics from estimates/proxies, and label synthetic data. Never fabricate successful tests, benchmark improvements, audit results, or cost savings. Preserve the privacy and audit requirements when adding new projects or modifying existing ones.
