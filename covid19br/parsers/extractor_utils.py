import re


def match_object_from_regexp(regexp, objects):
    """Return the matching result for"""
    for obj in objects:
        result = regexp.findall(obj.text)
        if result:
            return result


def is_only_number(value):
    return re.compile("^([0-9.,]+)$").findall(value.strip())
