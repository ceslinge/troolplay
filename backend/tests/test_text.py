import pytest

from backend.text import of_name


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Gorrik", "de Gorrik"),
        ("Ombre", "d’Ombre"),
        ("Élodie", "d’Élodie"),
        ("Ysolde", "d’Ysolde"),
        ("Yugo", "de Yugo"),
        ("Hilda", "de Hilda"),
    ],
)
def test_the_name_is_elided_before_a_vowel(name: str, expected: str) -> None:
    assert of_name(name) == expected
