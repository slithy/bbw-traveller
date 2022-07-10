import draconic.exceptions

from cogst5.models.errors import BambleweenyException


class EvaluationError(BambleweenyException, draconic.exceptions.DraconicException):
    """Raised when a cvar evaluation causes an error."""

    def __init__(self, original, expression=None):
        super().__init__(f"Error evaluating expression: {original}")
        self.original = original
        self.expression = expression


class FunctionRequiresCharacter(BambleweenyException):
    """
    Raised when a function that requires a character is called without one.
    """

    def __init__(self, msg=None):
        super().__init__(msg or "This alias requires an active character.")


class CollectionNotFound(BambleweenyException):
    """Raised when a WorkshopCollection is not found."""

    def __init__(self, msg=None):
        super().__init__(msg or "The specified collection was not found.")


class CollectableNotFound(BambleweenyException):
    """Raised when a collectable (alias/snippet) is not found in a collection."""

    def __init__(self, msg=None):
        super().__init__(msg or "The specified object was not found.")


class AliasNameConflict(BambleweenyException):
    """Unable to run command because two aliases share the same name."""

    pass


class CollectableRequiresLicenses(BambleweenyException):
    """Unable to invoke collectable because one or more licenses are missing"""

    def __init__(self, entities, collectable, has_connected_ddb):
        super().__init__(f"insufficient license to view {', '.join(e.name for e in entities)}")
        self.entities = entities
        self.collectable = collectable
        self.has_connected_ddb = has_connected_ddb
