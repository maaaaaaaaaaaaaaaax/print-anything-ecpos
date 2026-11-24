import pytest
from pydantic import ValidationError

from printbot.kernel import Document, Paragraph, Run, TextSource


def test_plain_text_source_builds_a_single_paragraph_document() -> None:
    source = TextSource(text="hello\nworld")

    document = Document(blocks=(Paragraph(runs=(Run(text=source.text),)),))

    assert document == Document(blocks=(Paragraph(runs=(Run(text="hello\nworld"),)),))


def test_document_rejects_empty_blocks() -> None:
    with pytest.raises(ValidationError):
        Document(blocks=())


def test_text_source_rejects_blank_text() -> None:
    with pytest.raises(ValidationError):
        TextSource(text=" \n")
