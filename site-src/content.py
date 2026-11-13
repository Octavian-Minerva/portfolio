# ALL website copy lives in this one file. Edit text here, then rebuild:
#     .venv/bin/python build_site.py            (warns loudly while any placeholder remains)
#     .venv/bin/python build_site.py --release  (refuses to build while any placeholder remains)
#
# How to fill a placeholder: replace the whole  RyanWrites(...)  call with your text in quotes.
#     PURPOSE = RyanWrites("Purpose statement ...", "30 to 50 words")
# becomes
#     PURPOSE = "I want to ..."
# Long text: separate paragraphs with a blank line inside triple quotes ("""...""").
# Optional items say so; set them to None to remove them from the page.
#
# Rules: Australian English. No em dashes (the build stops if it finds one); en dashes only in ranges.
# Straight quotes and apostrophes are fine: the build turns them into curly ones.


# DRAFTS (13 Nov 2026): Ryan asked the assistant to draft all copy for a feedback preview.
# 14 Nov 2026: Ryan reviewed and accepted all drafts; the Draft(...) markers were removed.
# Every assistant-drafted item is wrapped in Draft(...). It renders normally, but the build counts drafts
# and "--release" refuses to build while any remain. To accept or replace one, swap ("...") for
# your own "..." (keep or rewrite the words). The tracker is ../DRAFT-TRACKER.md.

DRAFTS = []

class DraftStr(str):
    pass

class DraftList(list):
    pass

def Draft(x):
    d = DraftList(x) if isinstance(x, list) else DraftStr(x)
    DRAFTS.append(d)
    return d


class RyanWrites:
    """A visible, dashed 'still to write' box. The build counts these and warns until none remain."""
    def __init__(self, what, length='', who='Ryan writes'):
        self.what, self.length, self.who = what, length, who


# ---------------------------------------------------------------- site settings
NAME = "Ryan O'Grady"
SITE_URL = "https://ryanoogrady.netlify.app"            # e.g. "https://ryan-ogrady.netlify.app" once the site has an address (used for link previews)
PAGE_TITLE = "Ryan O'Grady | Bachelor of Arts (Politics, Power and Technology), Swinburne"
META_DESCRIPTION = "Portfolio of Ryan O'Grady, Bachelor of Arts student majoring in Politics, Power and Technology at Swinburne University of Technology."
YEAR = "2026"
LAST_UPDATED = "November 2026"   # shown in the footer; change it whenever the site is updated

NAV = [("About", "about"), ("Work", "work"), ("Skills", "skills"), ("Experience", "experience"), ("Contact", "contact")]

# ---------------------------------------------------------------- 1. hero
HERO_KICKER = "Bachelor of Arts (Politics, Power and Technology) · Swinburne"
DESCRIPTOR = ("Politics student interested in power, the organisation of work and the social consequences of automation.")
# Photo: put the file in site-src/img-src/ and set PHOTO = ("your-photo.jpg", "Alt text describing the photo").
# Portrait, 4:5, at least 900 px wide. Until then a neutral monogram shows inside a placeholder box.
PHOTO = ("ryan-portrait.jpg", "Ryan sitting on a rocky summit above a layer of cloud, smiling.")   # cropped from Ryan's photo; location metadata stripped

# ---------------------------------------------------------------- 2. about
ABOUT_HEAD = "About"
PURPOSE = ("I am most interested in studying how power is held and reproduced over time, particularly through the organisation of work, and how increasing automation may redistribute it. I am particularly drawn to problems that require sustained analysis.")
ABOUT_BIO = ("Since I was eighteen I have worked in street fundraising, hospitality, COVID-19 pathology collection (including hotel quarantine) and, for nearly four years, customer service and administration at a self-storage business. Each of these workplaces organised labour differently, and observing them first-hand has shaped my interest in how work is structured and whom it serves. Travel has also shaped my thinking, particularly about how differently inequality is experienced from place to place. I returned to study in 2025 through a university pathway diploma.")
INTERESTS_LABEL = "Areas of interest"
INTERESTS = (["Who holds power, how is it maintained over time, and why do those without it so often accept arrangements that work against them?", "How would power be distributed in a society whose economy no longer needs most people's labour?", "Why do people with shared material interests come to see themselves as opponents, divided by race or income, while the wealthiest go largely unchallenged?"])
EXPLORING_LABEL = "At present (November 2026)"
EXPLORING = (["Halfway through a Bachelor of Arts (Politics, Power and Technology)", "Beginning work adapting an AI agent platform to client businesses", "Developing an interest in scientific management and its parallels in automation"])

# ---------------------------------------------------------------- 3. featured project (also feeds the detail page)
FEATURED = {
    "kicker": "Group campaign strategy",
    "title": "Not Our Game",
    "unit_code": "ART20003",
    "unit_name": "Skills and Strategies for Social Change",
    "year": "2026",
    "type": "Group campaign strategy",
    "role": "The campaign website, and the messaging and artefact sections of the report",
    "live_url": "https://not-our-game.netlify.app",
    "live_label": "Visit the live campaign site",
    "detail_label": "Read about the project",
    "blurb": ("Not Our Game is a campaign strategy addressing domestic and family violence associated with State of Origin, during which recorded domestic assaults in New South Wales rise by 40.7%. The campaign asks the NRL and its broadcasters to include prevention messaging and support-service information in the 2027 Origin broadcasts. I developed the campaign website and wrote the report's messaging and artefact sections."),
    # Screenshots of the campaign site (sources in site-src/img-src/). First two show on the home page.
    "shots": [
        ("campaign-home-desktop.png", "desktop", "Home page, desktop",
         "Home page of the Not Our Game campaign website on a desktop screen, headed 'Love the game. Respect everyone.' over an AI-generated image of four fans watching a game at home, with support phone numbers above."),
        ("campaign-mates-phone.png", "phone", "For mates page, phone",
         "The For mates page on a phone, headed 'Look out for your mates', with a fixed bar of support numbers and a quick exit button along the bottom."),
        ("campaign-request-desktop.png", "desktop", "Our request page, desktop",
         "The Our request page on a desktop screen, headed 'Put family violence support in every Origin broadcast', over a darkened lounge room with a game on the television."),
        ("campaign-help-desktop.png", "desktop", "Get help page, desktop",
         "The Get help page on a desktop screen, headed 'You deserve to be safe', with three large call buttons for support services."),
    ],
}

# Detail page (not-our-game.html). Section headings are labels; the prose is yours.
FEATURED_PAGE = {
    "overview_head": "Overview",
    "overview": ("Not Our Game was a group project for ART20003 Skills and Strategies for Social Change. It responds to evidence that recorded domestic assaults in New South Wales rise by 40.7% on State of Origin nights. Rather than positioning fans as the problem, the campaign addresses three audiences: the NRL and its broadcasters, who are able to make the change; fans, particularly men watching in groups; and people experiencing violence, together with those supporting them and men concerned about their own behaviour. Its central request is that prevention messaging and support-service information be included in the 2027 Origin broadcasts. My contribution was the campaign website and the report's messaging and artefact sections."),
    "website_head": "The website",
    "website": ("The website functions as the campaign's hub. Each social media post links to it, as does the QR code displayed with support information during broadcasts, and its pages are organised around the three audiences. A quick-exit button and support numbers appear on every page, including on mobile, following research on domestic violence websites that recommends a clearly labelled exit that remains visible."),
    "messaging_head": "The messaging section",
    "messaging": ("The central message, \"Love the Game, Respect Everyone\", separates the sport from the violence, allowing supporters to reject violence without being cast as critics of the game. Fan-facing material avoids leading with assault statistics, since publicising the prevalence of a harmful behaviour can reinforce it. It instead suggests low-key forms of bystander action, such as checking in with a friend the following day."),
    "tiles_head": "Social posts",
}
# Social tiles you made: (file in site-src/img-src/, alt text, caption). Leave empty to show a placeholder.
SOCIAL_TILES = []
SOCIAL_TILES_TODO = None  # dropped 12 Nov: the campaign tiles were groupmates' work, not Ryan's

# ---------------------------------------------------------------- 4. selected work
# One dict per card. Reorder, delete or add cards freely. Titles are exact titles from the submitted files.
# "read": optional {"src": file in ../essays-src/ (.docx preferred, else .pdf), "page": output file, "fixes": [(old, new)] to match the submitted PDF}.
# "pdf": optional (source file in ../essays-src/, public file name); adds a "Read the full essay (PDF)" button.
# "thumb": (file in site-src/img-src/, alt text) shown at the top of the card, cropped to 4:3.
# "links": optional [(label, href, external)] buttons.
# "slides": optional images (file in site-src/img-src/, alt text); a card with slides spans the full width.
WORK_HEAD = "Selected work"
WORK = [
    {
        "title": "Technological Progress and Power",
        "read": {"src": "phi10009.pdf", "page": "essay-technological-progress-and-power.html"},   # reading page built from the submitted file; checked word for word against the PDF
        "pdf": ("phi10009.pdf", "ryan-ogrady-technological-progress-and-power.pdf"),
        "thumb": ("essay-phi10009-p1.png", "First page of the essay, headed Technological Progress and Power."),
        "type": "Major essay",
        "unit_code": "PHI10009", "unit_name": "Introduction to Power in the Digital Age", "year": "2026",
        "topic": ("Does technological progress distribute power or concentrate it?"),
        "tags": ["Power", "Automation", "Platform monopolies"],
        "blurb": ("Whether progress distributes or concentrates power depends less on the technology than on the social and institutional frameworks into which it emerges. Drawing on Lukes and Clegg, I trace how platform monopolies and a research agenda tilted towards labour-replacing automation concentrate power, and how policy intervention could distribute its gains more widely."),
    },
    {
        "title": "Deterring Arrival: Asylum Policy in Australia and the United States",
        "read": {"src": "soc20013.docx", "page": "essay-deterring-arrival.html"},   # reading page built from the submitted file; checked word for word against the PDF
        "pdf": ("soc20013.pdf", "ryan-ogrady-deterring-arrival-asylum-policy.pdf"),
        "thumb": ("essay-soc20013-p1.png", "First page of the essay, headed Deterring Arrival: Asylum Policy in Australia and the United States."),
        "type": "Major essay",
        "unit_code": "SOC20013", "unit_name": "Race, Ethnicity and Migration", "year": "2026",
        "topic": ("How do Australia and the United States keep asylum seekers from reaching the territory where they could claim protection?"),
        "tags": ["Asylum policy", "Migration", "Comparative policy"],
        "blurb": ("Both countries have constructed similar architectures of deterrence in response to comparable moral panics. Geography explains most differences in form, offshore detention in Australia and land buffers in the United States. The more significant contrast lies in durability, with Australia's bipartisan consensus differing from US policy, which shifts between administrations and is contested in the courts."),
    },
    {
        "title": "Insulating News from the Market and the State",
        "read": {"src": "his10006-final.docx", "page": "essay-insulating-news.html", "fixes": [("Funding has been a second lever; Dodd (2020)", "Funding has been a second lever whereby the government has applied pressure. Dodd (2020)")]},   # reading page built from the submitted file; checked word for word against the PDF
        "pdf": ("his10006.pdf", "ryan-ogrady-insulating-news.pdf"),
        "thumb": ("essay-his10006-p1.png", "First page of the essay, headed Insulating News from the Market and the State."),
        "type": "Major essay",
        "unit_code": "HIS10006", "unit_name": "Propaganda: A History of Media and Politics", "year": "2026",
        "topic": ("Should news and information, as public goods, be quarantined from the commercial market, and would that make them independent?"),
        "tags": ["Media policy", "Public goods", "Public broadcasting"],
        "blurb": ("I argue that news is only partly a public good, and that quarantining it from the market would not secure its independence. Cases from the Chicago press in 1918 to Poland's public broadcaster in 2021 suggest that removing the market leaves control with the state. News should instead be insulated from both, through regulatory protection and secure funding."),
    },
    {
        "title": "Migrant Settlement and Gentrification in Footscray",
        "pdf": ("soc20013-presentation.pdf", "ryan-ogrady-footscray-presentation-slides.pdf"), "pdf_label": "View the slides",
        "thumb_fit": "contain",   # 16:9 slide: show it whole rather than cropping the title
        "thumb": ("footscray-final-p1.png", "Title slide, 'Migrant Settlement and Gentrification in Footscray', over a photo of apartment towers beside the river at Footscray."),
        "type": "Tutorial presentation",
        "unit_code": "SOC20013", "unit_name": "Race, Ethnicity and Migration", "year": "2026",
        "topic": ("What happens to a migrant gateway suburb when urban renewal and gentrification arrive?"),
        "tags": ["Migration", "Housing", "Urban renewal", "Melbourne"],
        "blurb": ("Footscray has served as a gateway suburb for successive waves of migrants, but government-led renewal and rents rising faster than in the outer west are eroding that role; the Ethiopian and Somali communities now live mostly in Wyndham, Brimbank and Hume. I recommend affordable housing beyond key workers, secure leases for migrant traders and settlement services where new arrivals now live."),
    },
    {
        "title": "Three vantage points of the Cold War: Hobsbawm, Gaddis, and Jervis",
        "read": {"src": "his10003.docx", "page": "essay-cold-war.html"},   # reading page built from the submitted file; checked word for word against the PDF
        "pdf": ("his10003.pdf", "ryan-ogrady-cold-war-three-vantage-points.pdf"),
        "thumb": ("essay-his10003-p1.png", "First page of the essay, headed Three vantage points of the Cold War: Hobsbawm, Gaddis, and Jervis."),
        "type": "Term essay",
        "unit_code": "HIS10003", "unit_name": "Global History", "year": "2026",
        "topic": ("Why do three major accounts of the Cold War, written before, shortly after and a decade after the Soviet collapse, reach different conclusions?"),
        "tags": ["Cold War", "International relations", "Historiography"],
        "blurb": ("The period in which Hobsbawm, Gaddis and Jervis each wrote, the information available to them and their theoretical frameworks all shaped their accounts. They largely agree on the observable features of the conflict, diverge on what drove the superpower rivalry, and converge, by different routes, on the Soviet role in ending it."),
    },
    {
        "title": "Not Our Game",
        "thumb": ("campaign-home-desktop.png", "Home page of the Not Our Game campaign website, headed 'Love the game. Respect everyone.' over an AI-generated image of four fans watching a game at home."),
        "type": "Group campaign strategy",
        "unit_code": "ART20003", "unit_name": "Skills and Strategies for Social Change", "year": "2026",
        "topic": ("How might State of Origin broadcasts be used to prevent domestic and family violence without positioning fans as the problem?"),
        "tags": ["Social campaign", "Domestic and family violence", "Messaging"],
        "blurb": FEATURED["blurb"],   # the same Draft as the project page summary
        "links": [("Read about the project", "not-our-game.html", False), ("Visit the live campaign site", "https://not-our-game.netlify.app", True)],
    },
]

# ---------------------------------------------------------------- 5. skills audit and reflection (marked requirement)
SKILLS_HEAD = "Skills audit and reflection"
SKILLS_KICKER = "Skills developed in ART20003 and beyond"
# Skill areas: each card has a heading, a short paragraph of evidence and a few labels.
SKILL_GROUPS = [
    {
        "title": "Research and argument",
        "text": ("Much of my academic writing is comparative, whether across historians' accounts of the Cold War, national approaches to asylum, or competing positions on how news should be funded. The most significant development in my writing this year followed tutor feedback to use sources as evidence, theory or context rather than as authority for claims already made. Integrating sources in this way has strengthened the structure of my arguments."),
        "tags": (["Comparative analysis", "Historiography", "Policy analysis", "Academic writing"]),
    },
    {
        "title": "Building systems with AI",
        "text": ("Although I have no formal training in programming, I have found that most of the work of directing AI lies in specification. A task must be divided into components, each with an explicit definition of completion expressed as conditions that can be verified as true or false, and the system is then refined until those conditions hold. Since June 2026 I have applied this approach as a contract developer on an AI agent platform, where I have also learnt that a tool's design largely determines whether people use more than its most basic functions."),
        "tags": (["Specification and acceptance criteria", "Systems design", "Interface design", "Iterative testing"]),
    },
    {
        "title": "Working with people",
        "text": ("Nearly four years in customer service and administration at a self-storage business has involved sales across phone, email and in-person channels, managing overdue accounts and resolving problems on site, as well as covering the assistant manager's shifts while that position was vacant. Earlier roles in street fundraising and COVID-19 pathology collection developed my confidence in communicating with the public and my ability to work within strict clinical protocols."),
        "tags": (["Customer service", "Account management", "Working to protocol", "Public speaking"]),
    },
]
REFLECTION_HEAD = "Reflection: the Not Our Game campaign"
SKILLS_AUDIT = ("""In developing the Not Our Game campaign strategy, I learnt most from its messaging. The most striking available figure was the 40.7% rise in domestic assaults on Origin nights, yet the research advised against leading with it. Publicising the prevalence of a harmful behaviour can normalise it, and a campaign that treats every fan as part of the problem risks alienating the audience it most needs to reach. The fan-facing material therefore begins from a view most men already hold, that disrespect is unacceptable, and suggests practical ways to act on it.

The experience has made me more attentive to how framing shapes the reception of an argument, independently of its accuracy. As the strategy was developed in a group, my sections also needed to align with the work of other members. In future research and writing, I intend to test my assumptions about framing against the available evidence.""")
SKILLS_LIST_LABEL = "Skills"
SKILLS_LIST = None   # replaced by the tags on each skill area (13 Nov)

# ---------------------------------------------------------------- 6. experience and involvement
EXPERIENCE_HEAD = "Experience and involvement"
EARLIER_HEAD = "Earlier work"
EXPERIENCE = [
    {
        "role": ("AI systems developer"),
        "org": "AI agent platform, contract",
        "dates": "June 2026 to present",
        "text": ("Contributions include an independent review agent that checks proposed code changes against the existing codebase, suggests fixes and re-reviews them until they pass; a 'factory floor' view that shows the status of every agent at a glance, with an assistant agent that summarises activity on request; and an orchestration mode that divides a plan into tickets for separate agents and assembles their output. Each feature was tested in a separate development deployment. I am now beginning work adapting the platform to the needs of client businesses."),
    },
    {
        "role": "Arx, personal project",
        "org": "Self-built study and work planner",
        "dates": "2026",
        "text": ("A self-built study planner that synchronised university deadlines from Canvas and scheduled work backwards from each due date; the project that led to my development work."),
    },
    {
        "role": "Customer service and administration",
        "org": "Self-storage business, casual",
        "dates": "December 2022 to present",
        "text": ("Sales across phone, email and in-person channels, management of overdue accounts and resolution of on-site issues, including covering the assistant manager's shifts while the position was vacant."),
    },
    {
        "role": "COVID-19 pathology collection",
        "earlier": True,   # listed under "Earlier work"
        "org": "Pathology provider: testing sites, then hotel quarantine",
        "dates": "2021 to 2022",
        "text": None,
    },
    {
        "role": "Team member",
        "earlier": True,
        "org": "Restaurant chain, Melbourne CBD",
        "dates": "2018 to 2021",
        "text": None,
    },
    {
        "role": "Player, left back",
        "org": "Swinburne Football (Soccer) Club, Metro League 5",
        "dates": "2026",
        "text": None,
    },
]

EDUCATION_HEAD = "Education"
EDUCATION = [   # same fields as EXPERIENCE
    {
        "role": "Bachelor of Arts (Politics, Power and Technology)",
        "org": "Swinburne University of Technology",
        "dates": "2026 to present",
        "text": None,
    },
    {
        "role": "Diploma of Arts and Communication (UniLink)",   # Ryan to check the exact name on his transcript
        "org": "Swinburne University of Technology; credited as the first year of the BA",
        "dates": "October 2025 to June 2026",
        "text": None,
    },
]

# ---------------------------------------------------------------- 7. contact
CONTACT_HEAD = "Contact"
CONTACT_LINE = None   # dropped 13 Nov (Ryan)
EMAIL = [("Personal", "ryan.ogrady77@gmail.com"), ("University", "103024469@student.swin.edu.au")]   # Ryan, 14 Nov

# ---------------------------------------------------------------- 8. footer
AI_NOTE = None   # dropped 12 Nov: Ryan will put an AI statement in the Canvas submission instead
COLOPHON = ("This site is a static build generated from a small Python script, with no frameworks, trackers or third-party requests. It follows your system's light or dark setting, can be printed as a plain document, and has been checked for keyboard access and WCAG AA colour contrast.")
CREDITS = [
    "Set in Newsreader and Source Sans 3, both under the SIL Open Font License (fonts/OFL-*.txt).",
    'Footscray title slide photo: "Saltwater River Crossing Site and Footscray Wharves Precinct" by Sgroey, CC BY-SA 4.0, via Wikimedia Commons.',
    "Campaign screenshots include AI-generated images made for the Not Our Game campaign; they do not show real people.",
]
CREDIT_LINKS = {  # text inside CREDITS that becomes a link
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "Wikimedia Commons": "https://commons.wikimedia.org/wiki/File:Saltwater_River_Crossing_Site_and_Footscray_Wharves_Precinct.jpg",
}

NOT_FOUND = ("Page not found", "That page does not exist. Go back to the home page.")
