def bubble_sort_dict(dictionary):
    for i in range(len(dictionary)):
        for j in (range(len(dictionary) - 1 - i)):
            if next(iter(dictionary[j].values())) > next(iter(dictionary[j + 1].values())):
                temp = dictionary[j]
                dictionary[j] = dictionary[j + 1]
                dictionary[j + 1] = temp

    return dictionary
