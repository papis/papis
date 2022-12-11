PDFJS_URL = https://github.com/mozilla/pdf.js/releases/download/v3.1.81/pdfjs-3.1.81-legacy-dist.zip
#PDFJS_URL = https://github.com/mozilla/pdf.js/releases/download/v3.1.81/pdfjs-3.1.81-dist.zip
pdfjs/web pdfjs/build: pdfjs/pdfjs.zip
	cd pdfjs && unzip pdfjs.zip

pdfjs/pdfjs.zip: pdfjs.zip
	mkdir -p $(@D)
	mv $< $(@D)

pdfjs.zip:
	wget $(PDFJS_URL) -O $@

clean:
	rm -r pdfjs
