"""One module per advisor. Each exposes a pure `advise(context,
candidates)` function (no I/O — testable without a database) and an
`advise_for_account(db, account_id, ...)` wrapper that loads the account
and candidate catalog rows, then delegates to it.
"""
