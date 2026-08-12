class DefaultBodyColors:  # Sets colorization for application use
    def __init__(self):  # Initialize the values for color
        pass
    CCYN = '\033[96m'
    CRED = '\033[91m'
    CGRN = '\033[92m'
    CYLW = '\033[93m'
    CBLU = '\033[94m'
    CPRP = '\033[95m'
    CEND = '\033[0m'
    CFON = '\33[5m'

    @classmethod
    def use(cls, code):
        """Return the escape sequence for a short code (e.g. 'RED', 'GRN')."""
        return getattr(cls, 'C' + str(code).upper(), cls.CEND)
