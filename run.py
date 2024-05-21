import subprocess

# shell = 'pyinstaller --add-data "config.ini:." --add-data "xiongmao.webp:." -F -w -n ' \
#         'AndroidTools main.py -y'
# shell = 'pyinstaller --add-data "config.ini:." --add-data "owl_256.png:."  --add-data "owl.icns:." -i owl.icns -n ' \
#         'AndroidTools -w -D main.py -y'
shell = 'pyinstaller --add-data "config.ini:." --add-data "owl_256.png:." --add-data "logo48.png:."  --add-data ' \
        '"owl.icns:." -i owl.icns -n AndroidTools -w -D main.py -y'
subprocess.run(shell)
