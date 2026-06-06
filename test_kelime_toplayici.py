import pytest
from kelime_toplayici import temizle_kelime

def test_TC_B06():
    result = temizle_kelime("merhaba")
    assert result == "merhaba"

def test_TC_B07():
    result = temizle_kelime("TüRkÇe-Dil")
    assert result == "türkçe-dil"

def test_TC_B08():
    result = temizle_kelime(" Selam123!@# ")
    assert result == "selam"