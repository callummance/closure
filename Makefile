
.PHONY: clean default

default: tray.svg

tray.scad: gen_mobo_tray.py Pipfile motherboard_layouts.json
	pipenv run python3 gen_mobo_tray.py

tray.svg: tray.scad
	openscad -o tray.svg --export-format svg ./tray.scad

clean:
	rm ./*.scad ./*.svg