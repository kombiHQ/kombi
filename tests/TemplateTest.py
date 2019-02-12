import os
import unittest
from .BaseTestCase import BaseTestCase
from chilopoda.Template import Template
from chilopoda.Template import TemplateRequiredPathNotFoundError, TemplateVarNotFoundError
from chilopoda.Crawler.Fs import FsPath

class TemplateTest(BaseTestCase):
    """Test Template crawler."""

    __file = os.path.join(BaseTestCase.dataDirectory(), 'RND-TST-SHT_lighting_beauty_sr.1001.exr')

    def testTemplate(self):
        """
        Test that the Template works properly.
        """
        crawler = FsPath.createFromPath(self.__file)
        value = '(dirname {filePath})/(newver <parent>)/{name}.(pad {frame} 6).{ext}'
        result = Template(value).valueFromCrawler(crawler)
        self.assertEqual(
            os.path.normpath(result),
            os.path.join(
                BaseTestCase.dataDirectory(),
                'v003',
                'RND-TST-SHT_lighting_beauty_sr.001001.exr'
            )
        )

    def testArithmeticOperations(self):
        """
        Test support for arithmetic operations.
        """
        self.assertEqual(
            Template("/({x} + 10 as <result>)/(<result> - 10)/(4.0 / {y})").value(
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
            Template("/(testsinglequote {foo} '2' 3)/").value({'foo': inputValue}),
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
            Template("/(assigntokenresult foo as <test>)/a/{someVar}/(assigntokenresult foo2 as <test2>)_<test>_x_{someVar}_x_<test2>/b/<test>/c/<test2>_{someVar}").value({'someVar': 'var'}),
            "/foo/a/var/foo2_foo_x_var_x_foo2/b/foo/c/foo2_var"
        )

    def testTemplateRequiredPath(self):
        """
        Test that the required path check works.
        """
        value = '{}/!badPath/test.exr'.format(BaseTestCase.dataDirectory())
        self.assertRaises(TemplateRequiredPathNotFoundError, Template(value).value)
        value = '{}/!glob'.format(BaseTestCase.dataDirectory())
        result = Template(value).value()
        self.assertEqual(result, os.path.join(BaseTestCase.dataDirectory(), 'glob'))

    def testTemplateVariable(self):
        """
        Test that you can pass variables to the template properly.
        """
        variables = {'otherVar': 'value'}
        self.assertRaises(TemplateVarNotFoundError, Template('{var}').value, variables)
        variables['var'] = 'test'
        self.assertEqual(Template('{var}').value(variables), 'test')


if __name__ == "__main__":
    unittest.main()
