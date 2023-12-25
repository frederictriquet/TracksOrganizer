class Conf(object):
    conf_data = {}

    @staticmethod
    def load(yaml_filename: str):
        import yaml
        with open(yaml_filename) as file:
            stringdata = yaml.safe_load(file)
            Conf.conf_data = stringdata

    @staticmethod
    def get_genre(genre: str) -> str:
        if genre not in Conf.conf_data['genres']:
            return f'{genre}?'
        return Conf.conf_data['genres'][genre]

if __name__ == '__main__':
    Conf.load('conf.yml')
