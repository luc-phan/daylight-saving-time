from datetime import date
from dst_notifier.core import get_last_sunday, get_dst_transitions

def test_get_last_sunday():
    # 2024: March 31 was Sunday
    assert get_last_sunday(2024, 3) == date(2024, 3, 31)
    # 2024: Oct 27 was Sunday
    assert get_last_sunday(2024, 10) == date(2024, 10, 27)
    
    # 2025: March 30 is Sunday
    assert get_last_sunday(2025, 3) == date(2025, 3, 30)

def test_get_dst_transitions():
    transitions = get_dst_transitions(2026)
    assert len(transitions) == 2
    
    # 2026: March 29 is Sunday
    assert transitions[0][0] == date(2026, 3, 29)
    assert "Summer Time" in transitions[0][1]
    
    # 2026: Oct 25 is Sunday
    assert transitions[1][0] == date(2026, 10, 25)
    assert "Winter Time" in transitions[1][1]
