#!/bin/sh

# ------------------- scientific_writing talk ---------------------
name=scientific_writing

# Note: since Doconce syntax is demonstrated inside !bc/!ec
# blocks we need a few fixes

doconce format html $name --pygments-html-style=perldoc --html-solarized
mv -f $name.html ${name}_solarized.html
doconce format html $name --pygments-html-style=default
mv -f $name.html ${name}_plain.html

doconce format html $name --pygments-html-style=native
doconce slides_html $name reveal --html-slide-theme=darkgray
# Fix selected backslashes inside verbatim envirs that doconce has added
# (only a problem when we want to show full doconce code with
# labels in !bc-!ec envirs).
doconce replace '\label{this:section}' 'label{this:section}' $name.html
doconce replace '\label{fig1}' 'label{fig1}' $name.html
doconce replace '\label{demo' 'label{demo' $name.html


doconce format pdflatex $name --minted-latex-style=trac
doconce ptex2tex $name envir=minted -DBOOK
pdflatex -shell-escape $name
mv -f $name.pdf ${name}_minted.pdf

doconce format pdflatex $name
doconce ptex2tex $name envir=ans:nt -DBOOK
pdflatex $name
mv -f $name.pdf ${name}_anslistings.pdf

# sphinx doesn't handle math inside code well, we drop it since
# other formats demonstrate doconce writing this way
doconce format sphinx $name
doconce sphinx_dir author="H. P. Langtangen" theme=pyramid $name
python automake_sphinx.py

doconce format pandoc $name  # Markdown (pandoc extended)
doconce format gwiki  $name  # Googlecode wiki

# These don't like slides with code after heading:
#doconce format rst    $name  # reStructuredText
#doconce format plain  $name  # plain, untagged text for email

pygmentize -l text -f html -o ${name}_doconce.html ${name}.do.txt

cp -r ${name}*.pdf *.md ${name}*.html reveal.js fig ../demos/slides/

doconce format html sw_index.do.txt
cp sw_index.html ../demos/slides/index.html

# ------------------- short demo talk ---------------------

# Make all the styles for the short demo talk
doconce slides_html demo all  # generates tmp_slides_html_all.sh
pygmentize -l text -f html -o demo_doconce.html demo.do.txt
sh -x tmp_slides_html_all.sh

doconce format pdflatex demo
doconce ptex2tex demo -DPALATINO envir=minted
pdflatex -shell-escape demo

cp -r demo.pdf demo_*.html reveal.js deck.js csss fig ../demos/slides/demo/
cat > ../demos/slides/demo/index.html <<EOF
<h1>Autogenerated slide styles</h1>
<b>Note:</b> View these slides in Firefox (not Chrome). Bring slide shows
up in separate tabs. You may need to reload some pages to get the
mathematics correctly rendered.
<ul>
<li> reveal.js: (the css style files are slightly changed: left-adjusted,
lower case headings with smaller fonts; "darkgray" corresponds to
the original "default" theme)
<ul>
<li><a href="demo_reveal_beige.html">reveal, beige theme</a>
<li><a href="demo_reveal_beigesmall.html">reveal, beigesmall theme</a>
<li><a href="demo_reveal_darkgrey.html">reveal, darkgrey theme</a>
<li><a href="demo_reveal_serif.html">reveal, serif theme</a>
<li><a href="demo_reveal_night.html">reveal, night theme</a>
<li><a href="demo_reveal_simple.html">reveal, simple theme</a>
<li><a href="demo_reveal_sky.html">reveal, sky theme</a>
</ul>
<li> deck.js: (the css styles are slightly changed, mainly somewhat
smaller fonts for verbatim code)
<ul>
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
</ul>
<li><a href="demo_dzslides_dzslides_default.html">dzslides</a>
<li><a href="demo_csss_csss_default.html">csss</a> (black background instead
of the original rainbow background)
<li><a href="demo.pdf">Handouts in PDF</a> (generated via LaTeX)
<li><a href="demo_doconce.html">Doconce source code for the slides</a>
<li><a href="../scientific_writing.html">Doconce: Why and How</a>
</ul>
EOF