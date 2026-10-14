# Bundled fonts

Inter and Noto Sans JP are self-hosted under the SIL Open Font License 1.1; the adjacent OFL files apply to the respective font files. The survey CC0 license does not replace these licenses.

Sources: [Inter](https://github.com/google/fonts/tree/main/ofl/inter), [Noto Sans JP](https://github.com/google/fonts/tree/main/ofl/notosansjp).

The variable WOFF2 files retain their weight axes. Inter covers Latin and common punctuation. Noto Sans JP covers common Japanese characters and the current survey text; additional characters use the system fallback. Rebuild the subset when adding uncommon Japanese characters. FontTools was used to subset the upstream TTF files and encode WOFF2.
