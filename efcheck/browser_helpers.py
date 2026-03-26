from __future__ import annotations

ACTIONABLE_DESCENDANT_SELECTOR = (
    "button, [role='button'], a, input[type='button'], input[type='submit']"
)


def day_label_candidates(day_number: int) -> list[str]:
    return [
        f"Day {day_number}",
        f"Day{day_number}",
        f"\u7b2c{day_number}\u5929",
        f"\u7b2c {day_number} \u5929",
    ]


def day_card_selector_candidates(day_number: int) -> list[str]:
    selectors: list[str] = []
    for label in day_label_candidates(day_number):
        selectors.extend(
            [
                (
                    "xpath="
                    f"//*[normalize-space()='{label}']/ancestor::*"
                    "[self::button or self::li or self::div][1]"
                ),
                (
                    "xpath="
                    f"//*[contains(normalize-space(), '{label}')]/ancestor::*"
                    "[self::button or self::li or self::div][1]"
                ),
            ]
        )
    return selectors
