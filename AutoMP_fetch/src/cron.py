import re
import time
from datetime import datetime


def validate_cron(cron_string):
    """
    Validates a cron job string with 5 values using regex.

    Args:
        cron_string (str): A string containing 5 space-separated values representing:
                          minute, hour, day of month, month, day of week

    Returns:
        bool: True if the cron string is valid, False otherwise
        str: Error message if invalid, empty string if valid
    """
    # Split the string into components
    components = cron_string.strip().split()

    # Check if there are exactly 5 components
    if len(components) != 5:
        return False, f"Expected 5 components, got {len(components)}"

    # Define regex patterns for each component
    patterns = [
        r"^(\*|([0-9]|[1-5][0-9])(-([0-9]|[1-5][0-9]))?(,([0-9]|[1-5][0-9])(-([0-9]|[1-5][0-9]))?)*)(\/[1-9][0-9]*)?$",  # minute: 0-59
        r"^(\*|([0-9]|1[0-9]|2[0-3])(-([0-9]|1[0-9]|2[0-3]))?(,([0-9]|1[0-9]|2[0-3])(-([0-9]|1[0-9]|2[0-3]))?)*)(\/[1-9][0-9]*)?$",  # hour: 0-23
        r"^(\*|([1-9]|[12][0-9]|3[01])(-([1-9]|[12][0-9]|3[01]))?(,([1-9]|[12][0-9]|3[01])(-([1-9]|[12][0-9]|3[01]))?)*)(\/[1-9][0-9]*)?$",  # day of month: 1-31
        r"^(\*|([1-9]|1[0-2])(-([1-9]|1[0-2]))?(,([1-9]|1[0-2])(-([1-9]|1[0-2]))?)*)(\/[1-9][0-9]*)?$",  # month: 1-12
        r"^(\*|([0-7])(-([0-7]))?(,([0-7])(-([0-7]))?)*)(\/[1-9][0-9]*)?$",  # day of week: 0-7
    ]

    # Validate each component with its corresponding regex pattern
    for i, (component, pattern) in enumerate(zip(components, patterns)):
        if not re.match(pattern, component):
            return False, f"Invalid format in component {i + 1}: {component}"

    return True, ""


def wait_for_datetime(target_datetime: datetime):
    delta = target_datetime - datetime.now()
    if delta.total_seconds() < 0:
        return
    time.sleep(delta.total_seconds())


def __run_tests():
    tests = [
        # Test cases for validate_cron function
        ("* * * * *", True, ""),  # Valid: every minute
        ("0 0 1 1 *", True, ""),  # Valid: midnight on January 1st
        ("59 23 31 12 7", True, ""),  # Valid: last minute of the year
        ("*/15 * * * *", True, ""),  # Valid: every 15 minutes
        ("0 12 1-15 * 1-5", True, ""),  # Valid: weekdays, first half of the month
        ("5,10,15 * * * *", True, ""),  # Valid: at 5, 10, and 15 minutes past the hour
        ("0-5 * * * *", True, ""),  # Valid: first 5 minutes of each hour
        (
            "60 * * * *",
            False,
            "Invalid format in component 1: 60",
        ),  # Invalid: minute out of range
        (
            "* 24 * * *",
            False,
            "Invalid format in component 2: 24",
        ),  # Invalid: hour out of range
        (
            "* * 32 * *",
            False,
            "Invalid format in component 3: 32",
        ),  # Invalid: day of month out of range
        (
            "* * * 13 *",
            False,
            "Invalid format in component 4: 13",
        ),  # Invalid: month out of range
        (
            "* * * * 8",
            False,
            "Invalid format in component 5: 8",
        ),  # Invalid: day of week out of range
    ]

    for test in tests:
        cron, expected_valid, expected_error = test
        valid, error = validate_cron(cron)
        assert valid == expected_valid, (
            f"validate_cron({cron}) should return {expected_valid}, but got {valid}"
        )
        assert error == expected_error, (
            f"validate_cron({cron}) should return error '{expected_error}', but got '{error}'"
        )
