import yaml


def obter_dados_config():
    with open('config.yml') as file:
        config = yaml.safe_load(file)

    return config
