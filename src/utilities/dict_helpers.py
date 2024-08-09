def get_nth_dict_key(dictionary, n=0):
    if n < 0:
        n += len(dictionary)
    for i, item in enumerate(dictionary.items()):
        if i == n:
            return item[0]
    raise IndexError("dictionary index out of range")


def get_nth_dict_value(dictionary, n=0):
    if n < 0:
        n += len(dictionary)
    for i, item in enumerate(dictionary.items()):
        if i == n:
            return item[1]
    raise IndexError("dictionary index out of range")


def get_nth_dict_key_and_val(dictionary, n=0) -> tuple:
    if n < 0:
        n += len(dictionary)
    for i, item in enumerate(dictionary.items()):
        if i == n:
            return item[0], item[1]
    raise IndexError("dictionary index out of range")
