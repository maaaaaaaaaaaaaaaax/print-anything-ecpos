# ingest

Turns a `Source` into a `Document` of blocks. Depends on `kernel` only.

## Current implementation

`PlainTextConverter` turns a `TextSource` into a `Document` with one paragraph and preserves the
original line breaks and text. It returns a typed `Conversion` value. Conversion errors are
represented by `ConversionError`.

## Planned

A converter protocol and registry, content-type detection, and converters for markdown, code files,
URLs, images, PDFs, Office files, and a receipt fallback. Heavy tools will run through a bounded
`ProcessRunner` port.
