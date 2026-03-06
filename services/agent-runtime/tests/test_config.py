import os
import pytest
from config.settings import load_config, get_config, ConfigurationError

def test_load_default_config():
    config = load_config()
    assert config['environment'] == 'development'

def test_get_config_nested():
    url = get_config('tool_gateway.url')
    assert url == 'http://localhost:8080'

def test_get_config_default():
    value = get_config('non_existent.key', 'default_value')
    assert value == 'default_value'

def test_load_specific_env():
    print("Current working directory:", os.getcwd())
    print("Config files in directory:", os.listdir(os.path.join(os.getcwd(), 'config')))
    
    os.environ['AGENT_ENV'] = 'staging'
    try:
        config = load_config()
        print("Loaded config:", config)
        assert config['environment'] == 'staging'
    finally:
        # Clean up environment variable
        del os.environ['AGENT_ENV']

def test_config_file_not_found():
    with pytest.raises(ConfigurationError):
        load_config('non_existent_env')
