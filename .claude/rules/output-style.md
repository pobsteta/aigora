# Output Style

Hard rules for how the AIGORA formats text it produces.

## Banned character: the em-dash

The em-dash character (the long dash, Unicode codepoint U+2014, the character
between the parentheses here: `[ — ]`) is **completely banned** from every
output the AIGORA generates. No exceptions.

This applies to:

- Chat responses to the user
- File content the AI writes or edits (markdown, code comments, docstrings)
- Commit messages, PR titles, PR bodies
- Documentation, READMEs, SKILL.md files
- Generated content (LinkedIn posts, emails, reports, .docx, .pdf)
- Voice script text passed to TTS
- Daily logs, memory entries, anywhere

If the AI is editing an existing file that already contains em-dashes, it must
not introduce new ones; existing em-dashes are left alone unless the user asks
for cleanup.

### What to use instead

Pick the punctuation that fits the actual structure of the sentence:

- Comma `,` for a soft pause inside a sentence
- Colon `:` to introduce a list, a definition, or an example
- Period `.` for a hard break (often two short sentences read better than one
  long one with an em-dash)
- Parentheses `(...)` for a true aside
- Hyphen `-` for compound adjectives (e.g. "well-known", "user-facing")
- Semicolon `;` to join two related independent clauses

### Why this rule exists

The user finds the em-dash a strong stylistic tell of AI-generated text and
does not want it appearing in any deliverable produced by their AIGORA, whether
the deliverable is for them or for a third party.

This rule is absolute. It overrides any default punctuation habit, any
stylistic guideline elsewhere in the system, and any pattern present in
training data.
