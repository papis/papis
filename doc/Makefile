include sphinx.mk

readme_src = ../README.md
readme_dest = source/README.rst

#$(MAKECMDGOALS): $(readme_dest)

$(readme_dest): $(readme_src)
	pandoc $(readme_src) -o $(readme_dest)
