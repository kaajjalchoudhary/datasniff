# Security Policy

## Supported versions

datasniff is pre-1.0. Security fixes land on `main` and in the next release only.

| Version | Supported |
| ------- | --------- |
| 0.1.x   | yes       |

## Reporting a vulnerability

Please do not open a public issue for security problems.

Use GitHub's private reporting instead: go to the **Security** tab of this repository and choose **Report a vulnerability**. Include:

- the datasniff version and Python version
- the command you ran and a minimal file that reproduces the problem
- what you expected and what happened

You should get a reply within 7 days. Once a fix is ready it will be released and credited in the CHANGELOG (unless you prefer to stay anonymous).

## Scope notes

datasniff reads local files through DuckDB and never uploads data anywhere. The `possible_pii` flag is a heuristic to help you spot personal data; it is not a guarantee that a file is free of PII.
