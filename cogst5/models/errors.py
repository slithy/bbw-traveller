class BambleweenyException(Exception):
    """A base exception class."""

    def __init__(self, msg):
        super().__init__(msg)


class NoCharacter(BambleweenyException):
    """Raised when a user has no active character."""

    def __init__(self):
        super().__init__("You have no character active.")


class NoActiveBrew(BambleweenyException):
    """Raised when a user has no active homebrew of a certain type."""

    def __init__(self):
        super().__init__("You have no homebrew of this type active.")


class ExternalImportError(BambleweenyException):
    """Raised when something fails to import."""

    def __init__(self, msg):
        super().__init__(msg)


class InvalidArgument(BambleweenyException):
    """Raised when an argument is invalid."""

    pass


class NotAllowed(BambleweenyException):
    """Raised when a user tries to do something they are not allowed to do by role or dependency."""

    pass


class OutdatedSheet(BambleweenyException):
    """Raised when a feature is used that requires an updated sheet."""

    def __init__(self, msg=None):
        super().__init__(msg or "This command requires an updated character sheet. Try running `!update`.")


class InvalidSaveType(BambleweenyException):
    def __init__(self):
        super().__init__("Invalid save type.")


class ConsumableException(BambleweenyException):
    """A base exception for consumable exceptions to stem from."""

    pass


class CounterOutOfBounds(ConsumableException):
    """Raised when a counter is set to a value out of bounds."""

    def __init__(self, msg=None):
        super().__init__(msg or "The new value is out of bounds.")


class NoReset(ConsumableException):
    """Raised when a consumable without a reset is reset."""

    def __init__(self):
        super().__init__("The counter does not have a reset value.")


class InvalidSpellLevel(ConsumableException):
    """Raised when a spell level is invalid."""

    def __init__(self):
        super().__init__("The spell level is invalid.")


class SelectionException(BambleweenyException):
    """A base exception for message awaiting exceptions to stem from."""

    pass


class NoSelectionElements(SelectionException):
    """Raised when get_selection() is called with no choices."""

    def __init__(self, msg=None):
        super().__init__(msg or "There are no choices to select from.")


class SelectionCancelled(SelectionException):
    """Raised when get_selection() is cancelled or times out."""

    def __init__(self):
        super().__init__("Selection timed out or was cancelled.")
