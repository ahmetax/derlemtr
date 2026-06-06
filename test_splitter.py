import pytest
from unittest.mock import mock_open, patch
import splitter

def test_TC_W01(monkeypatch):
    monkeypatch.setattr(splitter, 'NUM_CHUNKS', 10)
    monkeypatch.setattr(splitter, 'INPUT_FILE', 'mock_input.txt')
    
    mock_data = "line\n" * 25
    
    with patch('builtins.open', mock_open(read_data=mock_data)) as m:
        splitter.split_file()
        
        written_chunks = [call_obj.args[0] for call_obj in m().writelines.call_args_list]
        
        for i in range(9):
            assert len(written_chunks[i]) == 2

def test_TC_W02(monkeypatch):
    monkeypatch.setattr(splitter, 'NUM_CHUNKS', 10)
    monkeypatch.setattr(splitter, 'INPUT_FILE', 'mock_input.txt')
    
    mock_data = "line\n" * 25
    
    with patch('builtins.open', mock_open(read_data=mock_data)) as m:
        splitter.split_file()
        
        written_chunks = [call_obj.args[0] for call_obj in m().writelines.call_args_list]
        
        assert len(written_chunks[9]) == 7

def test_TC_B01(monkeypatch):
    monkeypatch.setattr(splitter, 'NUM_CHUNKS', 10)
    monkeypatch.setattr(splitter, 'INPUT_FILE', 'mock_input.txt')
    
    mock_data = "" 
    
    with patch('builtins.open', mock_open(read_data=mock_data)) as m:
        splitter.split_file()
        written_chunks = [call_obj.args[0] for call_obj in m().writelines.call_args_list]
        
        assert len(written_chunks) == 10
        for chunk in written_chunks:
            assert len(chunk) == 0

def test_TC_B02(monkeypatch):
    monkeypatch.setattr(splitter, 'NUM_CHUNKS', 1)
    monkeypatch.setattr(splitter, 'INPUT_FILE', 'mock_input.txt')
    
    mock_data = "line\n" * 100 
    
    with patch('builtins.open', mock_open(read_data=mock_data)) as m:
        splitter.split_file()
        written_chunks = [call_obj.args[0] for call_obj in m().writelines.call_args_list]
        
        assert len(written_chunks) == 1
        assert len(written_chunks[0]) == 100

def test_TC_B03(monkeypatch):
    monkeypatch.setattr(splitter, 'NUM_CHUNKS', 0)
    monkeypatch.setattr(splitter, 'INPUT_FILE', 'mock_input.txt')

    mock_data = "line\n" * 100
    m = mock_open(read_data=mock_data)

    with patch('builtins.open', m):
        with pytest.raises(ZeroDivisionError):
            splitter.split_file()

def test_TC_B04(monkeypatch):
    monkeypatch.setattr(splitter, 'NUM_CHUNKS', 10)
    monkeypatch.setattr(splitter, 'INPUT_FILE', 'mock_input.txt')
    
    mock_data = "line\n" * 5
    
    with patch('builtins.open', mock_open(read_data=mock_data)) as m:
        splitter.split_file()
        written_chunks = [call_obj.args[0] for call_obj in m().writelines.call_args_list]
        
        for i in range(9):
            assert len(written_chunks[i]) == 0
        assert len(written_chunks[9]) == 5

def test_TC_B05(monkeypatch):
    monkeypatch.setattr(splitter, 'NUM_CHUNKS', 10)
    monkeypatch.setattr(splitter, 'INPUT_FILE', 'mock_input.txt')
    
    mock_data = "line\n" * 10 
    
    with patch('builtins.open', mock_open(read_data=mock_data)) as m:
        splitter.split_file()
        written_chunks = [call_obj.args[0] for call_obj in m().writelines.call_args_list]
        
        assert len(written_chunks) == 10
        for chunk in written_chunks:
            assert len(chunk) == 1