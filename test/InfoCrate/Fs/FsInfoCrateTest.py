import os
import unittest
from ...BaseTestCase import BaseTestCase
from kombi.InfoCrate import InfoCrate
from kombi.InfoCrate.Fs import FsInfoCrate
from kombi.InfoCrate.Fs import FileInfoCrate
from kombi.InfoCrate.PathHolder import PathHolder
from kombi.InfoCrate.Fs.Render import ExrRenderInfoCrate
from kombi.InfoCrate.Fs.Image import ExrInfoCrate
from kombi.InfoCrate.InfoCrate import InfoCrateInvalidVarError
from kombi.InfoCrate.InfoCrate import InfoCrateInvalidTagError

class FsInfoCrateTest(BaseTestCase):
    """Test Directory infoCrate."""

    __dir = os.path.join(BaseTestCase.dataTestsDirectory(), "glob")
    __turntableFile = os.path.join(__dir, "images", "RND_ass_lookdev_default_beauty_tt.1001.exr")
    __shotRenderFile = os.path.join(__dir, "images", "RND-TST-SHT_lighting_beauty_sr.1001.exr")

    def testFsInfoCrate(self):
        """
        Test that the fs infoCrate test works.
        """
        pathHolder = PathHolder(self.__dir)
        self.assertTrue(FsInfoCrate.test(pathHolder, None))

        notAPathHolder = {}
        self.assertFalse(FsInfoCrate.test(notAPathHolder, None))

    def testFsInfoCrateGlob(self):
        """
        Test the glob functionality.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__dir))
        infoCrates = infoCrate.glob()
        result = self.collectFiles(self.__dir)
        result = list(map(lambda x: x.rstrip("/"), result))
        infoCratePaths = list(map(lambda x: x.var("filePath"), infoCrates))
        self.assertCountEqual(result, infoCratePaths)

        infoCrates = infoCrate.glob(filterTypes=["turntable", "shotRender"])
        infoCratePaths = list(map(lambda x: x.var("filePath"), infoCrates))
        self.assertCountEqual(infoCratePaths, [self.__turntableFile, self.__shotRenderFile])

        infoCrates = infoCrate.glob(filterTypes=[ExrRenderInfoCrate])
        infoCratePaths = list(map(lambda x: x.var("filePath"), infoCrates))
        result = self.collectFiles(self.__dir, "RND*.exr")
        result = list(map(lambda x: x.rstrip("/"), result))
        self.assertCountEqual(result, infoCratePaths)

        infoCrates = infoCrate.glob(filterTypes=['exr'])
        infoCratePaths = list(map(lambda x: x.var("filePath"), infoCrates))
        result = self.collectFiles(self.__dir, "*.exr")
        result = list(map(lambda x: x.rstrip("/"), result))
        self.assertCountEqual(result, infoCratePaths)

        infoCrate = InfoCrate.create(PathHolder(self.__turntableFile))
        otherInfoCrates = infoCrate.globFromParent(filterTypes=[ExrRenderInfoCrate])
        infoCratePaths = list(map(lambda x: x.var("filePath"), infoCrates))
        otherInfoCratePaths = list(map(lambda x: x.var("filePath"), otherInfoCrates))
        self.assertCountEqual(infoCratePaths, otherInfoCratePaths)

    def testPathVariables(self):
        """
        Test that the infoCrate variables are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__turntableFile))
        name, ext = os.path.splitext(self.__turntableFile)
        self.assertEqual(infoCrate.var('filePath'), self.__turntableFile)
        self.assertEqual(infoCrate.var('ext'), ext.lstrip("."))
        self.assertEqual(infoCrate.var('baseName'), os.path.basename(self.__turntableFile))
        self.assertEqual(infoCrate.var('name'), os.path.basename(name).split(".")[0])
        self.assertEqual(infoCrate.var('sourceDirectory'), os.path.dirname(name))
        self.assertRaises(InfoCrateInvalidVarError, infoCrate.var, "dummyVar")

    def testInfoCrateTags(self):
        """
        Test that the InfoCrate tags are set properly.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__turntableFile))
        self.assertRaises(InfoCrateInvalidTagError, infoCrate.tag, "dummyTag")

    def testInfoCrateRegistration(self):
        """
        Test that you can register a new infoCrate.
        """
        class DummyInfoCrate(FileInfoCrate):
            @classmethod
            def test(cls, pathHolder, parentInfoCrate):
                return False

        InfoCrate.register("dummy", DummyInfoCrate)
        self.assertIn("dummy", InfoCrate.registeredNames())
        self.assertIn(DummyInfoCrate, InfoCrate.registeredSubclasses("file"))
        self.assertIn(DummyInfoCrate, InfoCrate.registeredSubclasses(FsInfoCrate))

    def testInfoCrateClone(self):
        """
        Test that cloning infoCrates works.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__turntableFile))
        clone = infoCrate.clone()
        self.assertCountEqual(infoCrate.varNames(), clone.varNames())
        self.assertCountEqual(infoCrate.contextVarNames(), clone.contextVarNames())
        self.assertCountEqual(infoCrate.tagNames(), clone.tagNames())

    def testInfoCrateJson(self):
        """
        Test that you can convert a infoCrate to json and back.
        """
        infoCrate = InfoCrate.create(PathHolder(self.__turntableFile))
        jsonResult = infoCrate.toJson()
        infoCrateResult = InfoCrate.createFromJson(jsonResult)
        self.assertCountEqual(infoCrate.varNames(), infoCrateResult.varNames())
        self.assertCountEqual(infoCrate.contextVarNames(), infoCrateResult.contextVarNames())
        self.assertCountEqual(infoCrate.tagNames(), infoCrateResult.tagNames())

    def testInfoCrateCreate(self):
        """
        Test that you can create a infoCrate with a specific type.
        """
        infoCrate = FsInfoCrate.createFromPath(self.__turntableFile, "exr")
        self.assertIsInstance(infoCrate, ExrInfoCrate)

    def testPathHolder(self):
        """
        Test PathHolder functions.
        """
        pathHolder = PathHolder(self.__turntableFile)
        self.assertEqual(pathHolder.size(), 5430903)
        self.assertEqual(pathHolder.name(), "RND_ass_lookdev_default_beauty_tt.1001")
        self.assertTrue(pathHolder.exists())
        pathHolder = PathHolder("/")
        self.assertEqual(pathHolder.baseName(), os.sep)


if __name__ == "__main__":
    unittest.main()
