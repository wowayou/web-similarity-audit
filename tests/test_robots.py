"""Tests for robots.txt parsing and enforcement."""

from web_similarity_audit.robots import RobotsRules, DEFAULT_USER_AGENT


def test_empty_robots_allows_all():
    rules = RobotsRules.parse("")
    assert rules.can_fetch("https://example.com/anything")
    assert rules.can_fetch("https://example.com/private")


def test_disallow_prefix_matching():
    """Disallow /admin/ must block /admin/page (prefix semantics)."""
    rules = RobotsRules.parse(
        "User-agent: *\n"
        "Disallow: /admin/\n"
    )
    assert rules.can_fetch("https://example.com/") is True
    assert rules.can_fetch("https://example.com/products") is True
    assert rules.can_fetch("https://example.com/admin/") is False
    assert rules.can_fetch("https://example.com/admin/users") is False
    assert rules.can_fetch("https://example.com/admin/settings/general") is False


def test_disallow_all():
    rules = RobotsRules.parse("User-agent: *\nDisallow: /\n")
    assert rules.can_fetch("https://example.com/") is False
    assert rules.can_fetch("https://example.com/page") is False


def test_allow_overrides_disallow_when_more_specific():
    rules = RobotsRules.parse(
        "User-agent: *\n"
        "Disallow: /private/\n"
        "Allow: /private/public/\n"
    )
    assert rules.can_fetch("https://example.com/private/secret") is False
    assert rules.can_fetch("https://example.com/private/public/info") is True


def test_longest_match_wins():
    """A longer Allow should beat a shorter Disallow."""
    rules = RobotsRules.parse(
        "User-agent: *\n"
        "Disallow: /a/\n"
        "Allow: /a/b/\n"
    )
    assert rules.can_fetch("https://example.com/a/x") is False
    assert rules.can_fetch("https://example.com/a/b/x") is True


def test_allow_wins_on_equal_length_tie():
    rules = RobotsRules.parse(
        "User-agent: *\n"
        "Disallow: /page\n"
        "Allow: /page\n"
    )
    assert rules.can_fetch("https://example.com/page") is True


def test_wildcard_matching():
    rules = RobotsRules.parse("User-agent: *\nDisallow: /*.pdf$\n")
    assert rules.can_fetch("https://example.com/doc.pdf") is False
    assert rules.can_fetch("https://example.com/docs/report.pdf") is False
    # Not ending in .pdf -> allowed
    assert rules.can_fetch("https://example.com/doc.pdf.html") is True


def test_dollar_end_anchor():
    rules = RobotsRules.parse("User-agent: *\nDisallow: /exact$\n")
    assert rules.can_fetch("https://example.com/exact") is False
    assert rules.can_fetch("https://example.com/exact/sub") is True


def test_specific_agent_group_preferred_over_wildcard():
    rules = RobotsRules.parse(
        "User-agent: *\n"
        "Disallow: /\n"
        "\n"
        "User-agent: web-similarity-audit\n"
        "Disallow: /blocked-only\n"
    )
    # Wildcard group would block everything, but our specific group allows all
    # except /blocked-only.
    assert rules.can_fetch("https://example.com/", DEFAULT_USER_AGENT) is True
    assert rules.can_fetch("https://example.com/blocked-only", DEFAULT_USER_AGENT) is False
    # A different agent still gets the wildcard rules.
    assert rules.can_fetch("https://example.com/", "other-bot") is False


def test_comments_and_blank_lines_ignored():
    rules = RobotsRules.parse(
        "# this is a comment\n"
        "User-agent: *   # inline comment\n"
        "\n"
        "Disallow: /secret  # another comment\n"
    )
    assert rules.can_fetch("https://example.com/secret") is False
    assert rules.can_fetch("https://example.com/public") is True


def test_query_string_included_in_match():
    rules = RobotsRules.parse("User-agent: *\nDisallow: /*?session=\n")
    assert rules.can_fetch("https://example.com/page?session=abc") is False
    assert rules.can_fetch("https://example.com/page") is True


def test_crawl_delay_parsed():
    rules = RobotsRules.parse(
        "User-agent: *\n"
        "Crawl-delay: 5\n"
        "Disallow: /x\n"
    )
    assert rules.crawl_delay == 5.0


def test_sitemap_parsed():
    rules = RobotsRules.parse(
        "Sitemap: https://example.com/sitemap.xml\n"
        "User-agent: *\n"
        "Disallow: /x\n"
    )
    assert "https://example.com/sitemap.xml" in rules.sitemaps


def test_multiple_agents_share_group():
    rules = RobotsRules.parse(
        "User-agent: bot-a\n"
        "User-agent: bot-b\n"
        "Disallow: /shared\n"
    )
    assert rules.can_fetch("https://example.com/shared", "bot-a") is False
    assert rules.can_fetch("https://example.com/shared", "bot-b") is False
    assert rules.can_fetch("https://example.com/shared", "bot-c") is True


def test_multiple_user_agent_blocks_are_separate():
    rules = RobotsRules.parse(
        "User-agent: bot-a\n"
        "Disallow: /alpha\n"
        "\n"
        "User-agent: *\n"
        "Disallow: /beta\n"
    )
    # bot-a gets its own group; the wildcard group does not apply to it.
    assert rules.can_fetch("https://example.com/alpha", "bot-a") is False
    assert rules.can_fetch("https://example.com/beta", "bot-a") is True
    # Other agents only get the wildcard group.
    assert rules.can_fetch("https://example.com/alpha", "other") is True
    assert rules.can_fetch("https://example.com/beta", "other") is False


def test_case_insensitive_agent_and_fields():
    rules = RobotsRules.parse(
        "USER-AGENT: *\n"
        "DISALLOW: /Secret\n"
    )
    assert rules.can_fetch("https://example.com/Secret") is False
