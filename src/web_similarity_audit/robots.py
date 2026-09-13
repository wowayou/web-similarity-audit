"""robots.txt parsing and enforcement.

Implements the subset of the Robots Exclusion Protocol that matters for
crawling decisions:

* ``User-agent`` groups with a specific agent or the ``*`` wildcard
* ``Disallow`` / ``Allow`` path rules with prefix semantics
* ``*`` wildcards inside paths and a trailing ``$`` end anchor
* longest-match precedence, with ``Allow`` winning ties
* ``Crawl-delay`` (exposed, not enforced automatically)

Reference: https://www.rfc-editor.org/rfc/rfc9309.html
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

# A product token that identifies this crawler to sites.
DEFAULT_USER_AGENT = "web-similarity-audit"


@dataclass(frozen=True)
class _Rule:
    """A single Allow/Disallow rule."""

    allow: bool
    pattern: str  # original path pattern (for debugging)
    regex: re.Pattern[str]

    @property
    def length(self) -> int:
        """Specificity of the rule, used for longest-match precedence."""
        # Count literal characters, ignoring regex metacharacters we added.
        return len(self.pattern.replace("*", "").replace("$", ""))


class RobotsRules:
    """Parsed robots.txt rules for a single host.

    A group is a set of ``User-agent`` lines followed by rules. The most
    specific matching group wins; if none match, the ``*`` group is used.
    """

    def __init__(self) -> None:
        # Map of lowercase agent token -> list of rules. "*" is the wildcard.
        self._groups: dict[str, list[_Rule]] = {}
        self.crawl_delay: float | None = None
        self.sitemaps: list[str] = []

    # -- construction ----------------------------------------------------

    @classmethod
    def parse(cls, text: str) -> "RobotsRules":
        """Parse robots.txt content into a :class:`RobotsRules` instance."""
        rules = cls()
        current_agents: list[str] = []
        # Track whether we've seen rules for the current agent group, so a new
        # User-agent line starts a fresh group even if separated by non-rules.
        group_has_rules = False

        for raw_line in text.splitlines():
            # Strip comments. A '#' starts a comment anywhere on the line.
            line = raw_line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue

            field_name, _, value = line.partition(":")
            field_name = field_name.strip().lower()
            value = value.strip()

            if field_name == "user-agent":
                if group_has_rules:
                    # Previous group finished; start a new one.
                    current_agents = []
                    group_has_rules = False
                if value:
                    current_agents.append(value.lower())

            elif field_name in ("disallow", "allow"):
                if not current_agents:
                    # Rules before any User-agent line are not valid; skip.
                    continue
                if field_name == "disallow" and value == "":
                    # "Disallow:" with empty value means "allow everything".
                    # Represent as an explicit allow-all so it can still lose
                    # to a more specific Disallow in a later group.
                    continue
                rule = cls._compile_rule(allow=(field_name == "allow"), path=value)
                for agent in current_agents:
                    rules._groups.setdefault(agent, []).append(rule)
                group_has_rules = True

            elif field_name == "crawl-delay":
                try:
                    rules.crawl_delay = float(value)
                except ValueError:
                    pass
                group_has_rules = True

            elif field_name == "sitemap" and value:
                rules.sitemaps.append(value)

        return rules

    @staticmethod
    def _compile_rule(allow: bool, path: str) -> _Rule:
        """Translate a robots.txt path pattern into an anchored regex."""
        # A trailing '$' anchors the end of the path.
        end_anchor = path.endswith("$")
        if end_anchor:
            path = path[:-1]

        # Escape regex metacharacters, then translate '*' back into '.*'.
        escaped = re.escape(path).replace(r"\*", ".*")

        suffix = "$" if end_anchor else ""
        regex = re.compile("^" + escaped + suffix)
        return _Rule(allow=allow, pattern=path, regex=regex)

    # -- queries ---------------------------------------------------------

    def _rules_for(self, user_agent: str) -> list[_Rule]:
        """Return the most specific matching rule group for *user_agent*."""
        agent = user_agent.lower()
        # Exact product-token match first (robots.txt matching is case
        # insensitive and based on substring of the product token in practice).
        best: list[_Rule] | None = None
        best_len = -1
        for token, group in self._groups.items():
            if token == "*":
                continue
            if token in agent or agent in token:
                if len(token) > best_len:
                    best = group
                    best_len = len(token)
        if best is not None:
            return best
        return self._groups.get("*", [])

    def can_fetch(self, url: str, user_agent: str = DEFAULT_USER_AGENT) -> bool:
        """Return ``True`` if *url* may be fetched by *user_agent*."""
        path = urlparse(url).path or "/"
        query = urlparse(url).query
        if query:
            path = f"{path}?{query}"

        rules = self._rules_for(user_agent)
        if not rules:
            return True

        # Longest match wins; Allow wins ties. Among equal-length matches we
        # therefore prefer Allow.
        best_rule: _Rule | None = None
        for rule in rules:
            if rule.regex.match(path):
                if best_rule is None:
                    best_rule = rule
                elif rule.length > best_rule.length:
                    best_rule = rule
                elif rule.length == best_rule.length and rule.allow:
                    best_rule = rule

        if best_rule is None:
            return True
        return best_rule.allow

    def allowed_paths_empty(self, user_agent: str = DEFAULT_USER_AGENT) -> bool:
        """True when the group has no Disallow rules (everything allowed)."""
        return not any(not r.allow for r in self._rules_for(user_agent))
