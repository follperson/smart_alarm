
class PlaylistNotFound(Exception):
    """ Couldnt find that, sport. give it another go."""
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class EmptyTable(Exception):
    """ Table is empty """
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InvalidInputError(Exception):
    """ Table is empty """
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)