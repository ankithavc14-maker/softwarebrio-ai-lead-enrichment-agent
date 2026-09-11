from cleaner import clean_html


def test_clean_html_removes_noise_and_extracts_contacts():
    html = """
    <html>
      <body>
        <nav>Menu</nav>
        <main>
          <h1>Example Company</h1>
          <p>Build software for developers.</p>
          <p>Contact info@example.com</p>
          <a href="https://linkedin.com/in/example">LinkedIn</a>
          <script>alert("do not include");</script>
          <style>.x{display:none}</style>
        </main>
        <footer>Legal boilerplate</footer>
      </body>
    </html>
    """
    text, emails, links = clean_html(html, 5000)

    assert "Example Company" in text
    assert "do not include" not in text
    assert "Legal boilerplate" not in text
    assert "info@example.com" in emails
    assert any("linkedin.com/in/example" in x for x in links)
