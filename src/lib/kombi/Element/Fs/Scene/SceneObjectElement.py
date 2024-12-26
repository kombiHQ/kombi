from ...Element import Element

class SceneObjectElement(Element):
    """
    Abstracted scene object element.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a scene object.
        """
        super(SceneObjectElement, self).__init__(*args, **kwargs)

        self.setVar('category', 'sceneObject')

        # setting icon
        self.setTag('icon', 'icons/elements/scene.png')

    def select(self):
        """
        Re-implementation: It should select the object in scene.
        """
        raise NotImplementedError
