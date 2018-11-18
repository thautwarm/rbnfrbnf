from typing import NamedTuple

Identifier = object





def make_node(*, id: Identifier, text: str, title: str, color: str, size: int):
    return {
        'id': id,
        'text': text,
        'title': title,
        'color': color,
        'size': size
    }


def make_link(*, start: Identifier, end: Identifier, value: int):
    return {'source': start, 'target': end, 'value': value}
