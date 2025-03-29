import os
import unittest
from ..BaseTestCase import BaseTestCase
from kombi.Template import Template
from kombi.Template import TemplateRequiredPathNotFoundError, TemplateVarNotFoundError
from kombi.Element.Fs import FsElement

class TemplateTest(BaseTestCase):
    """Test Template element."""

    __file = os.path.join(BaseTestCase.dataTestsDirectory(), 'RND-TST-SHT_lighting_beauty_sr.1001.exr')

    def testNestProcedureTemplateSimple(self):
        """
        Test simple nested procedures in the template.
        """
        element = FsElement.createFromPath(self.__file)
        value = "/a/b/c/(dirname(dirname '/d/e/f'))/(newver <parent>)/{name}.(pad {frame} 6).{ext}"
        result = Template('!kt ' + value).valueFromElement(element)
        self.assertEqual(
            os.path.normpath(result),
            os.path.normpath('/a/b/c/d/v001/RND-TST-SHT_lighting_beauty_sr.001001.exr')
        )

    def testNestProcedureTemplateSimpleWithQuote(self):
        """
        Test simple nested procedures in the template.
        """
        element = FsElement.createFromPath(self.__file)
        value = "/a/b/c/(concat '(teste(bla - blaa))' '_foo')/(newver <parent>)/{name}.(pad {frame} 6).{ext}"
        result = Template('!kt ' + value).valueFromElement(element)
        self.assertEqual(
            os.path.normpath(result),
            os.path.normpath('/a/b/c/(teste(bla - blaa))_foo/v001/RND-TST-SHT_lighting_beauty_sr.001001.exr')
        )

    def testNestProcedureTemplateMultiple(self):
        """
        Test multiple nested procedures in the template.
        """
        element = FsElement.createFromPath(self.__file)
        value = "/a/b/c/(concat (dirname(dirname (dirname '/d/e/f/g'))) '_' (dirname (dirname {var})))/(newver <parent>)/{name}.(pad {frame} 6).{ext}"
        result = Template('!kt ' + value).valueFromElement(
            element,
            extraVars={
                'var': 'h/j/l'
            }
        )
        self.assertEqual(
            os.path.normpath(result),
            os.path.normpath('/a/b/c/d_h/v001/RND-TST-SHT_lighting_beauty_sr.001001.exr')
        )

    def testNestProcedureTemplateMultipleAssignToken(self):
        """
        Test multiple nested procedures by assigning the result to a token in the template.
        """
        element = FsElement.createFromPath(self.__file)
        value = "/a/b/c/(concat (dirname(dirname (dirname '/d/e/f/g'))) '_' (dirname (dirname {var})) as <result>)/(newver <parent>)/(concat <result> '_' 'foo')/{name}.(pad {frame} 6).{ext}"
        result = Template('!kt ' + value).valueFromElement(
            element,
            extraVars={
                'var': 'h/j/l'
            }
        )
        self.assertEqual(
            os.path.normpath(result),
            os.path.normpath('/a/b/c/d_h/v001/d_h_foo/RND-TST-SHT_lighting_beauty_sr.001001.exr')
        )

    def testNestProcedureTemplateArithmetic(self):
        """
        Test arithmetic nested procedures in the template.
        """
        element = FsElement.createFromPath(self.__file)
        value = "/a/b/c/({a} + (sum {b} 2))/(newver <parent>)/{name}.(pad {frame} 6).{ext}"
        result = Template('!kt ' + value).valueFromElement(
            element,
            extraVars={
                'a': 2,
                'b': 3
            }
        )
        self.assertEqual(
            os.path.normpath(result),
            os.path.normpath('/a/b/c/7/v001/RND-TST-SHT_lighting_beauty_sr.001001.exr')
        )

    def testTemplate(self):
        """
        Test that the Template works properly.
        """
        element = FsElement.createFromPath(self.__file)
        value = '(dirname {filePath})/(newver <parent>)/{name}.(pad {frame} 6).{ext}'
        result = Template('!kt ' + value).valueFromElement(element)
        self.assertEqual(
            os.path.normpath(result),
            os.path.join(
                BaseTestCase.dataTestsDirectory(),
                'v003',
                'RND-TST-SHT_lighting_beauty_sr.001001.exr'
            )
        )

    def testArithmeticOperations(self):
        """
        Test support for arithmetic operations.
        """
        self.assertEqual(
            Template("!kt /({x} + 10 as <result>)/(<result> - 10)/(4.0 / {y})").value(
                {
                    'x': 5,
                    'y': 2
                }
            ),
            "/15/5/2"
        )

    def testSingleQuote(self):
        """
        Test that the template can return a value with single quote.
        """
        def __testSingleQuoteProcedure(*args):
            return ' '.join(args)
        Template.registerProcedure('testsinglequote', __testSingleQuoteProcedure)

        inputValue = "my 'random\' value'"
        self.assertEqual(
            Template("!kt /(testsinglequote {foo} '2' 3)/").value({'foo': inputValue}),
            "/{} 2 3/".format(inputValue)
        )

    def testAssignToToken(self):
        """
        Test that the template can assign the return of procedure to a token.
        """
        def __assignTokenResult(*args):
            return ' '.join(args)
        Template.registerProcedure('assigntokenresult', __assignTokenResult)

        self.assertEqual(
            Template("!kt /(assigntokenresult foo as <test>)/a/{someVar}/(assigntokenresult foo2 as <test2>)_<test>_x_{someVar}_x_<test2>/b/<test>/c/<test2>_{someVar}").value({'someVar': 'var'}),
            "/foo/a/var/foo2_foo_x_var_x_foo2/b/foo/c/foo2_var"
        )

    def testTemplateRequiredPath(self):
        """
        Test that the required path check works.
        """
        value = '{}/!badPath/test.exr'.format(BaseTestCase.dataTestsDirectory())
        self.assertRaises(TemplateRequiredPathNotFoundError, Template('!kt ' + value).value)
        value = '{}/!glob'.format(BaseTestCase.dataTestsDirectory())
        result = Template('!kt ' + value).value()
        self.assertEqual(result, os.path.join(BaseTestCase.dataTestsDirectory(), 'glob'))

    def testTemplateVariable(self):
        """
        Test that you can pass variables to the template properly.
        """
        variables = {'otherVar': 'value'}
        self.assertRaises(TemplateVarNotFoundError, Template('!kt {var}').value, variables)
        variables['var'] = 'test'
        self.assertEqual(Template('!kt {var}').value(variables), 'test')


if __name__ == "__main__":
    unittest.main()
