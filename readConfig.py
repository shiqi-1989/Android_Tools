# coding=utf-8
import codecs
import configparser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
config_path = BASE_DIR / "config.ini"


class ReadConfig:
    def __init__(self):
        with open(config_path, encoding='utf-8') as fd:
            data = fd.read()
            #  remove BOM 检测及消除BOM
            if data[:3] == codecs.BOM_UTF8:
                data = data[3:]
                with codecs.open(config_path, "w") as file:
                    file.write(data)

        self.cf = configparser.ConfigParser()
        self.cf.read(config_path, encoding='utf-8')

    def get_history(self):
        value = self.cf.get("history", "record")
        return value

    def get_phone(self):
        value = self.cf.get("phone", "phone")
        return value

    def set_history(self, value):
        self.cf.set("history", "record", value)
        with open(config_path, 'w+', encoding='utf-8') as f:
            self.cf.write(f)

    def set_phone(self, value):
        self.cf.set("phone", "phone", value)
        with open(config_path, 'w+', encoding='utf-8') as f:
            self.cf.write(f)

    def get_iterm(self, option):
        items = self.cf.items(option)
        return dict(items)


if __name__ == '__main__':
    b = ReadConfig()
    phone = b.get_iterm('ssh')
    print(phone)
    # print(eval(phone['host']))
    print((phone['host'], phone['port']))
    # phone = b.get_phone()
    # print(phone)
    # print(type(phone))
    # print(eval(phone))
