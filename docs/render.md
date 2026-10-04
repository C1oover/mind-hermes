# Configuring the context text

The `pre_llm_call` hook builds its text with `mindcore/render.py`. Override any snippet by creating
`render.json` in the state dir (`~/.hermes/mind-hermes/` by default) or by pointing
`MIND_HERMES_RENDER_CONFIG` at a JSON file. Only the keys you set change; invalid files fall back to defaults.

| Key | Meaning |
|---|---|
| `template` | Wrapper text; `{state}` is the joined items |
| `item_format` | Per value (numeric mode); `{key} {label} {value} {word}` |
| `word_item_format` | Per value in words mode |
| `separator` | Joins items |
| `mode` | `numeric` or `words` |
| `source` | `shown` (persona-adjusted) or `raw` |
| `fields` | Which state keys to include, in order |
| `labels` | Display names per key |
| `bands` / `field_bands` | `[[upper_bound, word], ...]` value-to-word mapping |
| `empty` | Text when no fields are selected |

Example:

```json
{
  "template": "(inner state: {state})",
  "mode": "words",
  "fields": ["mood", "arousal", "bond"],
  "labels": {"bond": "closeness"}
}
```
