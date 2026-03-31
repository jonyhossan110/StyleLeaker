from core.html_parser import HTMLParser


def test_html_parser_extracts_stylesheet_links_from_rel_list():
    parser = HTMLParser()
    html = """
    <html>
      <head>
        <link rel="preload stylesheet" href="/a.css">
        <link rel="stylesheet" href="/b.css">
        <style>.x { color: red; }</style>
      </head>
      <body>
        <script src="/app.js"></script>
        <!-- TODO internal endpoint -->
        <form action="/login" method="post">
          <input type="hidden" name="csrf_token" value="abc123">
        </form>
      </body>
    </html>
    """
    data = parser.parse(html, "https://example.com")

    assert "https://example.com/a.css" in data["stylesheet_links"]
    assert "https://example.com/b.css" in data["stylesheet_links"]
    assert "https://example.com/app.js" in data["script_sources"]
    assert len(data["inline_styles"]) == 1
    assert len(data["comments"]) == 1
    assert data["forms"][0]["fields"][0]["type"] == "hidden"
