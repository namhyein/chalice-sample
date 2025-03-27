import random
import re
import string
import unicodedata


def make_slug(*args) -> str:
    args = list(filter(lambda x: x is not None, args))
    args = list(map(str, args))
    _id = " ".join(args)
    _id = _deaccent(_id)
    _id = re.sub(r"_|[^\s\w]", " ", _id)
    _id = re.sub(r"\s+", " ", _id)
    _id = _id.strip()
    _id = re.sub(r"\s", "-", _id)
    # Change alpha -> a, beta -> b, gamma -> g, ...
    german_alphabet = {
        "ß": "ss",
    }
    for k, v in german_alphabet.items():
        _id = _id.replace(k, v)
    return _id.lower().strip()


def replace_to_multi_language(document: dict, field: str, language: str) -> dict:
    if language not in ["ko", "ja"]:
        return document.get(language, {}).get(field, document.get(field))
    return document.get(field)


def generate_code(length: int) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _deaccent(text):
    """Remove letter accents from the given string.

    Parameters
    ----------
    text : str
        Input string.

    Returns
    -------
    str
        Unicode string without accents.

    Examples
    --------
    .. sourcecode:: pycon

        >>> from gensim.utils import deaccent
        >>> deaccent("Šéf chomutovských komunistů dostal poštou bílý prášek")
        u'Sef chomutovskych komunistu dostal postou bily prasek'

    """
    if not isinstance(text, str):
        # assume utf8 for byte strings, use default (strict) error handling
        text = text.decode("utf8")
    norm = unicodedata.normalize("NFD", text)
    result = "".join(ch for ch in norm if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", result)