class DentalCaseError(Exception):
    """
    Base class for dental case domain errors.
    """


class DashboardMetricsError(DentalCaseError):
    """
    Raised when the production indicators cannot be calculated.

    The presentation layer catches this error to show a message
    to the user instead of breaking the dashboard.
    """
