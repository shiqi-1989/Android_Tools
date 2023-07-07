import os

# shell = 'pyinstaller --add-data "config.ini:." --add-data "xiongmao.webp:." -F -w -n ' \
#         'AndroidTools main.py -y'
shell = 'pyinstaller --add-data "config.ini:." --add-data "owl_512.png:." --add-data "owl.icns:." -i owl.icns -n ' \
        'AndroidTools -w -D main.py -y'
os.system(shell)
