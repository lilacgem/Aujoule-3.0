# Synthetic legacy-adapter fixtures

These contain invented test values, not founder history or original media.
`baseline.txt` exercises all seven legacy fields. `changed.txt` demonstrates a
changed version/value and independent source digest; its version number does not
prove a correction was approved or that these files have a trusted parent link.
Activity=.7 and complexity=.4 are supplied explicitly in tests.

The full specification's conflicting-evidence fixture belongs to the later
reconciliation stage. This adapter accepts one seven-line state and rejects
additional conflicting/trailing records rather than silently selecting a claim.
It does not implement general conflict resolution or complete Compiler 3 fixtures.
