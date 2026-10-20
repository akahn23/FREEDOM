# Contributing to FREEDOM

The workflow for accepting external pull requests is still being prepared (see [Contribution](README.md#contribution)).
Until then, please report bugs and feature requests via GitHub Issues.
This file documents the conventions that apply to every change to this GitHub repository.

## Documentation translations
User-facing documentation is maintained in English and Japanese as hand-written pairs.
The two files in a pair must stay equivalent in content.

| English | Japanese |
|---|---|
| [README.md](README.md) | [README_ja.md](README_ja.md) |
| [docs/install.md](docs/install.md) | [docs/install_ja.md](docs/install_ja.md) |

Rules:
- When you change one file of a pair, make the equivalent change to its counterpart **in the same pull request**. This includes added or removed steps, commands, versions, URLs, tables, and notes.
- If you cannot write the translation yourself, still update the counterpart with the new content in the language you can write. Mark it with `<!-- TODO: translate -->` and mention it in the pull request so a maintainer can finish it.
- Keep the section structure (headings, numbered steps, tables) aligned between the two files so they can be compared side by side.
- Each paired file starts with a **Translations** note that links to its counterpart. Keep that note when you edit the file.
- When you add a new paired document, add it to the table above and give both files a Translations note.
- Localized assets (for example `docs/FREEDOM_key_visual.png` / `docs/FREEDOM_key_visual_ja.png`) follow the same rule.

This file (`CONTRIBUTING.md`) is intentionally English-only because it describes code conventions.

## Docstring convention
Write all docstrings in `backend/src/` in **English**.

- Use the Google-style sections already used in the codebase: a one-line summary, optional detail lines, then `Args:`, `Returns:`, and `Attributes:` as needed.
- Keep the `name (type): description` format for arguments and attributes.
  ```python
  def make_logger(self, name:str, prefix:str=None) -> logic.Adapter:
      """Create a logger
      Args:
          name (str): Logger name
          prefix (str): Prefix
      Returns:
          logic.Adapter: Logger
      """
  ```
- Write new `#` comments in English too. Some existing Japanese comments remain; translate them when you touch the surrounding code.
- User-facing text shown in the Web UI is not covered by this rule. Localize it through the next-intl message catalogs in `frontend/messages/` (currently `ja.json`) instead of hard-coding it in source.
