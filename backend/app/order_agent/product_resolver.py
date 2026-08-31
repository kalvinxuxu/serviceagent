from .repositories import REPOSITORY
def resolve(description):
    matches = REPOSITORY.find_product(description)
    return matches[0] if len(matches) == 1 else None
