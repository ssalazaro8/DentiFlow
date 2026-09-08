class ReportError(Exception):
    """
    Base class for operational report errors.
    """


class ReportGenerationError(ReportError):
    """
    Raised when a report cannot be generated.

    The presentation layer catches this error to show a message
    instead of breaking the page.
    """
