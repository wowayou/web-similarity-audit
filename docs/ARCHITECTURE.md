# Architecture

The current pipeline is input/CSV or crawl → protected fetch → extraction →
template detection → pairwise similarity → JSON/CSV/Markdown reporting.

Implemented modules are `cli`, `crawler`, `extractor`, `fetcher`, `models`,
`reporter`, `robots`, `similarity`, `state`, `template`, and `__main__`.

Exit codes are: 0 success; 1 input/parameter error; 2 more than 20% fetch
failures; 3 more than 20% extraction failures; 4 interruption or fatal error.

For actual limitations, data flow, and the planned target architecture, read
[ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md). This file intentionally does
not describe unimplemented module names or APIs.