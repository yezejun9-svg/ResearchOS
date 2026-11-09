"""Use the observed agent_message plain content item type: input_text."""
from __future__ import annotations

import ast
from pathlib import Path

P = Path(__file__).resolve().parent
profile_path = P / "formal_profile_w09.after.py"
controls_path = P / "source_controls_v3.py"
profile = profile_path.read_text(encoding="utf-8")
controls = controls_path.read_text(encoding="utf-8")
old_profile = 'and content_items[0]["type"] == "text"'
new_profile = 'and content_items[0]["type"] == "input_text"'
old_control = 'assert set(message["payload"]["content"][0]) == {"type", "text"}\n'
new_control = (old_control +
               'assert message["payload"]["content"][0]["type"] == "input_text"\n')
assert profile.count(old_profile) == 1
assert controls.count(old_control) == 1
candidate_profile = profile.replace(old_profile, new_profile, 1)
candidate_controls = controls.replace(old_control, new_control, 1)
ast.parse(candidate_profile, filename=str(profile_path))
ast.parse(candidate_controls, filename=str(controls_path))
assert profile_path.read_text(encoding="utf-8") == profile
assert controls_path.read_text(encoding="utf-8") == controls
profile_path.write_text(candidate_profile, encoding="utf-8", newline="")
controls_path.write_text(candidate_controls, encoding="utf-8", newline="")
print("V3_OBSERVED_INPUT_TEXT_SHAPE_AST_PASS")
