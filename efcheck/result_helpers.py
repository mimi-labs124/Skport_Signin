from efcheck.statuses import ALREADY_DONE, ERROR, SUCCESS


def final_signin_status(*, day_number: int, refreshed_state: str, post_seen: bool) -> tuple[str, str]:
    if refreshed_state == ALREADY_DONE:
        return SUCCESS, f"SUCCESS: clicked Day {day_number} and attendance state refreshed."
    if post_seen:
        return (
            ERROR,
            f"ERROR: the sign-in POST for Day {day_number} returned success, but the refreshed page state could not be verified.",
        )
    return (
        ERROR,
        f"ERROR: tried to click Day {day_number}, but the page still shows an available reward.",
    )
