from printbot.ingest import PlainTextConverter
from printbot.kernel import Document, Paragraph, Run, TextSource


async def test_plain_text_conversion_preserves_text_in_one_paragraph() -> None:
    conversion = await PlainTextConverter().convert(TextSource(text="hello\nworld"))

    assert conversion.document == Document(blocks=(Paragraph(runs=(Run(text="hello\nworld"),)),))
    assert len(conversion.document.blocks) == 1
