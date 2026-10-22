# Loomwell layout workflow

Original Loomwell templates built with DesignCraft's command engine. The pack contains no customer records, third-party brand artwork or performance claims. It uses Forest `#182822`, Paper `#f5f2e9`, Sage `#d5e5b3` and Terracotta `#b86e4d`.

```sh
python3 loomwell/export.py list
python3 loomwell/export.py export all --output ./loomwell/exports --cli /path/to/designcraft-cli
python3 loomwell/export.py export social --output ./loomwell/campaign --content ./campaign.json --cli /path/to/designcraft-cli
```

The CLI resolver also accepts `DESIGNCRAFT_CLI`, a local `target/release/designcraft-cli`, a CLI on PATH, or Loomwell's existing Atlas source-build location. With `--cli`, the pack is independent of Atlas and requires only Python's standard library and DesignCraft.

Templates:

| ID | Canvas | Use |
|---|---|---|
| `website` | 1600×900 | Website hero graphic |
| `social` | 1200×630 | Sharing card |
| `square` | 1080×1080 | Square social card |
| `brief` | 612×792 | Letter-size website creative brief |

Each export writes an editable `.dcs` command script and `.designcraft` document, a one-page PDF, a PNG at exact canvas dimensions, and a digest manifest. The editable defaults are also retained in `templates/`. Modify the native document directly in DesignCraft, or change the generated source in `export.py` for systematic layout changes.

`content.json` contains all editable copy. A partial overrides file can use common keys shared by the other Loomwell packs:

```json
{
  "headline": "See the exception.\nKeep the context.",
  "subheadline": "A fictional exchange example for discussing an evaluation pilot.",
  "eyebrow": "SYNTHETIC FORMAT EXAMPLE",
  "footer": "EARLY PILOT / SCOPE AND AVAILABILITY AGREED INDIVIDUALLY"
}
```

The brief also accepts `brief_title`, `audience`, `objective`, `deliverables`, `proof` and `guardrail`. Inputs are bounded and validated. The exporter inspects the saved native document and refuses text overflow. Failed renders preserve existing outputs; successful renders replace only declared template files and the manifest.

Source Serif 4 and Source Sans 3 are supplied by DesignCraft; no font files are copied into this pack. The original block-weave artwork and layouts are MIT OR Apache-2.0, matching the repository. Attribution is in `ASSETS.md` and `NOTICE`. The pack does not rebrand or redistribute a modified application binary; ArtCraft's separate mark license still applies to the upstream application and documentation.

Verification:

```sh
DESIGNCRAFT_CLI=/path/to/designcraft-cli python3 -m unittest discover -s loomwell/tests
```

Before publishing any copy, review the business claims and replace draft text deliberately. A template is not evidence of buyer demand, available licensed inventory, or measured training improvement.
