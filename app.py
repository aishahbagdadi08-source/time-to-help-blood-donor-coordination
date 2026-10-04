from datetime import datetime
import uuid

import streamlit as st

st.set_page_config(page_title="Time to Help", page_icon="TH", layout="wide")

GROUPS = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
# A simplified red-cell screening table for a prototype. It is not medical confirmation.
COMPATIBLE = {
    "O-": {"O-"},
    "O+": {"O-", "O+"},
    "A-": {"O-", "A-"},
    "A+": {"O-", "O+", "A-", "A+"},
    "B-": {"O-", "B-"},
    "B+": {"O-", "O+", "B-", "B+"},
    "AB-": {"O-", "A-", "B-", "AB-"},
    "AB+": set(GROUPS),
}
DEFAULT_WEIGHTS = {
    "Blood group": 35,
    "Availability": 30,
    "Distance": 20,
    "Response time": 15,
}
RESPONSE_STATES = ["Contacted", "Accepted", "No Response", "Declined", "Unavailable"]


def seed_donors():
    # All distances and response estimates are fictional demo values.
    rows = [
        ("TD-104", "O-", 1.2, "Confirmed Available", 12),
        ("TD-218", "A+", 2.4, "Unconfirmed", 18),
        ("TD-307", "B+", 4.8, "Confirmed Available", 25),
        ("TD-411", "O+", 3.1, "Confirmed Available", 20),
        ("TD-526", "AB+", 1.7, "Unavailable", 10),
        ("TD-638", "A-", 6.2, "Confirmed Available", 35),
        ("TD-742", "B-", 2.9, "Unconfirmed", 22),
        ("TD-853", "AB-", 7.5, "Confirmed Available", 40),
        ("TD-964", "O+", 8.1, "Unconfirmed", 45),
        ("TD-175", "A+", 5.3, "Confirmed Available", 30),
        ("TD-286", "O-", 9.4, "Unavailable", 50),
        ("TD-390", "B+", 3.6, "Confirmed Available", 16),
        ("TD-502", "AB+", 11.0, "Unconfirmed", 55),
        ("TD-614", "A-", 4.2, "Confirmed Available", 28),
    ]
    return [
        {"id": donor_id, "group": group, "km": km, "availability": availability,
         "minutes": minutes, "response": "Not contacted"}
        for donor_id, group, km, availability, minutes in rows
    ]


def rank_candidate(donor, request, weights):
    exact = donor["group"] == request["group"]
    group_fraction = 1.0 if exact else 0.63
    availability_fraction = 1.0 if donor["availability"] == "Confirmed Available" else 0.47
    distance_fraction = max(0.0, 1 - donor["km"] / 15)

    urgency_multiplier = {"EMERGENCY": 0.40, "Critical": 0.60, "High": 0.80, "Moderate": 1.0}[request["urgency"]]
    response_window = max(5, request["deadline"] * urgency_multiplier)
    response_fraction = max(0.0, 1 - donor["minutes"] / response_window)

    parts = {
        "Blood group": weights["Blood group"] * group_fraction,
        "Availability": weights["Availability"] * availability_fraction,
        "Distance": weights["Distance"] * distance_fraction,
        "Response time": weights["Response time"] * response_fraction,
    }
    total_weight = sum(weights.values()) or 1
    score = round(100 * sum(parts.values()) / total_weight)
    match_text = "exact group match" if exact else "prototype-compatible group"
    avail_text = donor["availability"].lower()
    why = (
        f"{match_text}; {avail_text}; simulated distance {donor['km']:.1f} km; "
        f"estimated response {donor['minutes']} min (urgency-adjusted target {response_window:.0f} min)."
    )
    breakdown = " · ".join(
        f"{name} {points:.1f}/{weights[name]}" for name, points in parts.items()
    )
    return score, why, breakdown


def add_audit(message):
    st.session_state.audit.insert(0, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message))


if "donors" not in st.session_state:
    st.session_state.donors = seed_donors()
    st.session_state.request = None
    st.session_state.request_key = None
    st.session_state.audit = []
    st.session_state.request_ids = []
    st.session_state.screening_intake = {}
    st.session_state.page = "Create Request"
    st.session_state.nav_section = "Requests"
    st.session_state.weights = DEFAULT_WEIGHTS.copy()
if "request_ids" not in st.session_state:
    current_id = st.session_state.request["id"] if st.session_state.request else None
    st.session_state.request_ids = [current_id] if current_id else []
if "screening_intake" not in st.session_state:
    st.session_state.screening_intake = {}
if "nav_section" not in st.session_state:
    st.session_state.nav_section = "Inputs" if st.session_state.page == "Donor Screening" else "Requests"
if "theme_default_v1" not in st.session_state:
    st.session_state.light_mode = True
    st.session_state.theme_default_v1 = True

header_left, header_right = st.columns([5, 1])
with header_right:
    st.toggle("Light theme", key="light_mode", help="Switch between light and dark appearance")

st.markdown(
    """<style>
    :root {color-scheme: dark;}
    .stApp {background: radial-gradient(ellipse at 80% 0%,rgba(22,115,129,.24),transparent 38%),radial-gradient(ellipse at 5% 35%,rgba(158,42,68,.12),transparent 34%),#07111b;color:#eaf2f5;font-family:'Segoe UI',Arial,sans-serif;}
    .block-container {max-width:1240px;padding-top:1.4rem;padding-bottom:3rem;}
    h1,h2,h3,[data-testid="stMetricValue"] {font-family:'Bahnschrift','Segoe UI',sans-serif;}
    .hero {position:relative;overflow:hidden;display:flex;align-items:center;justify-content:space-between;gap:1.5rem;min-height:205px;padding:1.8rem 2.1rem;border:1px solid rgba(121,213,216,.22);border-radius:24px;color:#f8fbfc;margin:0 0 1.1rem;background:linear-gradient(112deg,rgba(12,34,49,.98),rgba(9,48,61,.94) 58%,rgba(19,65,72,.78));box-shadow:0 22px 70px rgba(0,0,0,.28),inset 0 1px rgba(255,255,255,.05);}
    .hero:after {content:'';position:absolute;width:340px;height:340px;right:8%;top:-235px;border:1px solid rgba(131,220,218,.22);border-radius:50%;box-shadow:0 0 0 28px rgba(131,220,218,.035),0 0 0 58px rgba(131,220,218,.025);pointer-events:none;}
    .hero-copy {position:relative;z-index:1;}
    .hero-brand {display:flex;align-items:center;gap:.9rem;margin-bottom:1rem;}
    .logo-mark {width:52px;height:52px;flex:none;filter:drop-shadow(0 0 18px rgba(255,94,107,.25));}
    .brand-name {font:700 1.05rem 'Bahnschrift','Segoe UI',sans-serif;letter-spacing:.02em;}
    .brand-caption {display:block;margin-top:.12rem;color:#9ab6c0;font-size:.69rem;letter-spacing:.16em;text-transform:uppercase;}
    .hero h1 {margin:0;color:#fff;font:700 clamp(2rem,4vw,3.25rem)/1.04 'Bahnschrift','Segoe UI',sans-serif;letter-spacing:-.045em;}
    .hero-motto {margin:.55rem 0 0;color:#c3d6dc;font-size:1.03rem;}
    .hero-motto strong {color:#ff7580;font-weight:600;}
    .hero-art {position:relative;z-index:1;display:flex;align-items:center;justify-content:center;width:180px;height:120px;flex:none;}
    .pulse-orbit {position:absolute;width:84px;height:84px;border:1px solid rgba(255,113,128,.42);border-radius:50%;animation:orbit-pulse 3.2s ease-out infinite;}
    .pulse-orbit.delay {animation-delay:1.6s;}
    .pulse-line {width:150px;height:64px;filter:drop-shadow(0 0 9px rgba(255,103,116,.58));animation:line-glow 2.8s ease-in-out infinite;}
    .demo-chip {display:inline-flex;align-items:center;gap:.45rem;margin-top:1.05rem;padding:.34rem .65rem;border:1px solid rgba(255,255,255,.13);border-radius:99px;background:rgba(4,17,26,.42);color:#b8cdd3;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;}
    .demo-dot {width:7px;height:7px;border-radius:50%;background:#f27680;box-shadow:0 0 10px #f27680;}
    @keyframes orbit-pulse {0%{transform:scale(.72);opacity:.75}80%,100%{transform:scale(1.65);opacity:0}}
    @keyframes line-glow {0%,100%{opacity:.75}50%{opacity:1}}
    @media (prefers-reduced-motion: reduce) {.pulse-orbit,.pulse-line{animation:none;}}
    @media (max-width:700px) {.hero{padding:1.35rem;min-height:175px}.hero-art{width:88px;opacity:.62}.pulse-line{width:90px}.logo-mark{width:43px;height:43px}}
    div[data-testid="stVerticalBlockBorderWrapper"] {border-color:rgba(135,177,190,.18)!important;border-radius:16px!important;background:rgba(13,29,41,.66);}
    div[data-testid="stMetric"] {padding:.45rem .7rem;border-left:2px solid #43b8b3;background:rgba(15,37,49,.65);border-radius:0 10px 10px 0;}
    div[data-testid="stMetricLabel"] {color:#9eb7c0!important;}
    div[data-testid="stMetricValue"] {color:#f7fbfc!important;}
    div[data-testid="stButton"]>button {border:1px solid rgba(255,117,128,.42);border-radius:10px;background:linear-gradient(135deg,#a91f35,#d54657);color:white;font-weight:650;transition:transform .18s ease,box-shadow .18s ease;}
    div[data-testid="stButton"]>button:hover {transform:translateY(-1px);box-shadow:0 8px 24px rgba(224,91,104,.24);border-color:#ff8892;color:white;}
    div[data-testid="stAlert"] {border-radius:12px;border:1px solid rgba(255,193,105,.34);background:rgba(49,39,27,.92)!important;color:#ffedcf!important;}
    div[data-testid="stAlert"] * {color:#ffedcf!important;}
    div[data-testid="stCaptionContainer"] {color:#9bb1ba;}
    div[role="radiogroup"] {gap:.35rem;}
    div[role="radiogroup"] label {padding:.45rem .8rem;border:1px solid rgba(145,182,194,.16);border-radius:10px;background:rgba(14,31,43,.7);}
    div[role="radiogroup"] label,div[role="radiogroup"] label * {color:#c6d7dc!important;}
    div[role="radiogroup"] label:has(input:checked) {border-color:rgba(91,196,190,.62);background:rgba(33,102,107,.30);}
    div[role="radiogroup"] label:has(input:checked),div[role="radiogroup"] label:has(input:checked) * {color:#fff!important;}
    div[data-testid="stWidgetLabel"] p {color:#d3e1e5!important;}
    [data-baseweb="input"]>div,[data-baseweb="select"]>div {background:#10222e;border-color:#294452;border-radius:9px;}
    </style>""",
    unsafe_allow_html=True,
)
if st.session_state.light_mode:
    st.markdown(
        """<style>
        .stApp {background:radial-gradient(ellipse at 85% 0%,rgba(203,47,68,.08),transparent 38%),#fffaf9!important;color:#28323a!important;}
        [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li, .stApp h1, .stApp h2, .stApp h3,
        .stApp label, .stApp [data-testid="stWidgetLabel"] p {color:#28323a!important;}
        .hero {background:linear-gradient(112deg,#fff,#fff0f1 62%,#fde5e7)!important;border-color:#edc5ca!important;box-shadow:0 18px 48px rgba(91,29,39,.09),inset 0 1px #fff!important;}
        .hero h1 {color:#43242a!important;}.hero-motto {color:#64474c!important;}.hero-motto strong {color:#b42336!important;}
        .brand-name {color:#43242a!important;}.brand-caption {color:#8f5961!important;}
        .demo-chip {background:rgba(255,255,255,.82)!important;border-color:#edc5ca!important;color:#77464e!important;}
        .pulse-orbit {border-color:rgba(180,35,54,.28)!important;}
        div[data-testid="stVerticalBlockBorderWrapper"] {background:rgba(255,255,255,.94)!important;border-color:#eadfe0!important;box-shadow:0 8px 24px rgba(68,32,37,.045);}
        div[data-testid="stMetric"] {background:#fff1f2!important;border-left-color:#bd3445!important;}
        div[data-testid="stMetricLabel"] {color:#70565a!important;}
        div[data-testid="stMetricValue"] {color:#43242a!important;}
        div[data-testid="stCaptionContainer"], div[data-testid="stCaptionContainer"] * {color:#665b5c!important;}
        div[role="radiogroup"] label {background:#fff!important;border-color:#eadfe0!important;}
        div[role="radiogroup"] label, div[role="radiogroup"] label * {color:#493a3c!important;}
        div[role="radiogroup"] label:has(input:checked) {background:#fff0f1!important;border-color:#cf6976!important;}
        div[role="radiogroup"] label:has(input:checked), div[role="radiogroup"] label:has(input:checked) * {color:#842b38!important;}
        [data-baseweb="input"]>div,[data-baseweb="select"]>div {background:#fff!important;border-color:#e2d5d7!important;}
        [data-baseweb="input"] input,[data-baseweb="select"] * {color:#28323a!important;}
        div[data-testid="stAlert"] {background:#fff4e3!important;border-color:#e7cc9b!important;color:#65451c!important;}
        div[data-testid="stAlert"] * {color:#65451c!important;}
        div[data-testid="stButton"]>button {color:#fff!important;}
        </style>""",
        unsafe_allow_html=True,
    )
st.markdown(
    '''<div class="hero">
      <div class="hero-copy">
        <div class="hero-brand">
        <svg class="logo-mark" viewBox="0 0 64 64" role="img" aria-label="Time to Help pulse logo">
            <circle cx="32" cy="32" r="27" fill="rgba(255,113,128,.08)" stroke="#e66b78" stroke-width="1.5"/>
            <circle cx="32" cy="32" r="20" fill="none" stroke="rgba(255,113,128,.22)" stroke-width="1"/>
            <path d="M7 34h13l5-10 8 20 7-15 4 5h13" fill="none" stroke="#ff7180" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="32" cy="32" r="2.4" fill="#fff"/>
          </svg>
          <div><span class="brand-name">TIME TO HELP</span><span class="brand-caption">Emergency coordination</span></div>
        </div>
        <h1>When every minute<br>moves someone closer.</h1>
        <p class="hero-motto"><strong>Every minute matters.</strong> Make the next step count.</p>
        <span class="demo-chip"><i class="demo-dot"></i> Prototype · fictional data · no messages sent</span>
      </div>
      <div class="hero-art" aria-hidden="true">
        <span class="pulse-orbit"></span><span class="pulse-orbit delay"></span>
        <svg class="pulse-line" viewBox="0 0 180 70" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 37h39l12-1 10-21 17 43 16-34 10 13h15l8-7h35" stroke="#ff7180" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M4 37h39l12-1 10-21 17 43 16-34 10 13h15l8-7h35" stroke="#ffdce0" stroke-opacity=".35" stroke-width="1"/>
        </svg>
      </div>
    </div>''',
    unsafe_allow_html=True,
)
st.warning(
    "Coordination aid only. Donors are potential candidates. This prototype does not "
    "confirm transfusion compatibility or medical eligibility. Authorized healthcare "
    "providers / blood banks must verify blood group and donor eligibility."
)

with st.expander("Prototype scoring weights", expanded=False):
    st.caption("Demo settings only; these are not medical rules. Adjust weights for the demonstration.")
    cols = st.columns(4)
    for col, name in zip(cols, DEFAULT_WEIGHTS):
        st.session_state.weights[name] = col.slider(
            name, min_value=0, max_value=60,
            value=st.session_state.weights[name], key=f"weight_{name}",
        )
    st.caption("Scores are normalized to 0-100 using the selected weights.")
active_weights = st.session_state.weights
if sum(active_weights.values()) == 0:
    st.warning("All weights are zero. Default demo weights are being used until at least one factor is raised above zero.")
    active_weights = DEFAULT_WEIGHTS

st.markdown("## Requests & Inputs")
st.caption("Choose a request workflow or open donor input screening. Your demo request data stays available as you move between sections.")
st.session_state.nav_section = st.radio(
    "Main section", ["Requests", "Inputs"], horizontal=True,
    index=["Requests", "Inputs"].index(st.session_state.nav_section),
    label_visibility="collapsed", key="main_section_nav",
)
request_pages = ["Create Request", "Prioritized Donors", "Live Request Status", "Request History / Audit"]
if st.session_state.nav_section == "Requests":
    if st.session_state.page == "Donor Screening":
        st.session_state.page = "Create Request"
    st.session_state.page = st.radio(
        "Requests", request_pages, horizontal=True,
        index=request_pages.index(st.session_state.page), label_visibility="collapsed",
        key="request_page_nav",
    )
else:
    st.session_state.page = "Donor Screening"
    st.markdown("### Donor inputs")
    st.caption("Donors can enter their own details; age must be 18 or older.")

pages = ["Create Request", "Prioritized Donors", "Live Request Status", "Donor Screening", "Request History / Audit"]

if st.session_state.page == pages[0]:
    st.subheader("Create emergency request")
    with st.form("create_request"):
        a, b, c = st.columns(3)
        request_id = a.text_input("Request ID", f"TH-{uuid.uuid4().hex[:6].upper()}")
        group = b.selectbox("Patient blood group", GROUPS, index=GROUPS.index("B+"))
        units = c.number_input("Units required", min_value=1, max_value=10, value=2)
        d, e, f = st.columns(3)
        hospital = d.text_input("Hospital / area", placeholder="City General · North")
        urgency = e.selectbox("Urgency", ["EMERGENCY", "Critical", "High", "Moderate"])
        deadline = f.number_input("Required within (minutes)", min_value=5, max_value=1440, value=90, step=5)
        verification = st.selectbox("Request verification status", ["Pending", "Verified by care team"])
        st.caption("This is a demo status only. The app does not verify requests; select Verified only after out-of-app care-team verification.")
        submitted = st.form_submit_button("Find Potential Donors", type="primary", use_container_width=True)

    if submitted:
        if not request_id.strip():
            st.error("Enter a request ID.")
        elif request_id.strip().casefold() in [saved.casefold() for saved in st.session_state.request_ids]:
            st.error("That request ID has already been used in this session. Enter a unique ID for a clear audit trail.")
        elif not hospital.strip():
            st.error("Enter a hospital or area.")
        elif verification != "Verified by care team":
            st.error("Care team verification is required before donor coordination.")
        else:
            st.session_state.request_key = uuid.uuid4().hex[:8]
            st.session_state.request = {
                "id": request_id.strip(), "group": group, "units": int(units),
                "hospital": hospital.strip(), "urgency": urgency,
                "deadline": int(deadline),
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            st.session_state.request_ids.append(request_id.strip())
            st.session_state.screening_intake = {}
            for donor in st.session_state.donors:
                donor["response"] = "Not contacted"
            add_audit(
                f"Request {request_id.strip()} created; demo verification set to Verified "
                "(care-team verification is not performed by this app)"
            )
            st.session_state.page = pages[1]
            st.rerun()

elif st.session_state.page == pages[1]:
    request = st.session_state.request
    if not request:
        st.info("Create and verify an emergency request first.")
    else:
        st.subheader("Prioritized potential donors")
        st.caption(
            f"{request['id']} · {request['group']} · {request['units']} units · "
            f"{request['hospital']} · {request['urgency']} · needed within {request['deadline']} min"
        )
        st.caption(
            "Demo distances and response estimates are fictional; they are not calculated "
            "from this hospital, live routes, or promises. Group screening is simplified "
            "and must be verified by a blood bank."
        )
        st.info(
            "Demo only: donor records are fictional, and this app does not send messages. "
            "Mark contacted only records a simulated contact. In real use, the authorized "
            "care team would contact verified candidates through an approved channel."
        )
        candidates = [
            donor for donor in st.session_state.donors
            if donor["group"] in COMPATIBLE[request["group"]]
            and donor["availability"] != "Unavailable"
            and donor["response"] not in ("Accepted", "No Response", "Declined", "Unavailable")
        ]
        ranked = sorted(
            [(rank_candidate(donor, request, active_weights), donor) for donor in candidates],
            key=lambda row: (-row[0][0], row[1]["id"]),
        )
        st.caption(f"{len(ranked)} potential candidates after prototype screening")
        if not ranked:
            st.info("No candidates remain. Confirm details with a blood bank and coordinate through the care team.")
        for position, ((value, why, breakdown), donor) in enumerate(ranked, 1):
            with st.container(border=True):
                left, middle, right = st.columns([2, 2, 1])
                left.markdown(f"**#{position} · {donor['id']}**  \n{donor['group']} blood group")
                middle.markdown(
                    f"{donor['km']:.1f} km · ~{donor['minutes']} min response  \n"
                    f"`{donor['availability']}`"
                )
                right.metric("Priority score", f"{value}/100")
                st.caption(why)
                st.caption(breakdown)
                if donor["response"] == "Contacted":
                    st.caption("Contact request recorded (simulated; no message sent)")
                if donor["response"] == "Not contacted" and st.button(
                    "Simulate contact", key=f"contact_{st.session_state.request_key}_{donor['id']}"
                ):
                    donor["response"] = "Contacted"
                    add_audit(
                        f"Simulated contact request recorded for potential donor {donor['id']} "
                        f"on request {request['id']}; no message sent"
                    )
                    st.rerun()

elif st.session_state.page == pages[2]:
    request = st.session_state.request
    if not request:
        st.info("Create and verify an emergency request first.")
    else:
        st.subheader("Live request status")
        remaining = [
            donor for donor in st.session_state.donors
            if donor["group"] in COMPATIBLE[request["group"]]
            and donor["availability"] != "Unavailable"
            and donor["response"] in ("Not contacted", "Contacted")
        ]
        ranked = sorted(
            [(rank_candidate(donor, request, active_weights), donor) for donor in remaining],
            key=lambda row: (-row[0][0], row[1]["id"]),
        )
        accepted_count = sum(donor["response"] == "Accepted" for donor in st.session_state.donors)
        secured_count = min(accepted_count, request["units"])
        a, b, c = st.columns(3)
        a.metric("Potentially secured", f"{secured_count} / {request['units']} units")
        b.metric("Remaining candidates", len(ranked))
        c.metric("Request", request["id"])
        st.progress(secured_count / request["units"])
        if accepted_count > request["units"]:
            st.caption(f"{accepted_count} donors accepted; the request is capped at {request['units']} units.")
        if secured_count >= request["units"]:
            st.success("Requested unit count is potentially secured. Confirm directly with the care team / blood bank.")
        elif ranked:
            value, why, _ = ranked[0][0]
            st.info(f"Next recommended candidate: {ranked[0][1]['id']} · {value}/100 · {why}")
        else:
            st.info("No remaining candidate is available in this prototype list.")

        st.markdown("**Update contacted donor responses**")
        st.caption("Responses are entered manually for this demo; no donor is notified by the app.")
        contacted = [d for d in st.session_state.donors if d["response"] != "Not contacted"]
        if not contacted:
            st.caption("Use Simulate contact on the Prioritized Donors screen to add a demo response here.")
        for donor in contacted:
            x, y, z = st.columns([2, 2, 2])
            x.write(f"**{donor['id']}** · {donor['group']}")
            y.write(donor["response"])
            key = f"status_{st.session_state.request_key}_{donor['id']}"
            selected = z.selectbox(
                "Response", RESPONSE_STATES,
                index=RESPONSE_STATES.index(donor["response"]), key=key,
                label_visibility="collapsed",
            )
            if selected != donor["response"]:
                old = donor["response"]
                donor["response"] = selected
                accepted_count = sum(d["response"] == "Accepted" for d in st.session_state.donors)
                secured_count = min(accepted_count, request["units"])
                add_audit(f"Donor {donor['id']} responded {selected.lower()} for request {request['id']}")
                add_audit(
                    f"Request {request['id']} status updated: "
                    f"{secured_count} of {request['units']} units potentially secured"
                )
                st.rerun()

elif st.session_state.page == pages[3]:
    request = st.session_state.request
    st.subheader("Donor self-entry")
    if not request:
        st.info("Create and verify an emergency request first.")
    else:
        st.caption(f"For request {request['id']}")
        st.info(
            "Donors enter their own details here. Entries stay in this active app session, "
            "are not shown in ranked results, and are not written to the audit log. "
            "This prototype has no sign-in or identity verification."
        )
        st.caption(
            "Self-entry is not medical clearance and does not add a donor to the ranked list. "
            "Authorized blood-bank staff must verify identity, measurements, blood group, and "
            "final eligibility. This prototype applies no health thresholds."
        )
        with st.form(f"donor_self_entry_{st.session_state.request_key}"):
            st.markdown("#### Donor details")
            donor_name = st.text_input("Name", placeholder="Enter your name")
            st.markdown("#### Age")
            age_text = st.text_input("Age in years (18 or older)", placeholder="Enter age")
            st.markdown("#### Weight")
            weight_text = st.text_input("Weight in kg", placeholder="Enter weight")
            st.markdown("#### Gender")
            gender = st.selectbox(
                "Gender", ["Prefer not to say", "Woman", "Man", "Another identity"]
            )
            st.markdown("#### Hemoglobin")
            hemoglobin_text = st.text_input(
                "Hemoglobin in g/dL (optional)", placeholder="If known"
            )
            donor_confirmed = st.checkbox("I am the donor and confirm these are my own details")
            submitted_intake = st.form_submit_button("Save donor details", type="primary")

        if submitted_intake:
            error = None
            if not donor_name.strip():
                error = "Enter your name."
            elif not age_text.strip().isdigit() or not 18 <= int(age_text.strip()) <= 120:
                error = "Age must be a whole number from 18 to 120."
            try:
                weight = float(weight_text.strip())
                if weight <= 0:
                    raise ValueError
            except ValueError:
                error = error or "Enter a weight greater than 0 kg."
            hemoglobin = None
            if hemoglobin_text.strip():
                try:
                    hemoglobin = float(hemoglobin_text.strip())
                    if hemoglobin <= 0:
                        raise ValueError
                except ValueError:
                    error = error or "Enter a positive hemoglobin value, or leave it blank."
            if not donor_confirmed:
                error = error or "Confirm that you are entering your own details."

            if error:
                st.error(error)
            else:
                donor_id = f"DNR-{uuid.uuid4().hex[:6].upper()}"
                intake_key = f"{st.session_state.request_key}:{donor_id}"
                st.session_state.screening_intake[intake_key] = {
                    "name": donor_name.strip(),
                    "age": int(age_text.strip()),
                    "weight_kg": weight,
                    "gender": gender,
                    "hemoglobin_g_dl": hemoglobin,
                    "review_status": "Blood-bank review pending",
                    "review_recorded_at": None,
                }
                add_audit(
                    f"Donor self-entry recorded as {donor_id} for request {request['id']}; "
                    "Blood-bank review pending"
                )
                st.rerun()

        saved_intakes = [
            (key, value)
            for key, value in st.session_state.screening_intake.items()
            if key.startswith(f"{st.session_state.request_key}:")
        ]
        if saved_intakes:
            st.markdown("#### Donor entries for this request")
        for intake_key, intake in saved_intakes:
            donor_id = intake_key.rsplit(":", 1)[-1]
            with st.container(border=True):
                st.markdown(f"**{donor_id} · {intake['name']}**")
                hb = intake["hemoglobin_g_dl"]
                hb_text = f"{hb:g} g/dL" if hb is not None else "not provided"
                st.caption(
                    f"Age {intake['age']} · Weight {intake['weight_kg']:g} kg · "
                    f"Gender: {intake['gender']} · Hemoglobin: {hb_text}"
                )
                if intake["review_status"] == "Blood-bank review pending":
                    st.warning("Blood-bank review pending · no eligibility decision made.")
                    if st.button("Record demo review step", key=f"review_{intake_key}"):
                        intake["review_status"] = "Review step recorded (demo only)"
                        intake["review_recorded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        add_audit(
                            f"Demo review step recorded for {donor_id}; no eligibility decision made"
                        )
                        st.rerun()
                else:
                    st.success(intake["review_status"])

else:
    st.subheader("Request history / audit")
    if st.session_state.request:
        request = st.session_state.request
        st.markdown(
            f"**Current request:** {request['id']} · {request['created']} · "
            f"{request['urgency']} · {request['hospital']}"
        )
    else:
        st.info("No request has been created in this session yet.")
    if st.session_state.audit:
        for timestamp, message in st.session_state.audit:
            st.text(f"{timestamp}  {message}")
    else:
        st.caption("Audit events appear here as the demo progresses.")

st.divider()
st.caption(
    "Preloaded ranking candidates are fictional · donor self-entry stays in this session only · "
    "final eligibility and blood verification remain with authorized healthcare providers / blood banks."
)
