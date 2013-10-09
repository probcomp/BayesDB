---
layout: "intro"
page_title: "How to use website-archetype"
prev_url: "#"
---

# How to use website-archetype

## Creating pages

To create a page, simply create a file named 'NAME.html.markdown' (substituting in the desired value for NAME) somewhere in the source folder.

## Linking pages

Simply creating a page will result in an orphaned page that isn't actually linked to.  You'll probably want to create a link to the page via one of the layouts' sidebar contents.  For example, this page was linked to by adding a 'li' entry with an href in layouts/intro.erb.  It was added to intro.erb because this page's source, why.html.markdown, uses 'layout: "intro"'.

Note: linking pages requires some familiarity with html, though this is minimal and hopefully this template makes everything possible through copy pasting with slight modifications.

## Modifying formats

Modifying formatting is a little less straightfoward: modifying the front page, 'source/index.html.erb', will require knowledge of html/css.

## More info

More detailed instructions are in the [docs section](/docs/)
