from .articles import TestArticle
from .editors import TestEditor
from .modules import TestModule
from .wines import TestWine

if __name__ == "__main__":
    TestArticle().run()
    TestEditor().run()
    TestModule().run()
    TestWine().run()