#!/bin/sh
name=scientific_writing

# Note: since Doconce syntax is demonstrated inside !bc/!ec
# blocks we need a few fixes

doconce format html $name --pygments-html-style=perldoc --html-solarized
mv -f $name.html ${name}_solarized.html
doconce format html $name --pygments-html-style=default
mv -f $name.html ${name}_plain.html

doconce format html $name --pygments-html-style=native
doconce slides_html $name reveal --html-slide-theme=darkgray
# fix:
doconce replace '\label{this:section}' 'label{this:section}' $name.html
doconce replace '\label{fig1}' 'label{fig1}' $name.html
doconce replace '\label{demo' 'label{demo' $name.html

doconce format pdflatex $name --minted-latex-style=trac
doconce ptex2tex $name envir=minted
pdflatex -shell-escape $name
mv -f $name.pdf ${name}_minted.pdf

doconce format pdflatex $name
doconce ptex2tex $name envir=ans:nt
pdflatex $name
mv -f $name.pdf ${name}_anslistings.pdf

doconce format sphinx $name
doconce sphinx_dir author="H. P. Langtangen" theme=pyramid $name
python automake_sphinx.py

doconce format pandoc $name  # Markdown (pandoc extended)
doconce format gwiki  $name  # Googlecode wiki

# These don't like slides with code after heading:
#doconce format rst    $name  # reStructuredText
#doconce format plain  $name  # plain, untagged text for email

pygmentize -l text -f html -o ${name}_doconce.html ${name}.do.txt

cp -r ${name}*.pdf *.md ${name}*.html reveal.js ../demos/slides/
cp -r sphinx-rootdir/_build/html ../demos/slides/sphinx

doconce format html sw_index.do.txt
cp sw_index.html ../demos/slides/index.html

doconce slides_html demo all
sh -x tmp_slides_html_all.sh
cp -r demo_*.html reveal.js deck.js csss fig ../demos/slides/demo/
cat > ../demos/slides/demo/index.html <<EOF
<h1>Autogenerated slide styles</h1>
<b>Note:</b> View these slides in Firefox (not Chrome).
<ul>
<li><a href="demo_reveal_beige.html">reveal, beige theme</a>
<li><a href="demo_reveal_beigesmall.html">reveal, beigesmall theme</a>
<li><a href="demo_reveal_darkgrey.html">reveal, darkgrey theme</a>
<li><a href="demo_reveal_night.html">reveal, night theme</a>
<li><a href="demo_reveal_simple.html">reveal, simple theme</a>
<li><a href="demo_reveal_sky.html">reveal, sky theme</a>
<li><a href="demo_deck_beamer.html">deck, beamer theme</a>
<li><a href="demo_deck_mnml.html">deck, mnml theme</a>
<li><a href="demo_deck_neon.html">deck, neon theme</a>
<li><a href="demo_deck_sandstone_aurora.html">deck, sandstone.aurora theme</a>
<li><a href="demo_deck_sandstone_dark.html">deck, sandstone.dark theme</a>
<li><a href="demo_deck_sandstone_default.html">deck, sandstone.default theme</a>
<li><a href="demo_deck_sandstone_firefox.html">deck, sandstone.firefox theme</a>
<li><a href="demo_deck_sandstone_light.html">deck, sandstone.light theme</a>
<li><a href="demo_deck_sandstone_mdn.html">deck, sandstone.mdn theme</a>
<li><a href="demo_deck_sandstone_mightly.html">deck, sandstone.mightly theme</a>
<li><a href="demo_deck_swiss.html">deck, swiss theme</a>
<li><a href="demo_deck_web-2_0.html">deck, web-2_0 theme</a>
<li><a href="demo_dzslides_dzslides_default.html">dzslides</a>
<li><a href="demo_csss_csss_default.html">csss</a>
</ul>
EOF