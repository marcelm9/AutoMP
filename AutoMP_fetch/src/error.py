def missing_item(item: str):
    return f"missing item: '{item}'"


def type_error(item: str, expected: str, received: str):
    return f"wrong item type for '{item}': expected '{expected}', received '{received}'"


def value_error(item: str, received: str, message: str):
    return f"wrong item value for '{item}': received '{received}', message: '{message}'"


def constraint_error(item: str, constraint: str, message: str):
    return f"constraint error for '{item}' ({constraint}): {message}"


def missing_dependency(item: str, dependent_on: str):
    return f"missing dependency: item '{item}' depends on missing item '{dependent_on}'"
