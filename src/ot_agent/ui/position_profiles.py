import streamlit as st
from pathlib import Path

from ot_agent.position_profiles_db import (
    ensure_profile,
    get_connection,
    list_companies,
    list_duties,
    list_hazards,
    list_positions_for_company,
    list_profile_links,
    list_work_types,
    upsert_link,
)

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

STATUS_OPTIONS = [
    "SUGGESTED",
    "CONFIRMED",
    "REJECTED",
    "REQUIRES_VERIFICATION",
]

LINK_TYPE_OPTIONS = [
    ("duty", "Duty"),
    ("hazard", "Hazard"),
    ("work", "Work type"),
]


def _ru(hex_codes: str) -> str:
    return "".join(chr(int(x, 16)) for x in hex_codes.split())


TITLE = _ru(
    "041f 0440 043e 0444 0438 043b 0438 "
    "0020 "
    "0434 043e 043b 0436 043d 043e 0441 0442 0435 0439"
)

COMPANY = _ru(
    "041a 043e 043c 043f 0430 043d 0438 044f"
)

POSITION = _ru(
    "0414 043e 043b 0436 043d 043e 0441 0442 044c"
)

STATUS = _ru(
    "0421 0442 0430 0442 0443 0441"
)

SOURCE = _ru(
    "0418 0441 0442 043e 0447 043d 0438 043a"
)

NOTE = _ru(
    "041f 0440 0438 043c 0435 0447 0430 043d 0438 0435"
)

SAVE = _ru(
    "0421 043e 0445 0440 0430 043d 0438 0442 044c"
)

SAVED = _ru(
    "0421 043e 0445 0440 0430 043d 0435 043d 043e"
) + "."

ADD_LINK = _ru(
    "0414 043e 0431 0430 0432 0438 0442 044c "
    "0020 "
    "0441 0432 044f 0437 044c"
)

LINK_TYPE = _ru(
    "0422 0438 043f "
    "0020 "
    "0441 0432 044f 0437 0438"
)

ITEM = _ru(
    "042d 043b 0435 043c 0435 043d 0442"
)

NO_COMPANIES = _ru(
    "041a 043e 043c 043f 0430 043d 0438 0438 "
    "0020 "
    "043d 0435 "
    "0020 "
    "043d 0430 0439 0434 0435 043d 044b"
)

NO_POSITIONS = _ru(
    "0414 043e 043b 0436 043d 043e 0441 0442 0438 "
    "0020 "
    "043d 0435 "
    "0020 "
    "043d 0430 0439 0434 0435 043d 044b"
)

NO_DATA = _ru(
    "041d 0435 0442 "
    "0020 "
    "0434 0430 043d 043d 044b 0445"
)


def render_position_profiles() -> None:
    st.title(TITLE)

    st.warning(
        "DRAFT / REQUIRES_VERIFICATION. "
        "Synthetic technical position profiles. "
        "Not a legal conclusion. "
        "Requires verification by an occupational safety specialist."
    )

    conn = get_connection(DB_PATH)

    try:
        companies = list_companies(conn)

        if not companies:
            st.info(NO_COMPANIES)
            return

        company_labels = [company["display_name"] for company in companies]
        company_ids = [company["company_id"] for company in companies]

        company_index = st.selectbox(
            COMPANY,
            range(len(company_labels)),
            format_func=lambda i: company_labels[i],
        )

        company_id = company_ids[company_index]

        positions = list_positions_for_company(conn, company_id)

        if not positions:
            st.info(NO_POSITIONS)
            return

        position_labels = [
            f"{position['position_id']} | {position['display_name']}"
            for position in positions
        ]
        position_ids = [position["position_id"] for position in positions]

        position_index = st.selectbox(
            POSITION,
            range(len(position_labels)),
            format_func=lambda i: position_labels[i],
        )

        position_id = position_ids[position_index]

        ensure_profile(conn, company_id, position_id)
        conn.commit()

        links = list_profile_links(conn, company_id, position_id)

        if links:
            st.dataframe(links, hide_index=True, width="stretch")
        else:
            st.info(NO_DATA)

        with st.expander(ADD_LINK):
            link_type_index = st.selectbox(
                LINK_TYPE,
                range(len(LINK_TYPE_OPTIONS)),
                format_func=lambda i: LINK_TYPE_OPTIONS[i][1],
            )

            link_type, _ = LINK_TYPE_OPTIONS[link_type_index]

            if link_type == "duty":
                items = list_duties(conn)
            elif link_type == "hazard":
                items = list_hazards(conn)
            elif link_type == "work":
                items = list_work_types(conn)
            else:
                items = []

            if not items:
                st.info(NO_DATA)
            else:
                item_labels = [
                    f"{item['code']} | {item['title']}"
                    for item in items
                ]
                item_codes = [item["code"] for item in items]

                item_index = st.selectbox(
                    ITEM,
                    range(len(item_labels)),
                    format_func=lambda i: item_labels[i],
                )

                status = st.selectbox(
                    STATUS,
                    STATUS_OPTIONS,
                    index=0,
                )

                source = st.text_input(
                    SOURCE,
                    value="",
                )

                note = st.text_input(
                    NOTE,
                    value="",
                )

                if st.button(SAVE):
                    try:
                        upsert_link(
                            conn,
                            company_id,
                            position_id,
                            link_type,
                            item_codes[item_index],
                            status,
                            source.strip() or None,
                            note.strip() or None,
                        )
                        conn.commit()
                        st.success(SAVED)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    finally:
        conn.close()


render = render_position_profiles
