import os
import unittest
from ...BaseTestCase import BaseTestCase
from kombi.Element import Element
from kombi.Element.Fs import FsElement
from kombi.Element.Fs import FileElement
from pathlib import Path
from kombi.Element.Fs.Render import ExrRenderElement
from kombi.Element.Fs.Image import ExrElement
from kombi.Element.Element import ElementInvalidVarError
from kombi.Element.Element import ElementInvalidTagError

class FsElementTest(BaseTestCase):
    """Test Directory element."""

    __dir = os.path.join(BaseTestCase.dataTestsDirectory(), "glob")
    __turntableFile = os.path.join(__dir, "images", "RND_ass_lookdev_default_beauty_tt.1001.exr")
    __shotRenderFile = os.path.join(__dir, "images", "RND-TST-SHT_lighting_beauty_sr.1001.exr")

    def testFsElement(self):
        """
        Test that the fs element test works.
        """
        path = Path(self.__dir)
        self.assertTrue(FsElement.test(path, None))

        notAPath = {}
        self.assertFalse(FsElement.test(notAPath, None))

    def testFsElementGlob(self):
        """
        Test the glob functionality.
        """
        element = Element.create(Path(self.__dir))
        elements = element.glob()
        result = self.collectFiles(self.__dir)
        result = list(map(lambda x: x.rstrip("/"), result))
        elementPaths = list(map(lambda x: x.var("filePath"), elements))
        self.assertCountEqual(result, elementPaths)

        elements = element.glob(filterTypes=["turntable", "shotRender"])
        elementPaths = list(map(lambda x: x.var("filePath"), elements))
        self.assertCountEqual(elementPaths, [self.__turntableFile, self.__shotRenderFile])

        elements = element.glob(filterTypes=[ExrRenderElement])
        elementPaths = list(map(lambda x: x.var("filePath"), elements))
        result = self.collectFiles(self.__dir, "RND*.exr")
        result = list(map(lambda x: x.rstrip("/"), result))
        self.assertCountEqual(result, elementPaths)

        elements = element.glob(filterTypes=['exr'])
        elementPaths = list(map(lambda x: x.var("filePath"), elements))
        result = self.collectFiles(self.__dir, "*.exr")
        result = list(map(lambda x: x.rstrip("/"), result))
        self.assertCountEqual(result, elementPaths)

        element = Element.create(Path(self.__turntableFile))
        otherElements = element.globFromParent(filterTypes=[ExrRenderElement])
        elementPaths = list(map(lambda x: x.var("filePath"), elements))
        otherElementPaths = list(map(lambda x: x.var("filePath"), otherElements))
        self.assertCountEqual(elementPaths, otherElementPaths)

    def testPathVariables(self):
        """
        Test that the element variables are set properly.
        """
        element = Element.create(Path(self.__turntableFile))
        name, ext = os.path.splitext(self.__turntableFile)
        self.assertEqual(element.var('filePath'), self.__turntableFile)
        self.assertEqual(element.var('ext'), ext.lstrip("."))
        self.assertEqual(element.var('baseName'), os.path.basename(self.__turntableFile))
        self.assertEqual(element.var('name'), os.path.basename(name).split(".")[0])
        self.assertEqual(element.var('sourceDirectory'), os.path.dirname(name))
        self.assertRaises(ElementInvalidVarError, element.var, "dummyVar")

    def testElementTags(self):
        """
        Test that the Element tags are set properly.
        """
        element = Element.create(Path(self.__turntableFile))
        self.assertRaises(ElementInvalidTagError, element.tag, "dummyTag")

    def testElementRegistration(self):
        """
        Test that you can register a new element.
        """
        class DummyElement(FileElement):
            @classmethod
            def test(cls, path, parentElement):
                return False

        Element.register("dummy", DummyElement)
        self.assertIn("dummy", Element.registeredNames())
        self.assertIn(DummyElement, Element.registeredSubclasses("file"))
        self.assertIn(DummyElement, Element.registeredSubclasses(FsElement))

    def testElementClone(self):
        """
        Test that cloning elements works.
        """
        element = Element.create(Path(self.__turntableFile))
        clone = element.clone()
        self.assertCountEqual(element.varNames(), clone.varNames())
        self.assertCountEqual(element.contextVarNames(), clone.contextVarNames())
        self.assertCountEqual(element.tagNames(), clone.tagNames())

    def testElementJson(self):
        """
        Test that you can convert a element to json and back.
        """
        element = Element.create(Path(self.__turntableFile))
        jsonResult = element.toJson()
        elementResult = Element.createFromJson(jsonResult)
        self.assertCountEqual(element.varNames(), elementResult.varNames())
        self.assertCountEqual(element.contextVarNames(), elementResult.contextVarNames())
        self.assertCountEqual(element.tagNames(), elementResult.tagNames())

    def testElementCreate(self):
        """
        Test that you can create a element with a specific type.
        """
        element = FsElement.createFromPath(self.__turntableFile, "exr")
        self.assertIsInstance(element, ExrElement)

    def testPath(self):
        """
        Test Path functions.
        """
        path = Path(self.__turntableFile)
        self.assertEqual(path.stat().st_size, 5430903)
        self.assertEqual(path.name, "RND_ass_lookdev_default_beauty_tt.1001.exr")
        self.assertTrue(path.exists())
        path = Path("/")
        self.assertEqual(path.name, os.sep)


if __name__ == "__main__":
    unittest.main()
