from ...Element import Element

class SceneNodeElement(Element):
    """
    Abstracted scene node element.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a scene node object.
        """
        super(SceneNodeElement, self).__init__(*args, **kwargs)

        self.setVar('category', 'sceneNode')

        # this information should be overriding by derived classes.
        self.setVar('nodeCategory', 'undefined')

        # setting icon
        self.setTag('icon', 'icons/elements/sceneNode.png')

    def node(self):
        """
        For re-implementation: should return the real runtime object passed during construction.
        """
        raise NotImplementedError

    def select(self):
        """
        For re-implementation: It should select the object in scene.
        """
        raise NotImplementedError

    @classmethod
    def createFromName(cls, name):
        """
        For re-implementation: It should return an instance Element by based on the name through the factory (Element.create).
        """
        raise NotImplementedError
