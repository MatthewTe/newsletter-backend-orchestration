from ast import List

from nameparser import HumanName

def parse_author_dict(authors: List) -> List:
    """Parses the RSS feeds author dictionary to make it a data structure that is compatable with the Django Model used to represent
    People. Assumes the author dict is in the format:

    [{'name': 'Emma Ashford and Matthew Kroenig'}] and gets converted to the format:
    
    [
        {'firstname': 'Emma', 'lastname': 'Ashford'}
        {'firstname': 'Matthew', 'lastname': 'Kroenig'}
    ]
    """
    # Creating list to populate with correct author name structures:
    author_lst = []

    # Iterating through the provided list of dict:
    for author_dict in authors:
        # Splitting the single dict string into a list of individual names:
        names = author_dict['name'].split(' and ')
        

        # For each name in the split list, we create a NameParser object to abstract away the regex of determining first and
        # last names:
        for name_str in names:
            name = HumanName(name_str)

            author_lst.append(name.as_dict())
    

    return author_lst

def parse_tags_dict(tags: List) -> List:
    # TODO: Implement this function and then implement them in the extract_fields_from_xml_entry function.
    pass