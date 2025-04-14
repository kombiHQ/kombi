from kombi.Element import Element
from kombi.Element.Fs.Texture import TextureElement

class InternalTextureElement(TextureElement):
    """
    Enable the test for texture element.
    """

    @classmethod
    def test(cls, path, parentElement):
        return super().test(path, parentElement, enable=True)


# register the element
Element.register('internalTexture', InternalTextureElement)
