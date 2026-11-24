from printbot.kernel import Document, Frozen, Paragraph, Run, TextSource


class Conversion(Frozen):
    document: Document


class PlainTextConverter:
    async def convert(self, source: TextSource) -> Conversion:
        document = Document(blocks=(Paragraph(runs=(Run(text=source.text),)),))
        return Conversion(document=document)
