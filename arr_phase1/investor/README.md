# Investor send package

## Files to share

1. **`Sudurpashchim_ARR_Investor_Plan.md`** — professional investor brief (send this).
2. **`charts/`** — PNG figures embedded in the brief (keep folder beside the markdown when exporting to PDF/DOCX).
3. Supporting data room: `../outputs/district_summary.csv`, `local_level_top25_screen.csv`, `methods_and_totals.json`, `feasibility_overview.png`.

## Export tip

Open the markdown in a Markdown→PDF tool (e.g. Pandoc, Typora, VS Code PDF) with `charts/` as the working directory parent so images resolve.

```bash
# Example
pandoc Sudurpashchim_ARR_Investor_Plan.md -o Sudurpashchim_ARR_Investor_Plan.pdf --resource-path=.
```
