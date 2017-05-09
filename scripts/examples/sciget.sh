#! /usr/bin/env bash

#link=ttp://sci-hub.io/10.1103/PhysRevLett.52.997
link=$1
output_pdf=output.pdf

if [[ ! ${link} =~ http* ]]; then
  link="http://sci-hub.io/$link"
fi

pdf_url=$(wget $link -qO - | grep -Eom1 'http://[^ ]+\.pdf')

echo
echo "pdf url = ${pdf_url}"
echo

if [[ -z ${pdf_url} ]]; then
  exit 1
fi

cat <<EOF


        Downloading...


EOF

wget ${pdf_url} -O ${output_pdf}

if ! file ${output_pdf} | grep PDF ; then
  echo "${output_pdf} is not a pdf, going to the website"
  (${BROWSER} ${pdf_url} &) &
fi

#vim-run: bash % 10.1103/PhysRevLett.52.997
#vim-run: bash % http://sci-hub.io/10.1103/PhysRevLett.52.997
